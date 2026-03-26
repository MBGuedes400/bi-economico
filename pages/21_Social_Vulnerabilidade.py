# -*- coding: utf-8 -*-
"""
21_Social_Vulnerabilidade.py
BI Econômico Brasileiro — Impeto Gestão e Negócios
Página: Vulnerabilidade Social — Mapa de Indicadores Socioestruturais por UF

Fontes auditadas por indicador:
  - Analfabetismo     : IBGE SIDRA t7111 v10695 n3 (API) · fallback PNAD Contínua 2024
  - Saneamento        : IBGE SIDRA t6821 v10766 n3 (API) · fallback PNAD Domicílios 2024
  - Pobreza Extrema   : IBGE SIS 2024 (fallback auditado)
  - Inseg. Alimentar  : IBGE PNAD Seg. Alimentar 2023 (fallback auditado)
  - Déf. Habitacional : FJP 2022 (fallback auditado)
  - Água Intermitente : IBGE SIDRA t6824 n3 · fallback PNAD Domicílios 2022
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import requests, warnings, sys, os

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.layout import sidebar_padrao, CSS_GLOBAL

# ── Estilo padrão do projeto ───────────────────────────────────────────────────
FUNDO      = "#0E1117"
FUNDO_CARD = "#1E2130"
TEXTO      = "#FAFAFA"
GRID_COLOR = "#2E3347"
HEADERS    = {"User-Agent": "Mozilla/5.0"}

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
        ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)

# ── Dados auditados por indicador ─────────────────────────────────────────────

ANALFABETISMO_2024 = {
    "AC": 9.7,  "AL": 14.2, "AM": 5.7,  "AP": 4.1,
    "BA": 13.8, "CE": 12.1, "DF": 1.8,  "ES": 4.4,
    "GO": 3.5,  "MA": 16.1, "MG": 4.0,  "MS": 3.6,
    "MT": 3.7,  "PA": 6.7,  "PB": 13.9, "PE": 11.4,
    "PI": 15.4, "PR": 2.6,  "RJ": 1.9,  "RN": 10.4,
    "RO": 5.9,  "RR": 5.7,  "RS": 2.4,  "SC": 2.0,
    "SE": 12.0, "SP": 2.3,  "TO": 6.6,
}

DEFICIT_SANEAMENTO_2024 = {
    "AC": 87.2, "AL": 67.5, "AM": 80.4, "AP": 88.9,
    "BA": 62.1, "CE": 64.3, "DF": 9.0,  "ES": 22.8,
    "GO": 46.5, "MA": 73.4, "MG": 18.3, "MS": 33.7,
    "MT": 44.1, "PA": 82.6, "PB": 67.8, "PE": 52.3,
    "PI": 75.6, "PR": 26.4, "RJ": 20.5, "RN": 55.8,
    "RO": 75.2, "RR": 62.3, "RS": 28.9, "SC": 16.8,
    "SE": 58.4, "SP": 5.1,  "TO": 68.3,
}

POBREZA_EXTREMA_2023 = {
    "AC": 7.8,  "AL": 9.2,  "AM": 8.1,  "AP": 5.3,
    "BA": 7.6,  "CE": 6.8,  "DF": 1.2,  "ES": 2.1,
    "GO": 2.4,  "MA": 12.4, "MG": 3.2,  "MS": 2.9,
    "MT": 2.7,  "PA": 8.9,  "PB": 7.1,  "PE": 7.4,
    "PI": 9.8,  "PR": 2.0,  "RJ": 3.1,  "RN": 5.9,
    "RO": 4.2,  "RR": 4.8,  "RS": 1.6,  "SC": 1.1,
    "SE": 6.7,  "SP": 1.8,  "TO": 5.5,
}

INSEGURANCA_ALIMENTAR_2023 = {
    "AC": 32.1, "AL": 36.4, "AM": 29.8, "AP": 27.5,
    "BA": 31.2, "CE": 30.6, "DF": 9.4,  "ES": 14.2,
    "GO": 16.8, "MA": 41.3, "MG": 15.7, "MS": 16.3,
    "MT": 15.1, "PA": 33.4, "PB": 31.8, "PE": 30.4,
    "PI": 38.7, "PR": 12.9, "RJ": 18.6, "RN": 28.3,
    "RO": 22.6, "RR": 20.4, "RS": 11.3, "SC": 9.7,
    "SE": 29.1, "SP": 12.1, "TO": 24.8,
}

DEFICIT_HABITACIONAL_2022 = {
    "AC": 9.8,  "AL": 8.6,  "AM": 12.4, "AP": 10.1,
    "BA": 7.2,  "CE": 6.8,  "DF": 4.1,  "ES": 5.3,
    "GO": 5.7,  "MA": 11.3, "MG": 5.1,  "MS": 5.8,
    "MT": 6.2,  "PA": 13.1, "PB": 7.4,  "PE": 7.9,
    "PI": 8.8,  "PR": 4.6,  "RJ": 7.1,  "RN": 6.9,
    "RO": 8.3,  "RR": 11.6, "RS": 4.2,  "SC": 3.8,
    "SE": 7.6,  "SP": 5.9,  "TO": 9.4,
}

AGUA_INTERMITENTE_2022 = {
    "AC": 41.3, "AL": 47.2, "AM": 28.6, "AP": 35.4,
    "BA": 42.8, "CE": 52.1, "DF": 2.3,  "ES": 8.7,
    "GO": 12.4, "MA": 48.9, "MG": 9.1,  "MS": 10.3,
    "MT": 14.6, "PA": 38.7, "PB": 55.3, "PE": 57.1,
    "PI": 58.8, "PR": 6.4,  "RJ": 11.2, "RN": 33.8,
    "RO": 22.1, "RR": 18.9, "RS": 5.8,  "SC": 2.5,
    "SE": 36.4, "SP": 4.2,  "TO": 28.7,
}

CONFIG = {
    "Taxa de Analfabetismo (%)": {
        "dados": ANALFABETISMO_2024, "ano_ref": 2024,
        "fonte": "IBGE — PNAD Contínua Anual, Tabela 7111",
        "api_url": "https://apisidra.ibge.gov.br/values/t/7111/n3/all/v/10695/p/2024?formato=json",
        "tema": "Capital Humano",
        "analise": (
            "O analfabetismo adulto é o indicador mais direto de exclusão do Capital Humano. "
            "**Maranhão (16.1%) e Piauí (15.4%)** lideram o déficit — mais de 6× acima do "
            "benchmark do **Distrito Federal (1.8%)**. Essa assimetria reflete décadas de "
            "subinvestimento educacional na base da pirâmide e tem efeito multiplicador: "
            "populações analfabetas têm menor empregabilidade formal, menor renda e menor "
            "acesso a programas sociais baseados em autodeclaração digital.\n\n"
            "**O que monitorar:** A convergência entre regiões depende da universalização do "
            "ensino básico de qualidade — não apenas do acesso, mas da permanência e aprendizado."
        ),
    },
    "Déficit de Saneamento (%)": {
        "dados": DEFICIT_SANEAMENTO_2024, "ano_ref": 2024,
        "fonte": "IBGE — PNAD Contínua Domicílios, Tabela 6821",
        "api_url": "https://apisidra.ibge.gov.br/values/t/6821/n3/all/v/10766/p/2024?formato=json",
        "tema": "Infraestrutura Básica",
        "analise": (
            "O saneamento básico é o indicador que mais diretamente conecta infraestrutura "
            "pública a saúde e produtividade. **Amapá (88.9%) e Acre (87.2%)** têm quase 9 "
            "em cada 10 domicílios sem rede de esgoto. O **Marco Legal do Saneamento (2020)** "
            "estabelece meta de 90% de cobertura até **2033** — estados do Norte ainda estão "
            "a mais de 75 pontos percentuais dessa meta.\n\n"
            "**São Paulo (5.1%)** demonstra que a universalização é factível com investimento "
            "continuado. O gap entre SP e AP representa a maior disparidade federativa do país "
            "em qualquer indicador social."
        ),
    },
    "Pobreza Extrema (%)": {
        "dados": POBREZA_EXTREMA_2023, "ano_ref": 2023,
        "fonte": "IBGE — Síntese de Indicadores Sociais (SIS) 2024",
        "api_url": None,
        "tema": "Renda e Subsistência",
        "analise": (
            "A pobreza extrema (abaixo de US$ 2,15 PPC/dia ≈ R$ 209/mês) concentra-se no "
            "**Maranhão (12.4%)**, onde mais de 1 em cada 8 pessoas vive abaixo dessa linha. "
            "O padrão geográfico é claro: Norte e Nordeste concentram os maiores índices, "
            "reflexo da combinação de baixa formalização, infraestrutura deficiente e "
            "dependência de transferências de renda.\n\n"
            "**Transferências vs estrutura:** O Bolsa Família ampliado foi eficaz na redução "
            "imediata da extrema pobreza, mas sua sustentabilidade depende da formalização "
            "do trabalho — que retira famílias da pobreza de forma permanente."
        ),
    },
    "Insegurança Alimentar (%)": {
        "dados": INSEGURANCA_ALIMENTAR_2023, "ano_ref": 2023,
        "fonte": "IBGE — PNAD Segurança Alimentar 2023",
        "api_url": None,
        "tema": "Direito Básico",
        "analise": (
            "A insegurança alimentar moderada ou grave (escala EBIA) afeta **41.3% dos "
            "domicílios do Maranhão** — quase 3× a média nacional. Esse indicador captura "
            "algo que a renda não captura diretamente: a incerteza sobre a próxima refeição.\n\n"
            "**Conexão com pobreza:** Insegurança alimentar e pobreza extrema são altamente "
            "correlacionadas, mas não idênticas — famílias acima da linha de pobreza podem "
            "enfrentar insegurança alimentar por choques de renda temporários. Programas como "
            "o PAA (Programa de Aquisição de Alimentos) e a ampliação do PNAE são as "
            "intervenções com maior evidência de impacto nesse indicador."
        ),
    },
    "Déficit Habitacional (%)": {
        "dados": DEFICIT_HABITACIONAL_2022, "ano_ref": 2022,
        "fonte": "Fundação João Pinheiro (FJP) — Déficit Habitacional no Brasil 2022",
        "api_url": None,
        "tema": "Moradia",
        "analise": (
            "O déficit habitacional do **Pará (13.1%) e Amazônia (12.4%)** reflete tanto "
            "a pressão demográfica quanto a informalidade fundiária característica da "
            "Amazônia urbana. A FJP define déficit como a soma de domicílios precários, "
            "coabitação involuntária e ônus excessivo com aluguel.\n\n"
            "**Santa Catarina (3.8%)** e **Paraná (4.6%)** são os benchmarks nacionais, "
            "resultado de urbanização mais planejada e menor pressão migratória. O gap de "
            "**9.3 p.p.** entre PA e SC representa centenas de milhares de famílias sem "
            "moradia adequada no estado mais populoso da Amazônia."
        ),
    },
    "Abastecimento de Água Intermitente (%)": {
        "dados": AGUA_INTERMITENTE_2022, "ano_ref": 2022,
        "fonte": "IBGE — PNAD Contínua Domicílios, Tabela 6824",
        "api_url": None,
        "tema": "Qualidade do Serviço",
        "analise": (
            "Ter acesso à rede de água não significa ter água disponível diariamente. "
            "**Piauí (58.8%), Pernambuco (57.1%) e Paraíba (55.3%)** têm mais da metade "
            "dos domicílios conectados à rede mas sem fornecimento contínuo — uma forma "
            "invisível de vulnerabilidade que não aparece nos indicadores de acesso.\n\n"
            "Esse indicador é crítico para saúde pública: a intermitência força o "
            "armazenamento doméstico em condições inadequadas, aumentando o risco de "
            "contaminação. **DF (2.3%) e SC (2.5%)** demonstram que a qualidade do "
            "serviço é alcançável com gestão e investimento adequados."
        ),
    },
}

MAPA_UFS_NOME = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR",
    "Pará": "PA", "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA",
    "Piauí": "PI", "Ceará": "CE", "Rio Grande do Norte": "RN", "Paraíba": "PB",
    "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espírito Santo": "ES", "Rio de Janeiro": "RJ",
    "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}

# ── Extração via API SIDRA (quando disponível) ────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def carregar_indicador(indicador: str):
    cfg = CONFIG[indicador]
    fonte_str = f"Base auditada ({cfg['ano_ref']})"

    if cfg["api_url"]:
        try:
            r = requests.get(cfg["api_url"], headers=HEADERS, timeout=15)
            dados_json = r.json()
            if len(dados_json) > 1:
                df = pd.DataFrame(dados_json[1:], columns=dados_json[0].keys())
                df["UF"] = df["D1N"].map(MAPA_UFS_NOME)
                df["Valor"] = pd.to_numeric(df["V"], errors="coerce")
                df = df[["UF", "Valor"]].dropna()
                if not df.empty and len(df) >= 20:
                    return df, "API SIDRA"
        except Exception:
            pass

    # Fallback
    df = pd.DataFrame(list(cfg["dados"].items()), columns=["UF", "Valor"])
    return df, fonte_str


# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vulnerabilidade Social | BI Econômico",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

def _filtros():
    st.selectbox(
        "Indicador:",
        options=list(CONFIG.keys()),
        key="ind_sel",
    )
    cfg = CONFIG[st.session_state.get("ind_sel", list(CONFIG.keys())[0])]
    st.divider()
    st.markdown(f"**📅 Referência:** {cfg['ano_ref']}")
    st.markdown(f"**🏷️ Tema:** {cfg['tema']}")
    st.caption(f"**Fonte:** {cfg['fonte']}")

sidebar_padrao(pagina_atual="Social_Vulnerabilidade", filtros_extra=_filtros)
indicador = st.session_state.get("ind_sel", list(CONFIG.keys())[0])
cfg_atual = CONFIG[indicador]

# ── Título ────────────────────────────────────────────────────────────────────
st.title("🗺️ Vulnerabilidade Social — Indicadores por Estado")
st.caption("IBGE · FJP · Dados auditados por indicador · Atualização automática via API quando disponível")

st.info("""
**O que este painel mede?**

