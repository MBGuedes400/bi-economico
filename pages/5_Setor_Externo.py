# =============================================================================
# pages/5_Setor_Externo.py — Setor Externo (Câmbio + Reservas)
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
from dateutil.relativedelta import relativedelta

from utils.dados  import get_cambio, get_reservas, get_focus_anual, ultimo_valor, focus_ultimo
from utils.layout import CSS_GLOBAL, rodape

st.set_page_config(page_title="Setor Externo | BI Econômico",
                   page_icon="🌎", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "Imagens", "impeto_Branco.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)

    st.markdown("---")
    st.markdown("**Navegação**")
    st.page_link("Home.py",                      label="🏠  Home")
    st.page_link("pages/1_Inflacao.py",          label="📊  Inflação")
    st.page_link("pages/2_Juros.py",             label="🏦  Juros")
    st.page_link("pages/3_Atividade.py",         label="📈  Atividade Econômica")
    st.page_link("pages/4_Mercado_Trabalho.py",  label="👷  Mercado de Trabalho")
    st.page_link("pages/5_Setor_Externo.py",     label="🌎  Setor Externo")

    st.markdown("---")
    st.markdown("**⚙️ Filtros — Setor Externo**")

    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2019, datetime.today().year)
    )

    moedas_disp = {
        "USD_BRL": "Dólar (USD)",
        "EUR_BRL": "Euro (EUR)",
        "CNY_BRL": "Yuan (CNY)",
        "GBP_BRL": "Libra (GBP)",
    }
    moedas_sel = st.multiselect(
        "Moedas no gráfico",
        options=list(moedas_disp.keys()),
        default=["USD_BRL", "EUR_BRL", "CNY_BRL"],
        format_func=lambda x: moedas_disp[x],
    )

    st.markdown("---")
    st.caption("Fonte: BCB/SGS | BCB/Focus")
    st.caption("Atualizado automaticamente a cada hora.")


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados do Setor Externo..."):
    df_cambio  = get_cambio()
    df_reservas = get_reservas()
    df_fa      = get_focus_anual()

# Corrige escala das reservas (BCB retorna em US$ milhões)
if not df_reservas.empty and "Reservas_USD_bi" in df_reservas.columns:
    if df_reservas["Reservas_USD_bi"].dropna().median() > 10000:
        df_reservas["Reservas_USD_bi"] = df_reservas["Reservas_USD_bi"] / 1000

# Mescla câmbio + reservas num único df para compatibilidade
if not df_cambio.empty and not df_reservas.empty:
    df_cambio = df_cambio.join(df_reservas, how="outer")
elif not df_reservas.empty:
    df_cambio = df_reservas.copy()

# Filtrar período
di     = pd.Timestamp(f"{ano_ini}-01-01")
df_fim = pd.Timestamp(f"{ano_fim}-12-31")

if not df_cambio.empty:
    df_cambio.index = pd.to_datetime(df_cambio.index)
    df_c = df_cambio[(df_cambio.index >= di) & (df_cambio.index <= df_fim)].copy()
else:
    df_c = pd.DataFrame()


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🌎 Setor Externo
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Câmbio (USD · EUR · CNY · GBP) · Reservas Internacionais · Expectativas Focus
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
ano_at = datetime.today().year

# Últimos valores (série completa — não filtrada)
v_usd, d_usd = ultimo_valor(df_cambio, "USD_BRL")
v_eur, _     = ultimo_valor(df_cambio, "EUR_BRL")
v_cny, _     = ultimo_valor(df_cambio, "CNY_BRL")
v_res, d_res = ultimo_valor(df_cambio, "Reservas_USD_bi")

def var_periodo(df, col, n=1):
    if df is None or df.empty or col not in df.columns:
        return None
    s = df[col].dropna()
    if len(s) < n + 1:
        return None
    return round((s.iloc[-1] / s.iloc[-1 - n] - 1) * 100, 2)

var_usd = var_periodo(df_cambio, "USD_BRL", 1)
var_res = var_periodo(df_cambio, "Reservas_USD_bi", 1)
fc_at   = focus_ultimo(df_fa, "Câmbio", "Anual", ano_at)
fc_prx  = focus_ultimo(df_fa, "Câmbio", "Anual", ano_at + 1)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    usd_str   = f"R$ {v_usd:.4f}" if v_usd else "—"
    delta_usd = f"{var_usd:+.2f}%" if var_usd is not None else "último período"
    st.metric("USD / BRL", usd_str,
              delta=delta_usd,
              delta_color="inverse" if var_usd and var_usd > 0 else "normal")

