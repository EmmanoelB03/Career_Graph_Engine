"""
FASE 3 — Construção do Grafo e Motor de Match
Conecta skills do candidato com perfis de cargo via NetworkX.
Calcula score de aderência e gaps de aprendizado por cargo.
Gera visualização interativa com PyVis.
"""

import json
import math
from pathlib import Path
from collections import defaultdict

import networkx as nx


def load_data() -> tuple[dict, list[str]]:
    market = json.loads(Path("data/market_data.json").read_text())
    candidate = json.loads(Path("data/candidate_profile.json").read_text())
    return market, candidate["skills"]


def build_knowledge_graph(market: dict, candidate_skills: list[str]) -> nx.Graph:
    """
    Constrói o Grafo de Conhecimento com três tipos de nós:
    - CANDIDATE  : nó central do candidato
    - ROLE       : nós de cargo (ex: Data Engineer)
    - SKILL      : nós de habilidade técnica
    
    Arestas:
    - candidate → skill   (habilidades que o candidato possui)
    - role      → skill   (habilidades que o cargo exige)
    - candidate → role    (afinidade calculada — peso = score)
    """
    G = nx.Graph()

    # Nó candidato
    G.add_node("CANDIDATE", node_type="candidate", label="Você")

    # Nós de skills do candidato
    for skill in candidate_skills:
        G.add_node(skill, node_type="candidate_skill", label=skill)
        G.add_edge("CANDIDATE", skill, edge_type="has_skill", weight=1.0)

    # Nós de cargo e suas skills
    for role, skill_weights in market["role_profiles"].items():
        G.add_node(role, node_type="role", label=role)
        for skill, weight in skill_weights.items():
            if not G.has_node(skill):
                G.add_node(skill, node_type="market_skill", label=skill)
            G.add_edge(role, skill, edge_type="requires", weight=round(weight, 3))

    return G