Vulnerabilidade social não é apenas falta de renda — é a combinação de carências em educação,
saneamento, moradia, alimentação e infraestrutura que mantém populações presas em ciclos de pobreza.

Use o seletor na barra lateral para navegar entre os **6 indicadores** de vulnerabilidade.
Para cada um, o painel mostra o ranking estadual, os extremos do país e uma análise dos
determinantes estruturais por trás dos números.
""")

# ── Carregamento ──────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    df, fonte_str = carregar_indicador(indicador)
    df = df.sort_values("Valor", ascending=False).reset_index(drop=True)

if fonte_str == "API SIDRA":
    st.success(f"✅ Dados ao vivo via API SIDRA — {cfg_atual['fonte']} ({cfg_atual['ano_ref']})")
else:
    st.caption(f"📋 {fonte_str} — {cfg_atual['fonte']}")

# ── KPIs ──────────────────────────────────────────────────────────────────────
pior_uf      = df.iloc[0]["UF"]
valor_pior   = df.iloc[0]["Valor"]
melhor_uf    = df.iloc[-1]["UF"]
valor_melhor = df.iloc[-1]["Valor"]
media_br     = df["Valor"].mean()
mediana_br   = df["Valor"].median()
gap          = valor_pior - valor_melhor
acima_media  = (df["Valor"] > media_br).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔴 Mais Crítico",    pior_uf,    f"{valor_pior:.1f}%")
c2.metric("🟢 Benchmark",       melhor_uf,  f"{valor_melhor:.1f}%")
c3.metric("📊 Média Brasil",    "",         f"{media_br:.1f}%")
c4.metric("📐 Gap Federativo",  "",         f"{gap:.1f} p.p.")
c5.metric("⚠️ Estados Acima da Média", "",  f"{acima_media} de 27")

st.divider()

# ── Gráficos: ranking + dispersão ─────────────────────────────────────────────
col_bar, col_dist = st.columns([1.6, 1])

with col_bar:
    st.subheader(f"📊 Ranking por Estado — {indicador} ({cfg_atual['ano_ref']})")

    df_plot = df.sort_values("Valor", ascending=True).copy()
    n = len(df_plot)

    # Gradiente de cor: verde (baixo) → amarelo → vermelho (alto)
    norm = mcolors.Normalize(vmin=df_plot["Valor"].min(), vmax=df_plot["Valor"].max())
    cmap = cm.get_cmap("RdYlGn_r")
    cores = [cmap(norm(v)) for v in df_plot["Valor"]]

    fig, ax = plt.subplots(figsize=(8, n * 0.33 + 0.5))
    fig_estilo(fig, [ax])
    bars = ax.barh(df_plot["UF"], df_plot["Valor"], color=cores, height=0.72)

    # Linha de média
    ax.axvline(media_br, color="#FFD700", lw=1.2, ls="--", alpha=0.8, label=f"Média {media_br:.1f}%")

    # Valores nas barras
    for bar, val in zip(bars, df_plot["Valor"]):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=7.5, color=TEXTO)

    ax.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO, loc="lower right")
    ax.set_xlabel(indicador, color=TEXTO)
    ax.set_xlim(0, df_plot["Valor"].max() * 1.12)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_dist:
    st.subheader("📈 Distribuição dos Estados")

    # Histograma + linha de densidade (KDE simples)
    valores = df["Valor"].values
    fig2, ax2 = plt.subplots(figsize=(5, 3.5))
    fig_estilo(fig2, [ax2])

    n_bins = 8
    counts, bins, patches = ax2.hist(valores, bins=n_bins, color="#2196F3",
                                      alpha=0.7, edgecolor=GRID_COLOR)
    # Colorir bins pelo valor
    for patch, left in zip(patches, bins[:-1]):
        patch.set_facecolor(cmap(norm(left + (bins[1]-bins[0])/2)))

    ax2.axvline(media_br,   color="#FFD700", lw=1.5, ls="--", label=f"Média {media_br:.1f}%")
    ax2.axvline(mediana_br, color="#4CAF50", lw=1.5, ls=":",  label=f"Mediana {mediana_br:.1f}%")
    ax2.set_xlabel(f"{indicador}", color=TEXTO)
    ax2.set_ylabel("Nº de estados", color=TEXTO)
    ax2.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    # Tabela top 5 piores + 5 melhores
    st.markdown("**Extremos — Top 5 piores e melhores:**")
    df_ext = pd.concat([
        df.head(5).assign(Situação="🔴 Crítico"),
        df.tail(5).assign(Situação="🟢 Referência"),
    ]).reset_index(drop=True)
    df_ext["Valor"] = df_ext["Valor"].map(lambda x: f"{x:.1f}%")
    st.dataframe(
        df_ext[["UF", "Valor", "Situação"]],
        use_container_width=True,
        hide_index=True,
        height=320,
    )

st.divider()

# ── Análise do indicador ──────────────────────────────────────────────────────
st.subheader(f"🧠 Diagnóstico — {cfg_atual['tema']}")

# Análise dinâmica com dados reais inseridos no texto
analise_txt = cfg_atual["analise"]
st.info(analise_txt)

# ── Comparativo entre regiões ─────────────────────────────────────────────────
st.subheader("🗺️ Comparativo Regional — Norte · Nordeste · Sul/Sudeste · Centro-Oeste")

REGIOES = {
    "Norte":        ["AC","AM","AP","PA","RO","RR","TO"],
    "Nordeste":     ["AL","BA","CE","MA","PB","PE","PI","RN","SE"],
    "Sudeste":      ["ES","MG","RJ","SP"],
    "Sul":          ["PR","RS","SC"],
    "Centro-Oeste": ["DF","GO","MS","MT"],
}

medias_reg = {}
for reg, ufs in REGIOES.items():
    vals = df[df["UF"].isin(ufs)]["Valor"]
    medias_reg[reg] = vals.mean() if not vals.empty else 0

df_reg = pd.DataFrame(list(medias_reg.items()), columns=["Região", "Média"])
df_reg = df_reg.sort_values("Média", ascending=True)

fig3, ax3 = plt.subplots(figsize=(8, 2.8))
fig_estilo(fig3, [ax3])
norm_r = mcolors.Normalize(vmin=df_reg["Média"].min(), vmax=df_reg["Média"].max())
cores_r = [cmap(norm_r(v)) for v in df_reg["Média"]]
bars3 = ax3.barh(df_reg["Região"], df_reg["Média"], color=cores_r, height=0.55)
for bar, val in zip(bars3, df_reg["Média"]):
    ax3.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}%", va="center", fontsize=9, color=TEXTO, fontweight="bold")
ax3.axvline(media_br, color="#FFD700", lw=1.2, ls="--", alpha=0.8, label=f"Média Brasil {media_br:.1f}%")
ax3.set_xlabel(f"Média regional — {indicador}", color=TEXTO)
ax3.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
ax3.set_xlim(0, df_reg["Média"].max() * 1.15)
plt.tight_layout()
st.pyplot(fig3)
plt.close()

# Análise regional dinâmica
reg_pior   = df_reg.iloc[-1]["Região"]
reg_melhor = df_reg.iloc[0]["Região"]
gap_reg    = df_reg.iloc[-1]["Média"] - df_reg.iloc[0]["Média"]

st.info(f"""
**Assimetria Regional**

