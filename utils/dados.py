# =============================================================================
# utils/dados.py — Coleta e cache de todos os dados econômicos
# Centraliza TODAS as chamadas de API em um único lugar.
# Cada função usa @st.cache_data para evitar rebuscar a cada interação.
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
from bcb import sgs
from datetime import datetime
from dateutil.relativedelta import relativedelta
import warnings
warnings.filterwarnings('ignore')


# -----------------------------------------------------------------------------
# CONSTANTES GLOBAIS
# -----------------------------------------------------------------------------
METAS_BCB = {
    2019: 4.25, 2020: 4.0, 2021: 3.75,
    2022: 3.5,  2023: 3.25, 2024: 3.0,
    2025: 3.0,  2026: 3.0,  2027: 3.0
}
TOLERANCIA_BCB = 1.5


# -----------------------------------------------------------------------------
# HELPER — COLETA BCB/SGS GENÉRICA
# -----------------------------------------------------------------------------
def _coletar_sgs(series_dict, anos=10):
    """Coleta séries do BCB/SGS e agrega para frequência mensal."""
    fim    = datetime.today()
    inicio = fim - relativedelta(years=anos)
    frames = {}
    for nome, cod in series_dict.items():
        try:
            s = sgs.get({nome: cod},
                        start=inicio.strftime("%Y-%m-%d"),
                        end=fim.strftime("%Y-%m-%d"))
            frames[nome] = s[nome].resample("MS").mean().round(4)
        except Exception as e:
            st.warning(f"Erro ao coletar {nome}: {e}")
    if not frames:
        return pd.DataFrame()
    df = pd.DataFrame(frames).astype("float64")
    df.index = pd.to_datetime(df.index)
    df.ffill(inplace=True)
    return df


def _coletar_focus_odata(endpoint, filtro, select):
    """Coleta dados do BCB/Focus via OData."""
    url = (f"https://olinda.bcb.gov.br/olinda/servico/Expectativas"
           f"/versao/v1/odata/{endpoint}"
           f"?$filter={filtro}&$select={select}&$format=json")
    try:
        req  = requests.Request("GET", url)
        prep = req.prepare()
        prep.url = url
        resp = requests.Session().send(prep, timeout=30)
        resp.raise_for_status()
        return pd.DataFrame(resp.json().get("value", []))
    except:
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# BLOCO INFLAÇÃO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_inflacao():
    """IPCA, IGP-M, INPC e família completa — BCB/SGS."""
    SERIES = {
        "IPCA": 433, "INPC": 188, "IPCA_15": 189,
        "IGPM": 189, "IGP_DI": 190, "IGP_10": 7447,
        "IPA_M": 225, "IPC_M": 4175, "INCC_M": 192, "IPC_FIPE": 193,
    }
    df = _coletar_sgs(SERIES, anos=10)
    if df.empty:
        return df
    # Acumulado 12m
    def acum12m(s):
        return ((1 + s/100).rolling(12, min_periods=12)
                .apply(np.prod, raw=True) - 1) * 100
    for col in list(df.columns):
        df[f"{col}_acum12m"] = acum12m(df[col])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_ipca_grupos():
    """IPCA por 9 grupos de despesa — IBGE/SIDRA."""
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
        df["Valor"] = pd.to_numeric(
            df["V"].astype(str).str.replace(",", "."), errors="coerce")
        df["Grupo"] = df["D4C"].map(GRUPOS)
        return df[["Data", "Grupo", "Valor"]].dropna()
    except:
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# BLOCO POLÍTICA MONETÁRIA
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_juros():
    """Selic, CDI, TR, TLP, Poupança — BCB/SGS."""
    SERIES = {
        "Selic_Meta": 432,    # Selic Meta — decisão COPOM (% a.a.)
        "Selic_Over": 1178,   # Selic Over — taxa diária efetiva
        "CDI":        4391,   # CDI mensal
        "TLP":        27574,  # Taxa de Longo Prazo (BNDES)
        "Poupanca":   196,    # Rendimento da poupança (% a.m.)
        # TR removida — série descontinuada no SGS para esse período
    }
    return _coletar_sgs(SERIES, anos=10)


# -----------------------------------------------------------------------------
# BLOCO CÂMBIO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_cambio():
    """USD, EUR, GBP, ARS, CNY e Reservas — BCB/SGS."""
    SERIES = {
        "USD_BRL": 1,        "EUR_BRL": 21619,
        "GBP_BRL": 21623,    "ARS_BRL": 21626,
        "CNY_BRL": 21634,    "Reservas_USD_bi": 13621,
    }
    return _coletar_sgs(SERIES, anos=10)


# -----------------------------------------------------------------------------
# BLOCO MERCADO DE TRABALHO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pnad():
    """PNAD Contínua — desemprego, informalidade, participação — IBGE/SIDRA."""
    VARIAVEIS = {
        4099:  "Taxa_Desocupacao",
        12466: "Taxa_Informalidade",
        4096:  "Taxa_Participacao",
        4090:  "Pessoas_Ocupadas",
    }
    fim    = datetime.today()
    inicio = fim - relativedelta(years=8)
    per    = f"{inicio.strftime('%Y%m')}-{fim.strftime('%Y%m')}"

    def tri_para_data(p):
        try:
            s = str(p)
            return datetime(int(s[:4]), (int(s[4:])-1)*3+1, 1)
        except:
            return None

    frames = {}
    for cod, nome in VARIAVEIS.items():
        url = (f"https://apisidra.ibge.gov.br/values/t/4093"
               f"/n1/all/v/{cod}/p/{per}?formato=json")
        try:
            df = pd.read_json(url)
            df = df.query("V not in ['Valor','...', '-']").copy()
            df["Data"]  = df["D3C"].apply(tri_para_data)
            df["Valor"] = pd.to_numeric(
                df["V"].astype(str).str.replace(",", "."), errors="coerce")
            df = df[["Data", "Valor"]].dropna().rename(columns={"Valor": nome})
            df.sort_values("Data", inplace=True)
            frames[nome] = df.set_index("Data")[nome]
        except:
            pass
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames)


