# BI Econômico Educacional

Painel de monitoramento da economia brasileira construído com Python + Streamlit.

## Estrutura do Projeto

```
bi_economico/
├── Home.py                    # Página inicial — resumo geral
├── pages/
│   ├── 1_Inflacao.py          # ✅ Inflação — IPCA, IGP-M, Focus, Grupos
│   ├── 2_Juros.py             # 🚧 Juros — Selic, CDI, Juro Real
│   ├── 3_Atividade.py         # 🚧 PIB, IBC-Br, Setores
│   ├── 4_Mercado_Trabalho.py  # 🚧 Desemprego, CAGED, Informalidade
│   ├── 5_Setor_Externo.py     # 🚧 Câmbio, Reservas, Balança
│   └── 6_Comparativos.py      # 🚧 Análises cruzadas
├── utils/
│   ├── dados.py               # Coleta e cache de todos os dados
│   ├── graficos.py            # Funções de visualização reutilizáveis
│   └── analise.py             # Geração automática de textos
├── .streamlit/
│   └── config.toml            # Tema global escuro
├── requirements.txt
└── README.md
```

## Fontes de Dados
- **BCB/SGS** — Séries temporais do Banco Central
- **IBGE/SIDRA** — PNAD Contínua, IPCA por grupos, PIB
- **BCB/Focus** — Expectativas de mercado (Relatório Focus)

## Como Rodar

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy (Streamlit Cloud)
1. Fork este repositório no GitHub
2. Acesse share.streamlit.io
3. Conecte o repositório
4. Defina `Home.py` como arquivo principal

## Status das Páginas
| Página | Status |
|---|---|
| Home | ✅ Completo |
| Inflação | ✅ Completo |
| Juros | 🚧 Em construção |
| Atividade | 🚧 Em construção |
| Mercado de Trabalho | 🚧 Em construção |
| Setor Externo | 🚧 Em construção |
| Comparativos | 🚧 Em construção |
