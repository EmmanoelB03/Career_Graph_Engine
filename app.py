"""
Career Graph Engine — Interface Streamlit
Projeto Final Unidade 2 — Grafos e Ontologias
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ──────────────────────────────────────────────
# ONTOLOGIA (dicionário Python — sem OWL/Protege)
# ──────────────────────────────────────────────
ONTOLOGY = {
    "classes": {
        "Candidate":      {"color": "#4f8ef7", "priority": 0,   "description": "Perfil do candidato que está sendo analisado"},
        "Role":           {"color": "#a855f7", "priority": 0,   "description": "Cargo-alvo no mercado de trabalho"},
        "CoreSkill":      {"color": "#00c896", "priority": 1.5, "description": "Skill essencial (peso relativo ≥0.6)"},
        "CommonSkill":    {"color": "#f0a500", "priority": 1.2, "description": "Skill comum (peso relativo 0.3–0.6)"},
        "NicheSkill":     {"color": "#e05c5c", "priority": 0.8, "description": "Skill de nicho (peso relativo <0.3)"},
    },
    "relations": {
        "has_skill":  "Candidato possui esta skill",
        "requires":   "Cargo exige esta skill",
        "affinity":   "Grau de aderência candidato→cargo",
    },
    # REGRA SEMÂNTICA: CoreSkills têm peso multiplicado por priority
    # no cálculo do caminho semântico, e o caminho mínimo semântico
    # considera apenas hubs de CoreSkill como nós intermediários válidos.
    "rules": [
        "CoreSkill (peso relativo ≥ 0.6): peso semântico = peso × 0.5  → caminho mais curto",
        "CommonSkill (0.3–0.6): peso semântico = peso × 1.0   → neutro",
        "NicheSkill (< 0.3): peso semântico = peso × 1.8       → caminho mais caro",
    ],
}

ROLES = [
    'Backend Engineer', 'Cloud Architect', 'Data Engineer',
    'Data Scientist', 'DevOps Engineer', 'Frontend Engineer',
    'Full Stack Engineer', 'ML Engineer'
]

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
st.set_page_config(page_title='Career Graph Engine', layout='wide')

st.markdown("""
<style>
.skill-badge {display:inline-block;border-radius:8px;padding:5px 12px;margin:4px;font-size:13px;font-weight:500;}
.skill-have  {background:#0d3d2e;color:#00c896;border:1px solid #00c896;}
.skill-gap   {background:#2e1f00;color:#f0a500;border:1px solid #f0a500;}
.result-box  {background:#1e2130;border-radius:14px;padding:24px 28px;margin-bottom:16px;}
.metric-box  {background:#161b22;border-radius:10px;padding:16px;margin:6px 0;}
.path-box    {background:#0d1117;border-left:4px solid #4f8ef7;padding:14px;border-radius:6px;margin:8px 0;font-family:monospace;}
.path-sem    {background:#0d1117;border-left:4px solid #00c896;padding:14px;border-radius:6px;margin:8px 0;font-family:monospace;}
.legend-item {display:flex;align-items:center;gap:10px;margin:6px 0;font-size:14px;}
.legend-dot  {width:14px;height:14px;border-radius:50%;display:inline-block;flex-shrink:0;}
.section-title {font-size:18px;font-weight:700;margin:20px 0 10px 0;color:#e2e8f0;}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("🕸️ Career Graph")
    gemini_key = st.text_input("🔑 Gemini API Key", type="password")
    if gemini_key:
        st.success("✅ Chave ativa")
    else:
        st.warning("⚠️ Sem chave IA")

    st.divider()
    st.markdown("**Ontologia — Classes**")
    for cls, info in ONTOLOGY["classes"].items():
        color = info["color"]
        st.markdown(
            f'<div class="legend-item"><span class="legend-dot" style="background:{color};"></span>{cls}: {info["description"]}</div>',
            unsafe_allow_html=True
        )
    st.divider()
    st.markdown("**Relações**")
    for rel, desc in ONTOLOGY["relations"].items():
        st.markdown(f"- `{rel}`: {desc}")
    st.divider()
    st.markdown("**Regras Semânticas**")
    for rule in ONTOLOGY["rules"]:
        st.markdown(f"- {rule}")

# ──────────────────────────────────────────────
# HEADER + INPUT
# ──────────────────────────────────────────────
st.title("🕸️ Career Graph Engine")
col_left, col_right = st.columns([3, 1], gap="large")
with col_left:
    resume_input = st.text_area("📄 Currículo:", height=180,
        placeholder="Cole aqui o texto do seu currículo...")
with col_right:
    target_role = st.selectbox("🎯 Cargo:", ROLES, index=2)
    run_btn = st.button("🚀 Analisar", type="primary", use_container_width=True)

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def classify_skill(weight: float) -> str:
    if weight >= 0.6:
        return "CoreSkill"
    elif weight >= 0.3:
        return "CommonSkill"
    else:
        return "NicheSkill"

def semantic_weight(raw_weight: float, skill_class: str) -> float:
    """Aplica regra ontológica: CoreSkill = caminho mais barato."""
    multipliers = {"CoreSkill": 0.5, "CommonSkill": 1.0, "NicheSkill": 1.8}
    return raw_weight * multipliers.get(skill_class, 1.0)

def build_structural_graph(market, candidate_skills):
    """Grafo PURO — sem semântica. Todos os nós são tratados como iguais (sem skill_class)."""
    import networkx as nx
    G = nx.Graph()
    # Nós sem qualquer atributo semântico — intencionalmente omitido skill_class
    G.add_node("CANDIDATE", node_type="candidate", label="Você")
    for skill in candidate_skills:
        # node_type genérico — sem classificação ontológica
        G.add_node(skill, node_type="skill", label=skill)
        G.add_edge("CANDIDATE", skill, edge_type="has_skill", weight=1.0)
    for role, skill_weights in market["role_profiles"].items():
        G.add_node(role, node_type="role", label=role)
        for skill, w in skill_weights.items():
            if not G.has_node(skill):
                G.add_node(skill, node_type="skill", label=skill)
            G.add_edge(role, skill, edge_type="requires", weight=round(w, 3))
    return G

def build_semantic_graph(market, candidate_skills, target_role):
    """Grafo SEMÂNTICO — grafo completamente novo e independente, com skill_class e semantic_weight."""
    import networkx as nx
    G = nx.Graph()  # objeto novo, sem compartilhar nada com o estrutural
    G.add_node("CANDIDATE", node_type="candidate", label="Você")
    role_profile = market["role_profiles"].get(target_role, {})

    for skill in candidate_skills:
        raw_w = role_profile.get(skill, 0.5)
        cls   = classify_skill(raw_w)
        sem_w = semantic_weight(raw_w if raw_w > 0 else 0.5, cls)
        # Nó com atributos ontológicos explícitos
        G.add_node(skill, node_type="candidate_skill", skill_class=cls, label=skill)
        G.add_edge("CANDIDATE", skill, edge_type="has_skill",
                   weight=1.0, semantic_weight=round(sem_w, 3))

    for role, skill_weights in market["role_profiles"].items():
        G.add_node(role, node_type="role", label=role)
        for skill, w in skill_weights.items():
            cls   = classify_skill(w)
            sem_w = semantic_weight(w, cls)
            if not G.has_node(skill):
                G.add_node(skill, node_type="market_skill",
                           skill_class=cls, label=skill)
            else:
                # Atualiza classe no grafo semântico apenas
                G.nodes[skill]["skill_class"] = cls
            G.add_edge(role, skill, edge_type="requires",
                       weight=round(w, 3), semantic_weight=round(sem_w, 3))
    return G

def structural_metrics(G):
    import networkx as nx
    metrics = {}
    metrics["total_vertices"] = G.number_of_nodes()
    metrics["total_arestas"] = G.number_of_edges()

    degrees = dict(G.degree())
    metrics["grau_medio"] = round(sum(degrees.values()) / len(degrees), 2)
    metrics["grau_max"] = max(degrees.values())
    metrics["vertice_maior_grau"] = max(degrees, key=degrees.get)

    # Betweenness centrality
    bc = nx.betweenness_centrality(G)
    metrics["betweenness_hub"] = max(bc, key=bc.get)
    metrics["betweenness_valor"] = round(bc[metrics["betweenness_hub"]], 4)

    # Componentes conexas
    comps = list(nx.connected_components(G))
    metrics["componentes_conexas"] = len(comps)

    # Ciclos
    try:
        cycles = nx.find_cycle(G)
        metrics["tem_ciclos"] = True
    except nx.NetworkXNoCycle:
        metrics["tem_ciclos"] = False

    # Bipartido
    metrics["e_bipartido"] = nx.is_bipartite(G)

    # Diâmetro (do maior componente)
    largest = max(comps, key=len)
    sub = G.subgraph(largest)
    try:
        metrics["diametro"] = nx.diameter(sub)
    except Exception:
        metrics["diametro"] = "N/A"

    # Emparelhamento máximo
    matching = nx.max_weight_matching(G)
    metrics["emparelhamento_max"] = len(matching)

    # Grau de cada vértice (top 10 por grau)
    metrics["degrees"] = dict(sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10])

    return metrics

def shortest_path_structural(G, source, target):
    import networkx as nx
    try:
        path = nx.shortest_path(G, source, target, weight="weight")
        length = nx.shortest_path_length(G, source, target, weight="weight")
        return path, round(length, 3)
    except Exception as e:
        return None, str(e)

def shortest_path_semantic(G_sem, source, target):
    import networkx as nx
    try:
        path = nx.shortest_path(G_sem, source, target, weight="semantic_weight")
        length = nx.shortest_path_length(G_sem, source, target, weight="semantic_weight")
        return path, round(length, 3)
    except Exception as e:
        return None, str(e)

def pyvis_graph(G, use_ontology=False, highlight_path=None):
    try:
        from pyvis.network import Network
    except ImportError:
        return None

    net = Network(height="600px", width="100%", bgcolor="#0f1117", font_color="white")
    net.barnes_hut(gravity=-5000, central_gravity=0.3, spring_length=120)

    path_set = set(highlight_path) if highlight_path else set()

    for node, data in G.nodes(data=True):
        ntype = data.get("node_type", "")
        # skill_class só lido no modo semântico; no estrutural é ignorado
        cls = data.get("skill_class", "") if use_ontology else ""

        if use_ontology:
            # Modo semântico: cores por tipo ontológico
            if ntype == "candidate":
                color, size, shape = "#4f8ef7", 40, "circle"
                title = "Candidato"
            elif ntype == "role":
                color, size, shape = "#a855f7", 28, "box"
                title = f"Role: {node}"
            elif cls:
                info  = ONTOLOGY["classes"].get(cls, {})
                color = info.get("color", "#888888")
                size  = 18 if cls == "CoreSkill" else 14
                shape = "dot"
                title = f"{node} [{cls}]"
            else:
                color, size, shape = "#888888", 12, "dot"
                title = node
        else:
            # Modo estrutural: todos iguais, sem semântica de cor
            if ntype == "candidate":
                color, size, shape = "#4f8ef7", 40, "circle"
                title = f"Nó: {node}"
            elif ntype == "role":
                color, size, shape = "#cccccc", 28, "box"
                title = f"Nó: {node}"
            else:
                # Skills todas com a mesma cor cinza — sem distinção de classe
                color, size, shape = "#888888", 12, "dot"
                title = node

        if node in path_set:
            color = "#ffffff"
            size  = max(size, 20)

        net.add_node(node, label=node if len(node) < 20 else node[:18]+"…",
                     color=color, size=size, shape=shape, title=title,
                     font={"size": 12})

    for u, v, data in G.edges(data=True):
        etype = data.get("edge_type", "")
        w_key = "semantic_weight" if use_ontology else "weight"
        w     = data.get(w_key, 1.0)

        if highlight_path and len(highlight_path) >= 2:
            pairs = list(zip(highlight_path, highlight_path[1:]))
            if (u, v) in pairs or (v, u) in pairs:
                net.add_edge(u, v, color="#ffffff", width=4,
                             title=f"{etype} w={round(w,3)}")
                continue

        if use_ontology:
            edge_color = "#4f8ef750" if etype == "has_skill" else \
                         "#a855f750" if etype == "affinity"  else "#88888840"
        else:
            # Estrutural: todas as arestas iguais, sem cor por tipo
            edge_color = "#aaaaaa30"

        net.add_edge(u, v, color=edge_color, width=1.5,
                     title=f"{etype} w={round(w,3)}")

    net.set_options('{"physics":{"barnesHut":{"gravitationalConstant":-5000},'
                    '"stabilization":{"iterations":200}},"interaction":{"hover":true}}')
    return net.generate_html()

# ──────────────────────────────────────────────
# MAIN FLOW
# ──────────────────────────────────────────────
if run_btn:
    if not resume_input.strip():
        st.error("Cole o currículo!")
        st.stop()

    with st.status("⚙️ Processando...", expanded=True) as status:
        from fase1_ingestion import run as f1
        from fase2_resume_parser import run as f2
        from fase3_graph_engine import calculate_match_for_role, load_data, generate_pyvis_for_role, build_knowledge_graph
        from fase4_validator import validate_match

        market = f1(target_role=target_role)
        api_key = gemini_key.strip() if gemini_key else None
        candidate_skills = f2(resume_text=resume_input, api_key=api_key)

        market_data, _ = load_data()

        # Grafos
        G_struct = build_structural_graph(market_data, candidate_skills)
        G_sem    = build_semantic_graph(market_data, candidate_skills, target_role)

        # Match e IA
        result = calculate_match_for_role(G_struct, market_data, candidate_skills, target_role)
        generate_pyvis_for_role(G_struct, result, candidate_skills)
        role_skills = list(market_data["role_profiles"].get(target_role, {}).keys())
        analise_ia  = validate_match(resume_input, target_role, role_skills, result["score"], api_key)

        # Métricas estruturais
        metrics = structural_metrics(G_struct)

        status.update(label="✅ Pronto!", state="complete")

    # Salva na session state para as abas
    st.session_state["result"]          = result
    st.session_state["metrics"]         = metrics
    st.session_state["analise_ia"]      = analise_ia
    st.session_state["candidate_skills"]= candidate_skills
    st.session_state["market_data"]     = market_data
    st.session_state["target_role"]     = target_role
    st.session_state["G_struct"]        = G_struct
    st.session_state["G_sem"]           = G_sem
    st.session_state["ran"]             = True

# ──────────────────────────────────────────────
# ABAS
# ──────────────────────────────────────────────
if st.session_state.get("ran"):
    result           = st.session_state["result"]
    metrics          = st.session_state["metrics"]
    analise_ia       = st.session_state["analise_ia"]
    candidate_skills = st.session_state["candidate_skills"]
    market_data      = st.session_state["market_data"]
    target_role      = st.session_state["target_role"]
    G_struct         = st.session_state["G_struct"]
    G_sem            = st.session_state["G_sem"]

    tab1, tab2, tab3 = st.tabs([
        "📐 Aba 1 — Grafo Estrutural",
        "🧠 Aba 2 — Grafo Semântico",
        "⚖️ Aba 3 — Comparação",
    ])

    # ─────────────────────────────────────────
    # ABA 1 — GRAFO ESTRUTURAL
    # ─────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-title">📐 Grafo Puro — Sem Semântica</div>', unsafe_allow_html=True)
        st.info("Nesta visão, todos os vértices e arestas são tratados como iguais — sem tipo, sem categoria, sem contexto.")

        # Score resumido
        sc    = result["score"]
        color = "#00c896" if sc >= 80 else "#f0a500" if sc >= 60 else "#e05c5c"
        st.markdown(
            f'<div class="result-box"><h2 style="color:{color};">{sc}% de Aderência — {target_role}</h2></div>',
            unsafe_allow_html=True
        )

        # ── 5+ Métricas Estruturais ──
        st.markdown('<div class="section-title">📊 Métricas Estruturais (≥5)</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vértices", metrics["total_vertices"])
        c2.metric("Arestas",  metrics["total_arestas"])
        c3.metric("Grau Médio", metrics["grau_medio"])
        c4.metric("Diâmetro",  metrics["diametro"])

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Componentes Conexas",  metrics["componentes_conexas"])
        c6.metric("Emparelhamento Máx",   metrics["emparelhamento_max"])
        c7.metric("Hub (betweenness)",     metrics["betweenness_hub"],
                  delta=f"BC={metrics['betweenness_valor']}")
        c8.metric("Tem Ciclos?",   "Sim" if metrics["tem_ciclos"] else "Não")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Grafo Bipartido?** {'✅ Sim' if metrics['e_bipartido'] else '❌ Não'}")
            st.markdown(f"**Vértice c/ maior grau:** `{metrics['vertice_maior_grau']}` (grau {metrics['grau_max']})")
        with col_b:
            st.markdown("**Top 10 vértices por grau:**")
            for v, d in metrics["degrees"].items():
                st.markdown(f"- `{v}`: {d}")

        # ── Visualização ──
        st.markdown('<div class="section-title">🗺️ Visualização do Grafo</div>', unsafe_allow_html=True)
        html_struct = pyvis_graph(G_struct, use_ontology=False)
        if html_struct:
            st.components.v1.html(html_struct, height=620, scrolling=True)

        # ── Skills
        st.markdown('<div class="section-title">Skills</div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown("#### ✅ Skills que você tem")
            badges = " ".join(
                [f'<span class="skill-badge skill-have">{s}</span>' for s in result["matched_skills"]]
            )
            st.markdown(badges or "Nenhuma.", unsafe_allow_html=True)
        with cb:
            st.markdown("#### 📌 Gaps (por impacto)")
            for g in result["gaps"][:8]:
                st.markdown(
                    f'<span class="skill-badge skill-gap">{g["skill"]} (+{g["impact"]}%)</span>',
                    unsafe_allow_html=True,
                )

    # ─────────────────────────────────────────
    # ABA 2 — GRAFO SEMÂNTICO
    # ─────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-title">🧠 Grafo Semântico — Com Ontologia</div>', unsafe_allow_html=True)
        st.info(
            "Aqui cada nó tem um **tipo** (Candidate, Role, CoreSkill, CommonSkill, NicheSkill) "
            "e os pesos das arestas são ajustados pelas regras semânticas da ontologia."
        )

        # Legenda visual
        st.markdown("**Legenda de cores:**")
        leg_cols = st.columns(len(ONTOLOGY["classes"]))
        for i, (cls, info) in enumerate(ONTOLOGY["classes"].items()):
            with leg_cols[i]:
                st.markdown(
                    f'<div style="background:{info["color"]};border-radius:6px;padding:6px 10px;'
                    f'font-size:12px;color:#000;text-align:center;font-weight:600;">{cls}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(info["description"])

        # Distribuição de skills por classe
        role_profile = market_data["role_profiles"].get(target_role, {})
        core_skills    = [s for s, w in role_profile.items() if w >= 0.6]
        common_skills  = [s for s, w in role_profile.items() if 0.3 <= w < 0.6]
        niche_skills   = [s for s, w in role_profile.items() if w < 0.3]

        st.markdown(f"""
| Classe | Qtd | Critério |
|--------|-----|---------|
    | CoreSkill | {len(core_skills)} | peso relativo ≥ 0.6 |
    | CommonSkill | {len(common_skills)} | peso relativo 0.3–0.6 |
    | NicheSkill | {len(niche_skills)} | peso relativo < 0.3 |
""")

        # Grafo semântico colorido
        html_sem = pyvis_graph(G_sem, use_ontology=True)
        if html_sem:
            st.components.v1.html(html_sem, height=620, scrolling=True)

        # Análises semânticas
        st.markdown('<div class="section-title">🔍 Análises Semânticas</div>', unsafe_allow_html=True)

        # Análise 1 — hubs por classe
        matched_set = set(result["matched_skills"])
        candidate_core   = [s for s in matched_set if s in core_skills]
        candidate_common = [s for s in matched_set if s in common_skills]
        candidate_niche  = [s for s in matched_set if s in niche_skills]

        st.markdown("**Análise Semântica 1 — Cobertura por Criticidade de Skill**")
        cols = st.columns(3)
        cols[0].metric("CoreSkills cobertas",   f"{len(candidate_core)}/{len(core_skills)}",
                       delta="Alta prioridade")
        cols[1].metric("CommonSkills cobertas", f"{len(candidate_common)}/{len(common_skills)}")
        cols[2].metric("NicheSkills cobertas",  f"{len(candidate_niche)}/{len(niche_skills)}")

        # Análise 2 — score semântico ponderado
        total_sem = sum(semantic_weight(w, classify_skill(w)) for w in role_profile.values())
        matched_sem = sum(
            semantic_weight(role_profile[s], classify_skill(role_profile[s]))
            for s in matched_set if s in role_profile
        )
        score_sem = round((matched_sem / total_sem) * 100, 1) if total_sem > 0 else 0

        st.markdown("**Análise Semântica 2 — Score com Peso Ontológico**")
        st.markdown(
            f'<div class="result-box">'
            f'<b>Score estrutural (pesos crus):</b> {result["score"]}%<br>'
            f'<b>Score semântico (pesos ontológicos):</b> {score_sem}%<br><br>'
            f'<small>A ontologia penaliza skills raras (NicheSkill × 1.8) e premia skills críticas (CoreSkill × 0.5). '
            f'Se o candidato tem muitas CoreSkills, o score semântico tende a ser <em>mais alto</em> que o estrutural. '
            f'Se tem muitas NicheSkills, tende a ser <em>mais baixo</em>.</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Parecer da IA
        st.markdown('<div class="section-title">🕵️ Parecer do Tech Recruiter IA</div>', unsafe_allow_html=True)
        if isinstance(analise_ia, dict) and "veredito" in analise_ia:
            st.markdown(
                f'<div class="result-box">'
                f'<h3>{analise_ia.get("veredito")}</h3>'
                f'<p><b>Nível:</b> {analise_ia.get("analise_senioridade")}</p>'
                f'<p>{analise_ia.get("justificativa_score")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**✅ Pontos Fortes**")
                for p in analise_ia.get("pontos_fortes", []):
                    st.write(f"- {p}")
            with c2:
                st.markdown("**⚠️ Pontos de Atenção**")
                for p in analise_ia.get("pontos_atencao", []):
                    st.write(f"- {p}")
        else:
            st.warning("IA qualitativa indisponível (sem chave ou falha na resposta).")

    # ─────────────────────────────────────────
    # ABA 3 — COMPARAÇÃO
    # ─────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-title">⚖️ Comparação: Grafo Puro vs Grafo Semântico</div>',
                    unsafe_allow_html=True)

        # ── Caminho Mínimo ──
        st.markdown("### 🗺️ Caminho Mínimo nas Duas Visões")
        st.markdown("Escolha dois nós do grafo e compare o caminho encontrado com e sem ontologia.")

        all_nodes = sorted(G_struct.nodes())
        col_src, col_tgt = st.columns(2)
        with col_src:
            node_src = st.selectbox("Nó de origem", all_nodes,
                                    index=all_nodes.index("CANDIDATE") if "CANDIDATE" in all_nodes else 0)
        with col_tgt:
            role_nodes = [n for n, d in G_struct.nodes(data=True) if d.get("node_type") == "role"]
            default_tgt = target_role if target_role in all_nodes else all_nodes[0]
            node_tgt = st.selectbox("Nó de destino", all_nodes,
                                    index=all_nodes.index(default_tgt))

        if st.button("🔍 Calcular Caminhos"):
            path_s, len_s = shortest_path_structural(G_struct, node_src, node_tgt)
            path_m, len_m = shortest_path_semantic(G_sem, node_src, node_tgt)

            col_p1, col_p2 = st.columns(2)

            with col_p1:
                st.markdown("#### 📐 Sem Ontologia (peso cru)")
                if path_s:
                    path_str = " → ".join(path_s)
                    st.markdown(
                        f'<div class="path-box">Caminho: {path_str}<br>Custo: {len_s}</div>',
                        unsafe_allow_html=True,
                    )
                    html_s = pyvis_graph(G_struct, use_ontology=False, highlight_path=path_s)
                    if html_s:
                        st.components.v1.html(html_s, height=400, scrolling=True)
                else:
                    st.error(f"Sem caminho: {len_s}")

            with col_p2:
                st.markdown("#### 🧠 Com Ontologia (peso semântico)")
                if path_m:
                    path_str2 = " → ".join(path_m)
                    st.markdown(
                        f'<div class="path-sem">Caminho: {path_str2}<br>Custo semântico: {len_m}</div>',
                        unsafe_allow_html=True,
                    )
                    html_m = pyvis_graph(G_sem, use_ontology=True, highlight_path=path_m)
                    if html_m:
                        st.components.v1.html(html_m, height=400, scrolling=True)
                else:
                    st.error(f"Sem caminho: {len_m}")

            # Explicação da diferença
            if path_s and path_m and path_s != path_m:
                st.success(
                    "✅ **Os caminhos são diferentes!** A ontologia redirecionou o trajeto.\n\n"
                    "**Por quê?** A regra semântica penaliza NicheSkills (×1.8) e premia CoreSkills (×0.5). "
                    "O algoritmo Dijkstra encontra o caminho de menor custo — e com a ontologia, "
                    "atravessar um nó CoreSkill é mais barato do que atravessar um NicheSkill, "
                    "mesmo que geometricamente o caminho original parecesse mais curto."
                )
            elif path_s and path_m and path_s == path_m:
                if len_s != len_m:
                    st.info(
                        "ℹ️ O caminho (sequência de nós) é o mesmo, mas os **custos diferem**: "
                        f"sem ontologia = {len_s} | com ontologia = {len_m}. "
                        "Os pesos semânticos mudam a percepção de \"distância\" mesmo percorrendo o mesmo trajeto."
                    )
                else:
                    st.info("ℹ️ Neste par de nós os dois caminhos coincidem. Tente outros nós para ver a diferença.")

        # ── Tabela comparativa de scores ──
        st.divider()
        st.markdown("### 📊 Score Estrutural vs Score Semântico")

        role_profile = market_data["role_profiles"].get(target_role, {})
        matched_set  = set(result["matched_skills"])

        score_raw = result["score"]
        total_sem_w  = sum(semantic_weight(w, classify_skill(w)) for w in role_profile.values())
        matched_sem_w = sum(
            semantic_weight(role_profile[s], classify_skill(role_profile[s]))
            for s in matched_set if s in role_profile
        )
        score_sem = round((matched_sem_w / total_sem_w) * 100, 1) if total_sem_w > 0 else 0
        delta     = round(score_sem - score_raw, 1)
        delta_str = f"+{delta}%" if delta >= 0 else f"{delta}%"

        comp_col1, comp_col2, comp_col3 = st.columns(3)
        comp_col1.metric("Score Estrutural",  f"{score_raw}%", help="Sem ontologia — todos os pesos valem igual")
        comp_col2.metric("Score Semântico",   f"{score_sem}%", delta=delta_str,
                         help="Com ontologia — CoreSkills valem mais")
        comp_col3.metric("Diferença",         delta_str,
                         help="Positivo = candidato tem mais CoreSkills do que NicheSkills relativas ao cargo")

        st.markdown(
            f"""
**Interpretação:**
- Score estrutural `{score_raw}%` trata todas as skills igualmente.
- Score semântico `{score_sem}%` valoriza quem domina as skills **mais críticas** do cargo
    (CoreSkill = peso relativo ≥0.6 no perfil de {target_role}).
- {'O candidato tem um perfil mais alinhado às skills críticas do que o score puro sugere ✅' if delta > 0
   else 'O candidato tem muitas skills de nicho que inflam o score puro — o alinhamento real é menor ⚠️' if delta < 0
   else 'O perfil do candidato tem distribuição equilibrada entre tipos de skill.'}
"""
        )

        # Listagem lado a lado — CoreSkill coverage
        st.markdown("### 🎯 Quais CoreSkills você já tem?")
        core_skills_role = [s for s, w in role_profile.items() if w >= 0.6]
        have_core = [s for s in core_skills_role if s in matched_set]
        miss_core = [s for s in core_skills_role if s not in matched_set]

        cca, ccb = st.columns(2)
        with cca:
            st.markdown("**✅ CoreSkills que você TEM**")
            if have_core:
                for s in have_core:
                    st.markdown(f'<span class="skill-badge skill-have">{s}</span>', unsafe_allow_html=True)
            else:
                st.write("Nenhuma CoreSkill detectada.")
        with ccb:
            st.markdown("**❌ CoreSkills que FALTAM (máximo impacto)**")
            if miss_core:
                for s in miss_core:
                    st.markdown(f'<span class="skill-badge skill-gap">{s}</span>', unsafe_allow_html=True)
            else:
                st.success("Você tem todas as CoreSkills! 🎉")

else:
    st.info("👆 Cole seu currículo, escolha o cargo e clique em **Analisar** para começar.")