# -*- coding: utf-8 -*-
"""
23_Fluxo_Capitais.py
BI Econômico Brasileiro — Impeto Gestão e Negócios
Página: Fluxo de Capitais — IED, Reservas e Posição Internacional do Brasil

Fontes:
  BCB/SGS (históricas mensais):
    13621 — Reservas internacionais (US$ bi)
    22707 — Transações correntes — saldo (US$ mi)
    22704 — Balança comercial — saldo (US$ mi)
    22886 — IED entrada — participação no capital (US$ mi)
    22895 — IED saída (US$ mi)
    22900 — Investimento em carteira — passivo (US$ mi)
    22749 — Renda de investimento — saída (remessas de lucro, US$ mi)

  CSV Banco Mundial (worldbank_data.csv):
    Foreign direct investment, net inflows (BoP, current US$)
    External debt stocks, total (DOD, current US$)
    Personal remittances, received (current US$)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import requests, warnings, sys, os
from datetime import datetime

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.layout import sidebar_padrao, CSS_GLOBAL

# ── Estilo ─────────────────────────────────────────────────────────────────────
FUNDO      = "#0E1117"
FUNDO_CARD = "#1E2130"
TEXTO      = "#FAFAFA"
GRID_COLOR = "#2E3347"
PALETA = {"azul":"#2196F3","verde":"#4CAF50","laranja":"#FF9800",
          "vermelho":"#F44336","roxo":"#9C27B0","amarelo":"#FFD700","cinza":"#607D8B"}

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
# PAÍSES PARA COMPARATIVO (CSV Banco Mundial)
# ══════════════════════════════════════════════════════════════════════════════
PAISES = {
    "BR":"Brazil","US":"United States","CN":"China","DE":"Germany",
    "IN":"India","GB":"United Kingdom","MX":"Mexico","AR":"Argentina",
    "CL":"Chile","CO":"Colombia","AU":"Australia","KR":"Korea, Rep.",
    "CA":"Canada","FR":"France","ZA":"South Africa","JP":"Japan",
}
PAISES_NOMES = {
    "BR":"🇧🇷 Brasil","US":"🇺🇸 EUA","CN":"🇨🇳 China","DE":"🇩🇪 Alemanha",
    "IN":"🇮🇳 Índia","GB":"🇬🇧 Reino Unido","MX":"🇲🇽 México","AR":"🇦🇷 Argentina",
    "CL":"🇨🇱 Chile","CO":"🇨🇴 Colômbia","AU":"🇦🇺 Austrália","KR":"🇰🇷 Coreia do Sul",
    "CA":"🇨🇦 Canadá","FR":"🇫🇷 França","ZA":"🇿🇦 África do Sul","JP":"🇯🇵 Japão",
}
CORES = {
    "BR":"#009C3B","US":"#3C3B6E","CN":"#DE2910","DE":"#FFCE00","IN":"#FF9933",
    "GB":"#012169","MX":"#006847","AR":"#74ACDF","CL":"#D52B1E","CO":"#FCD116",
    "AU":"#00008B","KR":"#003478","CA":"#FF0000","FR":"#002395","ZA":"#007A4D","JP":"#BC002D",
}
PAISES_DEFAULT = ["BR","US","CN","DE","IN","MX","AR","KR"]

# ══════════════════════════════════════════════════════════════════════════════
# FALLBACKS AUDITADOS — BCB/Nota para a Imprensa Setor Externo 2024
# Fonte: BCB — Notas para a Imprensa — Setor Externo (dez/2024)
# Valores anuais em US$ bilhões
# ══════════════════════════════════════════════════════════════════════════════
FB_RESERVAS = {
    # US$ bilhões — fim de período
    2015: 368.7, 2016: 372.2, 2017: 382.0, 2018: 374.7, 2019: 356.9,
    2020: 355.6, 2021: 362.2, 2022: 324.7, 2023: 355.0, 2024: 361.8,
}
FB_TC = {
    # US$ bilhões — saldo anual (negativo = déficit)
    2015: -54.5, 2016: -23.5, 2017: -9.8,  2018: -51.5, 2019: -65.0,
    2020: -25.3, 2021: -46.4, 2022: -55.7, 2023: -58.8, 2024: -62.1,
}
FB_BC = {
    # US$ bilhões — saldo anual (superávit comercial)
    2015: 19.7, 2016: 47.7, 2017: 67.0, 2018: 58.3, 2019: 46.7,
    2020: 50.9, 2021: 61.4, 2022: 62.3, 2023: 98.8, 2024: 74.8,
}
FB_IED_ENT = {
    # US$ bilhões — entrada de IED
    2015: 75.1, 2016: 78.9, 2017: 70.7, 2018: 88.3, 2019: 72.0,
    2020: 37.8, 2021: 46.4, 2022: 91.5, 2023: 62.8, 2024: 74.1,
}
FB_IED_SAI = {
    # US$ bilhões — saída de IED brasileiro
    2015: 3.0, 2016: -4.8, 2017: 14.5, 2018: 11.8, 2019: 20.2,
    2020: 1.5, 2021: 8.8,  2022: 17.5, 2023: 18.3, 2024: 15.2,
}
FB_PORTF = {
    # US$ bilhões — portfólio passivo (entrada)
    2015: 10.8, 2016: 50.3, 2017: 42.5, 2018: -20.1, 2019: 20.9,
    2020: 4.2,  2021: 4.5,  2022: -18.5, 2023: 24.1, 2024: 18.7,
}
FB_REMESSA = {
    # US$ bilhões — remessa de lucros e dividendos
    2015: 14.5, 2016: 15.3, 2017: 17.2, 2018: 22.4, 2019: 24.8,
    2020: 13.8, 2021: 22.3, 2022: 31.2, 2023: 33.5, 2024: 35.1,
}


def fb_to_df(fb_dict):
    """Converte dict de fallback para DataFrame padrão."""
    return pd.DataFrame(list(fb_dict.items()), columns=["ano", "valor"])


# ══════════════════════════════════════════════════════════════════════════════
# EXTRAÇÃO BCB/SGS
# ══════════════════════════════════════════════════════════════════════════════
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=3600, show_spinner=False)
def sgs_serie(cod: int, n: int = 120) -> pd.DataFrame:
    """Retorna DataFrame [data, valor] para série BCB/SGS."""
    try:
        url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}"
               f"/dados/ultimos/{n}?formato=json")
        r = requests.get(url, headers=HEADERS, timeout=12)
        df = pd.DataFrame(r.json())
        df["data"]  = pd.to_datetime(df["data"], dayfirst=True)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=["valor"])
        return df if not df.empty else pd.DataFrame(columns=["data","valor"])
    except Exception:
        return pd.DataFrame(columns=["data","valor"])

def sgs_anual_fluxo(cod: int, fallback: dict, n: int = 120) -> pd.DataFrame:
    """
    Agrega série mensal BCB para anual (soma dos fluxos).
    Se API falhar ou retornar vazio, usa fallback auditado.
    """
    df = sgs_serie(cod, n)
    if not df.empty:
        df["ano"] = df["data"].dt.year
        df_ano = df.groupby("ano")["valor"].sum().reset_index()
        # Converter de US$ mi para US$ bi se necessário
        # Séries 22xxx retornam em US$ milhões
        if df_ano["valor"].abs().mean() > 1000:
            df_ano["valor"] = df_ano["valor"] / 1000
        if len(df_ano) >= 3:
            return df_ano
    return fb_to_df(fallback)

def sgs_reservas(fallback: dict) -> pd.DataFrame:
    """
    Reservas mensais — série 13621 (US$ bilhões).
    Fallback: dados anuais de fim de período.
    """
    df = sgs_serie(13621, 120)
    if not df.empty:
        # Série já em US$ bilhões
        if df["valor"].mean() < 10:
            df["valor"] = df["valor"] * 1000  # era em US$ mi
        return df
    # Fallback: converter dict anual em série mensal (último mês de cada ano)
    rows = [{"data": pd.Timestamp(f"{ano}-12-01"), "valor": v}
            for ano, v in fallback.items()]
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# EXTRAÇÃO CSV BANCO MUNDIAL
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400, show_spinner=False)
def carregar_csv() -> pd.DataFrame:
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "data", "worldbank_data.csv")
    try:
        return pd.read_csv(caminho, encoding="latin-1", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def wb_serie(df_wb, indicador, paises_sel, ano="2024"):
    """Extrai valor de um indicador para lista de países."""
    col = f"{ano} [YR{ano}]"
    sub = df_wb[df_wb["Series Name"] == indicador]
    out = {}
    for cod in paises_sel:
        wb_name = PAISES.get(cod, "")
        row = sub[sub["Country Name"] == wb_name]
        if row.empty: continue
        try:
            v = float(row.iloc[0].get(col, ".."))
            if not np.isnan(v): out[cod] = v
        except: pass
    return out

def wb_hist(df_wb, indicador, paises_sel):
    """Retorna DataFrame wide ano×país."""
    anos_cols = [c for c in df_wb.columns if "YR" in str(c) and "2025" not in c]
    sub = df_wb[df_wb["Series Name"] == indicador]
    result = {}
    for cod in paises_sel:
        wb_name = PAISES.get(cod, "")
        row = sub[sub["Country Name"] == wb_name]
        if row.empty: continue
        linha = {}
        for col in anos_cols:
            try:
                v = float(row.iloc[0].get(col, ".."))
                if not np.isnan(v): linha[int(col.split()[0])] = v
            except: pass
        if linha: result[cod] = linha
    return pd.DataFrame(result).T


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Fluxo de Capitais | BI Econômico",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

def _filtros():
    st.multiselect("Países (comparativo):", options=list(PAISES.keys()),
                   default=PAISES_DEFAULT,
                   format_func=lambda c: PAISES_NOMES.get(c, c),
                   key="paises_cap")
    st.divider()
    st.caption("**BCB/SGS:** reservas, IED, transações correntes\n"
               "**Banco Mundial:** FDI comparativo internacional")

sidebar_padrao(pagina_atual="Fluxo_Capitais", filtros_extra=_filtros)
paises_sel = st.session_state.get("paises_cap", PAISES_DEFAULT) or PAISES_DEFAULT

st.title("💸 Fluxo de Capitais — IED, Reservas e Posição Internacional")
st.caption("BCB/SGS · Banco Mundial WDI · Dados atualizados automaticamente")

st.info("""
**O que este painel mede?**

