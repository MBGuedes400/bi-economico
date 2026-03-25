# =============================================================================
# utils/dados.py — Coleta e cache de todos os dados econômicos
# =============================================================================

import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bcb import sgs
from datetime import datetime
from dateutil.relativedelta import relativedelta
import warnings
warnings.filterwarnings('ignore')

METAS_BCB = {
    2019: 4.25, 2020: 4.0, 2021: 3.75,
    2022: 3.5,  2023: 3.25, 2024: 3.0,
    2025: 3.0,  2026: 3.0,  2027: 3.0
}
TOLERANCIA_BCB = 1.5


# -----------------------------------------------------------------------------
# HELPERS DE COLETA
# -----------------------------------------------------------------------------
def _fetch_sgs_rest(cod, inicio_str, fim_str, timeout=60):
    """Busca série via API REST do BCB com timeout explícito.
    inicio_str / fim_str no formato DD/MM/YYYY."""
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados"
           f"?formato=json&dataInicial={inicio_str}&dataFinal={fim_str}")
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    resp = sess.get(url, timeout=timeout)
    resp.raise_for_status()
    dados = resp.json()
    if not dados:
        return None
    df = pd.DataFrame(dados)
    df["data"]  = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str).str.replace(",", "."), errors="coerce")
    s = df.set_index("data")["valor"].dropna()
    s.index = pd.to_datetime(s.index)
    return s.resample("MS").mean().round(4)


def _coletar_sgs(series_dict, anos=10):
    """Coleta séries do BCB/SGS.
    Estratégia: API REST direta (timeout=60s, 3 tentativas) → fallback python-bcb."""
    fim     = datetime.today()
    inicio  = fim - relativedelta(years=anos)
    ini_dmy = inicio.strftime("%d/%m/%Y")
    fim_dmy = fim.strftime("%d/%m/%Y")
    ini_ymd = inicio.strftime("%Y-%m-%d")
    fim_ymd = fim.strftime("%Y-%m-%d")
    frames  = {}

    for nome, cod in series_dict.items():
        s = None
        # 1) API REST com timeout explícito
        for tentativa in range(3):
            try:
                s = _fetch_sgs_rest(cod, ini_dmy, fim_dmy, timeout=60)
                if s is not None and not s.empty:
                    break
                s = None
            except Exception:
                s = None

        # 2) Fallback: python-bcb
        if s is None:
            for tentativa in range(2):
                try:
                    raw = sgs.get({nome: cod}, start=ini_ymd, end=fim_ymd)
                    s   = raw[nome].resample("MS").mean().round(4)
                    break
                except Exception:
                    s = None

        if s is not None and not s.empty:
            frames[nome] = s

    if not frames:
        return pd.DataFrame()
    df = pd.DataFrame(frames).astype("float64")
    df.index = pd.to_datetime(df.index)
    df.ffill(inplace=True)
    return df


def _coletar_focus_odata(endpoint, filtro, select, top=5000):
    """Coleta dados da API OData do BCB/Focus.
    Usa requests.get(params=) para encoding automatico e correto dos acentos.
    Estrategia 1: params dict (encoding pelo requests).
    Estrategia 2: URL manual com quote(safe='') como fallback.
    """
    from urllib.parse import quote
    base = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
    url_endpoint = f"{base}/{endpoint}"

    params_dict = {
        "$filter":  filtro,
        "$select":  select,
        "$format":  "json",
        "$top":     str(top),
        "$orderby": "Data desc",
    }

    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    for timeout in [45, 90]:
        # Estrategia 1: deixa o requests montar a query string
        try:
            sess = requests.Session()
            sess.headers.update(headers)
            resp = sess.get(url_endpoint, params=params_dict, timeout=timeout)
            resp.raise_for_status()
            dados = resp.json().get("value", [])
            if dados:
                return pd.DataFrame(dados)
        except Exception:
            pass

        # Estrategia 2: URL manual com quote preservando aspas simples e espacos
        try:
            filtro_enc = quote(filtro, safe=" '")
            url_manual = (f"{url_endpoint}"
                          f"?$filter={filtro_enc}"
                          f"&$select={select}"
                          f"&$format=json"
                          f"&$top={top}"
                          f"&$orderby=Data%20desc")
            sess2 = requests.Session()
            sess2.headers.update(headers)
            resp2 = sess2.get(url_manual, timeout=timeout)
            resp2.raise_for_status()
            dados2 = resp2.json().get("value", [])
            if dados2:
                return pd.DataFrame(dados2)
        except Exception:
            pass

    return pd.DataFrame()


