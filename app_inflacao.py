# =============================================================================
# BI ECONÔMICO — PÁGINA DE INFLAÇÃO
# Framework: Streamlit
# Deploy: streamlit.app (gratuito)
#
# INSTALAÇÃO:
#   pip install streamlit python-bcb pandas numpy matplotlib requests
#
# RODAR LOCALMENTE:
#   streamlit run app_inflacao.py
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import requests
import warnings
from bcb import sgs
from datetime import datetime
from dateutil.relativedelta import relativedelta
warnings.filterwarnings('ignore')


# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BI Econômico — Inflação",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado — tema escuro profissional
st.markdown("""
<style>
    /* Fundo principal */
    .stApp { background-color: #0F1117; color: #CCCCCC; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1A1D27; }
    
    /* Cards de métricas */
    [data-testid="stMetric"] {
        background-color: #1A1D27;
        border: 1px solid #2A2D3A;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricValue"] { color: white; font-size: 1.8rem; }
    [data-testid="stMetricLabel"] { color: #AAAAAA; font-size: 0.8rem; }
    [data-testid="stMetricDelta"] { font-size: 0.85rem; }

    /* Título principal */
    h1 { color: white; font-weight: 700; }
    h2, h3 { color: #CCCCCC; }

    /* Divisor */
    hr { border-color: #2A2D3A; }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# COLETA DE DADOS (com cache de 1 hora)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_inflacao():
    """Coleta indicadores de inflação via BCB/SGS."""
    SERIES = {
        "IPCA": 433, "INPC": 188, "IPCA_15": 189,
        "IGPM": 189, "IGP_DI": 190, "IGP_10": 7447,
        "IPA_M": 225, "IPC_M": 4175, "INCC_M": 192, "IPC_FIPE": 193,
    }
    fim    = datetime.today()
    inicio = fim - relativedelta(years=10)
    frames = {}
    for nome, cod in SERIES.items():
        try:
            s = sgs.get({nome: cod},
                        start=inicio.strftime("%Y-%m-%d"),
                        end=fim.strftime("%Y-%m-%d"))
            s[nome] = s[nome].resample("MS").mean()
            frames[nome] = s[nome]
        except:
            pass
    if not frames:
        return pd.DataFrame()
    df = pd.DataFrame(frames).astype("float64")
    df.index = pd.to_datetime(df.index)
    df.ffill(inplace=True)
    # Acumulado 12m
    def acum12m(s):
        return ((1 + s/100).rolling(12, min_periods=12)
                .apply(np.prod, raw=True) - 1) * 100
    for col in list(df.columns):
        df[f"{col}_acum12m"] = acum12m(df[col])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_ipca_grupos():
    """Coleta IPCA por grupos via IBGE/APISIDRA."""
    GRUPOS = {
        "7170": "Alimentação e bebidas", "7445": "Habitação",
        "7486": "Artigos de residência", "7558": "Vestuário",
        "7625": "Transportes",           "7660": "Saúde e cuidados pessoais",
        "7712": "Despesas pessoais",     "7766": "Educação",
        "7786": "Comunicação",
    }
    fim    = datetime.today()
    inicio = fim - relativedelta(years=5)
    per    = f"{inicio.strftime('%Y%m')}-{fim.strftime('%Y%m')}"
    url    = (f"https://apisidra.ibge.gov.br/values/t/7060"
              f"/n1/all/v/63/p/{per}/c315/allxt?formato=json")
    try:
        df = pd.read_json(url)
        df = df.query("V not in ['Valor','...', '-']").copy()
        df["D4C"] = df["D4C"].astype(str)
        df = df[df["D4C"].isin(GRUPOS.keys())].copy()
        df["Data"]  = pd.to_datetime(df["D3C"], format="%Y%m")
        df["Valor"] = pd.to_numeric(df["V"].str.replace(",", "."), errors="coerce")
        df["Grupo"] = df["D4C"].map(GRUPOS)
        return df[["Data", "Grupo", "Valor"]].dropna()
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_focus():
    """Coleta expectativas Focus via BCB/OLINDA."""
    fim    = datetime.today()
    inicio = fim - relativedelta(years=4)
    fi     = inicio.strftime("%Y-%m-%d")
    ff     = fim.strftime("%Y-%m-%d")

    def buscar(endpoint, filtro, select):
        url = (f"https://olinda.bcb.gov.br/olinda/servico/Expectativas"
               f"/versao/v1/odata/{endpoint}"
               f"?$filter={filtro}&$select={select}&$format=json")
        try:
            req     = requests.Request("GET", url)
            prep    = req.prepare()
            prep.url = url
            resp    = requests.Session().send(prep, timeout=30)
            resp.raise_for_status()
            return pd.DataFrame(resp.json().get("value", []))
        except:
            return pd.DataFrame()

    # IPCA 12 meses
    df12 = buscar(
        "ExpectativasMercadoInflacao12Meses",
        f"Indicador eq 'IPCA' and Data ge '{fi}' and Data le '{ff}' and Suavizada eq 'S'",
        "Indicador,Data,Mediana,Minimo,Maximo"
    )
    if not df12.empty:
        df12["Data"]    = pd.to_datetime(df12["Data"])
        df12["Fonte"]   = "Inflacao12m"
        for c in ["Mediana","Minimo","Maximo"]:
            df12[c] = pd.to_numeric(df12[c], errors="coerce")

    # Anuais
    indicadores = ["IPCA","Selic","PIB Total","Câmbio"]
    frames_anuais = []
    for ind in indicadores:
        df_a = buscar(
            "ExpectativasMercadoAnuais",
            f"Indicador eq '{ind}' and Data ge '{fi}' and Data le '{ff}' and baseCalculo eq 0",
            "Indicador,Data,DataReferencia,Mediana"
        )
        if not df_a.empty:
            df_a["Data"]    = pd.to_datetime(df_a["Data"])
            df_a["Fonte"]   = "Anual"
            df_a["Mediana"] = pd.to_numeric(df_a["Mediana"], errors="coerce")
            frames_anuais.append(df_a)

    df_anual = pd.concat(frames_anuais, ignore_index=True) if frames_anuais else pd.DataFrame()
    return df12, df_anual


# -----------------------------------------------------------------------------
# SIDEBAR — FILTROS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Filtros")
    st.markdown("---")

    anos_disponiveis = list(range(2016, datetime.today().year + 1))
    ano_inicio, ano_fim = st.select_slider(
        "Período",
        options=anos_disponiveis,
        value=(2021, datetime.today().year)
    )

    st.markdown("---")
    st.markdown("### Índices")
    indices_sel = st.multiselect(
        "Selecione os índices",
        ["IPCA", "IGPM", "INPC", "IPC_FIPE", "IGP_DI"],
        default=["IPCA", "IGPM", "INPC"]
    )

    st.markdown("---")
    st.markdown("### Sobre")
    st.markdown("""
    **BI Econômico Educacional**
    
    Dados: BCB/SGS · IBGE/SIDRA · BCB/Focus
    
    Atualizado automaticamente a cada hora.
    """)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados econômicos..."):
    df_infl  = carregar_inflacao()
    df_grupos = carregar_ipca_grupos()
    df_focus12, df_focus_anual = carregar_focus()

# Filtrar por período
data_inicio = pd.Timestamp(f"{ano_inicio}-01-01")
data_fim    = pd.Timestamp(f"{ano_fim}-12-31")

if not df_infl.empty:
    df_infl_f = df_infl[
        (df_infl.index >= data_inicio) &
        (df_infl.index <= data_fim)
    ].copy()
else:
    df_infl_f = pd.DataFrame()

if not df_grupos.empty:
    df_grupos_f = df_grupos[
        (df_grupos["Data"] >= data_inicio) &
        (df_grupos["Data"] <= data_fim)
    ].copy()
else:
    df_grupos_f = pd.DataFrame()


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding: 0.5rem 0;'>
    📊 Inflação — Painel de Monitoramento
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Análise comparativa de índices · Expectativas de mercado · Decomposição por grupos
</p>
""", unsafe_allow_html=True)

