# 🕸️ Career Graph Engine

> Motor de análise de carreiras que cruza o currículo do candidato com o estado real do mercado de trabalho — usando IA e Teoria dos Grafos para transformar intuição em diagnóstico matemático.

---

## 🚀 Como usar

### 1. Instale as dependências

```bash
pip install requests networkx pyvis streamlit google-generativeai
```

### 2. Interface visual (recomendado)

```bash
cd career_graph_engine
streamlit run app.py
```

### 3. Ou rode o pipeline via CLI

```bash
python main.py
```

---

## 🔑 Gemini API Key (opcional)

Para parser semântico real, exporte sua chave:

```bash
export GEMINI_API_KEY="sua-chave-aqui"
```

Sem a chave, o sistema usa um parser de fallback por regex sobre uma base de skills conhecidas. A chave pode também ser inserida diretamente na sidebar da interface.

---

## 📁 Estrutura

```
career_graph_engine/
├── main.py                    # Pipeline CLI (roda as 3 fases)
├── app.py                     # Interface Streamlit
├── fase1_ingestion.py         # Ingestão Adzuna API → JSON
├── fase2_resume_parser.py     # Parser currículo (Gemini/regex)
├── fase3_graph_engine.py      # Grafo NetworkX + motor de match
├── data/
│   ├── market_data.json       # Dados do mercado processados
│   ├── candidate_profile.json # Perfil extraído do currículo
│   └── match_results.json     # Scores e gaps calculados
└── output/
    └── career_graph.html      # Grafo interativo PyVis
```

---

## 🧪 O Pipeline

### Fase 1 — Ingestão de dados do mercado
O usuário seleciona o cargo-alvo no dropdown. O sistema busca até **2000 vagas reais** daquele cargo específico na **Adzuna API (US)**, via paginação. As descrições em HTML são limpas e as skills são extraídas e normalizadas semanticamente — eliminando variações como `reactjs`, `react.js` e `ReactJS`, todas mapeadas para `react`.

### Fase 2 — Processamento do currículo
O usuário cola o texto bruto do currículo. A **Gemini API** atua como parser semântico exaustivo: lê o contexto e extrai todas as tecnologias, ferramentas e conceitos técnicos mencionados — inclusive os implícitos. Um fallback por regex garante extração mesmo sem a chave da API. As skills passam pela mesma normalização semântica da Fase 1 para garantir compatibilidade.

### Fase 3 — Grafo de conhecimento + motor de match
Os dados se conectam em um **Grafo de Conhecimento** via NetworkX com três tipos de nós: candidato, skills e cargo-alvo. O algoritmo calcula um **score ponderado** — cada skill vale proporcionalmente à sua frequência nas vagas reais do cargo. Os gaps são ordenados por impacto: a skill que mais aumentaria o score aparece primeiro. O grafo interativo é gerado via PyVis.

---

## 🎯 Como funciona o score

O score **não é uma contagem simples**. É uma soma ponderada:

```
score = Σ(peso das skills que você tem) / Σ(peso de todas as skills do cargo) × 100
```

O peso de cada skill é calculado pela frequência com que ela aparece nas vagas reais do cargo-alvo. Uma skill presente em 90% das vagas vale muito mais do que uma que aparece em 10%.

---

## 📊 Output

- **Score de aderência** — ex: `73% compatibilidade com Data Engineer`
- **Skills que você já tem** — lista das que batem com o cargo
- **Gaps por impacto** — skills ordenadas pelo quanto aumentam o score
- **Grafo interativo** — `output/career_graph.html` (abre no browser)

---

## 🛠️ Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python |
| IA / NLP | Google Gemini API |
| Grafos | NetworkX |
| Fonte de dados | Adzuna API (US) |
| Visualização | PyVis + Streamlit |
| Normalização semântica | Regex canônico + dicionário de aliases |