# -----------------------------------------------------------------------------
# BLOCO INFLAÇÃO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_inflacao():
    SERIES = {
        "IPCA": 433, "INPC": 188, "IPCA_15": 189,
        "IGPM": 189, "IGP_DI": 190, "IGP_10": 7447,
        "IPA_M": 225, "IPC_M": 4175, "INCC_M": 192, "IPC_FIPE": 193,
    }
    df = _coletar_sgs(SERIES, anos=10)
    if df.empty:
        return df
    def acum12m(s):
        return ((1 + s/100).rolling(12, min_periods=12)
                .apply(np.prod, raw=True) - 1) * 100
    for col in list(df.columns):
        df[f"{col}_acum12m"] = acum12m(df[col])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_ipca_grupos():
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
    except Exception:
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# BLOCO POLÍTICA MONETÁRIA
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_juros():
    SERIES = {
        "Selic_Meta": 432,
        "Selic_Over": 1178,
        "CDI":        4391,
        "TLP":        27574,
        "Poupanca":   196,
    }
    return _coletar_sgs(SERIES, anos=10)


# -----------------------------------------------------------------------------
# BLOCO CÂMBIO — séries separadas para evitar timeout
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_cambio():
    """USD, EUR, GBP, CNY — via API REST BCB com timeout=60s."""
    SERIES = {
        "USD_BRL": 1,
        "EUR_BRL": 21619,
        "GBP_BRL": 21623,
        "CNY_BRL": 21634,
    }
    return _coletar_sgs(SERIES, anos=10)


@st.cache_data(ttl=3600, show_spinner=False)
def get_reservas():
    """Reservas internacionais — série 13621 via API REST BCB."""
    return _coletar_sgs({"Reservas_USD_bi": 13621}, anos=10)


# -----------------------------------------------------------------------------
# BLOCO MERCADO DE TRABALHO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pnad():
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
        except Exception:
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
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames)


@st.cache_data(ttl=3600, show_spinner=False)
def get_caged():
    SERIES = {"CAGED_Saldo": 28763, "Massa_Salarial": 28195}
    return _coletar_sgs(SERIES, anos=8)


# -----------------------------------------------------------------------------
# BLOCO PIB
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pib():
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
        except Exception:
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
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_ibcbr():
    return _coletar_sgs({"IBC_Br": 24363}, anos=10)