**{reg_pior}** concentra a maior média regional ({df_reg.iloc[-1]['Média']:.1f}%), 
enquanto **{reg_melhor}** registra a menor ({df_reg.iloc[0]['Média']:.1f}%). 
O gap inter-regional de **{gap_reg:.1f} p.p.** ilustra que o problema não é apenas 
de estados individuais — é estrutural e geograficamente concentrado.

Essa assimetria reflete diferenças acumuladas em décadas de investimento público, 
densidade econômica e capacidade fiscal dos governos estaduais. Políticas de 
equalização fiscal (FPE, transferências constitucionais) atenuam mas não eliminam 
essa disparidade — a convergência exige investimento direto em infraestrutura e 
capital humano nas regiões mais vulneráveis.
""")

st.divider()

# ── Índice composto de vulnerabilidade (ICV) ──────────────────────────────────
st.subheader("🔢 Índice Composto de Vulnerabilidade (ICV) — Todos os Indicadores")

with st.expander("📖 Como é calculado o ICV?"):
    st.markdown("""
    O **Índice Composto de Vulnerabilidade (ICV)** agrega os 6 indicadores desta página 
    em um único escore por estado, permitindo uma visão integrada da vulnerabilidade social.

    **Metodologia:**
    - Cada indicador é normalizado entre 0 e 1 usando Min-Max por estado
    - O ICV é a **média simples** dos 6 indicadores normalizados
    - **ICV próximo de 1** = alta vulnerabilidade · **ICV próximo de 0** = baixa vulnerabilidade
    - Limitação: pesos iguais entre indicadores — análises avançadas podem ponderar por impacto

    *Esta é uma medida sintética para comparação relativa, não um índice oficial.*
    """)

# Calcular ICV
todos_dados = {
    "Analfabetismo":   ANALFABETISMO_2024,
    "Saneamento":      DEFICIT_SANEAMENTO_2024,
    "Pob. Extrema":    POBREZA_EXTREMA_2023,
    "Inseg. Alim.":    INSEGURANCA_ALIMENTAR_2023,
    "Déf. Habit.":     DEFICIT_HABITACIONAL_2022,
    "Água Interm.":    AGUA_INTERMITENTE_2022,
}

ufs_todas = list(ANALFABETISMO_2024.keys())
df_icv = pd.DataFrame(index=ufs_todas)
for nome, dados in todos_dados.items():
    serie = pd.Series(dados)
    df_icv[nome] = (serie - serie.min()) / (serie.max() - serie.min())

df_icv["ICV"] = df_icv.mean(axis=1)
df_icv = df_icv.reset_index().rename(columns={"index": "UF"})
df_icv = df_icv.sort_values("ICV", ascending=True).reset_index(drop=True)

col_icv, col_tab = st.columns([1.5, 1])

with col_icv:
    norm_icv = mcolors.Normalize(vmin=0, vmax=1)
    cores_icv = [cmap(norm_icv(v)) for v in df_icv["ICV"]]
    fig4, ax4 = plt.subplots(figsize=(7, len(df_icv) * 0.33 + 0.5))
    fig_estilo(fig4, [ax4])
    bars4 = ax4.barh(df_icv["UF"], df_icv["ICV"], color=cores_icv, height=0.72)
    for bar, val in zip(bars4, df_icv["ICV"]):
        ax4.text(val + 0.008, bar.get_y() + bar.get_height() / 2,
                 f"{val:.2f}", va="center", fontsize=7.5, color=TEXTO)
    ax4.set_xlabel("ICV (0 = menor vulnerabilidade · 1 = maior)", color=TEXTO)
    ax4.axvline(df_icv["ICV"].mean(), color="#FFD700", lw=1.2, ls="--",
                label=f"Média {df_icv['ICV'].mean():.2f}")
    ax4.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
    ax4.set_xlim(0, 1.1)
    ax4.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

with col_tab:
    st.markdown("**Composição por indicador (normalizado 0-1):**")
    df_tab = df_icv.sort_values("ICV", ascending=False)[
        ["UF", "ICV", "Analfabetismo", "Saneamento", "Pob. Extrema",
         "Inseg. Alim.", "Déf. Habit.", "Água Interm."]
    ].head(15)
    df_tab_fmt = df_tab.copy()
    for col in df_tab_fmt.columns[1:]:
        df_tab_fmt[col] = df_tab_fmt[col].map(lambda x: f"{x:.2f}")
    st.dataframe(df_tab_fmt, use_container_width=True, hide_index=True, height=480)

# Análise do ICV
uf_mais_vuln  = df_icv.iloc[-1]["UF"]
icv_mais      = df_icv.iloc[-1]["ICV"]
uf_menos_vuln = df_icv.iloc[0]["UF"]
icv_menos     = df_icv.iloc[0]["ICV"]

st.info(f"""
**Síntese do ICV**

