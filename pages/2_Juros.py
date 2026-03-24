# =============================================================================
# pages/2_Juros.py — Juros e Política Monetária
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

from utils.dados   import get_juros, get_inflacao, get_focus_anual, ultimo_valor, METAS_BCB
from utils.analise import analisar_juro_real
from utils.layout  import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Juros | BI Econômico",
                   page_icon="🏦", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
ano_ini, ano_fim = 2019, datetime.today().year
series_sel = ["Selic_Meta", "CDI", "Poupanca"]

def _filtros():
    global ano_ini, ano_fim, series_sel
    st.markdown("**⚙️ Filtros — Juros**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2019, datetime.today().year)
    )
    series_sel = st.multiselect(
        "Séries para comparativo",
        ["Selic_Meta", "CDI", "Poupanca"],
        default=["Selic_Meta", "CDI", "Poupanca"]
    )

sidebar_padrao(pagina_atual="Juros", filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados de juros..."):
    df_juros = get_juros()
    df_infl  = get_inflacao()
    df_fa    = get_focus_anual()

# Filtrar período
di     = pd.Timestamp(f"{ano_ini}-01-01")
df_fim = pd.Timestamp(f"{ano_fim}-12-31")
df_j = df_juros[(df_juros.index >= di) & (df_juros.index <= df_fim)] if not df_juros.empty else df_juros
df_i = df_infl[(df_infl.index >= di) & (df_infl.index <= df_fim)] if not df_infl.empty else df_infl


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🏦 Juros — Política Monetária
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Selic · CDI · Juro real · Expectativas Focus · Ciclos de aperto e afrouxamento
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
selic_v,  _ = ultimo_valor(df_j, "Selic_Meta")
cdi_v,    _ = ultimo_valor(df_j, "CDI")
poupc_v,  _ = ultimo_valor(df_j, "Poupanca")
ipca_v,   _ = ultimo_valor(df_i, "IPCA_acum12m")

juro_real = None
if selic_v and ipca_v:
    juro_real = round(((1 + selic_v/100) / (1 + ipca_v/100) - 1) * 100, 2)

juro_exante = None
focus_ipca  = None
ano_at = datetime.today().year
if not df_fa.empty and selic_v:
    f = df_fa[(df_fa["Indicador"]=="IPCA") & (df_fa["DataReferencia"]==str(ano_at))]
    if not f.empty:
        focus_ipca  = round(float(f.sort_values("Data").iloc[-1]["Mediana"]), 2)
        juro_exante = round(((1 + selic_v/100) / (1 + focus_ipca/100) - 1) * 100, 2)

selic_focus = None
if not df_fa.empty:
    f = df_fa[(df_fa["Indicador"]=="Selic") & (df_fa["DataReferencia"]==str(ano_at))]
    if not f.empty:
        selic_focus = round(float(f.sort_values("Data").iloc[-1]["Mediana"]), 2)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Selic Meta", f"{selic_v:.2f}%" if selic_v else "—",
              delta="a.a.", delta_color="off")
with c2:
    st.metric("CDI", f"{cdi_v:.2f}%" if cdi_v else "—",
              delta="a.m.", delta_color="off")
with c3:
    st.metric("Juro Real", f"{juro_real:.2f}%" if juro_real else "—",
              delta="Selic - IPCA 12m", delta_color="off")
with c4:
    st.metric("Juro Real Ex-ante", f"{juro_exante:.2f}%" if juro_exante else "—",
              delta="Selic - Focus IPCA", delta_color="off")