# -----------------------------------------------------------------------------
# BLOCO FOCUS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_focus_inflacao12m():
    """Expectativas de inflacao 12 meses — BCB/Focus OData.
    Tenta primeiro com Suavizada='S', fallback sem esse filtro.
    """
    fim    = datetime.today()
    inicio = fim - relativedelta(years=4)
    fi, ff = inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")
    frames = []
    for ind in ["IPCA", "IGP-M"]:
        # Tentativa 1: com suavizacao
        df = _coletar_focus_odata(
            "ExpectativasMercadoInflacao12Meses",
            f"Indicador eq '{ind}' and Data ge '{fi}' and Data le '{ff}' and Suavizada eq 'S'",
            "Indicador,Data,Mediana,Minimo,Maximo,numeroRespondentes"
        )
        # Tentativa 2 (fallback): sem filtro de suavizacao
        if df.empty:
            df = _coletar_focus_odata(
                "ExpectativasMercadoInflacao12Meses",
                f"Indicador eq '{ind}' and Data ge '{fi}' and Data le '{ff}'",
                "Indicador,Data,Mediana,Minimo,Maximo,numeroRespondentes"
            )
        if not df.empty:
            df["Data"]  = pd.to_datetime(df["Data"])
            df["Fonte"] = "Inflacao12m"
            for c in ["Mediana", "Minimo", "Maximo"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_focus_anual():
    """Expectativas anuais — BCB/Focus OData.
    Nomes EXATOS confirmados diretamente na API (GET sem filtro de Indicador):
      - "Câmbio" (com acento, IndicadorDetalhe=None)
      - "IPCA", "IGP-M", "Selic", "PIB Total" (sem acento)
    A estrategia params=dict no requests envia UTF-8 sem double-encoding.
    Alias interno: "Cambio" (sem acento) para filtros nas paginas.
    """
    fim    = datetime.today()
    inicio = fim - relativedelta(years=8)  # 8 anos para suportar slider ate 6 na pagina
    fi, ff = inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")

    # Mapeamento: nome_na_api -> alias_interno
    # Nomes EXATOS confirmados via GET /ExpectativasMercadoAnuais?$select=Indicador
    # Aliases sem acento para comparacoes nas paginas (evita bugs de encoding)
    INDICADORES = {
        "IPCA":                        "IPCA",
        "IGP-M":                       "IGP-M",
        "Selic":                       "Selic",
        "PIB Total":                   "PIB Total",
        "C\u00e2mbio":                 "Cambio",           # Câmbio
        "Taxa de desocupa\u00e7\u00e3o": "Taxa de desocupacao",  # Taxa de desocupação
        "IPCA Servi\u00e7os":          "IPCA Servicos",    # IPCA Serviços
        "IPCA Administrados":          "IPCA Administrados",
        "IPCA Livres":                 "IPCA Livres",
        "IPCA Alimenta\u00e7\u00e3o no domic\u00edlio": "IPCA Alimentacao",  # IPCA Alimentação no domicílio
        "IPCA Bens industrializados":  "IPCA Bens Industrializados",
        "PIB Ind\u00fastria":          "PIB Industria",    # PIB Indústria
        "PIB Servi\u00e7os":           "PIB Servicos",     # PIB Serviços
        "PIB Agropecu\u00e1ria":       "PIB Agropecuaria", # PIB Agropecuária
    }

    frames = []
    for nome_api, alias in INDICADORES.items():
        for filtro in [
            f"Indicador eq '{nome_api}' and Data ge '{fi}' and Data le '{ff}' and baseCalculo eq 0",
            f"Indicador eq '{nome_api}' and Data ge '{fi}' and Data le '{ff}'",
        ]:
            df = _coletar_focus_odata(
                "ExpectativasMercadoAnuais",
                filtro,
                "Indicador,Data,DataReferencia,Mediana,DesvioPadrao,Minimo,Maximo"
            )
            if not df.empty:
                df["Indicador"] = alias   # padroniza para alias sem acento
                df["Data"]  = pd.to_datetime(df["Data"])
                df["Fonte"] = "Anual"
                for c in ["Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                frames.append(df)
                break  # nao tenta o fallback se ja achou

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()



# -----------------------------------------------------------------------------
# BLOCO MERCADO FINANCEIRO — parquet local (gerado por scripts/atualizar_dados.py)
# Atualização mensal: rodar scripts/atualizar_dados.py localmente e fazer commit
# -----------------------------------------------------------------------------
def _parquet_path(nome):
    p1 = os.path.join(os.getcwd(), "data", f"{nome}.parquet")
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", f"{nome}.parquet")
    return os.path.normpath(p2)
 
 
@st.cache_data(ttl=3600, show_spinner=False)
def get_ibovespa():
    """Ibovespa mensal + top ações diárias — lidos de data/ibovespa.parquet e data/acoes.parquet.
    Arquivos gerados por scripts/atualizar_dados.py (roda localmente com yfinance).
    Retorna: (df_ibovespa_mensal, df_acoes_diarias)
    """
    df_ibov  = pd.DataFrame()
    df_acoes = pd.DataFrame()
    try:
        p = _parquet_path("ibovespa")
        if os.path.exists(p):
            df_ibov = pd.read_parquet(p)
            df_ibov.index = pd.to_datetime(df_ibov.index)
    except Exception:
        pass
    try:
        p = _parquet_path("acoes")
        if os.path.exists(p):
            df_acoes = pd.read_parquet(p)
            df_acoes.index = pd.to_datetime(df_acoes.index)
    except Exception:
        pass
    return df_ibov, df_acoes
 
 
@st.cache_data(ttl=3600, show_spinner=False)
def get_commodities():
    """Commodities — lidas de data/commodities.parquet.
    Fonte: World Bank Pink Sheet (via scripts/atualizar_dados.py).
    Colunas: Petroleo, Ouro, Soja, Milho, Trigo, Cafe, Acucar — todas em USD.
    """
    try:
        p = _parquet_path("commodities")
        if not os.path.exists(p):
            return pd.DataFrame()
        df = pd.read_parquet(p)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_fundos_cvm(meses=12):
    """PL e captacao liquida por categoria ANBIMA — CVM dados abertos.
    Usa registro_fundo_classe.zip (RCVM 175) para mapear CNPJ_Classe → categoria.
    Normaliza CNPJ removendo pontuacao para o match.
    Saida: DataFrame mensal, PL em R$ bi, captacao liquida CL_ em R$ bi.
    """
    import zipfile, io as _io

    def _categoria(c):
        if pd.isna(c): return None
        c = str(c).lower()
        if "renda fixa" in c:          return "Renda Fixa"
        if "multimercado" in c:        return "Multimercado"
        if "acoes" in c or "\u00e7\u00f5es" in c: return "Acoes"
        if "previd" in c:              return "Previdencia"
        if "cambial" in c:             return "Cambial"
        if "fii" in c or "imobili" in c: return "FII"
        if "fidc" in c:                return "FIDC"
        if "fip" in c or "particip" in c: return "FIP"
        return "Outros"

    # 1. Cadastro classes RCVM 175
    mapa_cnpj = {}
    try:
        r_cad = requests.get(
            "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip",
            timeout=90, headers={"User-Agent": "Mozilla/5.0"})
        r_cad.raise_for_status()
        z_cad = zipfile.ZipFile(_io.BytesIO(r_cad.content))
        df_cls = pd.read_csv(
            _io.StringIO(z_cad.read("registro_classe.csv").decode("latin1")),
            sep=";", dtype=str, on_bad_lines="skip",
            usecols=["CNPJ_Classe", "Classificacao_Anbima"])
        df_cls["CNPJ_norm"] = (df_cls["CNPJ_Classe"]
                               .str.replace(r"[.\-/]", "", regex=True).str.strip())
        df_cls["Categoria"] = df_cls["Classificacao_Anbima"].apply(_categoria)
        mapa_cnpj = df_cls.dropna(subset=["Categoria"]).set_index("CNPJ_norm")["Categoria"].to_dict()
    except Exception:
        pass

    # 2. Informes diarios mensais
    hoje = datetime.today()
    frames = []
    for i in range(meses):
        ref  = hoje - relativedelta(months=i+1)
        aamm = ref.strftime("%Y%m")
        url  = (f"https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/"
                f"inf_diario_fi_{aamm}.zip")
        try:
            r = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200: continue
            z  = zipfile.ZipFile(_io.BytesIO(r.content))
            df = pd.read_csv(z.open(z.namelist()[0]), sep=";", low_memory=False,
                             usecols=["CNPJ_FUNDO_CLASSE", "DT_COMPTC",
                                      "VL_PATRIM_LIQ", "CAPTC_DIA", "RESG_DIA"],
                             dtype={"CNPJ_FUNDO_CLASSE": str})
            df["DT_COMPTC"] = pd.to_datetime(df["DT_COMPTC"], errors="coerce")
            df["Mes"]       = df["DT_COMPTC"].dt.to_period("M")
            df["CNPJ_norm"] = (df["CNPJ_FUNDO_CLASSE"]
                               .str.replace(r"[.\-/]", "", regex=True).str.strip())
            df["Categoria"] = df["CNPJ_norm"].map(mapa_cnpj)
            df = df.dropna(subset=["Categoria"])
            # PL: ultimo dia do mes por fundo
            ult = df.groupby("CNPJ_norm")["DT_COMPTC"].transform("max")
            df_ult = df[df["DT_COMPTC"] == ult]
            df_pl  = df_ult.groupby(["Mes","Categoria"])["VL_PATRIM_LIQ"].sum().reset_index()
            df_cap = (df.groupby(["Mes","Categoria"])
                       .agg(Cap=("CAPTC_DIA","sum"), Res=("RESG_DIA","sum")).reset_index())
            frames.append(df_pl.merge(df_cap, on=["Mes","Categoria"]))
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)
    df_all["Data"] = df_all["Mes"].dt.to_timestamp()

    pl = (df_all.groupby(["Data","Categoria"])["VL_PATRIM_LIQ"]
          .sum().unstack(fill_value=0) / 1e9).round(1)
    cl = ((df_all.groupby(["Data","Categoria"])["Cap"].sum()
           - df_all.groupby(["Data","Categoria"])["Res"].sum())
          .unstack(fill_value=0) / 1e9).round(1)
    cl.columns = [f"CL_{c}" for c in cl.columns]
    return pl.join(cl).sort_index()


@st.cache_data(ttl=3600, show_spinner=False)
def get_credito_sfn():
    """Operações de crédito, taxas e inadimplência — BCB/SGS.
    Séries de saldo: R$ milhões → dividir por 1000 para bilhões.
    Taxas: % a.a. (já em percentual, não converter).
    Inadimplência: % (já em percentual, não converter).
    Credito_PIB (20542): retorna valor absoluto em R$ milhões — NÃO é porcentagem.
    """
    SERIES = {
        "Credito_Total":        20539,  # R$ milhões — saldo total
        "Credito_PF":           20588,  # R$ milhões — pessoa física
        "Credito_PJ":           20589,  # R$ milhões — pessoa jurídica
        "Credito_Livre":        20546,  # R$ milhões — crédito livre
        "Credito_Dir":          20547,  # R$ milhões — crédito direcionado
        "Taxa_Media_Total":     20714,  # % a.a. — taxa média total
        "Taxa_Media_PF":        20739,  # % a.a. — PF livre
        "Taxa_Media_PJ":        20740,  # % a.a. — PJ livre
        "Inadimplencia_Total":  21082,  # % > 90 dias — total
        "Inadimplencia_PF":     21084,  # % > 90 dias — PF
        "Inadimplencia_PJ":     21085,  # % > 90 dias — PJ
    }
    df = _coletar_sgs(SERIES, anos=10)
    if df.empty:
        return df
    # Converte R$ milhões → R$ bilhões (somente colunas de saldo)
    for col in ["Credito_Total", "Credito_PF", "Credito_PJ",
                "Credito_Livre", "Credito_Dir"]:
        if col in df.columns:
            df[col] = (df[col] / 1000).round(2)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_tesouro_direto():
    """Títulos do Tesouro Direto — Tesouro Transparente CSV.
    Retorna DataFrame com colunas: Tipo Titulo, Data Base, Data Vencimento,
    Taxa Venda Manha, PU Venda Manha.
    URL atualizada em mar/2026 — resource ID 80c9 (anterior 80a4 retornava 404).
    Usa requests com User-Agent para evitar bloqueio, depois parseia via StringIO.
    """
    import io
    url = ("https://www.tesourotransparente.gov.br/ckan/dataset/"
           "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
           "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv")
    try:
        resp = requests.get(url, timeout=60,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.content.decode("latin1")),
                         sep=";", decimal=",")
        df.columns = df.columns.str.strip()
        df["Data Base"]       = pd.to_datetime(df["Data Base"],       format="%d/%m/%Y", errors="coerce")
        df["Data Vencimento"] = pd.to_datetime(df["Data Vencimento"], format="%d/%m/%Y", errors="coerce")
        for col in ["Taxa Venda Manha", "PU Venda Manha", "Taxa Compra Manha"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=5)
        df = df[df["Data Base"] >= cutoff].copy()
        return df.dropna(subset=["Data Base", "Data Vencimento", "Taxa Venda Manha"])
    except Exception:
        return pd.DataFrame()


