# =============================================================================
# utils/layout.py — Componentes de layout reutilizáveis
# =============================================================================

import streamlit as st
import os

# Mapeamento: nome_pagina → grupo
GRUPOS = {
    "Home":                 "visao_geral",
    "Inflacao":             "macro",
    "Juros":                "macro",
    "Atividade":            "macro",
    "Mercado_Trabalho":     "macro",
    "Setor_Externo":        "macro",
    "Comparativos":         "analises",
    "Analises_Monetarias":  "analises",
    "Analises_Reais":       "analises",
    "Acuracia_Focus":       "analises",
    # Onda 1
    "Ibovespa":             "mercado",
    "Fundos":               "mercado",
    "Liquidez":             "mercado",
    "Credito":              "mercado",
    "Commodities":          "mercado",
    # Onda 2
    "Industria":            "setorial",
    "Comercio":             "setorial",
    "Agropecuaria":         "setorial",
    # Onda 3
    "Internacional":        "internacional",
    "Cambios":              "internacional",
    "Commodities":          "internacional",
}


def sidebar_padrao(pagina_atual=None, filtros_extra=None):
    """
    Renderiza a sidebar com menu agrupado em expanders.
    pagina_atual: string com o nome da página (ex: 'Inflacao')
    filtros_extra: função opcional que adiciona filtros específicos da página.
    """
    # Determina o grupo da página atual para expandir automaticamente
    grupo_ativo = GRUPOS.get(pagina_atual, "visao_geral") if pagina_atual else None

    with st.sidebar:
        # Logo
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

        # ── GRUPO 1: Visão Geral ─────────────────────────────────────────
        with st.expander("🏠  Visão Geral",
                         expanded=(grupo_ativo == "visao_geral")):
            st.page_link("Home.py", label="🏠  Home")

        # ── GRUPO 2: Indicadores Macro ───────────────────────────────────
        with st.expander("📈  Indicadores Macro",
                         expanded=(grupo_ativo == "macro")):
            st.page_link("pages/1_Inflacao.py",
                         label="📊  Inflação")
            st.page_link("pages/2_Juros.py",
                         label="🏦  Juros")
            st.page_link("pages/3_Atividade.py",
                         label="📈  Atividade Econômica")
            st.page_link("pages/4_Mercado_Trabalho.py",
                         label="👷  Mercado de Trabalho")
            st.page_link("pages/5_Setor_Externo.py",
                         label="🌎  Setor Externo")

        # ── GRUPO 3: Análises Avançadas ──────────────────────────────────
        with st.expander("🔬  Análises Avançadas",
                         expanded=(grupo_ativo == "analises")):
            st.page_link("pages/6_Comparativos.py",
                         label="📊  Comparativos")
            st.page_link("pages/7_Analises_Monetarias.py",
                         label="🔬  Análises Monetárias")
            st.page_link("pages/8_Analises_Reais.py",
                         label="🏗️  Análises Reais")
            st.page_link("pages/9_Acuracia_Focus.py",
                         label="🎯  Acurácia Focus")

        # ── GRUPO 4: Mercado Financeiro ──────────────────────────────────
        with st.expander("💹  Mercado Financeiro",
                         expanded=(grupo_ativo == "mercado")):
            st.page_link("pages/10_Ibovespa.py",   label="📉  Ibovespa & Ações")
            st.page_link("pages/11_Fundos.py",      label="💼  Fundos de Investimento")
            st.page_link("pages/12_Liquidez.py",    label="💧  Liquidez & Meios de Pgto")
            st.page_link("pages/13_Credito.py",     label="🏧  Crédito & Inadimplência")
            st.page_link("pages/14_Commodities.py", label="🌽  Commodities")

        # ── GRUPO 5: Setorial ────────────────────────────────────────────
        with st.expander("🏭  Setorial",
                         expanded=(grupo_ativo == "setorial")):
            st.page_link("pages/15_Industria.py", label="⚙️  Produção Industrial")
            st.page_link("pages/16_Comercio.py",  label="🛒  Varejo & Confiança")
            st.markdown(
                "<span style='color:#555;font-size:0.8rem;padding-left:8px'>"
                "🚧 Agropecuária — em breve</span>", unsafe_allow_html=True)

        # ── GRUPO 6: Internacional ───────────────────────────────────────
        with st.expander("🌐  Internacional",
                         expanded=(grupo_ativo == "internacional")):
            st.page_link("pages/19_Cambios.py", label="💱  Câmbios & PPP")
            st.markdown(
                "<span style='color:#555;font-size:0.8rem;padding-left:8px'>"
                "🚧 PIB Global — em breve</span>", unsafe_allow_html=True)

        # Filtros da página
        if filtros_extra:
            filtros_extra()
            st.markdown("---")

        st.caption("Fonte: BCB/SGS | IBGE/SIDRA | BCB/Focus | Tesouro")
        st.caption("Atualizado a cada hora · Horário de Brasília (BRT)")


def rodape():
    """Rodapé padrão com assinatura."""
    st.markdown("---")
    st.markdown("""
<div style='text-align:center; padding: 0.5rem 0;'>
    <p style='color:#555555; font-size:0.8rem; margin:0;'>
        Dados: BCB/SGS · IBGE/SIDRA · BCB/Focus · Tesouro Transparente · Desenvolvido com Python + Streamlit
    </p>
    <p style='color:#444444; font-size:0.75rem; margin:4px 0 0;'>
        Desenvolvido por <strong style="color:#666666;">Impeto Gestão e Negócios</strong>
    </p>
</div>
""", unsafe_allow_html=True)


CSS_GLOBAL = """
<style>
/* Fundo geral */
.stApp { background-color: #0F1117; color: #CCCCCC; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1A1D27;
    overflow-y: auto !important;
}

/* Métricas */
[data-testid="stMetric"] {
    background-color: #1A1D27;
    border: 1px solid #2A2D3A;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: white; font-size: 1.6rem; }
[data-testid="stMetricLabel"] { color: #AAAAAA; font-size: 0.8rem; }

/* Títulos */
h1, h2, h3 { color: white; }

/* Card bloco */
.card-bloco {
    background: #1A1D27;
    border: 1px solid #2A2D3A;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
}

/* Expanders do menu — estilo compacto */
[data-testid="stSidebar"] .streamlit-expanderHeader {
    font-size: 0.88rem !important;
    padding: 6px 8px !important;
    background-color: #22263A !important;
    border-radius: 6px !important;
    margin-bottom: 2px !important;
    color: #CCCCCC !important;
}
[data-testid="stSidebar"] .streamlit-expanderContent {
    padding: 4px 0 4px 8px !important;
    border-left: 2px solid #2A2D3A !important;
    margin-left: 4px !important;
}

/* Links do menu */
[data-testid="stSidebar"] a {
    font-size: 0.85rem !important;
    padding: 3px 6px !important;
    color: #AAAAAA !important;
    display: block;
}
[data-testid="stSidebar"] a:hover {
    color: #00D4FF !important;
}

/* Esconde navegação automática do Streamlit */
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
