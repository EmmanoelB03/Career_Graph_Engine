"""
FASE 1 — Ingestão de dados do mercado
Consome a API da Adzuna (US) buscando especificamente o cargo-alvo,
extraindo até 2000 vagas limpas daquele cargo.
"""

import requests
import json
import re
import time
from collections import Counter
from pathlib import Path

# ── Adzuna credentials ────────────────────────────────────
ADZUNA_APP_ID    = "0b6a6595"
ADZUNA_APP_KEY   = "475e0ab9354ea1fcd65e68fd85e274be"
ADZUNA_BASE      = "https://api.adzuna.com/v1/api/jobs/us/search"
RESULTS_PER_PAGE = 50
MAX_JOBS         = 2000

# Mapa do cargo canônico para a query de busca na Adzuna
ROLE_TO_QUERY = {
    "Backend Engineer":    "backend engineer",
    "Cloud Architect":     "cloud architect",
    "Data Engineer":       "data engineer",
    "Data Scientist":      "data scientist",
    "DevOps Engineer":     "devops engineer",
    "Frontend Engineer":   "frontend engineer",
    "Full Stack Engineer": "full stack engineer",
    "ML Engineer":         "machine learning engineer",
}

# ── Normalização semântica ────────────────────────────────
def _canonical(s: str) -> str:
    return re.sub(r"[\.\-\s\/]", "", s.lower())

SKILL_ALIASES = {
    "js": "javascript", "javascript": "javascript",
    "reactjs": "react", "react.js": "react", "reactjsx": "react",
    "vuejs": "vue", "vue.js": "vue",
    "angularjs": "angular",
    "nextjs": "next.js", "next.js": "next.js",
    "nodejs": "node.js", "node.js": "node.js", "node": "node.js",
    "expressjs": "express", "express.js": "express",
    "ts": "typescript",
    "py": "python",
    "ml": "machine learning", "dl": "deep learning",
    "tf": "tensorflow", "tensorflow2": "tensorflow",
    "sklearn": "scikit-learn", "scikitlearn": "scikit-learn",
    "gcp": "google cloud", "googlecloud": "google cloud",
    "aws": "aws", "amazonwebservices": "aws",
    "azurecloud": "azure",
    "k8s": "kubernetes",
    "cicd": "ci cd", "ci/cd": "ci cd",
    "githubactions": "github actions",
    "postgres": "postgresql", "postgresql": "postgresql",
    "mongo": "mongodb", "mongodb": "mongodb",
    "elasticsearch": "elasticsearch", "elastic": "elasticsearch",
    "powerbi": "power bi",
}

KNOWN_SKILLS = {
    "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
    "scala", "kotlin", "ruby", "php", "swift", "r",
    "react", "vue", "angular", "next.js", "html", "css", "tailwind", "express",
    "node.js", "django", "fastapi", "flask", "spring", "rails", "graphql", "rest",
    "pandas", "numpy", "spark", "hadoop", "dbt", "airflow", "kafka", "flink",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "nlp", "llm", "data engineering", "data science", "analytics",
    "aws", "google cloud", "azure", "docker", "kubernetes", "terraform",
    "ci cd", "github actions", "jenkins", "linux",
    "git", "jira", "agile", "scrum",
    "tableau", "power bi", "streamlit", "plotly", "matplotlib",
    "networkx", "neo4j", "graph databases",
}

_CANONICAL_MAP = {_canonical(s): s for s in KNOWN_SKILLS}
for alias, canon in SKILL_ALIASES.items():
    _CANONICAL_MAP[_canonical(alias)] = canon


def normalize_skill(raw: str) -> str | None:
    raw = raw.lower().strip()
    raw = re.sub(r"[^\w\s\.\+\#]", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if raw in KNOWN_SKILLS:
        return raw
    if raw in SKILL_ALIASES:
        return SKILL_ALIASES[raw]
    canon = _canonical(raw)
    if canon in _CANONICAL_MAP:
        result = _CANONICAL_MAP[canon]
        return result if result in KNOWN_SKILLS else None
    return None


def strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    return re.sub(r'\s+', ' ', text).strip()


def extract_skills_from_text(text: str) -> list[str]:
    text = strip_html(text)
    text_lower = text.lower()
    found = set()
    for skill in KNOWN_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)
    tokens = re.findall(r'[\w\.\+\#\-]+', text_lower)
    for token in tokens:
        result = normalize_skill(token)
        if result:
            found.add(result)
    return sorted(found)


