# =============================================================================
# pages/11_Fundos.py — Fundos de Investimento
# Fonte: CVM dados abertos (informe diário + registro_fundo_classe RCVM 175)
# =============================================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from datetime import datetime

from utils.dados  import get_fundos_cvm, get_juros, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Fundos | BI Econômico", page_icon="💼", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2023, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2022, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2023, datetime.today().year))
sidebar_padrao(pagina_atual="Fundos", filtros_extra=_filtros)

with st.spinner("Carregando fundos CVM — primeira carga pode levar ~30s..."):
    df_fi = get_fundos_cvm(meses=18)
    df_jr = get_juros()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

if not df_fi.empty:
    df_fi.index = pd.to_datetime(df_fi.index)
    df_fif = df_fi[(df_fi.index >= dt_ini) & (df_fi.index <= dt_fim_)]
else:
    df_fif = pd.DataFrame()

# Cores e labels por categoria
CORES = {
    "Renda Fixa":   "#00D4FF",
    "Multimercado": "#FFB800",
    "Acoes":        "#FF4B6E",
    "Previdencia":  "#A78BFA",
    "FII":          "#00D4AA",
    "FIDC":         "#F59E0B",
    "FIP":          "#34D399",
    "Cambial":      "#F87171",
    "Outros":       "#555555",
}
LABELS = {
    "Renda Fixa":   "Renda Fixa",
    "Multimercado": "Multimercado",
    "Acoes":        "Ações",
    "Previdencia":  "Previdência",
    "FII":          "FII",
    "FIDC":         "FIDC",
    "FIP":          "FIP",
    "Cambial":      "Cambial",
    "Outros":       "Outros",
}

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    💼 Fundos de Investimento
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Patrimônio líquido · Captação líquida · Composição por categoria — CVM / ANBIMA
</p>""", unsafe_allow_html=True)
st.markdown("---")

if df_fi.empty:
    st.warning("Dados de fundos não disponíveis no momento.")
    rodape()
    st.stop()

# Colunas de PL e CL disponíveis
cats_pl = [c for c in df_fi.columns if not c.startswith("CL_") and c in CORES]
cats_cl = [c for c in df_fi.columns if c.startswith("CL_") and c[3:] in CORES]

# Última linha disponível
ultima = df_fi.iloc[-1]
total_pl = sum(ultima.get(c, 0) for c in cats_pl)

selic_v, _ = ultimo_valor(df_jr, "Selic_Meta") if not df_jr.empty else (None, None)

# =============================================================================
# KPIs
# =============================================================================
c1, c2, c3, c4, c5 = st.columns(5)
def fmt_bi(v):
    if pd.isna(v) or v == 0: return "—"
    return f"R$ {v/1000:.2f} tri" if v >= 1000 else f"R$ {v:.0f} bi"

with c1:
    st.metric("PL Total", fmt_bi(total_pl))
with c2:
    rf = ultima.get("Renda Fixa", 0)
    st.metric("Renda Fixa", fmt_bi(rf),
              delta=f"{rf/total_pl*100:.0f}% do total" if total_pl else None,
              delta_color="off")
with c3:
    mm = ultima.get("Multimercado", 0)
    st.metric("Multimercado", fmt_bi(mm),
              delta=f"{mm/total_pl*100:.0f}% do total" if total_pl else None,
              delta_color="off")
with c4:
    ac = ultima.get("Acoes", 0)
    st.metric("Ações", fmt_bi(ac),
              delta=f"{ac/total_pl*100:.0f}% do total" if total_pl else None,
              delta_color="off")
with c5:
    prev = ultima.get("Previdencia", 0)
    st.metric("Previdência", fmt_bi(prev),
              delta=f"{prev/total_pl*100:.0f}% do total" if total_pl else None,
              delta_color="off")

st.markdown("---")

# =============================================================================
# ANÁLISE INTERPRETATIVA DINÂMICA
# =============================================================================
if len(df_fi) >= 2 and total_pl > 0:
    pl_ini = sum(df_fi.iloc[0].get(c, 0) for c in cats_pl)
    var_pl = round((total_pl / pl_ini - 1) * 100, 1) if pl_ini > 0 else None

    # Categoria dominante e tendência
    dom_cat  = max(cats_pl, key=lambda c: ultima.get(c, 0))
    dom_pct  = round(ultima.get(dom_cat, 0) / total_pl * 100, 0)

    # Captação líquida do último mês
    cl_ultimo = {c[3:]: df_fif[c].iloc[-1] if not df_fif.empty and c in df_fif.columns else 0
                 for c in cats_cl}
    maior_entrada = max(cl_ultimo, key=cl_ultimo.get) if cl_ultimo else None
    maior_saida   = min(cl_ultimo, key=cl_ultimo.get) if cl_ultimo else None

    selic_txt = f"com Selic em **{selic_v:.1f}% a.a.**" if selic_v else ""

    st.info(
        f"**Panorama atual da indústria de fundos**\n\n"
        f"O patrimônio líquido total alcança **{fmt_bi(total_pl)}**"
        + (f" — {'alta' if (var_pl or 0) >= 0 else 'queda'} de **{abs(var_pl):.1f}%** no período. " if var_pl else ". ") +
        f"A **{LABELS.get(dom_cat, dom_cat)}** domina com **{dom_pct:.0f}%** do total, "
        f"{selic_txt} — juro real elevado torna a renda fixa mais atrativa que ativos de risco.\n\n"
        + (f"No último mês, a maior **entrada líquida** foi em **{LABELS.get(maior_entrada, maior_entrada)}** "
           f"({cl_ultimo.get(maior_entrada, 0):+.1f} bi) e a maior **saída** em "
           f"**{LABELS.get(maior_saida, maior_saida)}** ({cl_ultimo.get(maior_saida, 0):+.1f} bi). "
           f"Esse fluxo revela a preferência dos investidores no ciclo atual de juros."
           if maior_entrada and maior_saida else "")
    )

st.markdown("---")

# =============================================================================
# GRÁFICO 1 — Evolução PL por categoria (área empilhada) + Pizza composição
# =============================================================================
st.markdown("### Patrimônio líquido — evolução e composição")
st.caption("Cada categoria empilhada mostra sua contribuição ao PL total ao longo do tempo.")

col1, col2 = st.columns([6, 4])

cats_order = ["Renda Fixa", "Multimercado", "Previdencia", "Acoes", "FII", "FIDC", "FIP", "Cambial", "Outros"]
cats_disp  = [c for c in cats_order if c in cats_pl and c in df_fif.columns]

with col1:
    if not df_fif.empty and cats_disp:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        bottom = np.zeros(len(df_fif))
        for cat in cats_disp:
            vals = df_fif[cat].fillna(0).values
            ax.fill_between(df_fif.index, bottom, bottom + vals,
                            color=CORES.get(cat, "#555"), alpha=0.8,
                            label=LABELS.get(cat, cat))
            bottom += vals
        ax.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x,_: f"R$ {x/1000:.1f} tri" if x >= 1000 else f"R$ {x:.0f} bi"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.legend(fontsize=7.5, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9, ncol=2, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados insuficientes para o período.")

with col2:
    st.markdown("#### Composição atual")
    vals_p = [max(ultima.get(c, 0), 0) for c in cats_disp]
    if sum(vals_p) > 0:
        fig2, ax2 = plt.subplots(figsize=(7, 4.5))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        _, _, autotexts = ax2.pie(
            vals_p,
            labels=[LABELS.get(c, c) for c in cats_disp],
            colors=[CORES.get(c, "#555") for c in cats_disp],
            autopct=lambda p: f"{p:.0f}%" if p > 4 else "",
            startangle=90,
            textprops={"color": "#AAAAAA", "fontsize": 8})
        for at in autotexts:
            at.set_color("white"); at.set_fontsize(8)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

        # Tabela resumo abaixo da pizza
        rows = []
        for cat in cats_disp:
            v = ultima.get(cat, 0)
            if v > 0:
                rows.append({"Categoria": LABELS.get(cat, cat),
                             "PL (R$ bi)": f"{v:.0f}",
                             "% do total": f"{v/total_pl*100:.1f}%"})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")

# =============================================================================
# GRÁFICO 2 — Captação líquida: a bússola do fluxo de capital
# =============================================================================
st.markdown("### Captação líquida — para onde o dinheiro está indo")
st.caption(
    "Captação líquida = entradas − saídas. "
    "**Positivo** = investidores aportando. **Negativo** = saques superando aplicações. "
    "Revela a preferência dos investidores mês a mês e antecipa rotações de portfólio."
)

if not df_fif.empty and cats_cl:
    cats_cl_disp = [c for c in cats_cl if c in df_fif.columns and c[3:] in cats_disp]

    fig3, ax3 = plt.subplots(figsize=(12, 4.5))
    fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")

    for col_cl in cats_cl_disp:
        cat = col_cl[3:]
        s   = df_fif[col_cl].fillna(0)
        ax3.plot(df_fif.index, s.values,
                 color=CORES.get(cat, "#555"), lw=1.8,
                 label=LABELS.get(cat, cat), marker="o", ms=3)

    ax3.axhline(0, color="#555", lw=0.8)
    ax3.grid(True, color="#FFF", alpha=0.04, lw=0.5)
    ax3.tick_params(colors="#AAAAAA", labelsize=9)
    ax3.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x,_: f"R$ {x:.0f} bi"))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax3.set_ylabel("R$ bilhões", color="#AAAAAA", fontsize=9)
    plt.xticks(rotation=30, ha="right")
    for sp in ax3.spines.values(): sp.set_edgecolor("#333")
    ax3.legend(fontsize=7.5, facecolor="#1A1D27", edgecolor="#333",
               labelcolor="#CCC", framealpha=0.9, ncol=4)
    plt.tight_layout()
    st.pyplot(fig3); plt.close()

    # Análise da captação
    if not df_fif.empty and len(df_fif) >= 2:
        # Soma captação líquida no período
        soma_cl = {c[3:]: df_fif[c].sum() for c in cats_cl_disp if c in df_fif.columns}
        top_entrada = sorted(soma_cl.items(), key=lambda x: x[1], reverse=True)
        top_saida   = sorted(soma_cl.items(), key=lambda x: x[1])

        st.markdown(
            f"**No período selecionado:** "
            f"as categorias com maior **entrada líquida acumulada** foram "
            f"**{LABELS.get(top_entrada[0][0], top_entrada[0][0])}** "
            f"(R$ {top_entrada[0][1]:+.0f} bi)"
            + (f" e **{LABELS.get(top_entrada[1][0], top_entrada[1][0])}** "
               f"(R$ {top_entrada[1][1]:+.0f} bi)" if len(top_entrada) > 1 else "") +
            f". As maiores **saídas** foram de "
            f"**{LABELS.get(top_saida[0][0], top_saida[0][0])}** "
            f"(R$ {top_saida[0][1]:+.0f} bi)."
        )

st.markdown("---")

# =============================================================================
# DIDÁTICA: o que cada categoria significa
# =============================================================================
st.markdown("### Guia das categorias de fundos")
c_a, c_b, c_c = st.columns(3)
with c_a:
    st.markdown("""
