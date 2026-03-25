# =============================================================================
# pages/4_Mercado_Trabalho.py — Mercado de Trabalho
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

from utils.dados  import get_pnad, get_caged, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Mercado de Trabalho | BI Econômico",
                   page_icon="👷", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
ano_ini, ano_fim = 2019, datetime.today().year

def _filtros():
    global ano_ini, ano_fim
    st.markdown("**⚙️ Filtros — Mercado de Trabalho**")
    anos = list(range(2015, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2019, datetime.today().year)
    )

sidebar_padrao(pagina_atual="Mercado_Trabalho", filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados de mercado de trabalho..."):
    df_pnad  = get_pnad()
    df_caged = get_caged()

# Filtrar período
di     = pd.Timestamp(f"{ano_ini}-01-01")
df_fim = pd.Timestamp(f"{ano_fim}-12-31")

df_pnad_f  = df_pnad[(df_pnad.index >= di) & (df_pnad.index <= df_fim)] if not df_pnad.empty else df_pnad
df_caged_f = df_caged[(df_caged.index >= di) & (df_caged.index <= df_fim)] if not df_caged.empty else df_caged


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    👷 Mercado de Trabalho
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Desemprego · Informalidade · CAGED · Massa salarial · Participação na força de trabalho
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
desemp_v,   _ = ultimo_valor(df_pnad, "Taxa_Desocupacao")
informal_v, _ = ultimo_valor(df_pnad, "Taxa_Informalidade")
partic_v,   _ = ultimo_valor(df_pnad, "Taxa_Participacao")

def saldo_mensal(col):
    if df_caged.empty or col not in df_caged.columns: return None
    s = df_caged[col].dropna()
    if len(s) < 2: return None
    return round(float(s.iloc[-1] - s.iloc[-2]), 0)

caged_v = saldo_mensal("CAGED_Saldo")
massa_v = (round(float(df_caged["Massa_Salarial"].dropna().iloc[-1]), 1)
           if not df_caged.empty and "Massa_Salarial" in df_caged.columns else None)

def delta_pnad(col, n=1):
    if df_pnad.empty or col not in df_pnad.columns: return None
    s = df_pnad[col].dropna()
    if len(s) <= n: return None
    return round(float(s.iloc[-1] - s.iloc[-1-n]), 2)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    d = delta_pnad("Taxa_Desocupacao")
    st.metric("Desemprego", f"{desemp_v:.1f}%" if desemp_v else "—",
              delta=f"{d:+.1f}pp" if d else None, delta_color="inverse")
with c2:
    d = delta_pnad("Taxa_Informalidade")
    st.metric("Informalidade", f"{informal_v:.1f}%" if informal_v else "—",
              delta=f"{d:+.1f}pp" if d else None, delta_color="inverse")
with c3:
    d = delta_pnad("Taxa_Participacao")
    st.metric("Participação", f"{partic_v:.1f}%" if partic_v else "—",
              delta=f"{d:+.1f}pp" if d else None, delta_color="normal")
with c4:
    st.metric("CAGED (saldo)", f"{caged_v:,.0f}" if caged_v else "—",
              delta="Empregos formais/mês", delta_color="off")
with c5:
    st.metric("Massa Salarial", f"R$ {massa_v/1000:.1f} bi" if massa_v else "—",
              delta="R$ bilhões", delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
col_g1, col_g2 = st.columns([6, 4])

with col_g1:
    st.markdown("#### Taxa de Desocupação e Informalidade — PNAD Contínua")

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0F1117")
    ax.set_facecolor("#0F1117")

    if not df_pnad_f.empty:
        if "Taxa_Desocupacao" in df_pnad_f.columns:
            s = df_pnad_f["Taxa_Desocupacao"].dropna()
            ax.plot(s.index, s.values, color="#FF4B6E", lw=2.5,
                    label="Taxa de Desocupação (%)", zorder=5)
            ax.fill_between(s.index, s.values, alpha=0.1, color="#FF4B6E")
            if len(s) > 0:
                ax.scatter(s.index[-1], s.iloc[-1], color="#FF4B6E", s=70, zorder=6)
                ax.annotate(f"  {s.iloc[-1]:.1f}%",
                            xy=(s.index[-1], s.iloc[-1]),
                            xytext=(8, 4), textcoords="offset points",
                            color="#FF4B6E", fontsize=10, fontweight="bold")

        if "Taxa_Informalidade" in df_pnad_f.columns:
            s2 = df_pnad_f["Taxa_Informalidade"].dropna()
            ax2_twin = ax.twinx()
            ax2_twin.plot(s2.index, s2.values, color="#FFB800",
                          lw=2.0, ls="--", label="Taxa de Informalidade (%)", alpha=0.85)
            ax2_twin.tick_params(colors="#AAAAAA", labelsize=9)
            ax2_twin.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax2_twin.set_facecolor("#0F1117")
            for sp in ax2_twin.spines.values(): sp.set_edgecolor("#333")
            if len(s2) > 0:
                ax2_twin.annotate(f"  {s2.iloc[-1]:.1f}%",
                                  xy=(s2.index[-1], s2.iloc[-1]),
                                  xytext=(8, -12), textcoords="offset points",
                                  color="#FFB800", fontsize=10, fontweight="bold")
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2_twin.get_legend_handles_labels()
            ax.legend(lines1+lines2, labels1+labels2,
                      fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                      labelcolor="#CCC", framealpha=0.9)

    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-12-01"),
               alpha=0.08, color="#FF4B6E")
    ax.annotate("Pandemia\nCOVID-19",
                xy=(pd.Timestamp("2020-07-01"), 1.0),
                color="#FF4B6E", fontsize=7.5, alpha=0.8,
                ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#1A1D27",
                          edgecolor="#FF4B6E", alpha=0.7))

    if not df_pnad_f.empty and "Taxa_Desocupacao" in df_pnad_f.columns:
        s_desemp = df_pnad_f["Taxa_Desocupacao"].dropna()
        if len(s_desemp) > 0:
            min_val = s_desemp.min()
            min_dt  = s_desemp.idxmin()
            ax.annotate(f"Mínimo\n{min_val:.1f}%",
                        xy=(min_dt, min_val),
                        xytext=(0, -35), textcoords="offset points",
                        color="#00D4AA", fontsize=7.5, ha="center",
                        arrowprops=dict(arrowstyle="->", color="#00D4AA", lw=1.0),
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#1A1D27",
                                  edgecolor="#00D4AA", alpha=0.7))

    ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax.tick_params(colors="#AAAAAA", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.set_ylabel("Desocupação (%)", color="#FF4B6E", fontsize=9)
    plt.xticks(rotation=30, ha="right")
    for sp in ax.spines.values(): sp.set_edgecolor("#333")
    plt.tight_layout()
    st.pyplot(fig); plt.close()


with col_g2:
    st.markdown("#### CAGED — Saldo de Empregos Formais")

    if not df_caged_f.empty and "CAGED_Saldo" in df_caged_f.columns:
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        s    = df_caged_f["CAGED_Saldo"].dropna()
        mm3  = s.rolling(3).mean()
        cores = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in s.values]
        ax2.bar(s.index, s.values, width=25, color=cores, alpha=0.85)
        ax2.plot(mm3.index, mm3.values, color="#FFB800",
                 lw=2.0, ls="--", label="Média móvel 3m")
        ax2.axhline(0, color="#555", lw=0.8)
        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        ax2.set_title("Saldo mensal (mil empregos)",
                      color="white", fontsize=11, fontweight="bold", pad=12)
        ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()
    else:
        st.info("Dados do CAGED não disponíveis.")

