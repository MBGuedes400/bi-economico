# =============================================================================
# pages/16_Comercio.py — Varejo e Confiança do Consumidor
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

from utils.dados  import get_pmc, get_comercio_indicadores, get_inflacao, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Comércio | BI Econômico", page_icon="🛒", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2020, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2015, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2020, datetime.today().year))
sidebar_padrao(pagina_atual="Comercio", filtros_extra=_filtros)

with st.spinner("Carregando dados do comércio..."):
    df_pmc  = get_pmc()
    df_com  = get_comercio_indicadores()
    df_infl = get_inflacao()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_pf  = filtrar(df_pmc)
df_cf  = filtrar(df_com)

def ultimo_val(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    return round(float(s.iloc[-1]), 2) if not s.empty else None

def var_12m_col(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    if len(s) < 13: return None
    return round((float(s.iloc[-1]) / float(s.iloc[-13]) - 1) * 100, 1)

def meses_consec(df, col, direcao="queda"):
    if df is None or df.empty or col not in df.columns: return 0
    s = df[col].dropna().pct_change().dropna()
    if s.empty: return 0
    count = 0
    for v in reversed(s.values):
        if direcao == "queda" and v < 0: count += 1
        elif direcao == "expansao" and v > 0: count += 1
        else: break
    return count

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    🛒 Varejo & Comércio
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Volume de vendas · Confiança do consumidor · Endividamento das famílias
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
varejo_idx = ultimo_val(df_pmc, "Indice")
varejo_12m = ultimo_val(df_pmc, "Var12m")
varejo_mes = ultimo_val(df_pmc, "VarMensal")
icc_v      = ultimo_val(df_com, "ICC_FGV")
endiv_v    = ultimo_val(df_com, "Endividamento")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Varejo — Índice (base 2014=100)",
              f"{varejo_idx:.1f}" if varejo_idx else "—",
              delta=f"{varejo_mes:+.1f}% mês" if varejo_mes else None)
with c2:
    st.metric("Var. acumulada 12 meses",
              f"{varejo_12m:+.1f}%" if varejo_12m is not None else "—",
              delta_color="normal" if (varejo_12m or 0) >= 0 else "inverse")
with c3:
    icc_sinal = "otimismo" if (icc_v or 0) > 100 else "pessimismo"
    st.metric("ICC FGV — Confiança Consumidor",
              f"{icc_v:.1f}" if icc_v else "—",
              delta=icc_sinal if icc_v else None,
              delta_color="normal" if (icc_v or 0) > 100 else "inverse")
with c4:
    st.metric("Endividamento Famílias (CNC)",
              f"{endiv_v:.1f}%" if endiv_v else "—")

st.markdown("---")

# =============================================================================
# BLOCO 1 — VOLUME DE VENDAS
# =============================================================================
st.markdown("### 🛍️ Volume de Vendas no Varejo")
st.caption("Índice base fixa 2014=100 · Sem ajuste sazonal · Fonte: IBGE/PMC")

col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Índice de volume de vendas")
    if not df_pf.empty and "Indice" in df_pf.columns:
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        s = df_pf["Indice"].dropna()
        ax.plot(s.index, s.values, color="#00D4FF", lw=2)
        ax.fill_between(s.index, s.values, s.min()*0.98, alpha=0.08, color="#00D4FF")
        ax.axhline(100, color="#555", lw=0.8, ls="--", label="Base 2014")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.set_ylabel("Índice", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC")
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados de volume de vendas não disponíveis.")

with col2:
    st.markdown("#### Variação mensal (%)")
    if not df_pf.empty and "VarMensal" in df_pf.columns:
        s = df_pf["VarMensal"].dropna()
        cors = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in s.values]
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        ax2.bar(s.index, s.values, color=cors, width=20)
        ax2.axhline(0, color="#555", lw=0.8)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        ax2.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig2); plt.close()

