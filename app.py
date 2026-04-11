"""
Career Graph Engine — Interface Streamlit
O usuário cola o currículo, escolhe o cargo-alvo e recebe
score de aderência + skills que já tem + gaps por impacto.
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROLES = [
    "Backend Engineer",
    "Cloud Architect",
    "Data Engineer",
    "Data Scientist",
    "DevOps Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "ML Engineer",
]

st.set_page_config(
    page_title="Career Graph Engine",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.skill-badge {
    display: inline-block;
    border-radius: 8px;
    padding: 5px 12px;
    margin: 4px;
    font-size: 14px;
    font-weight: 500;
}
.skill-have  { background: #0d3d2e; color: #00c896; border: 1px solid #00c896; }
.skill-gap   { background: #2e1f00; color: #f0a500; border: 1px solid #f0a500; }
.result-box  {
    background: #1e2130;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🕸️ Career Graph Engine")
    st.markdown("Descubra o seu nível de aderência a um cargo e o que falta para chegar lá.")
    st.divider()
    gemini_key = st.text_input(
        "🔑 Gemini API Key (opcional)",
        type="password",
        help="Com a chave, o parser usa IA semântica. Sem ela, usa regex."
    )
    st.divider()
    st.markdown("**Como funciona:**")
    st.markdown("1. 📡 Busca vagas reais na Adzuna (US)")
    st.markdown("2. 🧠 Extrai suas skills do currículo")
    st.markdown("3. 🕸️ Calcula matching via Teoria dos Grafos")
    st.divider()
    st.caption("Career Graph Engine")

st.title("🕸️ Career Graph Engine")
st.markdown("Cole seu currículo, escolha o **cargo que você quer** e veja onde seu perfil está hoje — e o que falta para chegar lá.")
st.divider()

col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    resume_input = st.text_area(
        "📄 Currículo:",
        height=260,
        placeholder="""João Silva — Engenheiro de Dados Sênior

Experiência:
- 5 anos desenvolvendo pipelines com Python e Apache Airflow
- SQL avançado em PostgreSQL, modelagem dimensional
- AWS (S3, Glue, Athena, Redshift), Docker, Kubernetes
- Apache Spark, dbt, Kafka
- Git, GitHub Actions, Scrum

Tecnologias: Python, SQL, Spark, Airflow, dbt, Kafka, AWS, Docker, PostgreSQL"""
    )

with col_right:
    target_role = st.selectbox(
        "🎯 Cargo que você quer:",
        ROLES,
        index=2,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Analisar", type="primary", use_container_width=True)

st.divider()

if run_btn:
    if not resume_input.strip():
        st.warning("Cole seu currículo antes de analisar.")
        st.stop()

    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    with st.status("📡 Buscando vagas do mercado (Adzuna US)...", expanded=False) as status:
        from fase1_ingestion import run as fase1_run
        market = fase1_run(target_role=target_role)
        status.update(label=f"✅ {market['total_jobs']} vagas de {target_role} processadas", state="complete")

    with st.status("🧠 Extraindo suas habilidades do currículo...", expanded=False) as status:
        from fase2_resume_parser import run as fase2_run
        api_key = gemini_key.strip() or None
        candidate_skills = fase2_run(resume_text=resume_input, api_key=api_key)
        status.update(label=f"✅ {len(candidate_skills)} habilidades extraídas", state="complete")

    with st.status(f"🕸️ Calculando match com {target_role}...", expanded=False) as status:
        from fase3_graph_engine import (
            load_data, build_knowledge_graph,
            calculate_match_for_role, generate_pyvis_for_role
        )
        market_data, _ = load_data()
        G = build_knowledge_graph(market_data, candidate_skills)
        result = calculate_match_for_role(G, market_data, candidate_skills, target_role)
        generate_pyvis_for_role(G, result, candidate_skills)
        status.update(label=f"✅ Análise de {target_role} concluída", state="complete")

    st.success("✅ Análise concluída!")

    score = result["score"]
    score_color = "#00c896" if score >= 80 else "#f0a500" if score >= 60 else "#e05c5c"
    score_label = "Excelente" if score >= 80 else "Intermediário" if score >= 60 else "Iniciante"

    st.markdown(f"""
    <div class="result-box">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
            <div>
                <div style="font-size:15px; color:#aaa; margin-bottom:4px;">Compatibilidade com</div>
                <div style="font-size:28px; font-weight:700; color:white;">{target_role}</div>
                <div style="font-size:14px; color:#aaa; margin-top:6px;">
                    {result['matched_count']} de {result['total_required']} skills do cargo identificadas no seu perfil
                </div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:64px; font-weight:800; color:{score_color}; line-height:1;">{score}%</div>
                <div style="font-size:14px; color:{score_color}; font-weight:600;">{score_label}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(int(score) / 100)
    st.divider()

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown("### ✅ Skills que você já tem")
        st.markdown(f"<small style='color:#aaa'>{len(result['matched_skills'])} skills compatíveis com o cargo</small>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if result["matched_skills"]:
            badges = " ".join(
                f'<span class="skill-badge skill-have">✓ {s}</span>'
                for s in result["matched_skills"]
            )
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.info("Nenhuma skill compatível encontrada.")

    with col_b:
        st.markdown("### 📌 O que você ainda precisa")
        st.markdown("<small style='color:#aaa'>Ordenado por impacto no score — foque de cima pra baixo</small>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if result["gaps"]:
            for g in result["gaps"]:
                st.markdown(
                    f'<span class="skill-badge skill-gap">⬆ {g["skill"]} &nbsp;<b>+{g["impact"]}%</b></span>',
                    unsafe_allow_html=True
                )
        else:
            st.success("Você já tem todas as skills desse cargo!")

    st.divider()
    st.markdown("### 🕸️ Grafo de Habilidades")
    st.markdown("<small style='color:#aaa'>Azul = suas skills &nbsp;|&nbsp; Verde = skills que você tem e o cargo exige &nbsp;|&nbsp; Laranja = gaps</small>", unsafe_allow_html=True)
    graph_path = Path("output/career_graph.html")
    if graph_path.exists():
        html_content = graph_path.read_text(encoding="utf-8")
        st.components.v1.html(html_content, height=650, scrolling=False)
        with open(graph_path, "rb") as f:
            st.download_button("⬇️ Baixar grafo", f, file_name="career_graph.html", mime="text/html")
    else:
        st.info("Instale PyVis para ver o grafo: pip install pyvis")

else:
    st.info("👆 Cole seu currículo, escolha o cargo e clique em **Analisar**.")
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        1. **📡 Ingestão** — Busca vagas reais de tech nos EUA via Adzuna API e mapeia as skills exigidas por cargo.
        2. **🧠 Parser** — Extrai suas habilidades técnicas do currículo (Gemini API ou fallback regex).
        3. **🕸️ Grafo** — NetworkX conecta seu perfil ao cargo escolhido e calcula matematicamente o score de aderência.

        O resultado mostra exatamente quais skills já contam a seu favor e quais são os gaps — ordenados por impacto no score.
        """)