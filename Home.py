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

st.set_page_config(
    page_title="BI Econômico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background-color: #0F1117; color: #CCCCCC; }
[data-testid="stSidebar"] { background-color: #1A1D27; }
[data-testid="stMetric"] {
    background-color: #1A1D27;
    border: 1px solid #2A2D3A;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: white; font-size: 1.6rem; }
[data-testid="stMetricLabel"] { color: #AAAAAA; font-size: 0.8rem; }
h1, h2, h3 { color: white; }
.card-bloco {
    background: #1A1D27;
    border: 1px solid #2A2D3A;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
}
/* Esconder menu nativo do Streamlit */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    import os
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Imagens", "impeto_Branco.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("### 📊 BI Econômico")

    st.markdown("---")
    st.markdown("**Navegação**")
    st.caption("Selecione uma análise abaixo:")

    # Menu manual na posição correta
    st.page_link("Home.py",                          label="🏠  Home")
    st.page_link("pages/1_Inflacao.py",               label="📊  Inflação")
    st.page_link("pages/2_Juros.py",                  label="🏦  Juros")
    st.page_link("pages/3_Atividade.py",              label="📈  Atividade Econômica")
    st.page_link("pages/4_Mercado_Trabalho.py",       label="👷  Mercado de Trabalho")
    st.page_link("pages/5_Setor_Externo.py",          label="🌎  Setor Externo")

    st.markdown("---")
    st.caption("Fonte: BCB/SGS | IBGE/SIDRA | BCB/Focus")
    st.caption("Atualizado automaticamente a cada hora.")


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando indicadores..."):
    df_infl  = get_inflacao()
    df_juros = get_juros()
    df_camb  = get_cambio()
    df_fa    = get_focus_anual()
    # PNAD é lento — carrega separado com tratamento de erro
    try:
        df_pnad = get_pnad()
    except:
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

# Resumo executivo
resumo = resumo_geral(df_infl, df_juros, df_camb, df_pnad, df_fa)
st.markdown(f"**Resumo:** {resumo}")
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
st.markdown("### Últimas leituras")

ano_ref  = datetime.today().year
meta_bcb = METAS_BCB.get(ano_ref, 3.0)

ipca_v, _  = ultimo_valor(df_infl,  "IPCA_acum12m")
selic_v, _ = ultimo_valor(df_juros, "Selic_Meta")
cdi_v, _   = ultimo_valor(df_juros, "CDI")
usd_v, _   = ultimo_valor(df_camb,  "USD_BRL")
desemp_v, _ = ultimo_valor(df_pnad,  "Taxa_Desocupacao")

# Deltas
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
        <h3>🔭 Expectativas Focus</h3>
        <p style="color:#AAAAAA; font-size:0.9rem;">
        Consenso de mercado para IPCA · Selic · PIB · Câmbio ·
        Dispersão entre analistas · Evolução histórica.
        </p></div>""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align:center; padding: 0.5rem 0;'>
    <p style='color:#555555; font-size:0.8rem; margin:0;'>
        Dados: BCB/SGS · IBGE/SIDRA · BCB/Focus · Desenvolvido com Python + Streamlit
    </p>
    <p style='color:#444444; font-size:0.75rem; margin:4px 0 0;'>
        Desenvolvido por <strong style="color:#666666;">Impeto Gestão e Negócios</strong>
    </p>
</div>
""", unsafe_allow_html=True)