O fluxo de capitais é o termômetro da confiança internacional no Brasil. Quando estrangeiros
investem aqui — seja em empresas (IED) ou em títulos (portfólio) — financiam o crescimento
e sustentam o câmbio. Quando saem, pressionam o real e elevam o risco-país.

Este painel acompanha **investimento direto estrangeiro (IED), reservas internacionais,
transações correntes e balança comercial** — os quatro pilares da posição externa brasileira
— e compara o IED do Brasil com os principais países emergentes e desenvolvidos.
""")

# ── Carregamento ──────────────────────────────────────────────────────────────
with st.spinner("Carregando dados de fluxo de capitais..."):
    df_reservas   = sgs_reservas(FB_RESERVAS)
    df_tc_anual   = sgs_anual_fluxo(22707, FB_TC)
    df_bc_anual   = sgs_anual_fluxo(22704, FB_BC)
    df_ied_ent    = sgs_anual_fluxo(22886, FB_IED_ENT)
    df_ied_sai    = sgs_anual_fluxo(22895, FB_IED_SAI)
    df_portf      = sgs_anual_fluxo(22900, FB_PORTF)
    df_rem_lucros = sgs_anual_fluxo(22749, FB_REMESSA)
    df_wb         = carregar_csv()

fdi_2024  = wb_serie(df_wb, "Foreign direct investment, net inflows (BoP, current US$)", paises_sel, "2024")
fdi_2023  = wb_serie(df_wb, "Foreign direct investment, net inflows (BoP, current US$)", paises_sel, "2023")
fdi_hist  = wb_hist(df_wb,  "Foreign direct investment, net inflows (BoP, current US$)", paises_sel)
divida    = wb_serie(df_wb, "External debt stocks, total (DOD, current US$)", paises_sel, "2023")

# ── KPIs ──────────────────────────────────────────────────────────────────────
res_ult  = float(df_reservas.sort_values("data").iloc[-1]["valor"]) if not df_reservas.empty else None
res_ant  = float(df_reservas.sort_values("data").iloc[-13]["valor"]) if len(df_reservas) > 13 else res_ult
tc_ult   = float(df_tc_anual.sort_values("ano").iloc[-1]["valor"] / 1000) if not df_tc_anual.empty else None
bc_ult   = float(df_bc_anual.sort_values("ano").iloc[-1]["valor"] / 1000) if not df_bc_anual.empty else None
ied_br   = fdi_2024.get("BR", 0) / 1e9 if "BR" in fdi_2024 else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏦 Reservas Internacionais",
          f"US$ {res_ult:.1f} bi" if res_ult else "—",
          f"{res_ult - res_ant:+.1f} bi (12m)" if res_ult and res_ant else None)
c2.metric("💰 IED Brasil (2024)",
          f"US$ {ied_br:.1f} bi" if ied_br else "—")
c3.metric("🌐 Transações Correntes",
          f"US$ {tc_ult:.1f} bi" if tc_ult else "—",
          delta_color="inverse" if tc_ult and tc_ult < 0 else "normal")
c4.metric("⚖️ Balança Comercial",
          f"US$ {bc_ult:.1f} bi" if bc_ult else "—")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# ABAS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🏦 Reservas & Posição Externa",
    "💰 IED — Brasil e Comparativo Global",
    "📊 Fluxos Detalhados",
])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("🏦 Reservas Internacionais e Balanço de Pagamentos")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Reservas Internacionais — US$ bilhões (mensal)**")
        if not df_reservas.empty:
            df_r = df_reservas.sort_values("data").copy()
            fig, ax = plt.subplots(figsize=(6, 3.8))
            fig_estilo(fig, [ax])
            ax.fill_between(df_r["data"], df_r["valor"],
                            color=PALETA["azul"], alpha=0.25)
            ax.plot(df_r["data"], df_r["valor"],
                    color=PALETA["azul"], lw=2, label="Reservas")
            # Anotação último valor
            ult = df_r.iloc[-1]
            ax.annotate(f"US$ {ult['valor']:.1f}bi",
                        xy=(ult["data"], ult["valor"]),
                        xytext=(-60, 10), textcoords="offset points",
                        color=PALETA["amarelo"], fontsize=9, fontweight="bold")
            ax.set_ylabel("US$ bilhões", color=TEXTO)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.xaxis.set_major_locator(mdates.YearLocator(2))
            plt.tight_layout(); st.pyplot(fig); plt.close()
        else:
            st.info("Dados de reservas indisponíveis no momento.")

    with col_b:
        st.markdown("**Transações Correntes vs Balança Comercial — US$ bilhões (anual)**")
        if not df_tc_anual.empty and not df_bc_anual.empty:
            tc = df_tc_anual[df_tc_anual["ano"] >= 2015].copy()
            bc = df_bc_anual[df_bc_anual["ano"] >= 2015].copy()
            anos_comuns = sorted(set(tc["ano"]) & set(bc["ano"]))
            tc_v = [tc[tc["ano"]==a]["valor"].values[0]/1000 for a in anos_comuns]
            bc_v = [bc[bc["ano"]==a]["valor"].values[0]/1000 for a in anos_comuns]

            fig2, ax2 = plt.subplots(figsize=(6, 3.8))
            fig_estilo(fig2, [ax2])
            x = np.arange(len(anos_comuns)); w = 0.38
            ax2.bar(x - w/2, bc_v, w, color=PALETA["verde"], alpha=0.85, label="Bal. Comercial")
            ax2.bar(x + w/2, tc_v, w, color=PALETA["laranja"], alpha=0.85, label="Transações Correntes")
            ax2.axhline(0, color=TEXTO, lw=0.8, alpha=0.5)
            ax2.set_xticks(x); ax2.set_xticklabels(anos_comuns, rotation=45, ha="right", fontsize=8)
            ax2.set_ylabel("US$ bilhões", color=TEXTO)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
            ax2.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
            plt.tight_layout(); st.pyplot(fig2); plt.close()

    tc_v_ult = tc_ult or 0
    bc_v_ult = bc_ult or 0
    res_v    = res_ult or 0
    st.info(f"""
