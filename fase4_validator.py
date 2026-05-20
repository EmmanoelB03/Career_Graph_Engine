"""
FASE 4 — Validação Qualitativa (AI Validator)
Usa o Gemini para atuar como um Tech Recruiter Sênior e validar 
qualitativamente o match matemático feito pelo grafo.
"""

import json
import re
import google.generativeai as genai

def validate_match(resume_text, target_role, role_skills, graph_score, api_key):
    """
    Usa o Gemini para fornecer uma análise qualitativa para validar se o 
    score do grafo faz sentido e fornecer um parecer humano.
    """
    if not api_key:
        return {"aviso": "IA de validação desativada (Chave API não fornecida)."}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Limita o tamanho do currículo para não estourar o contexto
        resume_snippet = resume_text[:4000] 

        prompt = f"""Você é um Tech Recruiter Sênior especializado em contratações de tecnologia de alta performance.
Um motor de grafos analisou um currículo e deu um score de {graph_score}% de aderência para o cargo de "{target_role}".

Sua tarefa é fornecer uma análise qualitativa profunda para validar se esse score matemático faz sentido na prática e fornecer um parecer "humano" e estratégico.

DADOS DA ANÁLISE:
- Cargo Alvo: {target_role}
- Algumas Skills Exigidas pelo Mercado para este cargo: {", ".join(role_skills[:15])}
- Score Matemático Calculado: {graph_score}%
- Texto do Currículo do Candidato:
---
{resume_snippet}
---

FORNEÇA SUA ANÁLISE EXCLUSIVAMENTE NO SEGUINTE FORMATO JSON (EM PORTUGUÊS):
{{
  "veredito": "Altamente Recomendado" | "Apto com Ressalvas" | "Não Recomendado",
  "analise_senioridade": "Sua percepção sobre o nível real do candidato (Ex: Junior, Pleno, Sênior, Especialista)",
  "pontos_fortes": ["Ponto 1", "Ponto 2", "Ponto 3"],
  "pontos_atencao": ["Riscos, gaps técnicos ou falta de experiência específica que o grafo pode ter ignorado"],
  "justificativa_score": "Explique brevemente se o score de {graph_score}% é justo ou se está inflado/subestimado com base no contexto do currículo."
}}
Retorne APENAS o JSON puro, sem blocos de código markdown.
"""

        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        
        # Limpeza de markdown caso a IA ignore a instrução
        raw_response = re.sub(r"```json|```", "", raw_response).strip()
        
        return json.loads(raw_response)
    except Exception as e:
        return {"erro": f"Falha na validação qualitativa: {str(e)}"}
