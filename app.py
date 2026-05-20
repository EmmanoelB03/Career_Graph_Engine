"""
Career Graph Engine — Interface Streamlit
"""
import streamlit as st
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROLES = ['Backend Engineer', 'Cloud Architect', 'Data Engineer', 'Data Scientist', 'DevOps Engineer', 'Frontend Engineer', 'Full Stack Engineer', 'ML Engineer']

st.set_page_config(page_title='Career Graph Engine', layout='wide')

st.markdown('<style>.skill-badge {display: inline-block; border-radius: 8px; padding: 5px 12px; margin: 4px; font-size: 14px; font-weight: 500;} .skill-have {background: #0d3d2e; color: #00c896; border: 1px solid #00c896;} .skill-gap {background: #2e1f00; color: #f0a500; border: 1px solid #f0a500;} .result-box {background: #1e2130; border-radius: 14px; padding: 28px 32px; margin-bottom: 20px;} .recruiter-box {background: #161b22; border-left: 5px solid #4f8ef7; padding: 20px; border-radius: 8px; margin-top: 10px;}</style>', unsafe_allow_html=True)

with st.sidebar:
    st.title('🕸️ Career Graph')
    gemini_key = st.text_input('🔑 Gemini API Key', type='password')
    if gemini_key: st.success('✅ Chave ativa')
    else: st.warning('⚠️ Sem chave IA')

st.title('🕸️ Career Graph Engine')

col_left, col_right = st.columns([3, 1], gap='large')
with col_left:
    resume_input = st.text_area('📄 Currículo:', height=200)
with col_right:
    target_role = st.selectbox('🎯 Cargo:', ROLES, index=2)
    run_btn = st.button('🚀 Analisar', type='primary', use_container_width=True)

if run_btn:
    if not resume_input.strip():
        st.error('Cole o currículo!')
        st.stop()

    with st.status('⚙️ Processando...', expanded=True) as status:
        from fase1_ingestion import run as f1
        from fase2_resume_parser import run as f2
        from fase3_graph_engine import calculate_match_for_role, build_knowledge_graph, load_data, generate_pyvis_for_role
        from fase4_validator import validate_match
        
        market = f1(target_role=target_role)
        api_key = gemini_key.strip() if gemini_key else None
        candidate_skills = f2(resume_text=resume_input, api_key=api_key)
        market_data, _ = load_data()
        G = build_knowledge_graph(market_data, candidate_skills)
        result = calculate_match_for_role(G, market_data, candidate_skills, target_role)
        generate_pyvis_for_role(G, result, candidate_skills)
        
        role_skills = list(market_data['role_profiles'].get(target_role, {}).keys())
        analise_ia = validate_match(resume_input, target_role, role_skills, result['score'], api_key)
        status.update(label='✅ Pronto!', state='complete')

    st.markdown('---')
    sc = result['score']
    color = '#00c896' if sc >= 80 else '#f0a500' if sc >= 60 else '#e05c5c'
    st.markdown(f'<div class="result-box"><h1 style="color:{color};">{sc}% de Aderência</h1><p>Cargo: {target_role}</p></div>', unsafe_allow_html=True)

    st.subheader('🕵️ Parecer do Tech Recruiter IA')
    if isinstance(analise_ia, dict) and 'veredito' in analise_ia:
        st.markdown(f'<div class="recruiter-box"><h3>{analise_ia.get("veredito")}</h3><p><b>Nível:</b> {analise_ia.get("analise_senioridade")}</p><p>{analise_ia.get("justificativa_score")}</p></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('**✅ Pontos Fortes**')
            for p in analise_ia.get('pontos_fortes', []): st.write(f'- {p}')
        with c2:
            st.markdown('**⚠️ Pontos de Atenção**')
            for p in analise_ia.get('pontos_atencao', []): st.write(f'- {p}')
    elif isinstance(analise_ia, dict) and 'erro' in analise_ia:
        st.error(f'❌ Erro na IA: {analise_ia["erro"]}')
    else:
        st.warning('⚠️ IA Qualitativa indisponível sem chave ou por falha na resposta.')

    st.divider()
    ca, cb = st.columns(2)
    with ca:
        st.markdown('#### ✅ Suas Skills')
        badges = ' '.join([f'<span class="skill-badge skill-have">{s}</span>' for s in result['matched_skills']])
        st.markdown(badges if badges else 'Nenhuma.', unsafe_allow_html=True)
    with cb:
        st.markdown('#### 📌 Gaps Prioritários')
        for g in result['gaps'][:6]:
            st.markdown(f'<span class="skill-badge skill-gap">{g.get("skill")} (+{g.get("impact")}%)</span>', unsafe_allow_html=True)

    st.divider()
    if Path('output/career_graph.html').exists():
        st.markdown('### 🕸️ Grafo de Carreira')
        st.components.v1.html(Path('output/career_graph.html').read_text(encoding='utf-8'), height=750, scrolling=True)
