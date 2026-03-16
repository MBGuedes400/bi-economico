# =============================================================================
# pages/8_Analises_Reais.py — Análises Reais Avançadas
# Blocos: Hiato do Produto · Nowcasting · Yield Curve · Beveridge · Dívida/PIB
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Análises Reais | BI Econômico",
                   page_icon="🏗️", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

sidebar_padrao()

st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🏗️ Análises Reais Avançadas
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Hiato do produto · Nowcasting · Yield curve · Curva de Beveridge · Dívida/PIB
</p>
""", unsafe_allow_html=True)
st.markdown("---")

st.info("🚧 Em construção — será implementado em breve com: Hiato do Produto (Filtro HP), "
        "Nowcasting IBC-Br vs PIB, Yield Curve (LTN/NTN-B), Curva de Beveridge e decomposição Dívida/PIB.")

rodape()