@st.cache_data(ttl=3600, show_spinner=False)
def get_caged():
    """CAGED e Massa Salarial — BCB/SGS."""
    SERIES = {"CAGED_Saldo": 28763, "Massa_Salarial": 28195}
    return _coletar_sgs(SERIES, anos=8)


# -----------------------------------------------------------------------------
# BLOCO PIB
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pib():
    """PIB por setor — IBGE/SIDRA tabela 1846."""
    SETORES = {
        "90707": "PIB_Total",       "90687": "Agropecuaria",
        "90691": "Industria",       "90696": "Servicos",
        "93404": "Consumo_Familias","93406": "Investimento_FBCF",
        "93407": "Exportacoes",     "93408": "Importacoes",
    }
    fim    = datetime.today()
    inicio = fim - relativedelta(years=10)
    per    = f"{inicio.strftime('%Y%m')}-{fim.strftime('%Y%m')}"

    def tri_para_data(p):
        try:
            s = str(p)
            return datetime(int(s[:4]), (int(s[4:])-1)*3+1, 1)
        except:
            return None

    url = (f"https://apisidra.ibge.gov.br/values/t/1846"
           f"/n1/all/v/585/p/{per}/c11255/allxt?formato=json")
    try:
        df = pd.read_json(url)
        df = df.query("V not in ['Valor','...', '-']").copy()
        df["D4C"] = df["D4C"].astype(str)
        df = df[df["D4C"].isin(SETORES.keys())].copy()
        df["Data"]   = df["D3C"].apply(tri_para_data)
        df["Setor"]  = df["D4C"].map(SETORES)
        df["Valor"]  = pd.to_numeric(
            df["V"].astype(str).str.replace(",", "."), errors="coerce")
        return df[["Data","Setor","Valor"]].dropna()
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_ibcbr():
    """IBC-Br — proxy mensal do PIB — BCB/SGS."""
    return _coletar_sgs({"IBC_Br": 24363}, anos=10)


# -----------------------------------------------------------------------------
# BLOCO FOCUS — EXPECTATIVAS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_focus_inflacao12m():
    """IPCA e IGP-M esperados para os próximos 12 meses."""
    fim    = datetime.today()
    inicio = fim - relativedelta(years=4)
    fi, ff = inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")
    frames = []
    for ind in ["IPCA", "IGP-M"]:
        df = _coletar_focus_odata(
            "ExpectativasMercadoInflacao12Meses",
            f"Indicador eq '{ind}' and Data ge '{fi}' and Data le '{ff}' and Suavizada eq 'S'",
            "Indicador,Data,Mediana,Minimo,Maximo,numeroRespondentes"
        )
        if not df.empty:
            df["Data"]    = pd.to_datetime(df["Data"])
            df["Fonte"]   = "Inflacao12m"
            for c in ["Mediana","Minimo","Maximo"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_focus_anual():
    """Expectativas anuais — IPCA, Selic, PIB, Câmbio, Desemprego etc."""
    fim    = datetime.today()
    inicio = fim - relativedelta(years=4)
    fi, ff = inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")
    INDICADORES = [
        "IPCA", "IGP-M", "Selic", "PIB Total", "Câmbio",
        "Taxa de desocupação", "IPCA Serviços", "IPCA Administrados",
    ]
    frames = []
    for ind in INDICADORES:
        df = _coletar_focus_odata(
            "ExpectativasMercadoAnuais",
            f"Indicador eq '{ind}' and Data ge '{fi}' and Data le '{ff}' and baseCalculo eq 0",
            "Indicador,Data,DataReferencia,Mediana,DesvioPadrao,Minimo,Maximo"
        )
        if not df.empty:
            df["Data"]    = pd.to_datetime(df["Data"])
            df["Fonte"]   = "Anual"
            for c in ["Mediana","DesvioPadrao","Minimo","Maximo"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# -----------------------------------------------------------------------------
# HELPER — ÚLTIMO VALOR DE UMA SÉRIE
# -----------------------------------------------------------------------------
def ultimo_valor(df, col):
    """Retorna o último valor não-nulo de uma coluna."""
    if df is None or df.empty or col not in df.columns:
        return None, None
    s = df[col].dropna()
    if s.empty:
        return None, None
    return round(s.iloc[-1], 4), s.index[-1]


def focus_ultimo(df_focus, indicador, fonte="Anual", ano=None):
    """Retorna a última mediana Focus para um indicador."""
    if df_focus is None or df_focus.empty:
        return None
    f = df_focus[df_focus["Indicador"] == indicador]
    if "Fonte" in f.columns:
        f = f[f["Fonte"] == fonte]
    if ano and "DataReferencia" in f.columns:
        f = f[f["DataReferencia"] == str(ano)]
    f = f.dropna(subset=["Mediana"])
    if f.empty:
        return None
    return round(f.sort_values("Data").iloc[-1]["Mediana"], 2)