with c2:
    eur_str = f"R$ {v_eur:.4f}" if v_eur else "—"
    st.metric("EUR / BRL", eur_str,
              delta="Euro", delta_color="off")

with c3:
    cny_str = f"R$ {v_cny:.4f}" if v_cny else "—"
    st.metric("CNY / BRL", cny_str,
              delta="Yuan chinês", delta_color="off")

with c4:
    res_str   = f"US$ {v_res:.1f} bi" if v_res else "—"
    delta_res = f"{var_res:+.2f}%" if var_res is not None else "último período"
    st.metric("Reservas Internacionais", res_str,
              delta=delta_res,
              delta_color="normal" if var_res and var_res > 0 else "inverse")

with c5:
    fc_str = f"R$ {fc_at:.2f}" if fc_at else "—"
    st.metric(f"Focus Câmbio {ano_at}", fc_str,
              delta="Mediana Focus", delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
CORES_MOEDA = {
    "USD_BRL": "#00D4FF",
    "EUR_BRL": "#FFB800",
    "CNY_BRL": "#00D4AA",
    "GBP_BRL": "#A78BFA",
    "ARS_BRL": "#FF4B6E",
}

EVENTOS = [
    {"data": "2020-03-01", "label": "COVID-19",        "cor": "#FF4B6E"},
    {"data": "2021-11-01", "label": "PEC Precatórios", "cor": "#FFB800"},
    {"data": "2022-10-01", "label": "Eleições 2022",   "cor": "#A78BFA"},
    {"data": "2023-01-01", "label": "8 de Janeiro",    "cor": "#FF4B6E"},
    {"data": "2024-06-01", "label": "Fiscal 2024",     "cor": "#FFB800"},
]

col_g1, col_g2 = st.columns([6, 4])

# --- Gráfico 1: Histórico câmbio ---
with col_g1:
    st.markdown("#### Câmbio — R$ por moeda estrangeira")

    if df_c.empty or not moedas_sel:
        st.info("Selecione ao menos uma moeda no painel lateral.")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0F1117")
        ax.set_facecolor("#0F1117")

        for moeda in moedas_sel:
            if moeda not in df_c.columns:
                continue
            s = df_c[moeda].dropna()
            if s.empty:
                continue
            ax.plot(s.index, s.values,
                    color=CORES_MOEDA.get(moeda, "#AAAAAA"),
                    lw=2.0, label=moedas_disp[moeda],
                    marker="o", ms=2)

        # Eventos
        ymin, ymax = ax.get_ylim()
        for ev in EVENTOS:
            ev_dt = pd.Timestamp(ev["data"])
            if ev_dt < di or ev_dt > df_fim:
                continue
            ax.axvline(ev_dt, color=ev["cor"], lw=0.8, ls="--", alpha=0.6)
            ax.text(ev_dt, ymax, ev["label"],
                    color=ev["cor"], fontsize=6.5,
                    rotation=90, va="top", ha="right", alpha=0.85)

        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"R$ {x:.2f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax.spines.values():
            sp.set_edgecolor("#333")
        ax.set_ylabel("R$ por unidade", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        if "ARS_BRL" in moedas_sel:
            st.caption("⚠️ O peso argentino opera em escala muito menor — "
                       "considere analisá-lo separadamente das demais moedas.")


# --- Gráfico 2: Reservas internacionais ---
with col_g2:
    st.markdown("#### Reservas Internacionais — US$ bi")

    if df_c.empty or "Reservas_USD_bi" not in df_c.columns:
        st.info("Dados de reservas não disponíveis.")
    else:
        s_res = df_c["Reservas_USD_bi"].dropna()

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        ax2.fill_between(s_res.index, s_res.values,
                         alpha=0.15, color="#00D4AA")
        ax2.plot(s_res.index, s_res.values,
                 color="#00D4AA", lw=2.0, alpha=0.9, label="Reservas")

        mm12 = s_res.rolling(12, min_periods=3).mean()
        ax2.plot(mm12.index, mm12.values,
                 color="#FFB800", lw=1.8, ls="--", label="Média 12m")

        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
        ax2.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"US$ {x:.0f}"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax2.spines.values():
            sp.set_edgecolor("#333")
        ax2.set_title("Reservas (US$ bi)", color="white",
                      fontsize=11, fontweight="bold", pad=12)
        ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

st.markdown("---")


# -----------------------------------------------------------------------------
# ANÁLISE AUTOMÁTICA + EXPECTATIVAS FOCUS
# -----------------------------------------------------------------------------
col_t, col_e = st.columns([6, 4])

with col_t:
    st.markdown("#### Análise Automática")

    linhas = []

    if v_usd and d_usd:
        var6m    = var_periodo(df_cambio, "USD_BRL", 6)
        direcao  = "depreciação" if (var_usd or 0) > 0 else "apreciação"
        usd_fmt  = f"R\\$ {v_usd:.4f}"
        txt = (
            f"**[Câmbio]** O dólar encerrou **{d_usd.strftime('%B/%Y')}** "
            f"cotado a **{usd_fmt}**"
        )
        if var_usd is not None:
            txt += f", registrando {direcao} de **{abs(var_usd):.2f}%** no último período"
        if var6m is not None:
            txt += f" e de **{var6m:+.2f}%** nos últimos 6 meses"
        txt += "."
        linhas.append(txt)

    if v_eur and v_cny:
        eur_fmt = f"R\\$ {v_eur:.4f}"
        cny_fmt = f"R\\$ {v_cny:.4f}"
        linhas.append(
            f"**[Outras moedas]** Euro cotado a **{eur_fmt}** e yuan chinês "
            f"a **{cny_fmt}**. A China é o maior parceiro comercial do Brasil, "
            f"tornando o CNY/BRL relevante para exportações do agronegócio."
        )

    if v_res and d_res:
        nivel = (
            "confortável (acima de US$ 350 bi)" if v_res > 350
            else "adequado (entre US$ 300 bi e US$ 350 bi)" if v_res > 300
            else "de atenção (abaixo de US$ 300 bi)"
        )
        res_fmt = f"US\\$ {v_res:.1f} bi"
        linhas.append(
            f"**[Reservas]** O estoque de reservas está em "
            f"**{res_fmt}** ({d_res.strftime('%b/%Y')}) — nível {nivel}. "
            f"Reservas robustas conferem capacidade de resistência a choques externos "
            f"e credibilidade junto a agências de rating."
        )

    if fc_at or fc_prx:
        fc_s  = ("R\\$ " + f"{fc_at:.2f}")  if fc_at  else "nd"
        fc_s2 = ("R\\$ " + f"{fc_prx:.2f}") if fc_prx else "nd"
        linhas.append(
            f"**[Expectativa]** O mercado (Focus/BCB) projeta câmbio em "
            f"**{fc_s}** para {ano_at} e **{fc_s2}** para {ano_at + 1}."
        )

    linhas.append(
        "**[Contexto]** O câmbio brasileiro é influenciado pelo diferencial de juros "
        "(Selic vs Fed Funds), fluxo de capitais, resultado comercial e percepção de "
        "risco fiscal. Taxa depreciada pressiona inflação via importações e dívida "
        "externa, mas favorece exportadores."
    )

    for linha in linhas:
        st.markdown(linha)

    if not linhas:
        st.info("Dados insuficientes para análise.")


with col_e:
    st.markdown("#### Expectativas Focus — Câmbio")

    if not df_fa.empty:
        df_cam_fa = df_fa[df_fa["Indicador"] == "Câmbio"].copy()
        if not df_cam_fa.empty:
            anos_ref = sorted(df_cam_fa["DataReferencia"].unique())
            anos_ref = [a for a in anos_ref if int(a) >= ano_at][:3]
            for ar in anos_ref:
                df_ar = df_cam_fa[df_cam_fa["DataReferencia"] == ar]
                if not df_ar.empty:
                    v = round(float(df_ar.sort_values("Data").iloc[-1]["Mediana"]), 2)
                    st.metric(f"Câmbio {ar}", f"R$ {v:.2f}",
                              delta="USD/BRL esperado", delta_color="off")

    st.caption("BCB/Focus — mediana · última coleta disponível")


# -----------------------------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------------------------
rodape()
