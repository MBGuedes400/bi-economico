# =============================================================================
# pages/3_Atividade.py — Atividade Econômica (PIB + IBC-Br)
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

from utils.dados  import get_pib, get_ibcbr, get_focus_anual, ultimo_valor, METAS_BCB
from utils.layout import CSS_GLOBAL, rodape

st.set_page_config(page_title="Atividade | BI Econômico",
                   page_icon="📈", layout="wide")
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
    st.markdown("**⚙️ Filtros — Atividade**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2018, datetime.today().year)
    )
    visao = st.radio(
        "Visualização PIB",
        ["Oferta (setores)", "Demanda (componentes)"],
        index=0
    )
    st.markdown("---")
    st.caption("Fonte: IBGE/SIDRA | BCB/SGS | BCB/Focus")
    st.caption("Atualizado automaticamente a cada hora.")


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados de atividade econômica..."):
    df_pib   = get_pib()
    df_ibcbr = get_ibcbr()
    df_fa = get_focus_anual()

# Filtrar período
di    = pd.Timestamp(f"{ano_ini}-01-01")
df_fim= pd.Timestamp(f"{ano_fim}-12-31")

df_pib_f   = df_pib[(df_pib["Data"] >= di) & (df_pib["Data"] <= df_fim)] if not df_pib.empty else df_pib
if not df_ibcbr.empty:
    df_ibcbr_r = df_ibcbr.copy()
    df_ibcbr_r.index = pd.to_datetime(df_ibcbr_r.index)
    df_ibcbr_r = df_ibcbr_r[(df_ibcbr_r.index >= di) & (df_ibcbr_r.index <= df_fim)]
    df_ibcbr_f = df_ibcbr_r
else:
    df_ibcbr_f = pd.DataFrame()


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    📈 Atividade Econômica
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    PIB trimestral por setor · IBC-Br mensal · Decomposição da demanda · Expectativas Focus
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
ano_at = datetime.today().year

# PIB Total — último trimestre disponível
pib_total_v = None
pib_total_dt = None
if not df_pib_f.empty:
    df_tot = df_pib_f[df_pib_f["Setor"] == "PIB_Total"].dropna(subset=["Valor"])
    if not df_tot.empty:
        pib_total_v  = round(float(df_tot.iloc[-1]["Valor"]), 0)
        pib_total_dt = df_tot.iloc[-1]["Data"].strftime("%dT/%Y") if pd.notna(df_tot.iloc[-1]["Data"]) else ""

# Variação anual do PIB (último tri vs mesmo tri ano anterior)
pib_var_anual = None
if not df_pib_f.empty:
    df_tot = df_pib_f[df_pib_f["Setor"] == "PIB_Total"].sort_values("Data")
    if len(df_tot) >= 5:
        v_atual    = df_tot.iloc[-1]["Valor"]
        v_ano_ant  = df_tot.iloc[-5]["Valor"]
        pib_var_anual = round((v_atual / v_ano_ant - 1) * 100, 2)

# IBC-Br último valor
ibcbr_v = None
if not df_ibcbr_f.empty and "IBC_Br" in df_ibcbr_f.columns:
    s = df_ibcbr_f["IBC_Br"].dropna()
    if len(s) > 0:
        ibcbr_v = round(float(s.iloc[-1]), 2)

# Focus PIB
pib_focus = None
if not df_fa.empty:
    f = df_fa[(df_fa["Indicador"] == "PIB Total") &
              (df_fa["DataReferencia"] == str(ano_at))]
    if not f.empty:
        pib_focus = round(float(f.sort_values("Data").iloc[-1]["Mediana"]), 2)

# Setor que mais cresceu
setor_destaque = None
if not df_pib_f.empty and pib_var_anual is not None:
    SETORES_OFERTA = ["Agropecuaria","Industria","Servicos"]
    crescimentos = {}
    for setor in SETORES_OFERTA:
        df_s = df_pib_f[df_pib_f["Setor"] == setor].sort_values("Data")
        if len(df_s) >= 5:
            v_at  = df_s.iloc[-1]["Valor"]
            v_ant = df_s.iloc[-5]["Valor"]
            crescimentos[setor] = round((v_at / v_ant - 1) * 100, 2)
    if crescimentos:
        setor_destaque = max(crescimentos, key=crescimentos.get)
        setor_val      = crescimentos[setor_destaque]

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("PIB (R$ bi)", f"R$ {pib_total_v/1000:.0f} bi" if pib_total_v else "—",
              delta=str(pib_total_dt), delta_color="off")
with c2:
    st.metric("Var. Anual PIB", f"{pib_var_anual:+.2f}%" if pib_var_anual else "—",
              delta="vs mesmo tri ano anterior", delta_color="normal" if pib_var_anual and pib_var_anual > 0 else "inverse")
with c3:
    st.metric("IBC-Br", f"{ibcbr_v:.2f}" if ibcbr_v else "—",
              delta="Proxy mensal PIB", delta_color="off")
with c4:
    st.metric(f"PIB Focus {ano_at}", f"{pib_focus:.2f}%" if pib_focus else "—",
              delta="Expectativa Focus", delta_color="off")
with c5:
    if setor_destaque:
        st.metric("Setor Destaque", setor_destaque,
                  delta=f"+{setor_val:.1f}% a/a", delta_color="normal")
    else:
        st.metric("Setor Destaque", "—")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
col_g1, col_g2 = st.columns([6, 4])

