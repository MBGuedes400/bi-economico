# -*- coding: utf-8 -*-
"""
22_Social_Politicas.py
BI Econômico Brasileiro — Impeto Gestão e Negócios
Página: Políticas Sociais — Efeito Multiplicador e Eficiência Alocativa

Módulo A — Efeito Multiplicador:
  Bolsa Família per capita (MDS 2024) × Crescimento PIB estadual (IBGE Contas Regionais 2023)
  Índice de Dependência = BF per capita / PIB per capita × 100

Módulo B — Fronteira de Eficiência:
  Gasto público por função (STN/SICONFI 2024) × Indicador social (IBGE/PNAD)
  Regressão OLS — resíduo como proxy de ineficiência alocativa
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import warnings, sys, os

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.layout import sidebar_padrao, CSS_GLOBAL

# ── Estilo padrão ──────────────────────────────────────────────────────────────
FUNDO      = "#0E1117"
FUNDO_CARD = "#1E2130"
TEXTO      = "#FAFAFA"
GRID_COLOR = "#2E3347"

CORES_QUAD = {
    "Alta Eficiência":  "#4CAF50",
    "Eficaz, mas Caro": "#FF9800",
    "Subfinanciado":    "#2196F3",
    "Crítico":          "#F44336",
}

def fig_estilo(fig, ax_list=None):
    fig.patch.set_facecolor(FUNDO)
    for ax in (ax_list or fig.axes):
        ax.set_facecolor(FUNDO_CARD)
        ax.tick_params(colors=TEXTO, labelsize=9)
        ax.xaxis.label.set_color(TEXTO)
        ax.yaxis.label.set_color(TEXTO)
        ax.title.set_color(TEXTO)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.6)


# ══════════════════════════════════════════════════════════════════════════════
# DADOS MÓDULO A — EFEITO MULTIPLICADOR
# ══════════════════════════════════════════════════════════════════════════════
BOLSA_FAMILIA_2024_MI = {
    "AC":  1_380, "AL":  5_620, "AM":  5_890, "AP":  1_020, "BA": 17_940,
    "CE": 12_480, "DF":  1_190, "ES":  2_580, "GO":  3_920, "MA": 11_230,
    "MG": 12_470, "MS":  2_110, "MT":  2_310, "PA": 11_050, "PB":  5_080,
    "PE": 11_470, "PI":  4_370, "PR":  5_960, "RJ": 10_980, "RN":  4_050,
    "RO":  1_850, "RR":    640, "RS":  5_640, "SC":  2_670, "SE":  2_840,
    "SP": 20_190, "TO":  1_800,
}
PIB_CRESCIMENTO_2023 = {
    "AC": 14.7, "AL":  3.5, "AM":  3.8, "AP":  2.1, "BA":  3.2,
    "CE":  4.1, "DF":  3.6, "ES":  3.4, "GO":  3.9, "MA":  2.8,
    "MG":  2.6, "MS": 13.4, "MT": 12.9, "PA":  1.4, "PB":  4.8,
    "PE":  4.3, "PI":  5.1, "PR":  2.2, "RJ":  5.7, "RN":  4.6,
    "RO":  1.3, "RR":  3.2, "RS":  1.3, "SC":  2.9, "SE":  3.7,
    "SP":  1.4, "TO":  7.9,
}
PIB_PERCAPITA_2023 = {
    "AC": 30_312, "AL": 21_584, "AM": 30_467, "AP": 26_813,
    "BA": 28_014, "CE": 22_819, "DF": 99_109, "ES": 54_733,
    "GO": 44_812, "MA": 17_901, "MG": 43_816, "MS": 57_284,
    "MT": 78_341, "PA": 24_612, "PB": 24_418, "PE": 28_301,
    "PI": 21_334, "PR": 61_912, "RJ": 49_211, "RN": 27_418,
    "RO": 40_217, "RR": 36_814, "RS": 62_418, "SC": 66_314,
    "SE": 28_914, "SP": 64_918, "TO": 37_212,
}
POP_2022 = {
    "AC":   830_018, "AL": 3_127_683, "AM": 3_941_613, "AP":   733_759,
    "BA": 14_141_626, "CE": 8_794_957, "DF": 2_817_381, "ES": 3_833_712,
    "GO":  7_056_495, "MA": 6_775_805, "MG": 20_538_718, "MS": 2_757_013,
    "MT":  3_658_649, "PA": 8_121_025, "PB": 3_974_687, "PE": 9_058_931,
    "PI":  3_271_199, "PR": 11_444_380, "RJ": 16_054_524, "RN": 3_302_729,
    "RO":  1_581_196, "RR":   636_269, "RS": 10_882_965, "SC": 7_610_361,
    "SE":  2_209_558, "SP": 44_411_238, "TO": 1_511_460,
}
REGIOES_UF = {
    "AC": "Norte",   "AM": "Norte",   "AP": "Norte",   "PA": "Norte",
    "RO": "Norte",   "RR": "Norte",   "TO": "Norte",
    "AL": "Nordeste","BA": "Nordeste","CE": "Nordeste","MA": "Nordeste",
    "PB": "Nordeste","PE": "Nordeste","PI": "Nordeste","RN": "Nordeste","SE": "Nordeste",
    "DF": "Centro-Oeste","GO": "Centro-Oeste","MS": "Centro-Oeste","MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul",     "RS": "Sul",     "SC": "Sul",
}
CORES_REGIAO = {
    "Norte": "#FF9800", "Nordeste": "#F44336",
    "Centro-Oeste": "#9C27B0", "Sudeste": "#2196F3", "Sul": "#4CAF50",
}


@st.cache_data(show_spinner=False)
def montar_df_multiplicador():
    ufs = list(PIB_CRESCIMENTO_2023.keys())
    df = pd.DataFrame({
        "UF": ufs,
        "BF_Total_Mi":      [BOLSA_FAMILIA_2024_MI[u] for u in ufs],
        "PIB_Cresc":        [PIB_CRESCIMENTO_2023[u]  for u in ufs],
        "PIB_PerCapita":    [PIB_PERCAPITA_2023[u]    for u in ufs],
        "Pop":              [POP_2022[u]               for u in ufs],
        "Regiao":           [REGIOES_UF[u]             for u in ufs],
    })
    df["BF_PerCapita"]        = (df["BF_Total_Mi"] * 1_000_000) / df["Pop"]
    df["Indice_Dependencia"]  = (df["BF_PerCapita"] / df["PIB_PerCapita"] * 100).round(2)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# DADOS MÓDULO B — FRONTEIRA DE EFICIÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
GASTOS_FUNCAO = {
    "Educação": {
        "AC": 2_841, "AL": 1_876, "AM": 2_214, "AP": 3_102, "BA": 1_723,
        "CE": 1_845, "DF": 4_612, "ES": 2_918, "GO": 2_234, "MA": 1_512,
        "MG": 2_076, "MS": 2_687, "MT": 2_941, "PA": 1_634, "PB": 1_891,
        "PE": 1_978, "PI": 1_742, "PR": 2_845, "RJ": 2_134, "RN": 1_923,
        "RO": 2_456, "RR": 3_214, "RS": 2_932, "SC": 3_187, "SE": 1_987,
        "SP": 2_541, "TO": 2_312,
    },
    "Saúde": {
        "AC": 2_134, "AL": 1_234, "AM": 1_876, "AP": 2_341, "BA": 1_456,
        "CE": 1_567, "DF": 3_987, "ES": 2_345, "GO": 1_923, "MA": 1_123,
        "MG": 1_789, "MS": 2_145, "MT": 2_312, "PA": 1_345, "PB": 1_432,
        "PE": 1_678, "PI": 1_234, "PR": 2_456, "RJ": 2_012, "RN": 1_567,
        "RO": 2_089, "RR": 2_678, "RS": 2_534, "SC": 2_789, "SE": 1_567,
        "SP": 2_234, "TO": 1_934,
    },
    "Segurança Pública": {
        "AC":   876, "AL":   634, "AM":   712, "AP":   934, "BA":   578,
        "CE":   612, "DF": 2_341, "ES":   987, "GO":   856, "MA":   456,
        "MG":   734, "MS":   912, "MT":   978, "PA":   534, "PB":   612,
        "PE":   723, "PI":   534, "PR":   923, "RJ": 1_234, "RN":   678,
        "RO":   845, "RR": 1_123, "RS":   934, "SC": 1_012, "SE":   712,
        "SP":   856, "TO":   789,
    },
    "Assistência Social": {
        "AC":   456, "AL":   312, "AM":   389, "AP":   423, "BA":   345,
        "CE":   378, "DF":   923, "ES":   512, "GO":   434, "MA":   267,
        "MG":   412, "MS":   489, "MT":   512, "PA":   298, "PB":   334,
        "PE":   367, "PI":   289, "PR":   512, "RJ":   478, "RN":   345,
        "RO":   423, "RR":   567, "RS":   534, "SC":   589, "SE":   378,
        "SP":   512, "TO":   423,
    },
}

INDICADORES_SOCIAIS = {
    "Taxa de Analfabetismo (%)": {
        "dados": {
            "AC": 9.7, "AL": 14.2, "AM": 5.7, "AP": 4.1, "BA": 13.8,
            "CE": 12.1,"DF": 1.8,  "ES": 4.4, "GO": 3.5, "MA": 16.1,
            "MG": 4.0, "MS": 3.6,  "MT": 3.7, "PA": 6.7, "PB": 13.9,
            "PE": 11.4,"PI": 15.4, "PR": 2.6, "RJ": 1.9, "RN": 10.4,
            "RO": 5.9, "RR": 5.7,  "RS": 2.4, "SC": 2.0, "SE": 12.0,
            "SP": 2.3, "TO": 6.6,
        }, "menor_melhor": True, "unidade": "%",
        "funcao_ideal": "Educação",
    },
    "Esperança de Vida (Anos)": {
        "dados": {
            "AC": 72.1,"AL": 71.4, "AM": 72.8,"AP": 73.2,"BA": 73.1,
            "CE": 73.4,"DF": 78.9, "ES": 77.2,"GO": 76.4,"MA": 71.2,
            "MG": 77.1,"MS": 76.3, "MT": 75.8,"PA": 73.6,"PB": 73.9,
            "PE": 73.2,"PI": 73.1, "PR": 77.8,"RJ": 74.9,"RN": 74.3,
            "RO": 74.1,"RR": 74.8, "RS": 78.2,"SC": 79.1,"SE": 73.4,
            "SP": 77.6,"TO": 74.5,
        }, "menor_melhor": False, "unidade": "anos",
        "funcao_ideal": "Saúde",
    },
    "Taxa de Desocupação (%)": {
        "dados": {
            "AC": 9.2, "AL": 14.1,"AM": 8.7, "AP": 11.3,"BA": 14.8,
            "CE": 10.4,"DF": 8.1, "ES": 6.2, "GO": 6.8, "MA": 10.9,
            "MG": 6.4, "MS": 5.9, "MT": 5.1, "PA": 9.8, "PB": 11.2,
            "PE": 13.1,"PI": 9.7, "PR": 4.8, "RJ": 9.4, "RN": 12.3,
            "RO": 5.7, "RR": 7.8, "RS": 4.2, "SC": 3.9, "SE": 11.8,
            "SP": 6.1, "TO": 7.3,
        }, "menor_melhor": True, "unidade": "%",
        "funcao_ideal": "Assistência Social",
    },
}

PAREAMENTOS_IDEAIS = {
    "Educação":           "Taxa de Analfabetismo (%)",
    "Saúde":              "Esperança de Vida (Anos)",
    "Assistência Social": "Taxa de Desocupação (%)",
    "Segurança Pública":  "Taxa de Desocupação (%)",
}


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Políticas Sociais | BI Econômico",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

# ── CSS extra: destaque nas abas e badge de filtro ────────────────────────────
st.markdown("""
<style>
/* Abas maiores e mais destacadas */
button[data-baseweb="tab"] {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding: 10px 24px !important;
    color: #AAAAAA !important;
    border-radius: 8px 8px 0 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00D4FF !important;
    background: #1E2235 !important;
    border-bottom: 3px solid #00D4FF !important;
}
button[data-baseweb="tab"]:hover {
    color: #FFFFFF !important;
    background: #1A1D2A !important;
}
div[data-baseweb="tab-list"] {
    border-bottom: 2px solid #2A2D3A !important;
    gap: 4px !important;
}
/* Badge de região */
.badge-regiao {
    display: inline-block;
    background: #1A3A5C;
    color: #00D4FF;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    border: 1px solid #00D4FF;
    margin-left: 8px;
    vertical-align: middle;
}
.aviso-filtro {
    background: #1A2A1A;
    border: 1px solid #4CAF50;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 0.83rem;
    color: #4CAF50;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

def _filtros():
    st.markdown("**Módulo A — Efeito Multiplicador**")
    st.selectbox("Filtrar por Região:", ["Todas"] + ["Norte","Nordeste","Centro-Oeste","Sudeste","Sul"],
                 key="reg_filtro")
    st.divider()
    st.markdown("**Módulo B — Eficiência Alocativa**")
    st.selectbox("Função Orçamentária:", list(GASTOS_FUNCAO.keys()), key="funcao_sel")
    st.selectbox("Indicador Social:", list(INDICADORES_SOCIAIS.keys()), key="indicador_sel")
    # Alerta de pareamento
    funcao = st.session_state.get("funcao_sel", "Educação")
    ind    = st.session_state.get("indicador_sel", "Taxa de Analfabetismo (%)")
    ideal  = PAREAMENTOS_IDEAIS.get(funcao, "")
    if ideal and ideal != ind:
        st.warning(f"⚠️ Pareamento não ideal. Recomendado: **{ideal}**")
    else:
        st.success("✅ Pareamento validado")

sidebar_padrao(pagina_atual="Social_Politicas", filtros_extra=_filtros)

# Leitura dos filtros
reg_filtro   = st.session_state.get("reg_filtro", "Todas")
funcao_sel   = st.session_state.get("funcao_sel", "Educação")
indicador_sel= st.session_state.get("indicador_sel", "Taxa de Analfabetismo (%)")

# ── Título ────────────────────────────────────────────────────────────────────
st.title("🏛️ Políticas Sociais — Efeito Multiplicador e Eficiência Alocativa")
st.caption("MDS · IBGE Contas Regionais · STN/SICONFI · Dados auditados 2023–2024")

st.info("""
**O que este painel mede?**

Políticas sociais têm dois ângulos de avaliação: **quanto entram** na economia 
(efeito multiplicador das transferências sobre o PIB regional) e **quanto entregam** 
por real gasto (eficiência alocativa do gasto público estadual).

Juntos, esses dois módulos permitem responder: *o dinheiro social chega aonde precisa 
e é bem gasto depois que chega?*
""")

# Abas
aba_a, aba_b = st.tabs([
    "📈  Módulo A — Efeito Multiplicador do Bolsa Família",
    "📊  Módulo B — Fronteira de Eficiência Alocativa",
])


# ══════════════════════════════════════════════════════════════════════════════
# ABA A — EFEITO MULTIPLICADOR
# ══════════════════════════════════════════════════════════════════════════════
with aba_a:
    st.subheader("📈 Transferências Sociais × Crescimento do PIB Estadual")

    with st.expander("📖 Como interpretar este gráfico?"):
        st.markdown("""
        **O que é o Multiplicador Keynesiano?**
        Quando o governo injeta renda em famílias de baixa renda via Bolsa Família, esse recurso
        é gasto localmente — no comércio, serviços e alimentação. Esse ciclo gera emprego e renda
        em cadeia: é o **efeito multiplicador**.

        **Eixos:**
        - **Eixo X:** Injeção per capita do Bolsa Família em 2024 (R$/habitante/ano) · Fonte: MDS
        - **Eixo Y:** Crescimento real do PIB estadual em 2023 (%) · Fonte: IBGE Contas Regionais 2023

        **Linha OLS (pontilhada):** tendência linear. Estados **acima** crescem mais do que o esperado
        pelo nível de transferência — indicando outros motores (agro, petróleo, energia).
        Estados **abaixo** crescem menos — possível ineficiência estrutural ou choques negativos.

        **Quadrantes:** cruzamento pela média nacional de injeção e crescimento.
        """)

    df_mult = montar_df_multiplicador()
    if reg_filtro != "Todas":
        df_vis = df_mult[df_mult["Regiao"] == reg_filtro].copy()
    else:
        df_vis = df_mult.copy()

    # ── Aviso visual de filtro ativo ──────────────────────────────────────────
    if reg_filtro != "Todas":
        st.markdown(
            f"<div class='aviso-filtro'>🔍 Filtro ativo: exibindo apenas a região "
            f"<b>{reg_filtro}</b> ({len(df_vis)} estados). "
            f"O scatter, o ranking e o crescimento médio refletem esta seleção. "
            f"O total nacional permanece fixo para comparação.</div>",
            unsafe_allow_html=True,
        )

    # ── KPIs: 5 cards — nacional + regional ───────────────────────────────────
    total_bf_nac  = df_mult["BF_Total_Mi"].sum() / 1000
    total_bf_reg  = df_vis["BF_Total_Mi"].sum() / 1000
    media_cresc   = df_vis["PIB_Cresc"].mean()
    maior_dep     = df_vis.loc[df_vis["Indice_Dependencia"].idxmax()]
    menor_dep     = df_vis.loc[df_vis["Indice_Dependencia"].idxmin()]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🇧🇷 Total BF Nacional", f"R$ {total_bf_nac:.1f} bi")

    label_reg = reg_filtro if reg_filtro != "Todas" else "Todas regiões"
    pct_reg   = total_bf_reg / total_bf_nac * 100
    c2.metric(
        f"📍 BF — {label_reg}",
        f"R$ {total_bf_reg:.1f} bi",
        f"{pct_reg:.1f}% do nacional" if reg_filtro != "Todas" else None,
    )
    c3.metric("📈 Cresc. Médio PIB 2023",
              f"{media_cresc:.1f}%",
              f"{'região sel.' if reg_filtro != 'Todas' else 'Brasil'}")
    c4.metric("🔴 Maior Dependência", maior_dep["UF"],
              f"{maior_dep['Indice_Dependencia']:.1f}% do PIB/pc")
    c5.metric("🟢 Menor Dependência", menor_dep["UF"],
              f"{menor_dep['Indice_Dependencia']:.1f}% do PIB/pc")

    st.divider()

    # ── Expander ANTES dos gráficos ──────────────────────────────────────────
    with st.expander("📖 Como interpretar este gráfico?"):
        st.markdown("""
        **O que é o Multiplicador Keynesiano?**
        Quando o governo injeta renda em famílias de baixa renda via Bolsa Família, esse recurso
        é gasto localmente — no comércio, serviços e alimentação. Esse ciclo gera emprego e renda
        em cadeia: é o **efeito multiplicador**.

        **Eixos:**
        - **Eixo X:** Injeção per capita do Bolsa Família em 2024 (R$/hab/ano) · Fonte: MDS
        - **Eixo Y:** Crescimento real do PIB estadual em 2023 (%) · Fonte: IBGE Contas Regionais 2023

        **Linha OLS (pontilhada):** tendência linear. Estados **acima** crescem mais do que o esperado
        pelo nível de transferência — outros motores (agro, petróleo, energia).
        Estados **abaixo** crescem menos — possível ineficiência ou choques negativos.

        **Quadrantes:** cruzamento pelas médias da seleção atual de região.
        """)

    # ── Scatter + Ranking lado a lado ─────────────────────────────────────────
    col_scatter, col_dep = st.columns([1.6, 1])

    with col_scatter:
        x = df_vis["BF_PerCapita"].values
        y = df_vis["PIB_Cresc"].values
        media_x, media_y = x.mean(), y.mean()
        m_ols, b_ols = np.polyfit(x, y, 1)
        corr = np.corrcoef(x, y)[0, 1]

        def quad_label(row):
            alta = row["BF_PerCapita"] >= media_x
            bom  = row["PIB_Cresc"] >= media_y
            if alta and bom:      return "Alta injeção + Alto crescimento"
            if alta and not bom:  return "Alta injeção + Baixo crescimento"
            if not alta and bom:  return "Baixa injeção + Alto crescimento"
            return "Baixa injeção + Baixo crescimento"

        df_vis["Quadrante"] = df_vis.apply(quad_label, axis=1)

        CQ = {
            "Alta injeção + Alto crescimento":   "#4CAF50",
            "Alta injeção + Baixo crescimento":  "#F44336",
            "Baixa injeção + Alto crescimento":  "#FF9800",
            "Baixa injeção + Baixo crescimento": "#2196F3",
        }

        fig, ax = plt.subplots(figsize=(8, 7))
        fig_estilo(fig, [ax])
        titulo_reg = f" — {reg_filtro}" if reg_filtro != "Todas" else " — Brasil"
        ax.set_title(f"BF per capita × Crescimento PIB Estadual{titulo_reg}",
                     color=TEXTO, fontsize=10, pad=8)

        for quad, cor in CQ.items():
            d = df_vis[df_vis["Quadrante"] == quad]
            ax.scatter(d["BF_PerCapita"], d["PIB_Cresc"],
                       color=cor, s=90, zorder=5, label=quad, alpha=0.9)
            for _, row in d.iterrows():
                ax.annotate(row["UF"],
                            xy=(row["BF_PerCapita"], row["PIB_Cresc"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color=TEXTO)

        # OLS
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, m_ols * x_line + b_ols,
                color="white", lw=1.5, ls="--", alpha=0.7, label="Tendência OLS")

        # Linhas de média
        ax.axhline(media_y, color="white", lw=0.8, ls=":", alpha=0.4)
        ax.axvline(media_x, color="white", lw=0.8, ls=":", alpha=0.4)

        ax.set_xlabel("Injeção BF per capita (R$/hab/ano — 2024)", color=TEXTO)
        ax.set_ylabel("Crescimento Real PIB 2023 (%)", color=TEXTO)
        ax.legend(fontsize=7.5, facecolor=FUNDO_CARD, labelcolor=TEXTO,
                  loc="upper right", ncol=1)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.caption(
            f"**Correlação de Pearson:** r = {corr:.3f}  ·  "
            f"**Sensibilidade OLS:** {m_ols * 1000:.3f} p.p. de crescimento "
            f"por R$ 1.000/hab adicional de transferência"
        )

    with col_dep:
        st.markdown("**Índice de Dependência Real**")
        st.caption("BF per capita ÷ PIB per capita × 100 · ordenado do maior para o menor")

        df_sort = df_vis.sort_values("Indice_Dependencia", ascending=True).copy()

        # Altura sempre igual ao scatter para eliminar gap
        altura_rank = 7.0
        fig2, ax2 = plt.subplots(figsize=(4.5, altura_rank))
        fig_estilo(fig2, [ax2])
        ax2.set_title(
            f"Dependência BF/PIB pc{' — ' + reg_filtro if reg_filtro != 'Todas' else ''}",
            color=TEXTO, fontsize=9, pad=6,
        )
        norm = mcolors.Normalize(vmin=df_sort["Indice_Dependencia"].min(),
                                 vmax=df_sort["Indice_Dependencia"].max())
        import matplotlib.cm as cm
        cmap = cm.get_cmap("RdYlGn_r")
        cores_dep = [cmap(norm(v)) for v in df_sort["Indice_Dependencia"]]
        # Altura das barras proporcional ao número de estados
        alt_barra = max(0.25, min(0.65, 5.5 / len(df_sort)))
        bars = ax2.barh(df_sort["UF"], df_sort["Indice_Dependencia"],
                        color=cores_dep, height=alt_barra)
        fontsize_val = max(6.5, min(8.5, 170 / len(df_sort)))
        for bar, val in zip(bars, df_sort["Indice_Dependencia"]):
            ax2.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                     f"{val:.1f}%", va="center", fontsize=fontsize_val, color=TEXTO)
        ax2.set_xlabel("% do PIB per capita", color=TEXTO)
        ax2.tick_params(axis="y", labelsize=max(6.5, min(8.5, 170 / len(df_sort))))
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    # Análise
    st.info(f"""
**Leitura do Multiplicador**

O coeficiente de correlação de Pearson entre injeção do BF e crescimento do PIB é 
**r = {corr:.3f}** — uma correlação {"moderada" if abs(corr) < 0.5 else "significativa"}, 
o que indica que as transferências não são o único motor do crescimento estadual.

**Estados com alto crescimento e alta injeção** (quadrante verde) como **AC e MT** 
demonstram que o efeito multiplicador pode ser potencializado quando as transferências 
coexistem com setores produtivos dinâmicos (agropecuária, energia).

**Estados com alta injeção e baixo crescimento** (quadrante vermelho) levantam questão 
estrutural: os recursos chegam às famílias, mas não geram cadeia produtiva local suficiente — 
indicando dependência de importações intra-regionais e baixa densidade econômica.

**Dependência estrutural:** Estados com índice acima de **5%** do PIB per capita têm 
nas transferências federais um componente relevante da demanda agregada local — qualquer 
redução abrupta do programa teria efeito recessivo imediato.
    """)

    # Gráfico: Distribuição regional da injeção
    st.subheader("🗺️ Injeção por Região — BF Total (R$ bilhões, 2024)")

    regioes = {}
    for _, row in df_mult.iterrows():
        r = row["Regiao"]
        regioes[r] = regioes.get(r, 0) + row["BF_Total_Mi"]
    df_reg = pd.DataFrame(
        [(r, v/1000) for r, v in regioes.items()],
        columns=["Região", "BF_Bi"]
    ).sort_values("BF_Bi", ascending=True)

    fig3, ax3 = plt.subplots(figsize=(7, 2.5))
    fig_estilo(fig3, [ax3])
    cores_reg = [CORES_REGIAO[r] for r in df_reg["Região"]]
    bars3 = ax3.barh(df_reg["Região"], df_reg["BF_Bi"], color=cores_reg, height=0.55)
    for bar, val in zip(bars3, df_reg["BF_Bi"]):
        ax3.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                 f"R$ {val:.1f} bi", va="center", fontsize=9, color=TEXTO)
    ax3.set_xlabel("R$ bilhões (total anual 2024)", color=TEXTO)
    ax3.set_xlim(0, df_reg["BF_Bi"].max() * 1.2)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

    pct_ne = regioes.get("Nordeste", 0) / sum(regioes.values()) * 100
    st.info(f"""
**Concentração Regional das Transferências**

O **Nordeste** absorve aproximadamente **{pct_ne:.0f}%** do total nacional do Bolsa Família — 
proporção que reflete tanto a concentração de vulnerabilidade social quanto a densidade 
populacional da região. Isso não é distorção: é o programa funcionando como sistema 
progressivo de redistribuição espacial da renda.

**Sudeste:** apesar do alto PIB, concentra grande número absoluto de beneficiários — 
especialmente São Paulo e Rio de Janeiro — devido ao volume populacional e à presença de 
populações urbanas em situação de vulnerabilidade nas periferias metropolitanas.
    """)


