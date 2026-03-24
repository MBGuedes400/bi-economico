# =============================================================================
# pages/10_Ibovespa.py — Ibovespa & Acoes
# =============================================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from datetime import datetime

from utils.dados  import get_ibovespa, get_juros, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Ibovespa | BI Econômico", page_icon="📉", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2019, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2019, datetime.today().year))
sidebar_padrao(pagina_atual="Ibovespa", filtros_extra=_filtros)

with st.spinner("Carregando dados de mercado..."):
    df_ibov, df_acoes = get_ibovespa()
    df_jr             = get_juros()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty:
        return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_if = filtrar(df_ibov)
df_af = filtrar(df_acoes)

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    📉 Ibovespa & Ações
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Índice histórico · Top ações · Variação e volatilidade
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
ibov_v, ibov_d = ultimo_valor(df_ibov, "Ibovespa")

if ibov_v:
    # Var no ano
    ano_atual = datetime.today().year
    ini_ano   = df_ibov[df_ibov.index.year == ano_atual]["Ibovespa"].dropna()
    var_ano   = round((ibov_v / ini_ano.iloc[0] - 1) * 100, 1) if len(ini_ano) > 1 else None

    # Var 12m
    s_ibov = df_ibov["Ibovespa"].dropna()
    var_12m = round((s_ibov.iloc[-1] / s_ibov.iloc[-13] - 1) * 100, 1) if len(s_ibov) >= 13 else None

    # Volatilidade 3m (desvio padrão dos retornos mensais)
    ret_3m  = s_ibov.pct_change().dropna().tail(3)
    vol_3m  = round(ret_3m.std() * ibov_v, 0) if len(ret_3m) >= 2 else None

    # Maxima 52 semanas
    if not df_acoes.empty:
        max_52 = df_ibov["Ibovespa"].dropna().tail(12).max()
    else:
        max_52 = s_ibov.tail(12).max()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Ibovespa", f"{ibov_v:,.0f}",
                  delta=f"+{var_12m:.1f}% em 12m" if var_12m else None)
    with c2:
        st.metric("Var. no ano", f"{var_ano:+.1f}%" if var_ano is not None else "—")
    with c3:
        st.metric("Volatilidade 3m (desvio)", f"{vol_3m:,.0f} pts" if vol_3m else "—")
    with c4:
        st.metric("Máxima 52 semanas", f"{max_52:,.0f}" if max_52 else "—")

st.markdown("---")

# =============================================================================
# ANALISE DIDATICA
# =============================================================================
selic_v, _ = ultimo_valor(df_jr, "Selic_Meta") if not df_jr.empty else (None, None)

if ibov_v and selic_v:
    # Earnings yield implícito: P/E histórico Brasil ~= 10x => earnings yield ~= 10%
    earnings_yield = 10.0
    premio_risco   = round(earnings_yield - selic_v, 1)
    sinal          = "comprimido" if premio_risco < 2 else ("atrativo" if premio_risco > 4 else "neutro")

    st.info(
        f"**Leitura do mercado acionário**\n\n"
        f"O Ibovespa em **{ibov_v:,.0f} pts** "
        f"{'acumula {:.1f}% no ano'.format(var_ano) if var_ano else ''} "
        f"e **{var_12m:.1f}% em 12 meses** contra a Selic de **{selic_v:.1f}% a.a.**\n\n"
        f"Com juro real elevado, o prêmio de risco das ações fica **{sinal}**: "
        f"investidores exigem retorno adicional sobre a renda fixa para justificar o risco da bolsa. "
        f"Historicamente, ciclos de corte de juros tendem a valorizar o Ibovespa, "
        f"enquanto altas prolongadas da Selic pressionar valuations para baixo."
    )

st.markdown("---")

# =============================================================================
# LINHA 1 — Historico mensal (esq) + Variacao mensal (dir)
# =============================================================================
col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Ibovespa — Histórico mensal")
    if not df_if.empty and "Ibovespa" in df_if.columns:
        s = df_if["Ibovespa"].dropna()
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        ax.plot(s.index, s.values, color="#00D4FF", lw=2.0)
        ax.fill_between(s.index, s.values, s.min() * 0.98, alpha=0.10, color="#00D4FF")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1000:.0f}k"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados do Ibovespa não disponíveis.")

with col2:
    st.markdown("#### Variação mensal (%)")
    if not df_if.empty and "Ibovespa" in df_if.columns:
        s    = df_if["Ibovespa"].dropna()
        ret  = s.pct_change().dropna() * 100
        cors = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in ret.values]
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        ax2.bar(ret.index, ret.values, color=cors, width=20)
        ax2.axhline(0, color="#555", lw=0.8)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

st.markdown("---")

# =============================================================================
# LINHA 2 — Top acoes base 100 (esq) + Retorno no periodo (dir)
# =============================================================================
st.markdown("#### Top ações — desempenho comparado (base 100)")
st.caption("Base 100 no início do período selecionado. Acima de 100 = valorização acumulada.")

CORES_ACOES = {
    "VALE3": "#00D4FF", "PETR4": "#FFB800", "ITUB4": "#00D4AA",
    "BBDC4": "#FF4B6E", "ABEV3": "#A78BFA", "WEGE3": "#F59E0B",
    "RENT3": "#34D399", "MGLU3": "#F87171",
}

