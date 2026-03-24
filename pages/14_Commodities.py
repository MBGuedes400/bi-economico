# =============================================================================
# pages/13_Commodities.py — Commodities
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

from utils.dados  import get_commodities, get_cambio, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Commodities | BI Econômico", page_icon="🌽", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2019, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2015, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2019, datetime.today().year))
sidebar_padrao(pagina_atual="Commodities", filtros_extra=_filtros)

with st.spinner("Carregando commodities..."):
    df_c  = get_commodities()
    df_fx = get_cambio()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty:
        return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_cf = filtrar(df_c)

UNIDADES = {
    "Soja":     "US¢/bu", "Milho":    "US¢/bu", "Trigo":    "US¢/bu",
    "Cafe":     "US¢/lb", "Acucar":   "US¢/lb",
    "Petroleo": "US$/barril", "Ouro":  "US$/oz",
}
CORES = {
    "Soja":     "#00D4AA", "Milho":    "#FFB800", "Trigo":    "#A78BFA",
    "Cafe":     "#FF4B6E", "Acucar":   "#00D4FF",
    "Petroleo": "#F59E0B", "Ouro":     "#FBBF24",
}

def var_periodo(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    if len(s) < 2: return None
    return round((s.iloc[-1] / s.iloc[0] - 1) * 100, 1)

def var_12m(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    if len(s) < 13: return None
    return round((s.iloc[-1] / s.iloc[-13] - 1) * 100, 1)

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    🌽 Commodities
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Soja · Milho · Trigo · Café · Açúcar · Petróleo · Ouro — via yfinance
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs — 7 commodities
# =============================================================================
if not df_c.empty:
    cols_kpi = st.columns(7)
    for i, (nome, unid) in enumerate(UNIDADES.items()):
        v, d = ultimo_valor(df_c, nome)
        var  = var_12m(df_c, nome)
        with cols_kpi[i]:
            st.metric(
                nome,
                f"{v:,.1f}" if v else "—",
                delta=f"{var:+.1f}% 12m" if var is not None else (unid),
                delta_color="normal" if var is not None else "off"
            )
            st.caption(unid)

st.markdown("---")

# =============================================================================
# ANALISE DIDATICA
# =============================================================================
usd_v, _ = ultimo_valor(df_fx, "USD_BRL") if not df_fx.empty else (None, None)
ouro_v,_ = ultimo_valor(df_c, "Ouro")
petro_v,_= ultimo_valor(df_c, "Petroleo")
soja_v,_ = ultimo_valor(df_c, "Soja")

if usd_v:
    impacto_cambio = "amplifica" if usd_v > 5.0 else "atenua"
    st.info(
        f"**Leitura do mercado de commodities**\n\n"
        f"Com **USD/BRL em R$ {usd_v:.2f}**, as commodities cotadas em dólar "
        f"têm seu impacto **{impacto_cambio}do** para o produtor e consumidor brasileiro. "
        f"Um dólar alto aumenta a receita do exportador (soja, milho, petróleo) "
        f"mas encarece combustíveis e alimentos no mercado interno.\n\n"
        + (f"O **ouro em US$ {ouro_v:,.0f}/oz** funciona como ativo de proteção (safe haven): "
           f"sobe em períodos de incerteza geopolítica e queda das taxas reais de juros globais. " if ouro_v else "")
        + (f"O **petróleo em US$ {petro_v:.1f}/barril** é insumo estratégico: "
           f"afeta diretamente combustíveis, frete e custo de produção em toda a cadeia. " if petro_v else "")
    )

st.markdown("---")

# =============================================================================
# LINHA 1 — Evolucao base 100 (esq) + Var no periodo (dir)
# =============================================================================
col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Evolução comparada (base 100)")
    st.caption("Base 100 = primeiro mês do período. Permite comparar ativos com unidades diferentes.")
    if not df_cf.empty:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        for nome in UNIDADES:
            if nome in df_cf.columns:
                s = df_cf[nome].dropna()
                if s.empty or s.iloc[0] == 0: continue
                ax.plot(s.index, s / s.iloc[0] * 100,
                        color=CORES.get(nome, "#AAA"), lw=1.5, label=nome)
        ax.axhline(100, color="#555", lw=0.8, ls="--")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.set_ylabel("Base 100", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9, ncol=2)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig); plt.close()

with col2:
    st.markdown("#### Var. no período (%)")
    if not df_cf.empty:
        retornos = {n: var_periodo(df_cf, n) for n in UNIDADES if n in df_cf.columns}
        retornos = {k: v for k, v in retornos.items() if v is not None}
        if retornos:
            ret_ord = dict(sorted(retornos.items(), key=lambda x: x[1]))
            fig2, ax2 = plt.subplots(figsize=(6, 4.5))
            fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
            nomes = list(ret_ord.keys())
            vals  = list(ret_ord.values())
            cors  = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in vals]
            ax2.barh(nomes, vals, color=cors, height=0.6)
            for i, (n, v) in enumerate(zip(nomes, vals)):
                ax2.text(v + (2 if v >= 0 else -2), i,
                         f"{v:+.1f}%", va="center",
                         ha="left" if v >= 0 else "right",
                         color="#CCC", fontsize=8)
            ax2.axvline(0, color="#555", lw=0.8)
            ax2.tick_params(colors="#AAAAAA", labelsize=9)
            ax2.grid(True, color="#FFF", alpha=0.04, lw=0.5, axis="x")
            for sp in ax2.spines.values(): sp.set_edgecolor("#333")
            plt.tight_layout()
            st.pyplot(fig2); plt.close()