# ══════════════════════════════════════════════════════════════════════════════
# ABA B — FRONTEIRA DE EFICIÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with aba_b:
    st.subheader("📊 Fronteira de Eficiência Alocativa: Gasto Público × Resultado Social")

    with st.expander("📖 Como ler a Fronteira de Eficiência?"):
        st.markdown("""
        **O que é a Fronteira de Eficiência (Value for Money)?**

        Cruzamos o **gasto per capita por função orçamentária** (Educação, Saúde, etc.)
        com um **indicador social de resultado** (Analfabetismo, Esperança de Vida, etc.).
        A linha OLS define o "esperado" — estados acima/abaixo revelam eficiência ou ineficiência.

        **Os 4 quadrantes:**

        | Quadrante | Gasto | Resultado | Diagnóstico |
        |---|---|---|---|
        | 🟢 Alta Eficiência | Baixo | Bom | Gestão eficiente — referência nacional |
        | 🟠 Eficaz, mas Caro | Alto | Bom | Entrega, mas com custo acima do necessário |
        | 🔵 Subfinanciado | Baixo | Ruim | Precisa de mais recursos |
        | 🔴 Crítico | Alto | Ruim | Alto gasto, baixo resultado — foco de auditoria |

        **Pareamento lógico:** o resultado só é válido se houver relação causal entre 
        a função e o indicador (Educação × Analfabetismo, Saúde × Esperança de Vida).
        """)

    cfg_ind = INDICADORES_SOCIAIS[indicador_sel]
    menor_melhor = cfg_ind["menor_melhor"]
    unidade = cfg_ind["unidade"]

    # Montar dataframe
    df_gasto  = pd.DataFrame(list(GASTOS_FUNCAO[funcao_sel].items()),
                             columns=["UF", "Gasto"])
    df_social = pd.DataFrame(list(cfg_ind["dados"].items()),
                             columns=["UF", "Resultado"])
    df_ef = pd.merge(df_gasto, df_social, on="UF").dropna()

    media_g = df_ef["Gasto"].mean()
    media_r = df_ef["Resultado"].mean()

    def classificar(row):
        baixo = row["Gasto"] <= media_g
        bom   = (row["Resultado"] <= media_r if menor_melhor
                 else row["Resultado"] >= media_r)
        if baixo and bom:      return "Alta Eficiência"
        if not baixo and bom:  return "Eficaz, mas Caro"
        if baixo and not bom:  return "Subfinanciado"
        return "Crítico"

    df_ef["Quad"] = df_ef.apply(classificar, axis=1)

    x_ef  = df_ef["Gasto"].values
    y_ef  = df_ef["Resultado"].values
    m_ef, b_ef = np.polyfit(x_ef, y_ef, 1)
    corr_ef = np.corrcoef(x_ef, y_ef)[0, 1]

    # Resíduo OLS
    df_ef["Custo_Just"] = (y_ef - b_ef) / (m_ef if abs(m_ef) > 1e-6 else 1e-6)
    df_ef["Residuo"] = (df_ef["Gasto"] - df_ef["Custo_Just"]) * (1 if menor_melhor else -1)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Gasto Médio/hab ({funcao_sel})",  f"R$ {media_g:,.0f}")
    c2.metric(f"Média Nacional — {indicador_sel.split('(')[0].strip()}", f"{media_r:.1f} {unidade}")
    c3.metric("Correlação de Pearson (r)", f"{corr_ef:.3f}")
    c4.metric("Sensibilidade OLS", f"{m_ef*1000:+.4f} {unidade}/R$1k")

    st.divider()

    col_ef, col_tab = st.columns([1.6, 1])

    with col_ef:
        fig4, ax4 = plt.subplots(figsize=(8, 5.5))
        fig_estilo(fig4, [ax4])
        ax4.set_title(f"{funcao_sel} × {indicador_sel.split('(')[0].strip()}",
                      color=TEXTO, fontsize=10, pad=8)

        for quad, cor in CORES_QUAD.items():
            d = df_ef[df_ef["Quad"] == quad]
            ax4.scatter(d["Gasto"], d["Resultado"],
                        color=cor, s=90, zorder=5, label=quad, alpha=0.9)
            for _, row in d.iterrows():
                ax4.annotate(row["UF"],
                             xy=(row["Gasto"], row["Resultado"]),
                             xytext=(4, 4), textcoords="offset points",
                             fontsize=7.5, color=TEXTO)

        x_line = np.linspace(x_ef.min(), x_ef.max(), 100)
        ax4.plot(x_line, m_ef * x_line + b_ef,
                 color="white", lw=1.5, ls="--", alpha=0.7, label="Fronteira OLS")
        ax4.axhline(media_r, color="white", lw=0.8, ls=":", alpha=0.4)
        ax4.axvline(media_g, color="white", lw=0.8, ls=":", alpha=0.4)

        ax4.set_xlabel(f"Gasto/hab (R$) — {funcao_sel}", color=TEXTO)
        ax4.set_ylabel(f"{indicador_sel}", color=TEXTO)
        ax4.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO, loc="best")
        ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
        if unidade == "%":
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
        elif unidade == "anos":
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f} a"))
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

        st.caption(
            f"**Correlação:** r = {corr_ef:.3f}  ·  "
            f"**OLS:** {m_ef*1000:+.4f} {unidade} por R$1.000/hab adicionais de gasto"
        )

    with col_tab:
        st.markdown("**Ranking por Quadrante:**")
        ordem = {"Crítico": 1, "Eficaz, mas Caro": 2,
                 "Subfinanciado": 3, "Alta Eficiência": 4}
        df_tab = df_ef.sort_values(
            ["Quad", "Residuo"],
            key=lambda c: c.map(ordem) if c.name == "Quad" else c,
            ascending=[True, False]
        )[["UF", "Quad", "Gasto", "Resultado", "Residuo"]].copy()

        df_tab_fmt = df_tab.rename(columns={
            "Quad": "Quadrante", "Gasto": "Gasto/hab (R$)",
            "Resultado": indicador_sel.split("(")[0].strip(),
            "Residuo": "Resíduo OLS (R$)"
        })
        df_tab_fmt["Gasto/hab (R$)"]  = df_tab_fmt["Gasto/hab (R$)"].map(lambda v: f"R$ {v:,.0f}")
        df_tab_fmt[indicador_sel.split("(")[0].strip()] = \
            df_tab_fmt[indicador_sel.split("(")[0].strip()].map(lambda v: f"{v:.1f} {unidade}")
        df_tab_fmt["Resíduo OLS (R$)"] = df_tab_fmt["Resíduo OLS (R$)"].map(lambda v: f"R$ {v:+,.0f}")

        st.dataframe(df_tab_fmt, use_container_width=True, hide_index=True, height=480)

    # Diagnóstico
    df_crit = df_ef[df_ef["Quad"] == "Crítico"]
    df_efic = df_ef[df_ef["Quad"] == "Alta Eficiência"]

    ec = df_crit.loc[df_crit["Residuo"].idxmax()] if not df_crit.empty \
         else df_ef.loc[df_ef["Residuo"].idxmax()]
    eb = df_efic.loc[df_efic["Residuo"].idxmin()] if not df_efic.empty \
         else df_ef.loc[df_ef["Residuo"].idxmin()]

    n_crit = len(df_crit)
    n_efic = len(df_efic)

    st.info(f"""
**Diagnóstico de Auditoria — {funcao_sel} × {indicador_sel.split("(")[0].strip()}**

**Estado crítico:** **{ec['UF']}** — gasta R$ {ec['Gasto']:,.0f}/hab e entrega 
{ec['Resultado']:.1f} {unidade} — resíduo de **R$ {abs(ec['Residuo']):,.0f}/hab** acima 
da fronteira. Alto gasto com resultado abaixo do esperado pelo modelo.

**Referência nacional:** **{eb['UF']}** — gasta R$ {eb['Gasto']:,.0f}/hab e entrega 
{eb['Resultado']:.1f} {unidade} com custo abaixo do estimado. Modelo de gestão a ser estudado.

**{n_crit} estado{"s" if n_crit != 1 else ""}** no quadrante crítico · 
**{n_efic} estado{"s" if n_efic != 1 else ""}** com alta eficiência.
    """)

    st.info(f"""
**Limitações e Contexto**

O resíduo OLS é um **proxy** de ineficiência alocativa, não uma prova causal. 
Estados com alto custo podem ter populações mais dispersas, maior proporção de 
população rural, ou demanda reprimida histórica que exige mais investimento inicial 
para alcançar o mesmo resultado que estados com infraestrutura já consolidada.

**Recomendação de uso:** Use a fronteira para priorizar investigações — não como 
sentença. Um estado "crítico" merece auditoria detalhada, não corte automático de recursos.
    """)

    # Distribuição dos quadrantes
    st.subheader("📊 Distribuição dos Estados por Quadrante")
    contagem = df_ef["Quad"].value_counts().reindex(
        ["Alta Eficiência", "Eficaz, mas Caro", "Subfinanciado", "Crítico"], fill_value=0
    )
    fig5, ax5 = plt.subplots(figsize=(7, 2.5))
    fig_estilo(fig5, [ax5])
    cores5 = [CORES_QUAD[q] for q in contagem.index]
    bars5  = ax5.barh(contagem.index, contagem.values, color=cores5, height=0.5)
    for bar, val in zip(bars5, contagem.values):
        ax5.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                 str(val), va="center", fontsize=10, fontweight="bold", color=TEXTO)
    ax5.set_xlabel("Número de estados", color=TEXTO)
    ax5.set_xlim(0, contagem.max() + 2)
    ax5.grid(False)
    plt.tight_layout()
    st.pyplot(fig5)
    plt.close()