# Narrativa bloco 1
if not df_pmc.empty:
    m_exp = meses_consec(df_pmc, "Indice", "expansao")
    m_que = meses_consec(df_pmc, "Indice", "queda")
    if m_exp >= 2:
        tendencia = str(m_exp) + " meses consecutivos de crescimento"
    elif m_que >= 2:
        tendencia = str(m_que) + " meses consecutivos de queda"
    else:
        tendencia = "sem tendência clara"

    ipca_12m = None
    if not df_infl.empty and "IPCA_acum12m" in df_infl.columns:
        s_ipca = df_infl["IPCA_acum12m"].dropna()
        if not s_ipca.empty:
            ipca_12m = round(float(s_ipca.iloc[-1]), 1)

    txt_var = f"O volume de vendas acumula **{varejo_12m:+.1f}%** em 12 meses. " if varejo_12m is not None else ""
    if ipca_12m and varejo_12m is not None:
        if varejo_12m > ipca_12m:
            txt_real = f"Com IPCA em **{ipca_12m:.1f}%**, o crescimento real supera a inflação — ganho de poder de compra. "
        else:
            txt_real = f"Com IPCA em **{ipca_12m:.1f}%**, o crescimento fica abaixo da inflação — perda real de volume. "
    else:
        txt_real = ""

    st.info(
        "**Leitura do varejo:**\n\n"
        + txt_var
        + "O índice registra " + tendencia + ". "
        + txt_real
        + "O varejo é um dos principais termômetros do consumo das famílias e responde ao nível de emprego, crédito e inflação."
    )

st.markdown("---")

# =============================================================================
# BLOCO 2 — CONFIANÇA DO CONSUMIDOR + VAREJO BCB
# =============================================================================
st.markdown("### 📊 Confiança do Consumidor e Varejo Ampliado")
st.caption("ICC FGV: acima de 100 = otimismo · Varejo BCB: índice de volume mensal")

col3, col4 = st.columns([5, 5])

with col3:
    st.markdown("#### ICC FGV — Índice de Confiança do Consumidor")
    if not df_cf.empty and "ICC_FGV" in df_cf.columns:
        s = df_cf["ICC_FGV"].dropna()
        fig3, ax3 = plt.subplots(figsize=(9, 4))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        cors3 = ["#00D4AA" if v > 100 else "#FF4B6E" for v in s.values]
        ax3.bar(s.index, s.values, color=cors3, width=20, alpha=0.8)
        ax3.plot(s.index, s.rolling(3).mean().values,
                 color="#FFB800", lw=1.5, ls="--", label="Média 3m")
        ax3.axhline(100, color="#555", lw=1.0, ls="--", label="Neutro (100)")
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax3.tick_params(colors="#AAAAAA", labelsize=9)
        ax3.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax3.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC")
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig3); plt.close()

        icc_media3 = round(float(s.tail(3).mean()), 1) if len(s) >= 3 else None
        icc_var12  = var_12m_col(df_com, "ICC_FGV")
        m_otim = meses_consec(df_com, "ICC_FGV", "expansao")
        m_pess = meses_consec(df_com, "ICC_FGV", "queda")
        if m_otim >= 2:
            tend_icc = str(m_otim) + " meses melhorando"
        elif m_pess >= 2:
            tend_icc = str(m_pess) + " meses piorando"
        else:
            tend_icc = "sem tendência clara"

        if icc_v and icc_v > 100:
            icc_humor = "acima de 100 — consumidores otimistas"
        else:
            icc_humor = "abaixo de 100 — consumidores pessimistas"

        txt_icc = "O ICC FGV em **" + (f"{icc_v:.1f}" if icc_v else "—") + "** " + icc_humor + ". "
        txt_media = f"Média dos últimos 3 meses: **{icc_media3:.1f}**, com {tend_icc}. " if icc_media3 else ""
        txt_var12 = f"Em 12 meses, o ICC variou **{icc_var12:+.1f} pontos**. " if icc_var12 else ""

        st.info(
            "**Confiança do consumidor:**\n\n"
            + txt_icc + txt_media + txt_var12
            + "O ICC é um indicador antecedente do varejo — consumidores confiantes tendem a "
            "consumir mais nos próximos meses, especialmente bens duráveis."
        )
    else:
        st.info("Dados do ICC FGV não disponíveis.")