with c5:
    st.metric("Selic Focus", f"{selic_focus:.2f}%" if selic_focus else "—",
              delta=f"Expectativa {ano_at}", delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
col_g1, col_g2 = st.columns([6, 4])

with col_g1:
    st.markdown("#### Selic Meta — Histórico e Ciclos")

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0F1117")
    ax.set_facecolor("#0F1117")

    if not df_j.empty and "Selic_Meta" in df_j.columns:
        s = df_j["Selic_Meta"].dropna()
        ax.plot(s.index, s.values, color="#00D4FF", lw=2.5,
                label="Selic Meta", zorder=5)
        ax.fill_between(s.index, s.values, alpha=0.08, color="#00D4FF")
        ax.scatter(s.index[-1], s.iloc[-1], color="#00D4FF", s=70, zorder=6)
        ax.annotate(f"  {s.iloc[-1]:.2f}%",
                    xy=(s.index[-1], s.iloc[-1]),
                    xytext=(8, 4), textcoords="offset points",
                    color="#00D4FF", fontsize=10, fontweight="bold")

    if (not df_j.empty and "Selic_Meta" in df_j.columns and
            not df_i.empty and "IPCA_acum12m" in df_i.columns):
        selic_s = df_j["Selic_Meta"].dropna()
        ipca_s  = df_i["IPCA_acum12m"].dropna()
        selic_df = selic_s.reset_index(); selic_df.columns = ["Data", "Selic"]
        ipca_df  = ipca_s.reset_index();  ipca_df.columns  = ["Data", "IPCA"]
        df_merge = pd.merge(selic_df, ipca_df, on="Data", how="inner")
        if not df_merge.empty:
            df_merge["JuroReal"] = ((1 + df_merge["Selic"]/100) /
                                    (1 + df_merge["IPCA"]/100) - 1) * 100
            ax.plot(df_merge["Data"], df_merge["JuroReal"],
                    color="#FFB800", lw=1.5, ls="--",
                    label="Juro Real (Selic - IPCA)", alpha=0.85)
            ax.axhline(0, color="#555", lw=0.8)

    ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax.tick_params(colors="#AAAAAA", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    plt.xticks(rotation=30, ha="right")
    for sp in ax.spines.values(): sp.set_edgecolor("#333")
    ax.set_ylabel("% a.a.", color="#AAAAAA", fontsize=9)
    ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
              labelcolor="#CCC", framealpha=0.9)
    plt.tight_layout()
    st.pyplot(fig); plt.close()


with col_g2:
    st.markdown("#### Comparativo de Taxas")

    CORES_SERIES = {
        "Selic_Meta": "#00D4FF",
        "CDI":        "#FFB800",
        "Poupanca":   "#00D4AA",
    }
    SERIES_MENSAIS = {"CDI", "Poupanca"}

    fig2, ax2 = plt.subplots(figsize=(7, 5))
    fig2.patch.set_facecolor("#0F1117")
    ax2.set_facecolor("#0F1117")

    for serie in series_sel:
        if serie in df_j.columns:
            s = df_j[serie].dropna()
            if len(s) == 0:
                continue
            if serie in SERIES_MENSAIS:
                s = ((1 + s/100)**12 - 1) * 100
                label = f"{serie.replace('_',' ')} (a.a.)"
            else:
                label = serie.replace("_", " ")
            ax2.plot(s.index, s.values,
                     color=CORES_SERIES.get(serie, "#AAAAAA"),
                     lw=2.0, label=label)
            ax2.annotate(f"  {s.iloc[-1]:.2f}%",
                         xy=(s.index[-1], s.iloc[-1]),
                         xytext=(5, 3), textcoords="offset points",
                         color=CORES_SERIES.get(serie, "#AAAAAA"),
                         fontsize=8, fontweight="bold")

    ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax2.tick_params(colors="#AAAAAA", labelsize=8)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    plt.xticks(rotation=30, ha="right")
    for sp in ax2.spines.values(): sp.set_edgecolor("#333")
    ax2.set_title("Selic × CDI × Poupança",
                  color="white", fontsize=11, fontweight="bold", pad=12)
    ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
               labelcolor="#CCC", framealpha=0.9)
    plt.tight_layout()
    st.pyplot(fig2); plt.close()

st.markdown("---")


# -----------------------------------------------------------------------------
# ANÁLISE AUTOMÁTICA + EXPECTATIVAS
# -----------------------------------------------------------------------------
col_t, col_e = st.columns([6, 4])

with col_t:
    st.markdown("#### Análise Automática")
    linhas = analisar_juro_real(selic_v, ipca_v, focus_ipca)
    st.markdown(linhas)

with col_e:
    st.markdown("#### Expectativas Focus — Selic")

    if not df_fa.empty:
        df_selic_focus = df_fa[df_fa["Indicador"] == "Selic"].copy()
        if not df_selic_focus.empty:
            anos_ref = sorted(df_selic_focus["DataReferencia"].unique())[-3:]
            for ar in anos_ref:
                df_ar = df_selic_focus[df_selic_focus["DataReferencia"] == ar]
                if not df_ar.empty:
                    v = round(float(df_ar.sort_values("Data").iloc[-1]["Mediana"]), 2)
                    st.metric(f"Selic {ar}", f"{v:.2f}%",
                              delta="Mediana Focus", delta_color="off")
    st.caption("BCB/Focus — mediana · última coleta disponível")

rodape()
