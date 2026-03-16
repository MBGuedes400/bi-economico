# =============================================================================
# utils/layout.py — Componentes de layout reutilizáveis
# =============================================================================

import streamlit as st
import os

def sidebar_padrao(filtros_extra=None):
    """
    Renderiza a sidebar padrão com logo, navegação e fonte dos dados.
    filtros_extra: função opcional que adiciona filtros específicos da página.
    """
    with st.sidebar:
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Imagens", "impeto_Branco.png"
        )
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("### 📊 BI Econômico")

        st.markdown("---")
        st.markdown("**Navegação**")

        st.page_link("Home.py",                               label="🏠  Home")
        st.page_link("pages/1_Inflacao.py",                   label="📊  Inflação")
        st.page_link("pages/2_Juros.py",                      label="🏦  Juros")
        st.page_link("pages/3_Atividade.py",                  label="📈  Atividade Econômica")
        st.page_link("pages/4_Mercado_Trabalho.py",           label="👷  Mercado de Trabalho")
        st.page_link("pages/5_Setor_Externo.py",              label="🌎  Setor Externo")
        st.page_link("pages/6_Comparativos.py",               label="📊  Comparativos")
        st.page_link("pages/7_Analises_Monetarias.py",        label="🔬  Análises Monetárias")
        st.page_link("pages/8_Analises_Reais.py",             label="🏗️  Análises Reais")
        st.page_link("pages/9_Acuracia_Focus.py",             label="🎯  Acurácia Focus")

        st.markdown("---")

        if filtros_extra:
            filtros_extra()
            st.markdown("---")

        st.caption("Fonte: BCB/SGS | IBGE/SIDRA | BCB/Focus")
        st.caption("Atualizado automaticamente a cada hora.")


def rodape():
    """Rodapé padrão com assinatura."""
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


CSS_GLOBAL = """
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
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
"""
