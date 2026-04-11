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