st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
def ultimo_valor(df, col):
    if df.empty or col not in df.columns:
        return None
    s = df[col].dropna()
    return s.iloc[-1] if len(s) > 0 else None

ipca_atual   = ultimo_valor(df_infl_f, "IPCA_acum12m")
ipca_ant     = df_infl_f["IPCA_acum12m"].dropna().iloc[-2] if (
    not df_infl_f.empty and len(df_infl_f["IPCA_acum12m"].dropna()) > 1
) else None
delta_ipca   = round(ipca_atual - ipca_ant, 2) if ipca_atual and ipca_ant else None

# Focus esperado
if not df_focus12.empty:
    ult_focus = (df_focus12
                 .sort_values("Data")
                 .dropna(subset=["Mediana"])
                 .iloc[-1])
    focus_med = ult_focus["Mediana"]
else:
    focus_med = None

surpresa = round(ipca_atual - focus_med, 2) if ipca_atual and focus_med else None

# Meses acima da meta
if not df_infl_f.empty and "IPCA_acum12m" in df_infl_f.columns:
    s = df_infl_f["IPCA_acum12m"].dropna()
    meses_acima = int((s > 4.5).sum())
    total_meses = len(s)
else:
    meses_acima = total_meses = 0

# Ano atual para meta
ano_ref  = datetime.today().year
METAS    = {2022:3.5, 2023:3.25, 2024:3.0, 2025:3.0, 2026:3.0}
meta_bcb = METAS.get(ano_ref, 3.0)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("IPCA 12m", f"{ipca_atual:.2f}%" if ipca_atual else "—",
              delta=f"{delta_ipca:+.2f}pp" if delta_ipca else None)
