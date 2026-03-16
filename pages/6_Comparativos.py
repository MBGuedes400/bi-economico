# =============================================================================
# pages/6_Comparativos.py — Análise Comparativa entre Indicadores
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

from utils.dados  import (get_inflacao, get_juros, get_cambio,
                           get_ibcbr, get_caged, get_pnad, ultimo_valor)
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Comparativos | BI Econômico",
                   page_icon="📊", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CATÁLOGO DE INDICADORES
# -----------------------------------------------------------------------------
CATALOGO = {
    "IPCA (% a.m.)":            ("inflacao",  "IPCA",              "% a.m."),
    "IPCA Acum. 12m (%)":       ("inflacao",  "IPCA_acum12m",      "% a.a."),
    "IGP-M (% a.m.)":           ("inflacao",  "IGPM",              "% a.m."),
    "IGP-M Acum. 12m (%)":      ("inflacao",  "IGPM_acum12m",      "% a.a."),
    "INPC (% a.m.)":            ("inflacao",  "INPC",              "% a.m."),
    "Selic Meta (% a.a.)":      ("juros",     "Selic_Meta",        "% a.a."),
    "Selic Over (% a.a.)":      ("juros",     "Selic_Over",        "% a.a."),
    "CDI (% a.m.)":             ("juros",     "CDI",               "% a.m."),
    "Poupança (% a.m.)":        ("juros",     "Poupanca",          "% a.m."),
    "USD / BRL":                ("cambio",    "USD_BRL",           "R$"),
    "EUR / BRL":                ("cambio",    "EUR_BRL",           "R$"),
    "CNY / BRL":                ("cambio",    "CNY_BRL",           "R$"),
    "GBP / BRL":                ("cambio",    "GBP_BRL",           "R$"),
    "IBC-Br (índice)":          ("ibcbr",     "IBC_Br",            "índice"),
    "CAGED Saldo (mil)":        ("caged",     "CAGED_Saldo",       "mil vagas"),
    "Massa Salarial (índice)":  ("caged",     "Massa_Salarial",    "índice"),
    "Taxa Desocupação (%)":     ("pnad",      "Taxa_Desocupacao",  "% pop."),
    "Taxa Informalidade (%)":   ("pnad",      "Taxa_Informalidade","% ocup."),
}

GRUPOS = {
    "🔥 Inflação × Juros":      ["IPCA Acum. 12m (%)", "IGP-M Acum. 12m (%)", "Selic Meta (% a.a.)"],
    "💱 Câmbio × Inflação":     ["USD / BRL", "IPCA Acum. 12m (%)"],
    "📈 Atividade × Emprego":   ["IBC-Br (índice)", "Taxa Desocupação (%)", "CAGED Saldo (mil)"],
    "🏦 Juros × Câmbio":        ["Selic Meta (% a.a.)", "USD / BRL"],
    "💰 Renda × Informalidade": ["Massa Salarial (índice)", "Taxa Informalidade (%)"],
}

CORES_PLOT = ["#00D4FF", "#FFB800", "#00D4AA", "#FF4B6E", "#A78BFA", "#FF9F43"]


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
grupo_sel  = "— selecionar manualmente —"
ano_ini, ano_fim = 2019, datetime.today().year
normalizar = False

def _filtros():
    global grupo_sel, ano_ini, ano_fim, normalizar
    st.markdown("**⚙️ Filtros — Comparativos**")
    grupo_opcoes = ["— selecionar manualmente —"] + list(GRUPOS.keys())
    grupo_sel = st.selectbox("Grupo pré-definido", grupo_opcoes, index=0)
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2019, datetime.today().year)
    )
    normalizar = st.toggle("Normalizar séries (base 100)", value=False,
                           help="Rebasa todas as séries para 100 no início do período.")

