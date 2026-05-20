"""
Career Graph Engine — Pipeline CLI
Roda as 3 fases em sequência pelo terminal.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("\n" + "╔" + "═" * 53 + "╗")
    print("║       🕸️  CAREER GRAPH ENGINE  🕸️              ║")
    print("║   IA + Teoria dos Grafos para análise de carreira ║")
    print("╚" + "═" * 53 + "╝\n")

    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # FASE 1
    from fase1_ingestion import run as fase1
    market = fase1()

    print()

    # FASE 2
    api_key = os.getenv("GEMINI_API_KEY")
    resume_text = os.getenv("RESUME_TEXT")  # Pode passar via env var

    from fase2_resume_parser import run as fase2
    candidate_skills = fase2(resume_text=resume_text, api_key=api_key)

    print()

    # FASE 3
    from fase3_graph_engine import run as fase3
    G, results = fase3()

    # FASE 4 — Validação Qualitativa
    print("\n" + "=" * 55)
    print("FASE 4 — Validação Qualitativa com IA")
    print("=" * 55)
    
    if api_key:
        print("\nConsultando Tech Recruiter IA para parecer final...")
        from fase4_validator import validate_match
        import json
        
        # Pega dados para validação
        top_result = results[0]
        market_data = json.loads(Path("data/market_data.json").read_text())
        role_skills = list(market_data["role_profiles"].get(top_result["role"], {}).keys())
        
        # Recupera texto do currículo original ou de exemplo
        if not resume_text:
            resume_text = "João Silva — Engenheiro de Dados Sênior. Pipelines Python, Airflow, SQL, AWS, Spark, Docker."

        analise = validate_match(
            resume_text=resume_text,
            target_role=top_result["role"],
            role_skills=role_skills,
            graph_score=top_result["score"],
            api_key=api_key
        )
        
        if isinstance(analise, dict) and "veredito" in analise:
            print(f"\n📢 VEREDITO: {analise['veredito']}")
            print(f"🏅 Nível Percebido: {analise['analise_senioridade']}")
            print(f"\n📝 Justificativa do Score ({top_result['score']}%):")
            print(f"   {analise['justificativa_score']}")
            
            print("\n✅ PONTOS FORTES:")
            for p in analise["pontos_fortes"]: print(f"   - {p}")
            
            print("\n⚠️ PONTOS DE ATENÇÃO:")
            for p in analise["pontos_atencao"]: print(f"   - {p}")
        elif isinstance(analise, dict) and "aviso" in analise:
            print(f"  ! {analise['aviso']}")
        else:
            print(f"  ! Falha na análise qualitativa.")
    else:
        print("\n  ⚠️ GEMINI_API_KEY não encontrada. Pulando validação qualitativa.")

    print("\n" + "╔" + "═" * 53 + "╗")
    print("║              PIPELINE COMPLETO ✓               ║")
    print("╚" + "═" * 53 + "╝")
    print("\nArquivos gerados:")
    print("  📄 data/market_data.json      — dados do mercado")
    print("  📄 data/candidate_profile.json — perfil do candidato")
    print("  📄 data/match_results.json     — scores e gaps")
    print("  🌐 output/career_graph.html    — grafo interativo")
    print("\nPara a interface visual, execute:")
    print("  streamlit run app.py\n")


if __name__ == "__main__":
    main()