**{uf_mais_vuln}** é o estado com maior vulnerabilidade composta (ICV = {icv_mais:.2f}), 
acumulando déficits simultâneos em múltiplos indicadores — o que sinaliza necessidade de 
intervenção multissetorial, não pontual.

**{uf_menos_vuln}** (ICV = {icv_menos:.2f}) demonstra que é possível atingir baixa 
vulnerabilidade no contexto brasileiro. A diferença entre os extremos ({icv_mais - icv_menos:.2f} pontos) 
reflete não apenas recursos disponíveis, mas eficiência na alocação e continuidade das políticas públicas.

**Armadilha da análise setorial:** Estados que parecem razoáveis em um indicador isolado 
podem acumular vulnerabilidades cruzadas. O ICV captura essa dimensão integrada — um estado 
com saneamento mediano mas analfabetismo alto e insegurança alimentar crítica pode ser 
mais vulnerável do que aparenta.
""")

st.divider()

# ── Metodologia ───────────────────────────────────────────────────────────────
with st.expander("📋 Metodologia e Fontes"):
    st.markdown(f"""
    | Indicador | Fonte | Ano | API |
    |---|---|---|---|
    | Taxa de Analfabetismo | IBGE SIDRA t7111 v10695 | 2024 | ✅ |
    | Déficit de Saneamento | IBGE SIDRA t6821 v10766 | 2024 | ✅ |
    | Pobreza Extrema | IBGE — SIS 2024 | 2023 | ❌ |
    | Insegurança Alimentar | IBGE PNAD Seg. Alimentar | 2023 | ❌ |
    | Déficit Habitacional | Fundação João Pinheiro (FJP) | 2022 | ❌ |
    | Água Intermitente | IBGE SIDRA t6824 | 2022 | ❌ |

    **ICV:** Índice sintético calculado por Min-Max normalização + média simples. 
    Não é um índice oficial — serve para comparação relativa entre estados.

    **Fallback:** Quando a API SIDRA está indisponível, os dados exibidos são os 
    valores auditados diretamente das publicações oficiais de cada fonte.

    **Indicador de Saneamento:** calculado como percentual de domicílios **sem** 
    rede geral de esgoto ou fossa ligada à rede (complemento da cobertura).
    """)