sidebar_padrao(filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    📊 Comparativos
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Compare livremente indicadores de inflação · juros · câmbio · atividade · emprego
</p>
""", unsafe_allow_html=True)
st.markdown("---")

default_ind = GRUPOS.get(grupo_sel, []) if grupo_sel != "— selecionar manualmente —" else []

indicadores_sel = st.multiselect(
    "Selecione os indicadores para comparar (máx. 6)",
    options=list(CATALOGO.keys()),
    default=default_ind,
    max_selections=6,
)

if not indicadores_sel:
    st.info("👆 Selecione ao menos um indicador acima, ou escolha um grupo pré-definido no painel lateral.")
    rodape()
    st.stop()

st.markdown("---")


# -----------------------------------------------------------------------------
# COLETA DE DADOS
# -----------------------------------------------------------------------------
GETTERS = {
    "inflacao": get_inflacao,
    "juros":    get_juros,
    "cambio":   get_cambio,
    "ibcbr":    get_ibcbr,
    "caged":    get_caged,
    "pnad":     get_pnad,
}

fontes_necessarias = set(CATALOGO[ind][0] for ind in indicadores_sel)

cache_dfs = {}
with st.spinner("Carregando dados..."):
    for fonte in fontes_necessarias:
        cache_dfs[fonte] = GETTERS[fonte]()

    # Corrigir reservas (milhões → bilhões) — removida do catálogo, mas mantém por segurança
    if "cambio" in cache_dfs and not cache_dfs["cambio"].empty:
        df_cam = cache_dfs["cambio"]
        if "Reservas_USD_bi" in df_cam.columns:
            if df_cam["Reservas_USD_bi"].dropna().median() > 10000:
                df_cam["Reservas_USD_bi"] = df_cam["Reservas_USD_bi"] / 1000


# -----------------------------------------------------------------------------
# MONTA SÉRIES FILTRADAS
# -----------------------------------------------------------------------------
di   = pd.Timestamp(f"{ano_ini}-01-01")
dfim = pd.Timestamp(f"{ano_fim}-12-31")

series   = {}
unidades = {}

for ind in indicadores_sel:
    fonte, col, unid = CATALOGO[ind]
    df = cache_dfs.get(fonte, pd.DataFrame())
    if df is None or df.empty or col not in df.columns:
        continue
    df.index = pd.to_datetime(df.index)
    s = df[col].dropna()
    s = s[(s.index >= di) & (s.index <= dfim)]
    if s.empty:
        continue
    if normalizar:
        base = s.iloc[0]
        if base != 0:
            s = (s / base) * 100
    series[ind]   = s
    unidades[ind] = "base 100" if normalizar else unid

if not series:
    st.warning("Nenhum dado disponível para os indicadores e período selecionados.")
    rodape()
    st.stop()


# -----------------------------------------------------------------------------
# EIXO DUPLO OU ÚNICO
# -----------------------------------------------------------------------------
unids_unicas    = list(dict.fromkeys(unidades.values()))
usar_eixo_duplo = (not normalizar) and (len(unids_unicas) >= 2) and (len(series) >= 2)

inds_eixo1 = list(series.keys())
inds_eixo2 = []

if usar_eixo_duplo:
    inds_eixo1 = [i for i in series if unidades[i] == unids_unicas[0]]
    inds_eixo2 = [i for i in series if unidades[i] == unids_unicas[1]]


# -----------------------------------------------------------------------------
# GRÁFICO COMPARATIVO
# -----------------------------------------------------------------------------
titulo_graf = " × ".join(indicadores_sel[:3])
if len(indicadores_sel) > 3:
    titulo_graf += f" + {len(indicadores_sel)-3} mais"

st.markdown(f"#### {titulo_graf}")

fig, ax1 = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor("#0F1117")
ax1.set_facecolor("#0F1117")

linhas_legenda = []
cor_idx = 0

for ind in inds_eixo1:
    cor = CORES_PLOT[cor_idx % len(CORES_PLOT)]
    l,  = ax1.plot(series[ind].index, series[ind].values,
                   color=cor, lw=2.0, marker="o", ms=2, label=ind)
    linhas_legenda.append(l)
    cor_idx += 1

ax1.grid(True, color="#FFF", alpha=0.05, lw=0.5)
ax1.tick_params(colors="#AAAAAA", labelsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
plt.xticks(rotation=30, ha="right")
for sp in ax1.spines.values(): sp.set_edgecolor("#333")
ax1.set_ylabel(unids_unicas[0] if unids_unicas else "", color="#AAAAAA", fontsize=9)

if usar_eixo_duplo and inds_eixo2:
    ax2 = ax1.twinx()
    ax2.set_facecolor("#0F1117")
    for sp in ax2.spines.values(): sp.set_edgecolor("#333")
    for ind in inds_eixo2:
        cor = CORES_PLOT[cor_idx % len(CORES_PLOT)]
        l,  = ax2.plot(series[ind].index, series[ind].values,
                       color=cor, lw=2.0, marker="o", ms=2, ls="--", label=f"{ind} →")
        linhas_legenda.append(l)
        cor_idx += 1
    ax2.tick_params(colors="#AAAAAA", labelsize=9)
    ax2.set_ylabel(unids_unicas[1] if len(unids_unicas) > 1 else "", color="#AAAAAA", fontsize=9)

labels = [l.get_label() for l in linhas_legenda]
ax1.legend(linhas_legenda, labels, fontsize=8, facecolor="#1A1D27", edgecolor="#333",
           labelcolor="#CCC", framealpha=0.9, loc="upper left")

if usar_eixo_duplo and inds_eixo2:
    ax1.annotate("── eixo esquerdo   - - eixo direito",
                 xy=(0.01, 0.02), xycoords="axes fraction", color="#666", fontsize=7)

plt.tight_layout()
st.pyplot(fig); plt.close()

if usar_eixo_duplo and inds_eixo2:
    st.caption(f"📌 Eixo esquerdo: {unids_unicas[0]} · Eixo direito (tracejado): {unids_unicas[1]}")

st.markdown("---")


# -----------------------------------------------------------------------------
# TABELA RESUMO
# -----------------------------------------------------------------------------
st.markdown("#### Últimos Valores Disponíveis")

rows = []
for ind in indicadores_sel:
    fonte, col, unid = CATALOGO[ind]
    df = cache_dfs.get(fonte, pd.DataFrame())
    if df is None or df.empty or col not in df.columns:
        rows.append({"Indicador": ind, "Último valor": "—", "Data": "—", "Unidade": unid})
        continue
    v, d = ultimo_valor(df, col)
    v_str = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if v else "—"
    d_str = d.strftime("%b/%Y") if d else "—"
    rows.append({"Indicador": ind, "Último valor": v_str, "Data": d_str, "Unidade": unid})

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# CORRELAÇÃO
# -----------------------------------------------------------------------------
if len(series) >= 2:
    st.markdown("#### Correlação entre Indicadores")
    df_corr = pd.DataFrame({ind: s for ind, s in series.items()}).dropna()

    if len(df_corr) >= 6:
        corr = df_corr.corr().round(2)
        n    = len(corr)
        fig3, ax3 = plt.subplots(figsize=(min(n * 2.2, 10), min(n * 1.8, 8)))
        fig3.patch.set_facecolor("#0F1117")
        ax3.set_facecolor("#1A1D27")
        im = ax3.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
        labels_corr = [l[:22] + "…" if len(l) > 22 else l for l in corr.columns]
        ax3.set_xticks(range(n)); ax3.set_yticks(range(n))
        ax3.set_xticklabels(labels_corr, rotation=30, ha="right", color="#AAAAAA", fontsize=8)
        ax3.set_yticklabels(labels_corr, color="#AAAAAA", fontsize=8)
        for i in range(n):
            for j in range(n):
                val = corr.values[i, j]
                ax3.text(j, i, f"{val:.2f}", ha="center", va="center",
                         color="black" if abs(val) > 0.6 else "white",
                         fontsize=9, fontweight="bold")
        plt.colorbar(im, ax=ax3, fraction=0.03, pad=0.04)
        plt.tight_layout()
        st.pyplot(fig3); plt.close()
        st.caption("🟢 Correlação positiva forte  ·  🔴 Correlação negativa forte  ·  Valores entre -1 e 1")
    else:
        st.info("Período muito curto para calcular correlação — aumente o intervalo no filtro.")

rodape()