# Análise dinâmica do período
if retornos:
    melhor   = max(retornos, key=retornos.get)
    pior     = min(retornos, key=retornos.get)
    n_alta   = sum(1 for v in retornos.values() if v > 0)
    n_queda  = sum(1 for v in retornos.values() if v < 0)
    soja_ret = retornos.get("Soja")
    cafe_ret = retornos.get("Cafe")
    ouro_ret = retornos.get("Ouro")

    st.info(
        f"**Leitura do período ({ano_ini}–{ano_fim}):**\n\n"
        f"Das {len(retornos)} commodities monitoradas, **{n_alta} subiram** e **{n_queda} caíram** no período. "
        f"Melhor desempenho: **{melhor}** ({retornos[melhor]:+.1f}%) · "
        f"Pior: **{pior}** ({retornos[pior]:+.1f}%).\n\n"
        + (f"A alta do **ouro** ({ouro_ret:+.1f}%) reflete busca por proteção em ambiente de incerteza global — "
           f"tipicamente associada a tensões geopolíticas e queda dos juros reais mundiais. " if ouro_ret and ouro_ret > 0 else "")
        + (f"O **café** ({cafe_ret:+.1f}%) teve desempenho expressivo — o Brasil é o maior exportador mundial "
           f"e eventos climáticos (geadas, secas) amplificam a volatilidade do preço. " if cafe_ret and cafe_ret > 5 else "")
        + (f"A **soja** ({soja_ret:+.1f}%) afeta diretamente a balança comercial brasileira — "
           f"é o principal produto de exportação do país. " if soja_ret else "")
    )

st.markdown("---")

# =============================================================================
# LINHA 2 — Agricolas (esq) + Energia e Metais (dir) em precos absolutos
# =============================================================================
col3, col4 = st.columns([5, 5])

with col3:
    st.markdown("#### Agrícolas — preço absoluto")
    st.caption("Soja, Milho, Trigo em US¢/bu · Café, Açúcar em US¢/lb")
    AGRI = ["Soja", "Milho", "Trigo", "Cafe", "Acucar"]
    if not df_cf.empty:
        fig3, ax3 = plt.subplots(figsize=(9, 4))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        ax3b = ax3.twinx()
        for nome in ["Soja", "Milho", "Trigo"]:
            if nome in df_cf.columns:
                s = df_cf[nome].dropna()
                ax3.plot(s.index, s.values, color=CORES[nome], lw=1.5, label=nome)
        for nome in ["Cafe", "Acucar"]:
            if nome in df_cf.columns:
                s = df_cf[nome].dropna()
                ax3b.plot(s.index, s.values, color=CORES[nome], lw=1.5, ls="--", label=nome)
        ax3.tick_params(colors="#AAAAAA", labelsize=8)
        ax3b.tick_params(colors="#AAAAAA", labelsize=8)
        ax3.set_ylabel("US¢/bu (grãos)", color="#AAAAAA", fontsize=8)
        ax3b.set_ylabel("US¢/lb (café/açúcar)", color="#AAAAAA", fontsize=8)
        ax3.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3b.get_legend_handles_labels()
        ax3.legend(lines1+lines2, labels1+labels2,
                   fontsize=7, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig3); plt.close()