def _normalizar_bilhoes(df, colunas):
    """Detecta escala automaticamente e normaliza para R$ bilhoes.
    M4 atual ~= R$ 13 tri = 13.000 bi.
    mediana > 1.000.000 => R$ milhoes => /1.000 para bilhoes
    mediana entre 100 e 1.000.000 => ja em bilhoes => sem conversao
    mediana < 10 => R$ trilhoes => *1.000 para bilhoes
    """
    for col in colunas:
        if col not in df.columns:
            continue
        med = df[col].dropna().median()
        if pd.isna(med) or med == 0:
            continue
        if med > 1_000_000:
            df[col] = (df[col] / 1_000).round(2)
        elif med < 10:
            df[col] = (df[col] * 1_000).round(2)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_fundos_bcb():
    """Meios de pagamento e poupanca — BCB/SGS.
    Saida padronizada em R$ bilhoes (deteccao automatica de escala).
    M1=27788, M2=27790, M4=27813, Poupanca=196
    """
    SERIES = {"M1": 27788, "M2": 27790, "M4": 27813, "Poupanca": 196}
    df = _coletar_sgs(SERIES, anos=10)
    if df.empty:
        return df
    return _normalizar_bilhoes(df, list(SERIES.keys()))



# -----------------------------------------------------------------------------
# BLOCO SETOR REAL — Indústria
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pim_pf():
    """Produção Industrial Mensal — IBGE SIDRA tabela 3653.
    Índice de base fixa sem ajuste sazonal (Base: média 2012 = 100).
    Retorna DataFrame wide: index=Data, colunas=setores.
    """
    SETORES = {
        "129315": "Extrativa",
        "129316": "Transformacao",
        "129317": "Alimentos",
        "129326": "Petroleo_Derivados",
        "129330": "Farmaceuticos",
        "129333": "Minerais_nao_Metalicos",
        "129334": "Metalurgia",
        "129337": "Maquinas_Equipamentos",
        "129338": "Veiculos",
        "129336": "Eletronicos",
    }
    url = ("https://apisidra.ibge.gov.br/values/t/3653"
           "/n1/all/v/3135/p/last%2036/c544/allxt?formato=json")
    try:
        df = pd.read_json(url)
        df = df.query("V not in ['Valor','...', '-']").copy()
        df = df[df["D4C"].astype(str).isin(SETORES.keys())].copy()
        df["Setor"] = df["D4C"].astype(str).map(SETORES)
        df["Valor"] = pd.to_numeric(
            df["V"].astype(str).str.replace(",", "."), errors="coerce")
        meses = {"janeiro":1,"fevereiro":2,"março":3,"abril":4,"maio":5,"junho":6,
                 "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
        def parse_mes(s):
            try:
                parts = str(s).lower().split()
                return pd.Timestamp(int(parts[1]), meses[parts[0]], 1)
            except Exception:
                return pd.NaT
        df["Data"] = df["D3N"].apply(parse_mes)
        df = df.dropna(subset=["Data","Valor"])
        wide = df.pivot_table(index="Data", columns="Setor",
                              values="Valor", aggfunc="last")
        wide.index = pd.to_datetime(wide.index)
        return wide.sort_index()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_industria_indicadores():
    """NUCI e ICEI — BCB/SGS.
    NUCI_FGV=24352, NUCI_CNI=28561, ICEI=4394
    """
    SERIES = {
        "NUCI_FGV": 24352,
        "NUCI_CNI": 28561,
        "ICEI":     4394,
    }
    return _coletar_sgs(SERIES, anos=8)



# -----------------------------------------------------------------------------
# BLOCO SETOR REAL — Comercio
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pmc():
    """Pesquisa Mensal de Comercio — IBGE SIDRA tabela 8880 (base 2022=100).
    Classificador c11046/allxt obrigatorio — sem ele retorna '..' em todos os valores.
    """
    VARS = {
        "7169":  "Indice",
        "11709": "VarMensal",
        "11711": "Var12m",
    }
    url = ("https://apisidra.ibge.gov.br/values/t/8880"
           "/n1/all/v/all/p/last%2036/c11046/allxt?formato=json")
    try:
        df = pd.read_json(url)
        df = df.query("V not in ['Valor','...', '-', '..']").copy()
        df = df[df["D2C"].astype(str).isin(VARS.keys())].copy()
        df["Variavel"] = df["D2C"].astype(str).map(VARS)
        df["Valor"] = pd.to_numeric(
            df["V"].astype(str).str.replace(",", "."), errors="coerce")
        meses = {"janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,
                 "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
        meses_pt = {"janeiro":1,"fevereiro":2,"ço":3,"abril":4,"maio":5,"junho":6,
                    "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
        def parse_mes(s):
            try:
                parts = str(s).lower().split()
                mes_num = None
                for k, v in {"janeiro":1,"fevereiro":2,"mar":3,"abril":4,"maio":5,
                              "junho":6,"julho":7,"agosto":8,"setembro":9,
                              "outubro":10,"novembro":11,"dezembro":12}.items():
                    if k in parts[0]:
                        mes_num = v
                        break
                if mes_num is None:
                    return pd.NaT
                return pd.Timestamp(int(parts[1]), mes_num, 1)
            except Exception:
                return pd.NaT
        df["Data"] = df["D3N"].apply(parse_mes)
        df = df.dropna(subset=["Data","Valor"])
        wide = df.pivot_table(index="Data", columns="Variavel",
                              values="Valor", aggfunc="last")
        wide.index = pd.to_datetime(wide.index)
        return wide.sort_index()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_comercio_indicadores():
    """Confianca do consumidor e endividamento — BCB/SGS.
    ICC_FGV=4393, Endividamento=29039, Comprometimento=29040,
    Inadimplencia=29042, Varejo_BCB=1455
    """
    SERIES = {
        "ICC_FGV":        4393,
        "Endividamento":  29039,
        "Comprometimento":29040,
        "Inadimplencia":  29042,
        "Varejo_BCB":     1455,
    }
    return _coletar_sgs(SERIES, anos=8)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def ultimo_valor(df, col):
    if df is None or df.empty or col not in df.columns:
        return None, None
    s = df[col].dropna()
    if s.empty:
        return None, None
    return round(s.iloc[-1], 4), s.index[-1]


def focus_ultimo(df_focus, indicador, fonte="Anual", ano=None):
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


def diagnostico_focus_cambio():
    """Funcao de diagnostico — retorna os indicadores disponiveis na API Focus.
    Chame no terminal: from utils.dados import diagnostico_focus_cambio; print(diagnostico_focus_cambio())
    """
    import requests
    url = ("https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
           "/ExpectativasMercadoAnuais"
           "?$select=Indicador,IndicadorDetalhe&$format=json&$top=500&$orderby=Data desc")
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        dados = resp.json().get("value", [])
        if not dados:
            return "API retornou vazio"
        df = pd.DataFrame(dados).drop_duplicates()
        cambio_rows = df[df["Indicador"].str.lower().str.contains("mbio", na=False)]
        return {
            "todos_indicadores": sorted(df["Indicador"].unique().tolist()),
            "indicadores_cambio": cambio_rows.to_dict("records"),
        }
    except Exception as e:
        return f"Erro: {e}"