if not df_af.empty:
    col3, col4 = st.columns([6, 4])

    with col3:
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        retornos = {}
        for ticker in df_af.columns:
            s = df_af[ticker].dropna()
            if s.empty or len(s) < 2:
                continue
            base = s.iloc[0]
            if base > 0:
                b100 = s / base * 100
                cor  = CORES_ACOES.get(ticker, "#AAAAAA")
                ax3.plot(b100.index, b100.values, color=cor, lw=1.5, label=ticker)
                retornos[ticker] = round(b100.iloc[-1] - 100, 1)
        ax3.axhline(100, color="#555", lw=0.8, ls="--")
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax3.tick_params(colors="#AAAAAA", labelsize=9)
        ax3.set_ylabel("Base 100", color="#AAAAAA", fontsize=9)
        ax3.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9, ncol=2)
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig3); plt.close()

    with col4:
        st.markdown("#### Var. no período (%)")
        if retornos:
            ret_ord = dict(sorted(retornos.items(), key=lambda x: x[1]))
            fig4, ax4 = plt.subplots(figsize=(6, 4))
            fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
            tickers = list(ret_ord.keys())
            vals    = list(ret_ord.values())
            cores4  = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in vals]
            ax4.barh(tickers, vals, color=cores4, height=0.6)
            for i, (t, v) in enumerate(zip(tickers, vals)):
                ax4.text(v + (1 if v >= 0 else -1), i,
                         f"{v:+.1f}%", va="center",
                         ha="left" if v >= 0 else "right",
                         color="#CCC", fontsize=8)
            ax4.axvline(0, color="#555", lw=0.8)
            ax4.tick_params(colors="#AAAAAA", labelsize=9)
            ax4.grid(True, color="#FFF", alpha=0.05, lw=0.5, axis="x")
            for sp in ax4.spines.values(): sp.set_edgecolor("#333")
            plt.tight_layout()
            st.pyplot(fig4); plt.close()

    # Leitura dinamica das acoes
    if retornos:
        melhor = max(retornos, key=retornos.get)
        pior   = min(retornos, key=retornos.get)
        n_pos  = sum(1 for v in retornos.values() if v > 0)
        n_neg  = sum(1 for v in retornos.values() if v < 0)
        st.info(
            f"**Leitura das ações no período:**  \n"
            f"Dos {len(retornos)} papéis monitorados, **{n_pos} valorizaram** e **{n_neg} caíram**.  \n"
            f"Melhor desempenho: **{melhor}** ({retornos[melhor]:+.1f}%) · "
            f"Pior: **{pior}** ({retornos[pior]:+.1f}%).  \n\n"
            f"Papéis acima da linha de base 100 **geraram alpha** — retorno acima do índice. "
            f"Trajetórias que se cruzam revelam **rotação setorial**: momentos em que o mercado "
            f"migra de um setor para outro (ex: saída de commodities para bancos em ciclos de juro alto)."
        )
else:
    st.info("Dados de ações não disponíveis.")

st.markdown("---")

# =============================================================================
# ANALISE TECNICA — contexto e interpretacao
# =============================================================================
st.markdown("#### Como interpretar estes dados")
c_a, c_b, c_c = st.columns(3)
with c_a:
    st.markdown("""
**📌 Ibovespa como termômetro**

O Ibovespa reúne as ~90 ações mais líquidas da B3, ponderadas por valor de mercado.
Reflete o humor do mercado sobre a economia brasileira e reage a:

- Decisões do COPOM — Selic mais alta = custo de oportunidade maior para ações
- Dados de inflação, atividade e fiscal
- Cenário externo: dólar forte, commodities, juros americanos (Fed)

Uma queda do Ibovespa não significa necessariamente recessão — pode ser ajuste de valuation ou saída de capital estrangeiro.
""")
with c_b:
    st.markdown("""
**📌 Base 100 — leitura relativa**

A base 100 normaliza preços absolutos diferentes e permite comparação direta:

- Ação em **150** → valorizou 50% no período
- Ação em **80** → desvalorizou 20%
- Abaixo da linha tracejada → desempenho abaixo do ponto de partida

Identifica quais papéis **geraram alpha** (retorno acima do índice) e quais destruíram valor relativo.
Trajetórias que se cruzam revelam **rotação setorial** — quando o mercado migra de um setor para outro.
""")
with c_c:
    selic_txt = f"Selic em {selic_v:.1f}% a.a." if selic_v else "juros elevados"
    st.markdown(f"""
**📌 Bolsa vs Renda Fixa**

Com {selic_txt}, o custo de oportunidade de investir em ações é alto — a renda fixa oferece retorno previsível sem risco de mercado.

O **prêmio de risco** das ações precisa compensar volatilidade, risco de resultado e eventos sistêmicos.

Historicamente no Brasil, o Ibovespa supera a Selic nos ciclos de **queda de juros** e perde em ciclos de **alta prolongada** — o timing macroeconômico importa tanto quanto a seleção de ativos.
""")

rodape()
