"""
Script para pré-carregar o dataset de vagas de todos os cargos.
Isso evita que o usuário tenha que esperar a primeira busca no app.py.
"""
from fase1_ingestion import run, ROLE_TO_QUERY
import time

def preload_all_roles():
    print("🚀 Iniciando pré-carregamento do dataset de vagas...")
    print(f"Cargos detectados: {list(ROLE_TO_QUERY.keys())}\n")
    
    for role in ROLE_TO_QUERY.keys():
        print(f"📥 Baixando vagas para: {role}")
        try:
            # force_refresh=False garante que se já existir, ele não baixe de novo
            run(target_role=role, force_refresh=False)
            print(f"✅ Sucesso: {role}")
        except Exception as e:
            print(f"❌ Erro ao baixar {role}: {e}")
        
        # Pequeno delay para respeitar limites de API se houver muitos cargos
        time.sleep(2)

    print("\n✨ Dataset completo! Agora o app.py será instantâneo para todos os cargos.")

if __name__ == "__main__":
    preload_all_roles()
