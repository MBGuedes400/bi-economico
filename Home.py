# =============================================================================
# Home.py — Página inicial do BI Econômico
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.dados import (
    get_inflacao, get_juros, get_cambio,
    get_pnad, get_focus_anual, ultimo_valor, focus_ultimo,
    METAS_BCB
)
from utils.analise import resumo_geral
from utils.layout  import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(
    page_title="BI Econômico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
sidebar_padrao()


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando indicadores..."):
    df_infl  = get_inflacao()
    df_juros = get_juros()
    df_camb  = get_cambio()
    df_fa    = get_focus_anual()
    try:
        df_pnad = get_pnad()
    except Exception:
        df_pnad = pd.DataFrame()


# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div style='text-align:center; padding: 1rem 0 0.5rem;'>
    <h1>📊 BI Econômico Brasileiro</h1>
    <p style='color:#AAAAAA; margin-top:-10px;'>
        Painel de monitoramento macroeconômico ·
        Atualizado em {datetime.now().strftime("%d/%m/%Y %H:%M")}
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

resumo = resumo_geral(df_infl, df_juros, df_camb, df_pnad, df_fa)
st.markdown(f"**Resumo:** {resumo}")
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
st.markdown("### Últimas leituras")

ano_ref  = datetime.today().year
meta_bcb = METAS_BCB.get(ano_ref, 3.0)

ipca_v,   _ = ultimo_valor(df_infl,  "IPCA_acum12m")
selic_v,  _ = ultimo_valor(df_juros, "Selic_Meta")
cdi_v,    _ = ultimo_valor(df_juros, "CDI")
usd_v,    _ = ultimo_valor(df_camb,  "USD_BRL")
desemp_v, _ = ultimo_valor(df_pnad,  "Taxa_Desocupacao")

def delta_v(df, col, n=1):
    if df is None or df.empty: return None
    if isinstance(df, pd.DataFrame):
        if col not in df.columns: return None
        s = df[col].dropna()
    else:
        s = df.dropna()
    if len(s) <= n: return None
    return round(float(s.iloc[-1] - s.iloc[-1-n]), 2)

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    d = delta_v(df_infl, "IPCA_acum12m")
    st.metric("IPCA 12m", f"{ipca_v:.2f}%" if ipca_v else "—",
              delta=f"{d:+.2f}pp" if d else None)
with c2:
    st.metric("Selic Meta", f"{selic_v:.2f}%" if selic_v else "—",
              delta="a.a.", delta_color="off")
with c3:
    st.metric("CDI", f"{cdi_v:.2f}%" if cdi_v else "—",
              delta="a.m.", delta_color="off")
with c4:
    d = delta_v(df_camb, "USD_BRL")
    st.metric("USD/BRL", f"R$ {usd_v:.2f}" if usd_v else "—",
              delta=f"{d:+.2f}" if d else None, delta_color="inverse")
with c5:
    st.metric("Desemprego", f"{desemp_v:.1f}%" if desemp_v else "—",
              delta="PNAD Contínua", delta_color="off")
with c6:
    st.metric("Meta BCB", f"{meta_bcb:.1f}%",
              delta=f"Teto: {meta_bcb+1.5:.1f}%", delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# CARDS DE NAVEGAÇÃO
# -----------------------------------------------------------------------------
st.markdown("### Análises por bloco")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""<div class="card-bloco">
        <h3>📊 Inflação</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        Comparativo IPCA × IGP-M × INPC · Decomposição por grupos ·
        Realizado vs Esperado (Focus) · Acumulados e tendências.
        </p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="card-bloco">
        <h3>🏦 Juros</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        Selic Meta e Over · CDI · Taxa real de juros ·
        Juro real ex-ante · Expectativa COPOM · Comparação histórica.
        </p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="card-bloco">
        <h3>📈 Atividade Econômica</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        PIB trimestral por setor · IBC-Br mensal ·
        Decomposição da demanda · Expectativas Focus · Ciclos econômicos.
        </p></div>""", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown("""<div class="card-bloco">
        <h3>👷 Mercado de Trabalho</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        Taxa de desocupação (PNAD) · Informalidade ·
        CAGED · Massa salarial real · Participação na força de trabalho.
        </p></div>""", unsafe_allow_html=True)
with col5:
    st.markdown("""<div class="card-bloco">
        <h3>🌎 Setor Externo</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        USD · EUR · CNY · Reservas internacionais ·
        Variação cambial acumulada · Pass-through cambial.
        </p></div>""", unsafe_allow_html=True)
with col6:
    st.markdown("""<div class="card-bloco">
        <h3>📊 Comparativos</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        Compare livremente indicadores de inflação · juros · câmbio ·
        atividade · emprego · correlação e eixo duplo automático.
        </p></div>""", unsafe_allow_html=True)

rodape()