def calculate_match_scores(
    G: nx.Graph,
    market: dict,
    candidate_skills: list[str]
) -> list[dict]:
    """
    Para cada cargo, calcula:
    - score       : % de aderência (skills do candidato / skills exigidas, ponderado)
    - matched     : skills que o candidato já tem
    - gaps        : skills que faltam, ordenadas por impacto (peso no cargo)
    """
    candidate_set = set(candidate_skills)
    results = []

    for role, skill_weights in market["role_profiles"].items():
        role_skills = set(skill_weights.keys())
        matched = candidate_set & role_skills
        gaps = role_skills - candidate_set

        # Score ponderado: soma dos pesos das skills que o candidato tem
        total_weight = sum(skill_weights.values())
        matched_weight = sum(skill_weights.get(s, 0) for s in matched)
        score = round((matched_weight / total_weight) * 100, 1) if total_weight > 0 else 0

        # Gaps ordenados por impacto (peso no cargo)
        gap_list = sorted(
            [{"skill": s, "impact": round(skill_weights[s] * 100, 1)} for s in gaps],
            key=lambda x: x["impact"],
            reverse=True
        )

        # Adiciona aresta candidato→cargo com peso = score
        G.add_edge("CANDIDATE", role, edge_type="affinity", weight=round(score / 100, 3))

        results.append({
            "role": role,
            "score": score,
            "matched_skills": sorted(matched),
            "matched_count": len(matched),
            "total_required": len(role_skills),
            "gaps": gap_list,
            "gap_count": len(gap_list),
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def calculate_match_for_role(G, market, candidate_skills, target_role):
    candidate_set = set(candidate_skills)
    skill_weights = market["role_profiles"].get(target_role, {})

    if not skill_weights:
        return {"role": target_role, "score": 0.0, "matched_skills": [],
                "matched_count": 0, "total_required": 0, "gaps": [], "gap_count": 0}

    role_skills = set(skill_weights.keys())
    matched = candidate_set & role_skills
    gaps = role_skills - candidate_set

    total_weight = sum(skill_weights.values())
    matched_weight = sum(skill_weights.get(s, 0) for s in matched)
    score = round((matched_weight / total_weight) * 100, 1) if total_weight > 0 else 0

    gap_list = sorted(
        [{"skill": s, "impact": round(skill_weights[s] * 100, 1)} for s in gaps],
        key=lambda x: x["impact"], reverse=True
    )

    G.add_edge("CANDIDATE", target_role, edge_type="affinity", weight=round(score / 100, 3))

    return {"role": target_role, "score": score, "matched_skills": sorted(matched),
            "matched_count": len(matched), "total_required": len(role_skills),
            "gaps": gap_list, "gap_count": len(gap_list)}


def generate_pyvis_for_role(G, result, candidate_skills):
    try:
        from pyvis.network import Network
    except ImportError:
        print("  PyVis não instalado.")
        return

    target_role = result["role"]
    matched_set = set(result["matched_skills"])
    gap_set = {g["skill"] for g in result["gaps"]}
    relevant_nodes = {"CANDIDATE", target_role} | matched_set | gap_set | set(candidate_skills)

    net = Network(height="620px", width="100%", bgcolor="#0f1117", font_color="white")
    net.barnes_hut(gravity=-6000, central_gravity=0.4, spring_length=130)

    for node in relevant_nodes:
        if not G.has_node(node):
            continue
        ntype = G.nodes[node].get("node_type", "")
        if ntype == "candidate":
            net.add_node(node, label="VOCÊ", color="#4f8ef7", size=42,
                         title="Seu perfil", shape="star", font={"size": 18, "bold": True})
        elif node == target_role:
            score = result["score"]
            color = "#00c896" if score >= 80 else "#f0a500" if score >= 60 else "#e05c5c"
            net.add_node(node, label=f"{node}\n{score}%", color=color, size=34,
                         title=f"{node}: {score}%", shape="box", font={"size": 14, "bold": True})
        elif node in matched_set:
            net.add_node(node, label=node, color="#00c896", size=16,
                         title="✓ Você tem essa skill", shape="dot", font={"size": 12})
        elif node in gap_set:
            net.add_node(node, label=node, color="#f0a500", size=14,
                         title="Gap: você ainda não tem essa skill", shape="dot", font={"size": 11})
        else:
            net.add_node(node, label=node, color="#4f8ef7", size=12,
                         title=f"Sua skill: {node}", shape="dot", font={"size": 11})

    for u, v, data in G.edges(data=True):
        if u not in relevant_nodes or v not in relevant_nodes:
            continue
        etype = data.get("edge_type", "")
        if etype == "has_skill":
            net.add_edge(u, v, color="#4f8ef740", width=1.5)
        elif etype == "affinity":
            score = data["weight"] * 100
            color = "#00c896" if score >= 80 else "#f0a500" if score >= 60 else "#e05c5c"
            net.add_edge(u, v, color=color, width=4, title=f"Afinidade: {score:.0f}%")
        elif etype == "requires":
            skill = v if u == target_role else u
            color = "#00c89660" if skill in matched_set else "#f0a50060"
            net.add_edge(u, v, color=color, width=2)

    net.set_options('{"physics":{"barnesHut":{"gravitationalConstant":-6000,"springLength":130},"stabilization":{"iterations":250}},"interaction":{"hover":true}}')
    Path("output").mkdir(exist_ok=True)
    net.save_graph("output/career_graph.html")
    print("  ✓ Grafo salvo em output/career_graph.html")

def print_report(match_results: list[dict]):
    print("\n" + "=" * 55)
    print("RESULTADOS — SCORE DE ADERÊNCIA POR CARGO")
    print("=" * 55)

    for r in match_results:
        bar_len = int(r["score"] / 3)
        bar = "█" * bar_len + "░" * (33 - bar_len)
        emoji = "🟢" if r["score"] >= 80 else "🟡" if r["score"] >= 60 else "🔴"
        print(f"\n{emoji} {r['role']:<24} {r['score']:>5.1f}%")
        print(f"   [{bar}]")
        print(f"   Skills compatíveis: {r['matched_count']}/{r['total_required']}")

    print("\n" + "=" * 55)
    print("GAPS PRIORITÁRIOS — TOP CARGO-ALVO")
    print("=" * 55)
    top = match_results[0]
    print(f"\nCargo: {top['role']} ({top['score']}% atual)")
    print(f"Para atingir 90%+, estude estas skills (por impacto):\n")
    for i, gap in enumerate(top["gaps"][:8], 1):
        bar = "▓" * int(gap["impact"] / 4)
        print(f"  {i}. {gap['skill']:<22} impacto: {gap['impact']}% {bar}")


def run():
    print("=" * 55)
    print("FASE 3 — Grafo de Conhecimento & Motor de Match")
    print("=" * 55)

    print("\nCarregando dados...")
    market, candidate_skills = load_data()
    print(f"  ✓ {market['total_jobs']} vagas, {len(market['role_profiles'])} cargos")
    print(f"  ✓ {len(candidate_skills)} skills do candidato")

    print("\nConstruindo Grafo de Conhecimento...")
    G = build_knowledge_graph(market, candidate_skills)
    print(f"  ✓ {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    print("\nCalculando scores de aderência...")
    match_results = calculate_match_scores(G, market, candidate_skills)

    # Salva resultados
    out = Path("data")
    out.mkdir(exist_ok=True)
    with open(out / "match_results.json", "w", encoding="utf-8") as f:
        json.dump(match_results, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Resultados salvos em data/match_results.json")

    print("\nGerando visualização PyVis...")
    generate_pyvis_graph(G, match_results, candidate_skills)

    print_report(match_results)

    return G, match_results


if __name__ == "__main__":
    run()
