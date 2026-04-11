"""
FASE 2 — Processamento do Currículo
Usa a Gemini API como parser semântico para extrair skills técnicas
do texto bruto do currículo e retorna um array JSON normalizado.
"""

import json
import re
import os
from pathlib import Path

KNOWN_SKILLS = {
    "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
    "scala", "kotlin", "ruby", "php", "swift", "r",
    "react", "vue", "angular", "next.js", "html", "css", "tailwind",
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

SKILL_ALIASES = {
    "js": "javascript", "ts": "typescript", "py": "python",
    "ml": "machine learning", "dl": "deep learning",
    "k8s": "kubernetes", "tf": "tensorflow",
    "gcp": "google cloud", "aws": "amazon web services",
    "ci/cd": "ci cd", "node": "node.js", "nodejs": "node.js",
    "reactjs": "react", "react.js": "react",
    "vuejs": "vue", "vue.js": "vue",
    "nextjs": "next.js",
    "sklearn": "scikit-learn", "scikitlearn": "scikit-learn",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "cicd": "ci cd",
    "githubactions": "github actions",
    "googlecloud": "google cloud", "gcp": "google cloud",
    "powerbi": "power bi",
}


def _canonical(s: str) -> str:
    return re.sub(r"[\.\-\s\/]", "", s.lower())

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


def parse_with_gemini(resume_text: str, api_key: str) -> list[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""Você é um extrator especializado em habilidades técnicas de currículos de tecnologia.

Sua tarefa é identificar TODAS as tecnologias, linguagens, frameworks, ferramentas, bibliotecas e conceitos técnicos mencionados no currículo abaixo — mesmo que apareçam indiretamente (ex: "trabalhei com contêineres" → docker, "metodologias ágeis" → agile).

REGRAS:
- Seja EXAUSTIVO: prefira extrair a mais do que deixar passar
- Normalize os nomes: "scikit-learn", não "sklearn"; "node.js", não "nodejs"
- Inclua ferramentas de infraestrutura, bancos de dados, cloud, metodologias e conceitos de IA
- Retorne SOMENTE um array JSON em letras minúsculas, sem explicações, sem markdown

Exemplos de como normalizar:
- "Apps Script" → "apps script"
- "PostgreSQL" → "postgresql"
- "SvelteKit" → "sveltekit"
- "RAG" → "rag"
- "MLOps" → "mlops"
- "LangChain" → "langchain"
- "Docker" → "docker"
- "Git" → "git"

CURRÍCULO:
{resume_text}

JSON:"""

        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        skills = json.loads(raw)
        return [s.lower().strip() for s in skills if isinstance(s, str)]
    except Exception as e:
        print(f"  Gemini API erro: {e}")
        return []


def parse_with_regex(resume_text: str) -> list[str]:
    text_lower = resume_text.lower()
    found = set()

    for skill in KNOWN_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)

    for alias in SKILL_ALIASES:
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, text_lower):
            canonical = SKILL_ALIASES[alias]
            if canonical in KNOWN_SKILLS:
                found.add(canonical)

    return sorted(found)


def parse_resume(resume_text: str, api_key: str = None) -> list[str]:
    raw_skills = []

    if api_key:
        print("  Usando Gemini API para parsing semântico...")
        raw_skills = parse_with_gemini(resume_text, api_key)

    if not raw_skills:
        print("  Usando parser de fallback (regex sobre base de skills)...")
        raw_skills = parse_with_regex(resume_text)

    normalized = []
    for s in raw_skills:
        result = normalize_skill(s)
        if result and result not in normalized:
            normalized.append(result)

    return sorted(normalized)


def run(resume_text: str = None, api_key: str = None) -> list[str]:
    print("=" * 55)
    print("FASE 2 — Processamento do Currículo")
    print("=" * 55)

    if resume_text is None:
        resume_text = """
        João Silva — Engenheiro de Dados Sênior
        
        Experiência:
        - 5 anos desenvolvendo pipelines de dados com Python e Apache Airflow
        - Modelagem e otimização de queries SQL em PostgreSQL e MySQL
        - Construção de data lakes na AWS (S3, Glue, Athena, Redshift)
        - Orquestração de containers com Docker e Kubernetes
        - Experiência com Apache Spark para processamento distribuído
        - Transformações com dbt e ingestão via Kafka
        - Versionamento com Git e CI/CD via GitHub Actions
        - Pandas e NumPy para manipulação de dados
        - Visualizações com Matplotlib e Plotly
        - Metodologias ágeis (Scrum)
        
        Tecnologias: Python, SQL, Spark, Airflow, dbt, Kafka, AWS,
        Docker, Kubernetes, PostgreSQL, Git, Pandas
        """
        print("\nUsando currículo de exemplo para demonstração.")

    print(f"\nTexto do currículo: {len(resume_text)} caracteres")
    print("Extraindo habilidades técnicas...")

    skills = parse_resume(resume_text, api_key)

    out = Path("data")
    out.mkdir(exist_ok=True)
    candidate = {"skills": skills, "skill_count": len(skills), "resume_length": len(resume_text)}
    with open(out / "candidate_profile.json", "w", encoding="utf-8") as f:
        json.dump(candidate, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(skills)} habilidades técnicas extraídas:")
    for i, skill in enumerate(skills, 1):
        print(f"  {i:2}. {skill}")

    print(f"\n✓ Perfil salvo em data/candidate_profile.json")
    return skills


if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    run(api_key=api_key)