with col4:
    st.markdown("#### Varejo BCB — índice de volume")
    if not df_cf.empty and "Varejo_BCB" in df_cf.columns:
        s4 = df_cf["Varejo_BCB"].dropna()
        fig4, ax4 = plt.subplots(figsize=(9, 4))
        fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
        ax4.plot(s4.index, s4.values, color="#A78BFA", lw=2)
        ax4.fill_between(s4.index, s4.values, s4.min()*0.98, alpha=0.08, color="#A78BFA")
        ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.1f}"))
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax4.tick_params(colors="#AAAAAA", labelsize=9)
        ax4.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax4.set_ylabel("Índice", color="#AAAAAA", fontsize=9)
        for sp in ax4.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig4); plt.close()

        varejo_bcb_12m = var_12m_col(df_com, "Varejo_BCB")
        varejo_bcb_v   = ultimo_val(df_com, "Varejo_BCB")
        if varejo_bcb_12m is not None:
            st.info(
                "**Varejo BCB:** índice em **" + f"{varejo_bcb_v:.1f}" + "**, "
                "com variação de **" + f"{varejo_bcb_12m:+.1f}%" + "** em 12 meses. "
                "Esta série complementa a PMC/IBGE com maior frequência de atualização."
            )
    else:
        st.info("Dados do varejo BCB não disponíveis.")

st.markdown("---")

# =============================================================================
# BLOCO 3 — ENDIVIDAMENTO E INADIMPLÊNCIA
# =============================================================================
st.markdown("### 💳 Endividamento e Inadimplência das Famílias")
st.caption("Fonte: CNC via BCB/SGS · Endividamento = % famílias com dívidas")

col5, col6 = st.columns([5, 5])

with col5:
    st.markdown("#### Endividamento e Comprometimento de Renda")
    if not df_cf.empty:
        fig5, ax5 = plt.subplots(figsize=(9, 4))
        fig5.patch.set_facecolor("#0F1117"); ax5.set_facecolor("#0F1117")
        ax5b = ax5.twinx()
        if "Endividamento" in df_cf.columns:
            s = df_cf["Endividamento"].dropna()
            ax5.plot(s.index, s.values, color="#FF4B6E", lw=2, label="Endividamento (%)")
        if "Comprometimento" in df_cf.columns:
            s2 = df_cf["Comprometimento"].dropna()
            ax5b.plot(s2.index, s2.values, color="#FFB800", lw=2, ls="--", label="Comprometimento renda")
        ax5.set_ylabel("% famílias endividadas", color="#FF4B6E", fontsize=8)
        ax5b.set_ylabel("Comprometimento renda (índice)", color="#FFB800", fontsize=8)
        ax5.tick_params(colors="#AAAAAA", labelsize=8)
        ax5b.tick_params(colors="#AAAAAA", labelsize=8)
        ax5.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax5.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        lines1, labels1 = ax5.get_legend_handles_labels()
        lines2, labels2 = ax5b.get_legend_handles_labels()
        ax5.legend(lines1+lines2, labels1+labels2,
                   fontsize=7, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC")
        for sp in ax5.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig5); plt.close()
    else:
        st.info("Dados de endividamento não disponíveis.")

with col6:
    st.markdown("#### Inadimplência do Consumidor")
    if not df_cf.empty and "Inadimplencia" in df_cf.columns:
        s6 = df_cf["Inadimplencia"].dropna()
        fig6, ax6 = plt.subplots(figsize=(9, 4))
        fig6.patch.set_facecolor("#0F1117"); ax6.set_facecolor("#0F1117")
        media_inadim = float(s6.mean())
        cors6 = ["#FF4B6E" if v > media_inadim else "#FFB800" for v in s6.values]
        ax6.bar(s6.index, s6.values, color=cors6, width=20, alpha=0.85)
        ax6.axhline(media_inadim, color="#555", lw=1.0, ls="--",
                    label=f"Média {media_inadim:.1f}")
        ax6.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.1f}"))
        ax6.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax6.tick_params(colors="#AAAAAA", labelsize=9)
        ax6.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax6.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC")
        for sp in ax6.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig6); plt.close()
    else:
        st.info("Dados de inadimplência não disponíveis.")