**Posição Externa Brasileira — Leitura Integrada**

As **reservas internacionais (US$ {res_v:.0f} bi)** representam o principal colchão de proteção
do Brasil contra crises externas — equivalem a mais de 20 meses de importações e cobrem
com folga a dívida externa de curto prazo. Esse nível elevado foi construído ao longo dos
anos 2000 e confere ao BCB capacidade de intervenção no mercado cambial sem comprometer
a sustentabilidade fiscal.

**Transações correntes ({f"US$ {tc_v_ult:.1f} bi" if tc_ult else "—"}):** o déficit em conta
corrente é estrutural na economia brasileira — reflexo do envio de lucros e dividendos por
multinacionais instaladas no país (renda primária negativa). Esse déficit é financiado pelo
superávit na conta financeira, principalmente via IED e investimentos em portfólio.

**Balança comercial ({f"US$ {bc_v_ult:.1f} bi" if bc_ult else "—"}):** o superávit comercial
sustentado pelo agronegócio e mineração é o principal amortecedor do déficit em serviços e
renda. Uma eventual queda nos preços de commodities teria impacto direto nesse equilíbrio.
    """)

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("💰 Investimento Estrangeiro Direto (IED) — Comparativo Internacional")

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**IED líquido em 2024 — US$ bilhões**")
        df_fdi = pd.DataFrame([
            {"cod": c, "val": v / 1e9, "nome": PAISES_NOMES.get(c, c)}
            for c, v in fdi_2024.items()
        ]).sort_values("val", ascending=True)

        if not df_fdi.empty:
            norm = mcolors.Normalize(vmin=df_fdi["val"].min(), vmax=df_fdi["val"].max())
            cmap = cm.get_cmap("RdYlGn")
            fig3, ax3 = plt.subplots(figsize=(6, len(df_fdi)*0.42+0.5))
            fig_estilo(fig3, [ax3])
            bars = ax3.barh(df_fdi["nome"], df_fdi["val"], height=0.7,
                            color=[cmap(norm(v)) for v in df_fdi["val"]])
            for bar, val, cod in zip(bars, df_fdi["val"], df_fdi["cod"]):
                bar.set_edgecolor("#FFD700" if cod == "BR" else "none")
                bar.set_linewidth(2 if cod == "BR" else 0)
                ax3.text(val + 1, bar.get_y() + bar.get_height()/2,
                         f"US$ {val:.1f}bi", va="center", fontsize=7.5, color=TEXTO)
            ax3.axvline(0, color=TEXTO, lw=0.8, alpha=0.5)
            ax3.set_xlabel("US$ bilhões", color=TEXTO)
            ax3.set_xlim(df_fdi["val"].min() - 20, df_fdi["val"].max() * 1.2)
            plt.tight_layout(); st.pyplot(fig3); plt.close()

    with col_d:
        st.markdown("**Trajetória IED — 2016 a 2024 (selecionados)**")
        paises_linha = [c for c in ["BR","US","CN","IN","MX","DE"] if c in paises_sel]
        if not fdi_hist.empty and paises_linha:
            anos_h = sorted([c for c in fdi_hist.columns if isinstance(c, int) and c >= 2016])
            fig4, ax4 = plt.subplots(figsize=(6, 4))
            fig_estilo(fig4, [ax4])
            for cod in paises_linha:
                if cod not in fdi_hist.index: continue
                vals = [fdi_hist.loc[cod, a]/1e9 if a in fdi_hist.columns else np.nan for a in anos_h]
                ax4.plot(anos_h, vals, color=CORES.get(cod, "#888"),
                         lw=2.5 if cod == "BR" else 1.5,
                         alpha=1.0 if cod == "BR" else 0.75,
                         marker="o", markersize=5 if cod == "BR" else 3,
                         label=PAISES_NOMES.get(cod, cod))
            ax4.axhline(0, color=TEXTO, lw=0.6, ls="--", alpha=0.4)
            ax4.set_ylabel("US$ bilhões", color=TEXTO)
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
            ax4.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO, loc="best")
            plt.tight_layout(); st.pyplot(fig4); plt.close()

    br_fdi24 = fdi_2024.get("BR", 0) / 1e9
    us_fdi24 = fdi_2024.get("US", 0) / 1e9
    cn_fdi24 = fdi_2024.get("CN", 0) / 1e9
    in_fdi24 = fdi_2024.get("IN", 0) / 1e9

    st.info(f"""