# Gráfico 1 — PIB por setor ou componente de demanda
with col_g1:
    if visao == "Oferta (setores)":
        st.markdown("#### PIB por Setor de Oferta — R$ bilhões")
        SETORES_PLOT = ["Agropecuaria", "Industria", "Servicos"]
        CORES_SETORES = {
            "Agropecuaria": "#00D4AA",
            "Industria":    "#FFB800",
            "Servicos":     "#00D4FF",
        }
    else:
        st.markdown("#### PIB por Componente de Demanda — R$ bilhões")
        SETORES_PLOT = ["Consumo_Familias", "Consumo_Governo",
                        "Investimento_FBCF", "Exportacoes"]
        CORES_SETORES = {
            "Consumo_Familias":  "#00D4FF",
            "Consumo_Governo":   "#FFB800",
            "Investimento_FBCF": "#00D4AA",
            "Exportacoes":       "#FF6B6B",
        }

    if not df_pib_f.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0F1117")
        ax.set_facecolor("#0F1117")

        for setor in SETORES_PLOT:
            df_s = df_pib_f[df_pib_f["Setor"] == setor].sort_values("Data")
            if not df_s.empty:
                vals = df_s["Valor"] / 1000  # R$ bilhões
                ax.plot(df_s["Data"], vals,
                        color=CORES_SETORES.get(setor, "#AAAAAA"),
                        lw=2.0, label=setor.replace("_", " "), marker="o", ms=3)

        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"R$ {x:.0f} bi"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.set_ylabel("R$ bilhões", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados de PIB não disponíveis.")


# Gráfico 2 — IBC-Br mensal
with col_g2:
    st.markdown("#### IBC-Br — Proxy Mensal do PIB")

    if not df_ibcbr_f.empty and "IBC_Br" in df_ibcbr_f.columns:
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        s = df_ibcbr_f["IBC_Br"].dropna()

        # Cor baseada na tendência
        ax2.fill_between(s.index, s.values, alpha=0.15, color="#00D4FF")
        ax2.plot(s.index, s.values, color="#00D4FF",
                 lw=2.0, alpha=0.9)

        # Média móvel 3m
        mm3 = s.rolling(3).mean()
        ax2.plot(mm3.index, mm3.values, color="#FFB800",
                 lw=2.0, ls="--", label="Média móvel 3m")

        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
        plt.xticks(rotation=30, ha="right")
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        ax2.set_title("IBC-Br (índice)", color="white",
                      fontsize=11, fontweight="bold", pad=12)
        ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()
    else:
        st.info("Dados do IBC-Br não disponíveis.")

st.markdown("---")


# -----------------------------------------------------------------------------
# ANÁLISE AUTOMÁTICA + EXPECTATIVAS
# -----------------------------------------------------------------------------
col_t, col_e = st.columns([6, 4])

with col_t:
    st.markdown("#### Análise Automática")

    linhas = []

    if pib_var_anual is not None and pib_total_dt:
        if pib_var_anual > 3:
            ritmo = "acima da média histórica"
            tom   = "positivo"
        elif pib_var_anual > 1:
            ritmo = "em ritmo moderado"
            tom   = "neutro"
        elif pib_var_anual > 0:
            ritmo = "em ritmo fraco"
            tom   = "alerta"
        else:
            ritmo = "em contração"
            tom   = "alerta"

        linhas.append(
            f"**[PIB]** No {pib_total_dt}, o PIB cresceu **{pib_var_anual:+.2f}%** "
            f"em relação ao mesmo período do ano anterior — {ritmo}."
        )

    if setor_destaque and crescimentos:
        outros = {k: v for k, v in crescimentos.items() if k != setor_destaque}
        linhas.append(
            f"**[Setores]** O setor de **{setor_destaque}** liderou o crescimento "
            f"com **+{setor_val:.1f}%** a/a. " +
            " · ".join([f"{k}: {v:+.1f}%" for k, v in outros.items()])
        )

    if pib_focus:
        linhas.append(
            f"**[Expectativa]** O mercado (Focus) espera crescimento de "
            f"**{pib_focus:.2f}%** para o PIB em {ano_at}."
        )

    if ibcbr_v:
        linhas.append(
            f"**[IBC-Br]** O Índice de Atividade do BCB registrou **{ibcbr_v:.2f}** "
            f"no último mês disponível — utilizado como proxy mensal do PIB."
        )

    for linha in linhas:
        st.markdown(linha)

    if not linhas:
        st.info("Dados insuficientes para análise.")

with col_e:
    st.markdown("#### Expectativas Focus — PIB")

    if not df_fa.empty:
        df_pib_fa = df_fa[df_fa["Indicador"] == "PIB Total"].copy()
        if not df_pib_fa.empty:
            anos_ref = sorted(df_pib_fa["DataReferencia"].unique())
            anos_ref = [a for a in anos_ref if int(a) >= ano_at][:3]
            for ar in anos_ref:
                df_ar = df_pib_fa[df_pib_fa["DataReferencia"] == ar]
                if not df_ar.empty:
                    v = round(float(df_ar.sort_values("Data").iloc[-1]["Mediana"]), 2)
                    delta_cor = "normal" if v > 0 else "inverse"
                    st.metric(f"PIB {ar}", f"{v:.2f}%",
                              delta="Var. real esperada", delta_color=delta_cor)
    st.caption("BCB/Focus — mediana · última coleta disponível")

rodape()