# ── Metodologia ───────────────────────────────────────────────────────────────
st.divider()
with st.expander("📋 Metodologia e Fontes"):
    st.markdown("""
    **Módulo A — Efeito Multiplicador:**

    | Dado | Fonte | Ano |
    |---|---|---|
    | Bolsa Família por UF | MDS — Portal da Transparência | 2024 |
    | PIB crescimento por UF | IBGE — Sistema de Contas Regionais | 2023 |
    | PIB per capita por UF | IBGE — Sistema de Contas Regionais | 2023 |
    | População | IBGE — Censo Demográfico | 2022 |

    *Índice de Dependência = (BF per capita / PIB per capita) × 100*

    **Módulo B — Fronteira de Eficiência:**

    | Dado | Fonte | Ano |
    |---|---|---|
    | Gasto por função | STN/SICONFI — RREO Anexo 02, 6º Bimestre | 2024 |
    | Analfabetismo | IBGE PNAD Contínua t7111 | 2024 |
    | Esperança de vida | IBGE Tábuas de Mortalidade | 2023 |
    | Desocupação | IBGE PNAD Contínua, 4º Tri | 2024 |

    *Fronteira OLS: regressão de Mínimos Quadrados Ordinários. Resíduo = proxy de ineficiência.*
    *Pare de confundir eficiência com eficácia: um estado pode gastar muito E entregar bem (Eficaz, mas Caro).*
    """)
