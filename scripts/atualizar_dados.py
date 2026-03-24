# =============================================================================
# scripts/atualizar_dados.py
# Atualização mensal de dados de mercado financeiro
# Rodar localmente: python scripts/atualizar_dados.py
#
# Pré-requisitos: pip install yfinance pandas pyarrow openpyxl requests
#
# Fluxo:
#   1. Baixa Pink Sheet do World Bank (ou usa arquivo local já baixado)
#   2. Extrai commodities → data/commodities.parquet
#   3. Baixa Ibovespa + top ações via yfinance → data/ibovespa.parquet
#                                                 data/acoes.parquet
#   4. Após rodar: git add data/ && git commit -m "data: atualização mensal"
# =============================================================================

import sys
import os
import requests
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from pathlib import Path

# Garante que roda da raiz do projeto
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando atualização de dados...")
print(f"Destino: {DATA_DIR}\n")

# =============================================================================
# 1. COMMODITIES — World Bank Pink Sheet
# =============================================================================
print("=" * 60)
print("1. COMMODITIES — World Bank Pink Sheet")
print("=" * 60)

# Mapeamento: nome interno → coluna no xlsx (0-indexed)
COLUNAS_WB = {
    "Petroleo": (4,  "Crude oil, WTI",     "$/bbl"),
    "Ouro":     (69, "Gold",               "$/troy oz"),
    "Soja":     (24, "Soybeans",           "$/mt"),
    "Milho":    (30, "Maize",              "$/mt"),
    "Trigo":    (36, "Wheat, US SRW",      "$/mt"),
    "Cafe":     (12, "Coffee, Arabica",    "$/kg"),
    "Acucar":   (47, "Sugar, world",       "$/kg"),
}

# URL do Pink Sheet (atualizar se der 404 — o hash muda a cada release)
URL_PINK = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
# Caminho local alternativo (caso URL falhe — baixe manualmente e coloque aqui)
LOCAL_PINK = ROOT / "data" / "CMO-Historical-Data-Monthly.xlsx"

df_raw = None

# Tenta download automático
try:
    print(f"  Baixando Pink Sheet... ", end="", flush=True)
    r = requests.get(URL_PINK, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code == 200 and len(r.content) > 200_000:
        df_raw = pd.read_excel(BytesIO(r.content), sheet_name="Monthly Prices", header=None)
        print(f"OK ({len(r.content)/1024:.0f} KB)")
    else:
        print(f"FALHOU (status={r.status_code}, size={len(r.content)})")
except Exception as e:
    print(f"ERRO: {e}")

# Fallback: arquivo local
if df_raw is None and LOCAL_PINK.exists():
    print(f"  Usando arquivo local: {LOCAL_PINK.name}")
    df_raw = pd.read_excel(LOCAL_PINK, sheet_name="Monthly Prices", header=None)

if df_raw is None:
    print("  ERRO: Não foi possível obter o Pink Sheet.")
    print("  → Baixe manualmente em: https://www.worldbank.org/en/research/commodity-markets")
    print(f"  → Salve em: {LOCAL_PINK}")
else:
    # Extrair dados (linha 6 em diante, coluna 0 = data no formato 1960M01)
    df_c = df_raw.iloc[6:].copy()
    df_c.columns = range(len(df_c.columns))
    df_c[0] = pd.to_datetime(
        df_c[0].astype(str).str.replace("M", "-") + "-01", errors="coerce"
    )
    df_c = df_c.dropna(subset=[0]).set_index(0)
    df_c.index.name = "Date"

    frames = {}
    for nome, (col, desc, unid) in COLUNAS_WB.items():
        s = pd.to_numeric(df_c[col], errors="coerce").dropna()
        # Filtrar últimos 15 anos
        s = s[s.index >= pd.Timestamp(datetime.today().year - 15, 1, 1)]
        frames[nome] = s
        print(f"  {nome:10} ({desc}): {len(s)} obs | "
              f"último={s.index[-1].strftime('%Y-%m')} val={s.iloc[-1]:.2f} {unid}")

    df_commodities = pd.DataFrame(frames).sort_index()
    out_c = DATA_DIR / "commodities.parquet"
    df_commodities.to_parquet(out_c)
    print(f"\n  ✓ Salvo: {out_c} ({out_c.stat().st_size/1024:.1f} KB)")
    print(f"  Período: {df_commodities.index[0].strftime('%Y-%m')} → "
          f"{df_commodities.index[-1].strftime('%Y-%m')}")

# =============================================================================
# 2. IBOVESPA + AÇÕES — yfinance (local only)
# =============================================================================
print()
print("=" * 60)
print("2. IBOVESPA + AÇÕES — yfinance")
print("=" * 60)

try:
    import yfinance as yf

    fim    = datetime.today()
    inicio = fim.replace(year=fim.year - 10)

    # --- Ibovespa ---
    print("  Baixando ^BVSP... ", end="", flush=True)
    ibov = yf.download("^BVSP", start=inicio, end=fim, progress=False, auto_adjust=True)
    if ibov.empty:
        print("VAZIO")
    else:
        ibov.index = pd.to_datetime(ibov.index)
        close = ibov["Close"]["^BVSP"] if isinstance(ibov.columns, pd.MultiIndex) else ibov["Close"]
        ibov_m = close.resample("MS").last().rename("Ibovespa").dropna().to_frame()
        out_ibov = DATA_DIR / "ibovespa.parquet"
        ibov_m.to_parquet(out_ibov)
        print(f"OK | {len(ibov_m)} obs | último={ibov_m.index[-1].strftime('%Y-%m')} "
              f"val={ibov_m['Ibovespa'].iloc[-1]:,.0f}")
        print(f"  ✓ Salvo: {out_ibov} ({out_ibov.stat().st_size/1024:.1f} KB)")

    # --- Top ações ---
    TICKERS = ["VALE3.SA","PETR4.SA","ITUB4.SA","BBDC4.SA",
               "ABEV3.SA","WEGE3.SA","RENT3.SA","MGLU3.SA"]
    print(f"  Baixando {len(TICKERS)} ações... ", end="", flush=True)
    raw = yf.download(TICKERS, start=inicio, end=fim, progress=False, auto_adjust=True)
    if raw.empty:
        print("VAZIO")
    else:
        acoes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        acoes.index = pd.to_datetime(acoes.index)
        acoes.columns = [str(c).replace(".SA", "") for c in acoes.columns]
        out_acoes = DATA_DIR / "acoes.parquet"
        acoes.to_parquet(out_acoes)
        print(f"OK | {len(acoes)} obs diárias | {list(acoes.columns)}")
        print(f"  ✓ Salvo: {out_acoes} ({out_acoes.stat().st_size/1024:.1f} KB)")

except ImportError:
    print("  yfinance não instalado. Rode: pip install yfinance")
except Exception as e:
    print(f"  ERRO: {e}")

# =============================================================================
# 3. RESUMO FINAL
# =============================================================================
print()
print("=" * 60)
print("RESUMO")
print("=" * 60)
for f in sorted(DATA_DIR.glob("*.parquet")):
    df_check = pd.read_parquet(f)
    print(f"  {f.name:30} | shape={df_check.shape} | "
          f"colunas={list(df_check.columns)}")

print()
print("Próximo passo:")
print("  git add data/")
print('  git commit -m "data: atualização mensal $(date +%Y-%m)"')
print("  git push origin main")
print()
print(f"[{datetime.now().strftime('%H:%M:%S')}] Concluído.")