# Narrativa endividamento
endiv  = ultimo_val(df_com, "Endividamento")
comp   = ultimo_val(df_com, "Comprometimento")
inadim = ultimo_val(df_com, "Inadimplencia")
endiv_12m = var_12m_col(df_com, "Endividamento")

if endiv and comp:
    if endiv > 78:
        risco = "elevado"
    elif endiv > 70:
        risco = "moderado"
    else:
        risco = "controlado"
    txt_endiv12 = f"Em 12 meses, o endividamento variou **{endiv_12m:+.1f}pp**. " if endiv_12m else ""
    st.info(
        "**Saúde financeira das famílias:**\n\n"
        f"Com **{endiv:.1f}%** das famílias endividadas e comprometimento de renda em "
        f"**{comp:.1f}** (índice CNC), o nível de endividamento é **{risco}**. "
        + txt_endiv12
        + "Endividamento alto comprime o consumo futuro — famílias com dívidas reduzem gastos "
        "discricionários, afetando diretamente o desempenho do varejo.\n\n"
        "O ciclo vicioso: dívida alta → corte de consumo → queda do varejo "
        "→ pressão no emprego → mais dificuldade de honrar dívidas."
    )

st.markdown("---")

# =============================================================================
# CARDS DIDÁTICOS
# =============================================================================
st.markdown("#### Como interpretar estes indicadores")
ca, cb, cc = st.columns(3)

with ca:
    st.markdown("""
**🛍️ PMC — Pesquisa Mensal de Comércio**

Mede o **volume físico** de vendas no varejo (IBGE) — sem efeito de preços. Base 2014 = 100.

**O que afeta o varejo:**
- Emprego e massa salarial — principal driver
- Crédito ao consumidor — facilita compras a prazo
- Inflação — corrói o poder de compra real
- Confiança — determina disposição para gastar

Varejo forte → maior receita tributária. Varejo fraco → sinal de desaceleração econômica.
""")

with cb:
    icc_txt = f"{icc_v:.1f}" if icc_v else "—"
    humor = "otimistas" if icc_v and icc_v > 100 else "pessimistas"
    st.markdown(
        "**📊 ICC FGV — Confiança do Consumidor**\n\n"
        "Acima de 100 = otimismo, abaixo = pessimismo. É um **indicador antecedente** do varejo.\n\n"
        f"Com ICC em {icc_txt}, consumidores estão **{humor}**. Consumidores confiantes:\n"
        "- Aumentam gastos com bens duráveis\n"
        "- Reduzem poupança precaucional\n"
        "- Tomam mais crédito para consumo\n\n"
        "O ICC reage rapidamente a choques: alta de juros, desemprego, instabilidade política. "
        "Antecede o varejo em 1 a 2 meses."
    )

with cc:
    endiv_txt = f"{endiv:.1f}%" if endiv else "—"
    risco_cc = "elevado" if endiv and endiv > 78 else ("moderado" if endiv and endiv > 70 else "controlado")
    st.markdown(
        "**💳 Endividamento e Inadimplência**\n\n"
        f"Com **{endiv_txt}** das famílias endividadas, o nível de risco é **{risco_cc}**.\n\n"
        "**O ciclo do crédito ao consumidor:**\n"
        "1. Crédito fácil → consumo sobe → varejo cresce\n"
        "2. Dívidas acumulam → comprometimento de renda sobe\n"
        "3. Inadimplência sobe → bancos restringem crédito\n"
        "4. Consumo cai → varejo desacelera\n\n"
        "Acompanhar endividamento + inadimplência revela em qual fase do ciclo a economia do consumidor está."
    )

rodape()