with col4:
    st.markdown("#### Energia & Metais — preço absoluto")
    st.caption("Petróleo WTI em US$/barril · Ouro em US$/oz (eixo direito)")
    if not df_cf.empty:
        fig4, ax4 = plt.subplots(figsize=(9, 4))
        fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
        ax4b = ax4.twinx()
        if "Petroleo" in df_cf.columns:
            s = df_cf["Petroleo"].dropna()
            ax4.plot(s.index, s.values, color=CORES["Petroleo"], lw=1.8, label="Petróleo (esq)")
        if "Ouro" in df_cf.columns:
            s = df_cf["Ouro"].dropna()
            ax4b.plot(s.index, s.values, color=CORES["Ouro"], lw=1.8, ls="--", label="Ouro (dir)")
        ax4.tick_params(colors="#AAAAAA", labelsize=8)
        ax4b.tick_params(colors="#AAAAAA", labelsize=8)
        ax4.set_ylabel("US$/barril", color="#AAAAAA", fontsize=8)
        ax4b.set_ylabel("US$/oz", color="#AAAAAA", fontsize=8)
        ax4.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4b.get_legend_handles_labels()
        ax4.legend(lines1+lines2, labels1+labels2,
                   fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        for sp in ax4.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig4); plt.close()

st.markdown("---")

# =============================================================================
# ANALISE TECNICA — contexto e interpretacao
# =============================================================================
st.markdown("#### Como as commodities afetam o Brasil")
ca, cb, cc = st.columns(3)
with ca:
    st.markdown("""
**🌱 Agro — motor da balança comercial**

O Brasil é líder mundial em exportação de **soja, milho, café e açúcar**. As commodities agrícolas representam mais de 50% das exportações totais do país.

**Como o câmbio amplifica o efeito:**
- Dólar alto + commodity cara = receita máxima para o exportador em R$
- Mas também encarece alimentos no mercado interno → pressão inflacionária via IPCA Alimentação

**O que monitorar:** preços agrícolas globais afetam diretamente o saldo comercial, o real e a inflação de alimentos — três variáveis-chave do ciclo econômico brasileiro.
""")
with cb:
    st.markdown("""
**⛽ Petróleo — insumo estratégico e inflação**

O petróleo afeta **toda a cadeia produtiva**: combustíveis, frete, fertilizantes, petroquímica.

O Brasil é quase autossuficiente, mas a Petrobras usa **paridade internacional de preços (PPI)** — alta do barril se transmite diretamente ao preço da gasolina e do diesel.

**Transmissão para a inflação:**
- Diesel caro → frete mais caro → todos os produtos encarecem
- Gasolina cara → IPCA Transportes sobe → inflação ao consumidor sobe
- BCB precifica esse efeito no IPCA projetado e calibra a Selic

**Risco geopolítico** (conflitos no Oriente Médio, cortes da OPEP+) é o principal driver de curto prazo.
""")
with cc:
    st.markdown("""
**🥇 Ouro — o termômetro do medo global**

O ouro é um **ativo de proteção (safe haven)** — não paga juros nem dividendos, mas preserva valor em crises.

**Quando o ouro sobe:**
- Tensões geopolíticas (guerras, sanções)
- Quedas dos juros reais globais → custo de oportunidade de carregar ouro cai
- Desconfiança no dólar → investidores diversificam para ouro
- Recessão iminente → fuga para ativos seguros

**Como usar como indicador:** ouro subindo + bolsas caindo = sinal de **aversão ao risco global**. Isso tende a pressionar o dólar/real para cima e aumentar a volatilidade nos mercados emergentes, incluindo o Brasil.
""")

rodape()