st.markdown("---")


# -----------------------------------------------------------------------------
# ANÁLISE AUTOMÁTICA
# -----------------------------------------------------------------------------
st.markdown("#### Análise Automática")
col_t, col_e = st.columns([6, 4])

with col_t:
    linhas = []

    if desemp_v is not None:
        nivel = ("em patamar baixo — mercado aquecido" if desemp_v <= 7
                 else "em patamar moderado" if desemp_v <= 10
                 else "em patamar elevado" if desemp_v <= 13
                 else "em patamar muito elevado — mercado deprimido")
        d = delta_pnad("Taxa_Desocupacao")
        tend = f" ({d:+.1f}pp vs trimestre anterior)" if d else ""
        linhas.append(f"**[Desemprego]** A taxa de desocupação está em **{desemp_v:.1f}%**{tend} — {nivel}.")

    if informal_v is not None:
        linhas.append(f"**[Informalidade]** **{informal_v:.1f}%** dos trabalhadores ocupados "
                      f"estão em empregos informais — "
                      f"{'acima' if informal_v > 40 else 'próximo'} da média histórica.")

    if caged_v is not None:
        sinal = "positivo" if caged_v >= 0 else "negativo"
        linhas.append(f"**[CAGED]** O saldo de empregos formais no último mês foi de "
                      f"**{caged_v:+,.0f}** vagas — resultado {sinal}.")

    if partic_v is not None:
        linhas.append(f"**[Participação]** A taxa de participação na força de trabalho está em "
                      f"**{partic_v:.1f}%** — indica o percentual da população em idade ativa "
                      f"que está trabalhando ou buscando emprego.")

    for linha in linhas:
        st.markdown(linha)

with col_e:
    st.markdown("#### Participação na Força de Trabalho")
    if not df_pnad_f.empty and "Taxa_Participacao" in df_pnad_f.columns:
        fig3, ax3 = plt.subplots(figsize=(6, 3.5))
        fig3.patch.set_facecolor("#0F1117")
        ax3.set_facecolor("#0F1117")
        s = df_pnad_f["Taxa_Participacao"].dropna()
        ax3.plot(s.index, s.values, color="#00D4FF", lw=2.0)
        ax3.fill_between(s.index, s.values, alpha=0.1, color="#00D4FF")
        ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax3.tick_params(colors="#AAAAAA", labelsize=8)
        ax3.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        ax3.set_title("Taxa de Participação (%)",
                      color="white", fontsize=10, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig3); plt.close()

rodape()
