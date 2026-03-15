import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils.layout import CSS_GLOBAL, rodape

st.set_page_config(page_title="Atividade | BI Economico", page_icon="📊", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

with st.sidebar:
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Imagens", "impeto_Branco.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.markdown("---")
    st.markdown("**Navegação**")
    st.page_link("Home.py",                        label="🏠  Home")
    st.page_link("pages/1_Inflacao.py",            label="📊  Inflação")
    st.page_link("pages/2_Juros.py",               label="🏦  Juros")
    st.page_link("pages/3_Atividade.py",           label="📈  Atividade Econômica")
    st.page_link("pages/4_Mercado_Trabalho.py",    label="👷  Mercado de Trabalho")
    st.page_link("pages/5_Setor_Externo.py",       label="🌎  Setor Externo")
    st.markdown("---")
    st.caption("Fonte: BCB/SGS | IBGE/SIDRA | BCB/Focus")

st.title("Atividade")
st.info("🚧  Em construção — análises serão adicionadas em breve.")

rodape()