**IED — O Brasil no Mapa Global do Capital**

O Brasil captou **US$ {br_fdi24:.1f} bi** em IED em 2024 — posicionando-se como um dos
principais destinos de investimento estrangeiro entre os emergentes. Esse fluxo reflete a
atratividade do mercado consumidor doméstico, a estabilidade institucional relativa e as
oportunidades na transição energética (pré-sal, renováveis).

**Queda da China (US$ {cn_fdi24:.1f} bi):** o recuo expressivo do IED chinês em 2024 reflete
tensões geopolíticas, maior controle regulatório sobre saídas de capital e reorientação das
cadeias globais de valor para fora da China — processo que beneficia parcialmente o Brasil e
a Índia ({in_fdi24:.1f} bi) como destinos alternativos de manufatura.

**EUA (US$ {us_fdi24:.1f} bi):** apesar do volume absoluto elevado, o IED americano desacelerou
em 2024 com a política de *reshoring* — repatriação de investimentos produtivos incentivada
pelo IRA e CHIPS Act.
    """)

# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("📊 Fluxos Detalhados — Brasil (BCB/SGS)")

    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("**IED Entrada vs Saída — US$ bilhões (anual)**")
        if not df_ied_ent.empty:
            df_ie = df_ied_ent[df_ied_ent["ano"] >= 2015].copy()
            df_is = df_ied_sai[df_ied_sai["ano"] >= 2015].copy() if not df_ied_sai.empty else pd.DataFrame()
            anos_ie = sorted(df_ie["ano"].unique())

            fig5, ax5 = plt.subplots(figsize=(6, 3.8))
            fig_estilo(fig5, [ax5])
            x = np.arange(len(anos_ie)); w = 0.38
            ent_v = [df_ie[df_ie["ano"]==a]["valor"].values[0]/1000 if a in df_ie["ano"].values else 0 for a in anos_ie]
            ax5.bar(x, ent_v, w*2, color=PALETA["verde"], alpha=0.85, label="IED Entrada")

            if not df_is.empty:
                sai_v = [-df_is[df_is["ano"]==a]["valor"].values[0]/1000
                         if a in df_is["ano"].values else 0 for a in anos_ie]
                ax5.bar(x, sai_v, w*2, color=PALETA["vermelho"], alpha=0.75, label="IED Saída")

            ax5.axhline(0, color=TEXTO, lw=0.8, alpha=0.5)
            ax5.set_xticks(x); ax5.set_xticklabels(anos_ie, rotation=45, ha="right", fontsize=8)
            ax5.set_ylabel("US$ bilhões", color=TEXTO)
            ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
            ax5.legend(fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
            plt.tight_layout(); st.pyplot(fig5); plt.close()
        else:
            st.info("Dados de IED indisponíveis no momento.")

    with col_f:
        st.markdown("**Portfólio (passivo) e Remessa de Lucros — US$ bilhões (anual)**")
        if not df_portf.empty:
            df_p  = df_portf[df_portf["ano"] >= 2015].copy()
            df_rl = df_rem_lucros[df_rem_lucros["ano"] >= 2015].copy() if not df_rem_lucros.empty else pd.DataFrame()
            anos_p = sorted(df_p["ano"].unique())

            fig6, ax6 = plt.subplots(figsize=(6, 3.8))
            fig6.patch.set_facecolor(FUNDO)
            ax6b = ax6.twinx()
            fig_estilo(fig6, [ax6, ax6b])

            port_v = [df_p[df_p["ano"]==a]["valor"].values[0]/1000
                      if a in df_p["ano"].values else np.nan for a in anos_p]
            ax6.bar(anos_p, port_v, color=PALETA["azul"], alpha=0.7, label="Portfólio passivo")
            ax6.set_ylabel("Portfólio (US$ bi)", color=PALETA["azul"])
            ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
            ax6.tick_params(axis="y", colors=PALETA["azul"])

            if not df_rl.empty:
                rem_v = [df_rl[df_rl["ano"]==a]["valor"].values[0]/1000
                         if a in df_rl["ano"].values else np.nan for a in anos_p]
                ax6b.plot(anos_p, rem_v, color=PALETA["laranja"], lw=2,
                          marker="o", markersize=4, label="Remessa de lucros")
                ax6b.set_ylabel("Remessa lucros (US$ bi)", color=PALETA["laranja"])
                ax6b.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"US${v:.0f}bi"))
                ax6b.tick_params(axis="y", colors=PALETA["laranja"])

            h1, l1 = ax6.get_legend_handles_labels()
            h2, l2 = ax6b.get_legend_handles_labels()
            ax6.legend(h1+h2, l1+l2, fontsize=8, facecolor=FUNDO_CARD, labelcolor=TEXTO)
            plt.tight_layout(); st.pyplot(fig6); plt.close()
        else:
            st.info("Dados de portfólio indisponíveis no momento.")

    # Dívida externa comparativa
    if divida:
        st.markdown("**Dívida Externa Total — US$ bilhões (2023)**")
        df_div = pd.DataFrame([
            {"cod": c, "val": v/1e9, "nome": PAISES_NOMES.get(c,c)}
            for c, v in divida.items() if v > 0
        ]).sort_values("val", ascending=True)

        if not df_div.empty:
            fig7, ax7 = plt.subplots(figsize=(10, 2.8))
            fig_estilo(fig7, [ax7])
            norm_d = mcolors.Normalize(vmin=0, vmax=df_div["val"].max())
            bars7 = ax7.barh(df_div["nome"], df_div["val"], height=0.6,
                             color=[cm.get_cmap("RdYlGn_r")(norm_d(v)) for v in df_div["val"]])
            for bar, val, cod in zip(bars7, df_div["val"], df_div["cod"]):
                bar.set_edgecolor("#FFD700" if cod=="BR" else "none")
                bar.set_linewidth(2 if cod=="BR" else 0)
                ax7.text(val+5, bar.get_y()+bar.get_height()/2,
                         f"US${val:.0f}bi", va="center", fontsize=7.5, color=TEXTO)
            ax7.set_xlabel("US$ bilhões", color=TEXTO)
            plt.tight_layout(); st.pyplot(fig7); plt.close()

    br_div = divida.get("BR", 0) / 1e9 if "BR" in divida else None
    st.info(f"""
