# =============================================================================
# pages/11_Fundos.py — Meios de Pagamento & Poupança
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

from utils.dados  import get_fundos_bcb, get_juros, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Liquidez | BI Econômico", page_icon="💧", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2019, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2019, datetime.today().year))
sidebar_padrao(pagina_atual="Liquidez", filtros_extra=_filtros)

with st.spinner("Carregando meios de pagamento..."):
    df_f  = get_fundos_bcb()
    df_jr = get_juros()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty:
        return df
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_ff = filtrar(df_f)

# Helpers — dados.py entrega tudo em R$ bilhoes
def fmt_val(v):
    if v is None:
        return "—"
    if v >= 1000:
        return f"R$ {v/1000:.2f} tri"
    return f"R$ {v:.0f} bi"

def var_12m(df, col):
    if df is None or df.empty or col not in df.columns:
        return None
    s = df[col].dropna()
    if len(s) < 13:
        return None
    return round((s.iloc[-1] / s.iloc[-13] - 1) * 100, 1)

CORES = {"M4": "#00D4FF", "M2": "#FFB800", "M1": "#00D4AA", "Poupanca": "#FF4B6E"}

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    💧 Liquidez & Meios de Pagamento
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Agregados monetários M1 · M2 · M4 · Poupança — BCB/SGS
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
if not df_f.empty:
    c1, c2, c3, c4 = st.columns(4)
    for col, label, container in [
        ("M4",      "M4 (R$ bi)",      c1),
        ("M2",      "M2 (R$ bi)",      c2),
        ("M1",      "M1 (R$ bi)",      c3),
        ("Poupanca","Poupança (R$ bi)", c4),
    ]:
        v, d  = ultimo_valor(df_f, col)
        var   = var_12m(df_f, col)
        delta = f"{var:+.1f}% em 12m" if var is not None else (d.strftime("%b/%Y") if d else None)
        with container:
            st.metric(label, fmt_val(v), delta=delta,
                      delta_color="normal" if var is not None else "off")

st.markdown("---")

# =============================================================================
# ANALISE — caixa interpretativa
# =============================================================================
m4_v, _   = ultimo_valor(df_f, "M4")
m1_v, _   = ultimo_valor(df_f, "M1")
m4_var    = var_12m(df_f, "M4")
selic_v,_ = ultimo_valor(df_jr, "Selic_Meta") if not df_jr.empty else (None, None)

if m4_v and m1_v and m1_v > 0:
    razao     = round(m4_v / m1_v, 1)
    if (m4_var or 0) > 8:
        liquidez = "expansionista"
    elif (m4_var or 0) < 4:
        liquidez = "contracionista"
    else:
        liquidez = "moderada"
    selic_txt = f"com Selic em **{selic_v:.1f}% a.a.**" if selic_v else ""
    var_txt   = f"— crescimento de **{m4_var:.1f}%** em 12 meses" if m4_var else ""

    st.info(
        f"**Leitura da liquidez monetária**\n\n"
        f"O **M4** (agregado mais amplo) soma **{fmt_val(m4_v)}** {var_txt}. "
        f"O multiplicador monetário (M4/M1) está em **{razao}x** — cada real de base monetária "
        f"gera {razao} reais de meios de pagamento ampliados. "
        f"A política monetária {selic_txt} mantém postura **{liquidez}**: "
        f"juro real elevado tende a desacelerar a expansão do crédito e dos agregados monetários."
    )

st.markdown("---")

# =============================================================================
# LINHA 1 — M4 historico (esq) + Composicao pizza (dir)
# =============================================================================
col_g1, col_g2 = st.columns([6, 4])