def fetch_jobs_from_adzuna(target_role: str) -> list[dict]:
    query = ROLE_TO_QUERY.get(target_role)
    if not query:
        raise ValueError(f"Cargo '{target_role}' não encontrado em ROLE_TO_QUERY.")

    all_jobs = []
    seen_ids = set()
    page = 1

    print(f"  Buscando '{query}' na Adzuna US...")

    while len(all_jobs) < MAX_JOBS:
        try:
            resp = requests.get(
                f"{ADZUNA_BASE}/{page}",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_APP_KEY,
                    "results_per_page": RESULTS_PER_PAGE,
                    "what": query,
                    "content-type": "application/json",
                },
                timeout=15
            )

            if resp.status_code != 200:
                print(f"  p{page} HTTP {resp.status_code}")
                break

            data = resp.json()
            jobs = data.get("results", [])
            total_available = data.get("count", 0)

            if not jobs:
                break

            new_jobs = [j for j in jobs if j.get("id") not in seen_ids]
            for j in new_jobs:
                seen_ids.add(j.get("id"))
            all_jobs.extend(new_jobs)

            max_pages = min(
                (total_available // RESULTS_PER_PAGE) + 1,
                (MAX_JOBS // RESULTS_PER_PAGE) + 1
            )

            print(f"  p{page}/{max_pages} — +{len(new_jobs)} vagas (total: {len(all_jobs)}/{min(total_available, MAX_JOBS)})")

            if page >= max_pages or len(jobs) < RESULTS_PER_PAGE:
                break

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"  p{page} Erro: {e}")
            break

    return all_jobs[:MAX_JOBS]


def process_jobs(raw_jobs: list[dict], target_role: str) -> list[dict]:
    processed = []
    skipped = 0

    for job in raw_jobs:
        company = job.get("company", {}).get("display_name", "Unknown")
        desc    = job.get("description", "")

        text_skills = extract_skills_from_text(desc) if desc else []
        skills = sorted(set(s for s in text_skills if s in KNOWN_SKILLS))

        if not skills:
            skipped += 1
            continue

        processed.append({
            "id":             job.get("id", 0),
            "title":          target_role,
            "original_title": job.get("title", ""),
            "company":        company,
            "skills":         skills,
            "skill_count":    len(skills),
        })

    print(f"  → {skipped} vagas sem skills identificadas (descartadas)")
    return processed


def aggregate_market_data(jobs: list[dict], target_role: str) -> dict:
    skill_counter = Counter()
    role_counter  = Counter()

    for job in jobs:
        for skill in job["skills"]:
            skill_counter[skill] += 1
            role_counter[skill]  += 1

    total = sum(role_counter.values())
    role_profile = {
        skill: round(count / total, 3)
        for skill, count in role_counter.most_common(15)
    }

    return {
        "total_jobs":      len(jobs),
        "target_role":     target_role,
        "skill_frequency": dict(skill_counter.most_common(50)),
        "role_profiles":   {target_role: role_profile},
        "jobs":            jobs,
        "source":          "adzuna",
    }


def run(target_role: str = "Data Engineer") -> dict:
    print("=" * 55)
    print(f"FASE 1 — Ingestão de Dados do Mercado (Adzuna US)")
    print(f"Cargo-alvo: {target_role}")
    print("=" * 55)

    raw_jobs = fetch_jobs_from_adzuna(target_role)
    print(f"\nProcessando {len(raw_jobs)} vagas brutas...")

    jobs   = process_jobs(raw_jobs, target_role)
    market = aggregate_market_data(jobs, target_role)

    out = Path("data")
    out.mkdir(exist_ok=True)
    with open(out / "market_data.json", "w", encoding="utf-8") as f:
        json.dump(market, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {market['total_jobs']} vagas de {target_role} processadas")
    print(f"✓ {len(market['skill_frequency'])} skills únicas identificadas")
    print(f"✓ Dados salvos em data/market_data.json")
    print(f"\nTop 10 skills mais demandadas em {target_role}:")
    for skill, freq in list(market["skill_frequency"].items())[:10]:
        bar = "█" * min(freq, 30)
        print(f"  {skill:<22} {bar} ({freq})")

    return market


if __name__ == "__main__":
    run()