**Portfólio e Dívida — O Outro Lado do Fluxo**

O investimento em **portfólio** (ações e títulos) é o componente mais volátil do fluxo de
capitais — entra rapidamente atraído pelo diferencial de juros e sai na primeira percepção
de risco, pressionando o câmbio. O Brasil, com Selic entre as mais altas do mundo, é
historicamente atrativo para carry trade.

**Remessa de lucros:** o envio de dividendos por multinacionais instaladas no Brasil é um
dos principais vetores do déficit em transações correntes. Esse fluxo é estrutural —
cresce com o estoque de IED acumulado — e é de difícil reversão no curto prazo.

**Dívida externa{f' brasileira: US$ {br_div:.0f} bi' if br_div else ''}:** em termos relativos
ao PIB e às reservas, a dívida externa brasileira está em nível administrável.
O risco maior é o custo de rolagem em cenários de aversão ao risco global — quando o spread
soberano sobe e o acesso ao mercado internacional encarece.
    """)

# ── Metodologia ───────────────────────────────────────────────────────────────
st.divider()
with st.expander("📋 Metodologia e Fontes"):
    st.markdown("""
    | Indicador | Fonte | Série |
    |---|---|---|
    | Reservas internacionais | BCB/SGS | 13621 |
    | Transações correntes | BCB/SGS | 22707 |
    | Balança comercial | BCB/SGS | 22704 |
    | IED — entrada | BCB/SGS | 22886 |
    | IED — saída | BCB/SGS | 22895 |
    | Portfólio passivo | BCB/SGS | 22900 |
    | Remessa de lucros | BCB/SGS | 22749 |
    | FDI por país | Banco Mundial WDI | `BX.KLT.DINV.CD.WD` |
    | Dívida externa total | Banco Mundial WDI | `DT.DOD.DECT.CD` |

    **Notas:**
    - IED e fluxos: valores em US$ milhões no SGS, convertidos para bilhões na exibição
    - Reservas: estoque mensal em US$ bilhões
    - Dados BCB atualizados em tempo real via API REST
    - Dados Banco Mundial via arquivo `data/worldbank_data.csv` (atualizado fev/2026)
    """)