with col_g1:
    st.markdown("#### Meios de Pagamento Ampliados — M4 (R$ tri)")
    if not df_ff.empty and "M4" in df_ff.columns:
        s = df_ff["M4"].dropna()
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        # bilhoes -> trilhoes: dividir por 1000
        y = s.values / 1000
        ax.plot(s.index, y, color="#00D4FF", lw=2.0)
        ax.fill_between(s.index, y, y.min() * 0.98, alpha=0.08, color="#00D4FF")
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"R$ {x:.1f} tri"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.set_ylabel("R$ trilhoes", color="#AAAAAA", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados M4 nao disponiveis.")

with col_g2:
    st.markdown("#### Composição — incrementos M1 → M2 → M4")
    ultimo = {}
    for col in ["M1", "M2", "M4"]:
        v, _ = ultimo_valor(df_f, col)
        if v and v > 0:
            ultimo[col] = v

    labels_p, vals_p, cores_p = [], [], []
    prev = 0
    for col in ["M1", "M2", "M4"]:
        if col in ultimo:
            inc = ultimo[col] - prev
            if inc > 0:
                labels_p.append(col)
                vals_p.append(inc)
                cores_p.append(CORES[col])
            prev = ultimo[col]

    if vals_p:
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        wedges, texts, autotexts = ax2.pie(
            vals_p, labels=labels_p, colors=cores_p,
            autopct="%1.1f%%", startangle=90,
            textprops={"color": "#AAAAAA", "fontsize": 9}
        )
        for at in autotexts: at.set_color("white"); at.set_fontsize(9)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

        st.markdown("**Composição atual (R$ bi):**")
        desc = {
            "M1": "Papel moeda + depósitos à vista",
            "M2": "Inclui poupança e títulos privados",
            "M4": "Inclui títulos públicos e cotas",
        }
        prev2 = 0
        for col in ["M1","M2","M4"]:
            if col in ultimo:
                inc = ultimo[col] - prev2
                pct = inc / ultimo.get("M4", 1) * 100
                cor = CORES[col]
                st.markdown(
                    f"<span style='color:{cor}'>■</span> **{col}** "
                    f"+{fmt_val(inc)} ({pct:.1f}%) — {desc[col]}",
                    unsafe_allow_html=True)
                prev2 = ultimo[col]
    else:
        st.info("Dados de composicao nao disponiveis.")

st.markdown("---")

# =============================================================================
# LINHA 2 — Evolucao M1/M2/M4 sobrepostos
# =============================================================================
st.markdown("#### Evolução comparada M1 · M2 · M4 (R$ trilhões)")
st.caption("M4 ⊃ M2 ⊃ M1 — quanto maior o agregado, menor a liquidez imediata dos ativos incluídos")

if not df_ff.empty:
    fig3, ax3 = plt.subplots(figsize=(12, 4))
    fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
    for col in ["M4", "M2", "M1"]:
        if col in df_ff.columns:
            s = df_ff[col].dropna()
            if not s.empty:
                ax3.plot(s.index, s.values / 1000,
                         color=CORES[col], lw=1.8, label=col)
    ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax3.tick_params(colors="#AAAAAA", labelsize=9)
    ax3.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"R$ {x:.1f} tri"))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    plt.xticks(rotation=30, ha="right")
    for sp in ax3.spines.values(): sp.set_edgecolor("#333")
    ax3.set_ylabel("R$ trilhoes", color="#AAAAAA", fontsize=9)
    ax3.legend(fontsize=9, facecolor="#1A1D27", edgecolor="#333",
               labelcolor="#CCC", framealpha=0.9)
    plt.tight_layout()
    st.pyplot(fig3); plt.close()
else:
    st.info("Dados nao disponiveis para o periodo selecionado.")

st.markdown("---")

# =============================================================================
# LINHA 3 — Poupanca historica + analise
# =============================================================================
col_p1, col_p2 = st.columns([6, 4])

with col_p1:
    st.markdown("#### Depósitos de Poupança (R$ bilhões)")
    if not df_ff.empty and "Poupanca" in df_ff.columns:
        s_p = df_ff["Poupanca"].dropna()
        if not s_p.empty:
            fig4, ax4 = plt.subplots(figsize=(10, 3.5))
            fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
            ax4.bar(s_p.index, s_p.values, color="#FF4B6E", alpha=0.6, width=20)
            ax4.plot(s_p.index, s_p.values, color="#FF4B6E", lw=1.5)
            ax4.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax4.tick_params(colors="#AAAAAA", labelsize=9)
            ax4.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f} bi"))
            ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax4.spines.values(): sp.set_edgecolor("#333")
            ax4.set_ylabel("R$ bilhoes", color="#AAAAAA", fontsize=9)
            plt.tight_layout()
            st.pyplot(fig4); plt.close()
        else:
            st.info("Dados de poupanca nao disponiveis.")

with col_p2:
    st.markdown("#### Por que acompanhar a poupança?")
    poup_v, poup_d = ultimo_valor(df_f, "Poupanca")
    poup_var       = var_12m(df_f, "Poupanca")
    var_poup_txt   = f"({poup_var:+.1f}% em 12m)" if poup_var else ""

    st.markdown(f"""
A poupança é o instrumento mais popular entre os brasileiros — isenta de IR para pessoas físicas e com liquidez diária.

**Saldo atual:** {fmt_val(poup_v)} {var_poup_txt}

**Lógica de mercado:**
- Com **Selic acima de 8,5% a.a.**, a poupança rende fixo 0,5%/mês + TR e perde atratividade relativa para CDBs e Tesouro Direto → saques líquidos tendem a crescer
- Com **Selic abaixo de 8,5% a.a.**, a poupança rende 70% da Selic — mais competitiva

Quedas no saldo geralmente refletem migração para fundos de renda fixa e Tesouro Direto, não necessariamente perda de riqueza das famílias.
""")

rodape()