**💰 Renda Fixa e Previdência**

Concentram o maior PL da indústria. Em ambiente de **juro real elevado** (Selic acima da inflação), são os campeões de captação — oferecem retorno alto com baixo risco.

Subtipos mais relevantes:
- **Duração Baixa**: menos sensível à variação de juros (DI, CDB)
- **Duração Livre / Crédito**: busca retorno maior via crédito privado (debêntures, CRIs)
- **Previdência RF**: isenção fiscal para longo prazo (PGBL/VGBL)

**O que monitorar:** quando a Selic cai, o dinheiro tende a migrar para categorias de maior risco.
""")
with c_b:
    st.markdown("""
**📊 Multimercado e Ações**

São os termômetros do **apetite por risco** da indústria.

- **Multimercado Livre / Macro**: gestores podem operar juros, câmbio, ações e derivativos — flexibilidade máxima
- **Multimercado L/S**: "long and short" — aposta em pares de ações, lucra mesmo em queda
- **Ações Livre**: alocação predominante em renda variável brasileira
- **Ações Invest. Exterior**: exposto a mercados internacionais

**Captação positiva em Ações** = mercado apostando em queda de juros e melhora de lucros corporativos.
""")
with c_c:
    st.markdown("""
**🏢 FII, FIDC e FIP**

Fundos estruturados com características específicas:

- **FII (Fundos Imobiliários)**: investem em imóveis ou títulos imobiliários. Distribuem rendimentos mensais isentos de IR para pessoas físicas. Negociados em bolsa como ações.
- **FIDC (Fundos de Recebíveis)**: compram direitos creditórios (duplicatas, mensalidades). Retorno atrelado ao crédito — risco de inadimplência.
- **FIP (Private Equity)**: investem em empresas fechadas. Ilíquidos, longo prazo. Reservados a investidores qualificados.

**PL de FIIs** reage inversamente aos juros: juro alto = concorrência com renda fixa, pressão sobre cotas.
""")

rodape()