with c2:
    st.metric("Focus 12m", f"{focus_med:.2f}%" if focus_med else "—",
              delta="Mediana mercado", delta_color="off")
with c3:
    st.metric("Meta BCB", f"{meta_bcb:.2f}%",
              delta=f"Teto: {meta_bcb+1.5:.1f}%", delta_color="off")
with c4:
    cor_surp = "normal" if surpresa and surpresa < 0 else "inverse"
    st.metric("Surpresa", f"{surpresa:+.2f}pp" if surpresa else "—",
              delta="vs Focus", delta_color="off")
with c5:
    st.metric("Acima da meta", f"{meses_acima} / {total_meses}",
              delta="meses no período", delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# LINHA PRINCIPAL — GRÁFICO IPCA × FOCUS + DECOMPOSIÇÃO
# -----------------------------------------------------------------------------
col_graf, col_decomp = st.columns([6, 4])

with col_graf:
    st.markdown("#### IPCA Realizado × Esperado pelo Mercado")

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0F1117")
    ax.set_facecolor("#0F1117")

    COR_IPCA  = "#00D4FF"
    COR_FOCUS = "#FFB800"
    COR_META  = "#FF4B6E"

    if not df_focus12.empty:
        df_foc_m = (df_focus12
                    .assign(Ano_Mes=lambda x: x["Data"].dt.to_period("M"))
                    .groupby("Ano_Mes")
                    .agg(Med=("Mediana","median"),
                         Min=("Minimo","min"),
                         Max=("Maximo","max"))
                    .reset_index())
        df_foc_m["Data"] = df_foc_m["Ano_Mes"].dt.to_timestamp()
        df_foc_m = df_foc_m[
            (df_foc_m["Data"] >= data_inicio) &
            (df_foc_m["Data"] <= data_fim)
        ]
        if not df_foc_m.empty:
            ax.fill_between(df_foc_m["Data"], df_foc_m["Min"],
                            df_foc_m["Max"], color=COR_FOCUS, alpha=0.07)
            ax.plot(df_foc_m["Data"], df_foc_m["Med"],
                    color=COR_FOCUS, lw=1.8, ls="--", alpha=0.9,
                    label="IPCA esperado 12m (Focus)")

    if not df_infl_f.empty and "IPCA_acum12m" in df_infl_f.columns:
        s = df_infl_f["IPCA_acum12m"].dropna()
        ax.plot(s.index, s.values, color=COR_IPCA, lw=2.5, zorder=5,
                label="IPCA acumulado 12m")
        if len(s) > 0:
            ax.scatter(s.index[-1], s.iloc[-1], color=COR_IPCA, s=60, zorder=6)
            ax.annotate(f"  {s.iloc[-1]:.2f}%",
                        xy=(s.index[-1], s.iloc[-1]),
                        xytext=(8,4), textcoords="offset points",
                        color=COR_IPCA, fontsize=10, fontweight="bold")

    # Metas por ano
    for ano in range(ano_inicio, ano_fim+1):
        if ano in METAS:
            ini = pd.Timestamp(f"{ano}-01-01")
            fim_ano = pd.Timestamp(f"{ano}-12-31")
            ax.hlines(METAS[ano], ini, fim_ano,
                      colors=COR_META, lw=1.0, ls=":", alpha=0.7)
            ax.fill_between([ini, fim_ano],
                            METAS[ano]-1.5, METAS[ano]+1.5,
                            color=COR_META, alpha=0.04)

    ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax.tick_params(colors="#AAAAAA", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b/%Y"))
    plt.xticks(rotation=30, ha="right")
    for sp in ax.spines.values(): sp.set_edgecolor("#333")
    ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
              labelcolor="#CCC", framealpha=0.9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


with col_decomp:
    st.markdown("#### Decomposição IPCA por Grupo")

    if not df_grupos_f.empty:
        CORES = {
            "Alimentação e bebidas":    "#FF6B6B",
            "Habitação":                "#4ECDC4",
            "Artigos de residência":    "#45B7D1",
            "Vestuário":                "#96CEB4",
            "Transportes":              "#FFEAA7",
            "Saúde e cuidados pessoais":"#DDA0DD",
            "Despesas pessoais":        "#98D8C8",
            "Educação":                 "#F7DC6F",
            "Comunicação":              "#85C1E9",
        }
        df_piv = (df_grupos_f
                  .groupby(["Data","Grupo"])["Valor"].mean()
                  .reset_index()
                  .pivot(index="Data", columns="Grupo", values="Valor")
                  .fillna(0))
        df_piv.sort_index(inplace=True)
        if len(df_piv) > 24:
            df_piv = df_piv.iloc[-24:]

        grupos = df_piv.columns.tolist()
        cores  = [CORES.get(g, "#AAA") for g in grupos]
        n_m    = len(df_piv)
        larg   = max(8, int(22 - n_m * 0.3))

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        bot_p = np.zeros(n_m)
        bot_n = np.zeros(n_m)
        for i, g in enumerate(grupos):
            vals_p = df_piv[g].clip(lower=0).values
            vals_n = df_piv[g].clip(upper=0).values
            ax2.bar(df_piv.index, vals_p, bottom=bot_p,
                    color=cores[i], alpha=0.85, width=larg, label=g)
            ax2.bar(df_piv.index, vals_n, bottom=bot_n,
                    color=cores[i], alpha=0.85, width=larg)
            bot_p += vals_p
            bot_n += vals_n

        total = df_piv.sum(axis=1)
        ax2.plot(df_piv.index, total, color="white",
                 lw=2.0, marker="o", ms=3, zorder=5)
        ax2.axhline(0, color="#555", lw=0.8)
        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5, axis="y")
        ax2.tick_params(colors="#AAA", labelsize=8)
        ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
        ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b/%y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        ax2.legend(fontsize=6.5, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", ncol=2, loc="upper left",
                   framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
    else:
        st.info("Dados de grupos não disponíveis.")


st.markdown("---")


# -----------------------------------------------------------------------------
# LINHA INFERIOR — ANÁLISE + EXPECTATIVAS FOCUS
# -----------------------------------------------------------------------------
col_txt, col_exp = st.columns([6, 4])

with col_txt:
    st.markdown("#### Análise Automática")

    if not df_infl_f.empty and "IPCA_acum12m" in df_infl_f.columns:
        s       = df_infl_f["IPCA_acum12m"].dropna()
        ipca_v  = s.iloc[-1] if len(s) > 0 else None
        mes_ref = s.index[-1].strftime("%b/%Y") if len(s) > 0 else "—"
        media_p = s.mean()
        pico_v  = s.max()
        min_v   = s.min()
        mes_pico= s.idxmax().strftime("%b/%Y")
        mes_min = s.idxmin().strftime("%b/%Y")
        tend    = round(s.iloc[-1] - s.iloc[-3], 2) if len(s) >= 3 else 0

        meta_v  = METAS.get(datetime.today().year, 3.0)
        teto_v  = meta_v + 1.5

        if ipca_v <= meta_v:
            sit = f"dentro da meta e abaixo do centro ({meta_v:.1f}%)"
        elif ipca_v <= teto_v:
            sit = f"dentro da banda de tolerância, mas acima da meta de {meta_v:.1f}%"
        else:
            sit = f"acima do teto da meta ({teto_v:.1f}%), em território de descumprimento"

        txt_tend = ("acelerando" if tend > 0.3
                    else "desacelerando" if tend < -0.3
                    else "estável")

        if focus_med:
            surp = ipca_v - focus_med if ipca_v else 0
            if abs(surp) < 0.1:
                txt_focus = f"em linha com o consenso Focus de {focus_med:.2f}%."
            elif surp > 0:
                txt_focus = (f"**{surp:.2f}pp acima** da mediana Focus de {focus_med:.2f}% "
                             f"— surpresa negativa para o mercado.")
            else:
                txt_focus = (f"**{abs(surp):.2f}pp abaixo** da mediana Focus de {focus_med:.2f}% "
                             f"— surpresa positiva.")
        else:
            txt_focus = "expectativas Focus não disponíveis."

        st.markdown(f"""
**[IPCA]** Em {mes_ref}, o IPCA acumulado em 12 meses ficou em **{ipca_v:.2f}%** — {sit}.

**[Focus]** O resultado ficou {txt_focus}

**[Tendência]** A inflação está **{txt_tend}** ({tend:+.2f}pp nos últimos 3 meses).

**[Período]** No intervalo selecionado: média de {media_p:.2f}%, 
pico de {pico_v:.2f}% ({mes_pico}) e mínimo de {min_v:.2f}% ({mes_min}).
        """)
    else:
        st.info("Dados insuficientes para análise.")


with col_exp:
    st.markdown("#### Expectativas Focus")

    ano_atual = datetime.today().year

    def focus_anual(indicador, ano):
        if df_focus_anual.empty: return None
        df_f = df_focus_anual[
            (df_focus_anual["Indicador"] == indicador) &
            (df_focus_anual["DataReferencia"] == str(ano))
        ]
        if df_f.empty: return None
        return df_f.sort_values("Data").iloc[-1]["Mediana"]

    f_ipca   = focus_anual("IPCA",      ano_atual)
    f_selic  = focus_anual("Selic",     ano_atual)
    f_pib    = focus_anual("PIB Total", ano_atual)
    f_cambio = focus_anual("Câmbio",    ano_atual)

    c1e, c2e = st.columns(2)
    with c1e:
        st.metric(f"IPCA {ano_atual}",
                  f"{f_ipca:.2f}%" if f_ipca else "—",
                  delta="Meta: 3,00%", delta_color="off")
        st.metric(f"PIB {ano_atual}",
                  f"{f_pib:.2f}%" if f_pib else "—",
                  delta="Var. real", delta_color="off")
    with c2e:
        st.metric(f"Selic {ano_atual}",
                  f"{f_selic:.2f}%" if f_selic else "—",
                  delta="Taxa básica", delta_color="off")
        st.metric(f"Câmbio {ano_atual}",
                  f"R$ {f_cambio:.2f}" if f_cambio else "—",
                  delta="USD/BRL", delta_color="off")

    st.caption(f"Fonte: BCB/Focus — mediana · última coleta disponível")


# -----------------------------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<p style='text-align:center; color:#555555; font-size:0.8rem;'>
    BI Econômico Educacional · Dados: BCB/SGS · IBGE/SIDRA · BCB/Focus · 
    Atualizado automaticamente
</p>
""", unsafe_allow_html=True)