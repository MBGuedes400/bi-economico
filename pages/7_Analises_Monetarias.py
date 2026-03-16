# =============================================================================
# pages/7_Analises_Monetarias.py — Análises Monetárias Avançadas
# Blocos: Juro Real · Núcleos de Inflação · Difusão · Phillips · Pass-through
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

from utils.dados  import (get_inflacao, get_juros, get_cambio,
                           get_pnad, get_focus_anual, _coletar_sgs,
                           ultimo_valor, METAS_BCB)
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Análises Monetárias | BI Econômico",
                   page_icon="🔬", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
ano_ini, ano_fim = 2019, datetime.today().year
bloco_sel = "Todos"

def _filtros():
    global ano_ini, ano_fim, bloco_sel
    st.markdown("**⚙️ Filtros — Análises Monetárias**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2019, datetime.today().year)
    )
    bloco_sel = st.radio(
        "Exibir",
        ["Todos", "Juro Real", "Núcleos", "Difusão", "Phillips", "Pass-through"],
        index=0
    )

sidebar_padrao(filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados..."):
    df_infl  = get_inflacao()
    df_juros = get_juros()
    df_camb  = get_cambio()
    df_pnad  = get_pnad()
    df_fa    = get_focus_anual()

    # Núcleos de inflação — séries BCB/SGS
    # EX0=4466, MS=11427, P55=16122, Dupla ponderação=16121
    try:
        df_nucleos = _coletar_sgs({
            "Nucleo_EX0": 4466,
            "Nucleo_MS":  11427,
            "Nucleo_P55": 16122,
            "Nucleo_DP":  16121,
        }, anos=10)
    except Exception:
        df_nucleos = pd.DataFrame()

    # Índice de Difusão do IPCA — série BCB 21379
    try:
        df_difusao = _coletar_sgs({"Difusao_IPCA": 21379}, anos=10)
    except Exception:
        df_difusao = pd.DataFrame()

# Filtrar período
di     = pd.Timestamp(f"{ano_ini}-01-01")
df_fim = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df.index = pd.to_datetime(df.index)
    return df[(df.index >= di) & (df.index <= df_fim)]

df_infl_f  = filtrar(df_infl)
df_juros_f = filtrar(df_juros)
df_camb_f  = filtrar(df_camb)
df_nuc_f   = filtrar(df_nucleos)
df_dif_f   = filtrar(df_difusao)


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🔬 Análises Monetárias Avançadas
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Juro real · Núcleos de inflação · Difusão · Curva de Phillips · Pass-through cambial
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# =============================================================================
# BLOCO 1 — JURO REAL EX-ANTE / EX-POST
# =============================================================================
mostrar = bloco_sel in ("Todos", "Juro Real")
if mostrar:
    st.markdown("### 💰 Juro Real Ex-ante vs Ex-post")
    st.caption("Ex-post: Selic deflacionada pelo IPCA realizado · Ex-ante: Selic deflacionada pela expectativa Focus IPCA 12m")

    # Calcula séries históricas de juro real
    jr_expost = pd.Series(dtype=float)
    jr_exante = pd.Series(dtype=float)

    if not df_juros_f.empty and "Selic_Meta" in df_juros_f.columns:
        selic = df_juros_f["Selic_Meta"].dropna()

        # Ex-post: Selic - IPCA acum12m
        if not df_infl_f.empty and "IPCA_acum12m" in df_infl_f.columns:
            ipca12 = df_infl_f["IPCA_acum12m"].dropna()
            df_m = pd.DataFrame({"Selic": selic, "IPCA": ipca12}).dropna()
            if not df_m.empty:
                jr_expost = ((1 + df_m["Selic"]/100) / (1 + df_m["IPCA"]/100) - 1) * 100

        # Ex-ante: Selic - Focus IPCA próximos 12m
        if not df_fa.empty:
            focus_ts = (df_fa[df_fa["Indicador"] == "IPCA"]
                        .sort_values("Data")
                        .drop_duplicates("Data", keep="last")
                        .set_index("Data")["Mediana"]
                        .dropna())
            focus_ts.index = pd.to_datetime(focus_ts.index)
            focus_ts = focus_ts[(focus_ts.index >= di) & (focus_ts.index <= df_fim)]
            df_m2 = pd.DataFrame({"Selic": selic, "Focus": focus_ts}).dropna()
            if not df_m2.empty:
                jr_exante = ((1 + df_m2["Selic"]/100) / (1 + df_m2["Focus"]/100) - 1) * 100

    col_g1, col_g2 = st.columns([6, 4])

    with col_g1:
        if not jr_expost.empty or not jr_exante.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")

            if not jr_expost.empty:
                ax.plot(jr_expost.index, jr_expost.values,
                        color="#00D4FF", lw=2.0, label="Ex-post (Selic - IPCA 12m)")
                ax.fill_between(jr_expost.index, jr_expost.values, 0,
                                where=jr_expost.values > 0,
                                alpha=0.08, color="#00D4FF")
            if not jr_exante.empty:
                ax.plot(jr_exante.index, jr_exante.values,
                        color="#FFB800", lw=2.0, ls="--",
                        label="Ex-ante (Selic - Focus IPCA)")

            ax.axhline(0, color="#555", lw=0.8)
            ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax.tick_params(colors="#AAAAAA", labelsize=9)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            ax.set_ylabel("% a.a.", color="#AAAAAA", fontsize=9)
            ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                      labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig); plt.close()
        else:
            st.info("Dados insuficientes para calcular juro real.")

    with col_g2:
        st.markdown("#### Leitura atual")
        selic_v, _ = ultimo_valor(df_juros, "Selic_Meta")
        ipca_v,  _ = ultimo_valor(df_infl,  "IPCA_acum12m")

        jr_now = None
        if selic_v and ipca_v:
            jr_now = round(((1 + selic_v/100) / (1 + ipca_v/100) - 1) * 100, 2)

        jr_ante_now = None
        if not df_fa.empty and selic_v:
            ano_at = datetime.today().year
            f = df_fa[(df_fa["Indicador"] == "IPCA") &
                      (df_fa["DataReferencia"] == str(ano_at))]
            if not f.empty:
                foc_v = round(float(f.sort_values("Data").iloc[-1]["Mediana"]), 2)
                jr_ante_now = round(((1 + selic_v/100) / (1 + foc_v/100) - 1) * 100, 2)

        st.metric("Juro Real Ex-post", f"{jr_now:.2f}%" if jr_now else "—",
                  delta="Selic - IPCA acum. 12m", delta_color="off")
        st.metric("Juro Real Ex-ante", f"{jr_ante_now:.2f}%" if jr_ante_now else "—",
                  delta="Selic - Focus IPCA", delta_color="off")

        if jr_now:
            if jr_now > 6:
                interp = "Política contracionista forte — juros reais elevados"
                cor = "#FF4B6E"
            elif jr_now > 3:
                interp = "Política contracionista moderada"
                cor = "#FFB800"
            elif jr_now > 0:
                interp = "Política levemente restritiva"
                cor = "#00D4AA"
            else:
                interp = "Política estimulante — juro real negativo"
                cor = "#00D4FF"
            st.markdown(
                f"<div style='background:#1A1D27;border-left:3px solid {cor};"
                f"border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px'>"
                f"<span style='color:{cor};font-size:0.85rem'>{interp}</span></div>",
                unsafe_allow_html=True
            )

    st.markdown("---")


# =============================================================================
# BLOCO 2 — NÚCLEOS DE INFLAÇÃO
# =============================================================================
mostrar = bloco_sel in ("Todos", "Núcleos")
if mostrar:
    st.markdown("### 🎯 Núcleos de Inflação (BCB)")
    st.caption("Medidas que excluem itens voláteis — revelam a tendência subjacente da inflação")

    col_g1, col_g2 = st.columns([6, 4])

    CORES_NUC = {
        "Nucleo_EX0": "#00D4FF",
        "Nucleo_MS":  "#FFB800",
        "Nucleo_P55": "#00D4AA",
        "Nucleo_DP":  "#A78BFA",
    }
    LABELS_NUC = {
        "Nucleo_EX0": "EX0 (ex-alimentação domiciliar e energia)",
        "Nucleo_MS":  "MS (médias aparadas)",
        "Nucleo_P55": "P55 (percentil 55)",
        "Nucleo_DP":  "Dupla ponderação",
    }

    with col_g1:
        if not df_nuc_f.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")
            for col in df_nuc_f.columns:
                s = df_nuc_f[col].dropna()
                if s.empty: continue
                ax.plot(s.index, s.values,
                        color=CORES_NUC.get(col, "#AAAAAA"),
                        lw=1.8, label=LABELS_NUC.get(col, col))
            # IPCA cheio como referência
            if not df_infl_f.empty and "IPCA" in df_infl_f.columns:
                ipca = df_infl_f["IPCA"].dropna()
                ax.plot(ipca.index, ipca.values,
                        color="#FF4B6E", lw=1.0, ls=":", alpha=0.6,
                        label="IPCA cheio (ref.)")
            # Meta BCB
            meta = METAS_BCB.get(datetime.today().year, 3.0)
            ax.axhline(meta, color="#555", lw=0.8, ls="--")
            ax.text(df_nuc_f.index[-1], meta + 0.1,
                    f"Meta {meta:.1f}%", color="#555", fontsize=8, ha="right")
            ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax.tick_params(colors="#AAAAAA", labelsize=9)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            ax.set_ylabel("% a.m.", color="#AAAAAA", fontsize=9)
            ax.legend(fontsize=7.5, facecolor="#1A1D27", edgecolor="#333",
                      labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig); plt.close()
        else:
            st.warning("Séries de núcleos não carregadas (BCB/SGS). Verifique a conexão.")

    with col_g2:
        st.markdown("#### Últimas leituras")
        for col, label in LABELS_NUC.items():
            v, d = ultimo_valor(df_nucleos, col)
            if v is not None:
                d_str = d.strftime("%b/%Y") if d else "—"
                st.metric(label.split("(")[0].strip(), f"{v:.2f}%",
                          delta=d_str, delta_color="off")
        st.caption("Núcleos acima da meta sinalizam inflação persistente — "
                   "difícil de combater apenas com juros.")

    st.markdown("---")


# =============================================================================
# BLOCO 3 — ÍNDICE DE DIFUSÃO
# =============================================================================
mostrar = bloco_sel in ("Todos", "Difusão")
if mostrar:
    st.markdown("### 📡 Índice de Difusão do IPCA")
    st.caption("% dos itens da cesta que registraram alta no mês — inflação generalizada vs pontual")

    if not df_dif_f.empty and "Difusao_IPCA" in df_dif_f.columns:
        col_g1, col_g2 = st.columns([6, 4])

        with col_g1:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")

            s   = df_dif_f["Difusao_IPCA"].dropna()
            mm3 = s.rolling(3).mean()
            cores_bar = ["#FF4B6E" if v > 60 else "#FFB800" if v > 50 else "#00D4AA"
                         for v in s.values]
            ax.bar(s.index, s.values, width=25, color=cores_bar, alpha=0.7)
            ax.plot(mm3.index, mm3.values, color="#00D4FF",
                    lw=2.0, label="Média móvel 3m")
            ax.axhline(50, color="#555", lw=0.8, ls="--")
            ax.text(s.index[-1], 51, "50% (neutro)", color="#555",
                    fontsize=8, ha="right")
            ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax.tick_params(colors="#AAAAAA", labelsize=9)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            ax.set_ylabel("% dos itens com alta", color="#AAAAAA", fontsize=9)
            ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                      labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig); plt.close()

        with col_g2:
            v_dif, d_dif = ultimo_valor(df_difusao, "Difusao_IPCA")
            st.metric("Difusão atual", f"{v_dif:.1f}%" if v_dif else "—",
                      delta=d_dif.strftime("%b/%Y") if d_dif else None,
                      delta_color="off")
            if v_dif:
                if v_dif > 65:
                    txt = "Inflação muito generalizada — pressão ampla nos preços."
                    cor = "#FF4B6E"
                elif v_dif > 55:
                    txt = "Inflação generalizada — maioria dos itens subindo."
                    cor = "#FFB800"
                elif v_dif > 45:
                    txt = "Difusão neutra — equilíbrio entre altas e baixas."
                    cor = "#00D4AA"
                else:
                    txt = "Inflação pontual — poucos itens pressionando o índice."
                    cor = "#00D4FF"
                st.markdown(
                    f"<div style='background:#1A1D27;border-left:3px solid {cor};"
                    f"border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px'>"
                    f"<span style='color:{cor};font-size:0.85rem'>{txt}</span></div>",
                    unsafe_allow_html=True
                )
            st.caption("Leitura acima de 50%: mais itens subindo do que caindo. "
                       "Acima de 60% sinaliza inflação disseminada.")
    else:
        st.warning("Série de difusão (BCB 21379) não disponível. Pode não estar acessível no Cloud.")

    st.markdown("---")


# =============================================================================
# BLOCO 4 — CURVA DE PHILLIPS
# =============================================================================
mostrar = bloco_sel in ("Todos", "Phillips")
if mostrar:
    st.markdown("### 📉 Curva de Phillips — Inflação × Desemprego")
    st.caption("Relação inversa clássica: desemprego baixo → pressão inflacionária · alto → desinflação")

    ipca_mensal = pd.Series(dtype=float)
    desemprego  = pd.Series(dtype=float)

    if not df_infl_f.empty and "IPCA_acum12m" in df_infl_f.columns:
        ipca_mensal = df_infl_f["IPCA_acum12m"].dropna()

    if not df_pnad.empty and "Taxa_Desocupacao" in df_pnad.columns:
        desemprego = df_pnad["Taxa_Desocupacao"].dropna()
        desemprego = desemprego[(desemprego.index >= di) & (desemprego.index <= df_fim)]

    col_g1, col_g2 = st.columns([5, 5])

    with col_g1:
        if not ipca_mensal.empty and not desemprego.empty:
            df_ph = pd.DataFrame({
                "IPCA_12m":   ipca_mensal,
                "Desemprego": desemprego
            }).dropna()

            if len(df_ph) >= 6:
                fig, ax = plt.subplots(figsize=(8, 5))
                fig.patch.set_facecolor("#0F1117")
                ax.set_facecolor("#0F1117")

                # Colorir por ano
                anos_unicos = df_ph.index.year.unique()
                cmap = plt.cm.get_cmap("plasma", len(anos_unicos))
                for i, ano in enumerate(sorted(anos_unicos)):
                    mask = df_ph.index.year == ano
                    ax.scatter(df_ph.loc[mask, "Desemprego"],
                               df_ph.loc[mask, "IPCA_12m"],
                               color=cmap(i), s=50, alpha=0.85,
                               label=str(ano), zorder=5)

                # Linha de tendência
                try:
                    z = np.polyfit(df_ph["Desemprego"], df_ph["IPCA_12m"], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(df_ph["Desemprego"].min(),
                                         df_ph["Desemprego"].max(), 100)
                    ax.plot(x_line, p(x_line), color="#AAAAAA",
                            lw=1.2, ls="--", alpha=0.6, label="Tendência")
                except Exception:
                    pass

                ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
                ax.tick_params(colors="#AAAAAA", labelsize=9)
                ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
                ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
                ax.set_xlabel("Taxa de Desocupação (%)", color="#AAAAAA", fontsize=9)
                ax.set_ylabel("IPCA acum. 12m (%)", color="#AAAAAA", fontsize=9)
                for sp in ax.spines.values(): sp.set_edgecolor("#333")
                ax.legend(fontsize=7.5, facecolor="#1A1D27", edgecolor="#333",
                          labelcolor="#CCC", framealpha=0.9, ncol=3)
                plt.tight_layout()
                st.pyplot(fig); plt.close()
            else:
                st.info("Poucos dados sobrepostos para plotar a curva.")
        else:
            st.info("Dados de IPCA ou desemprego não disponíveis.")

    with col_g2:
        st.markdown("#### Série temporal comparada")
        if not ipca_mensal.empty and not desemprego.empty:
            fig2, ax1 = plt.subplots(figsize=(8, 5))
            fig2.patch.set_facecolor("#0F1117")
            ax1.set_facecolor("#0F1117")

            ax1.plot(ipca_mensal.index, ipca_mensal.values,
                     color="#00D4FF", lw=2.0, label="IPCA 12m (%)")
            ax1.fill_between(ipca_mensal.index, ipca_mensal.values,
                             alpha=0.07, color="#00D4FF")

            ax2 = ax1.twinx()
            ax2.plot(desemprego.index, desemprego.values,
                     color="#FF4B6E", lw=2.0, ls="--",
                     label="Desemprego (%)", alpha=0.85)
            ax2.tick_params(colors="#AAAAAA", labelsize=8)
            ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax2.set_facecolor("#0F1117")
            for sp in ax2.spines.values(): sp.set_edgecolor("#333")

            ax1.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax1.tick_params(colors="#AAAAAA", labelsize=9)
            ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax1.spines.values(): sp.set_edgecolor("#333")
            ax1.set_ylabel("IPCA 12m", color="#00D4FF", fontsize=9)
            ax2.set_ylabel("Desemprego", color="#FF4B6E", fontsize=9)

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1+lines2, labels1+labels2,
                       fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig2); plt.close()

    st.markdown("---")


# =============================================================================
# BLOCO 5 — PASS-THROUGH CAMBIAL
# =============================================================================
mostrar = bloco_sel in ("Todos", "Pass-through")
if mostrar:
    st.markdown("### 💱 Pass-through Cambial")
    st.caption("Quanto uma variação do dólar se transmite ao IPCA após n meses")

    usd = pd.Series(dtype=float)
    ipca = pd.Series(dtype=float)

    if not df_camb_f.empty and "USD_BRL" in df_camb_f.columns:
        usd = df_camb_f["USD_BRL"].dropna()
        usd_var = usd.pct_change(1) * 100  # variação % mensal

    if not df_infl_f.empty and "IPCA" in df_infl_f.columns:
        ipca = df_infl_f["IPCA"].dropna()

    col_g1, col_g2 = st.columns([6, 4])

    with col_g1:
        if not usd.empty and not ipca.empty:
            # Correlação com defasagem de 0 a 12 meses
            usd_var_clean = usd.pct_change(1).dropna() * 100
            corrs = []
            lags  = list(range(0, 13))
            for lag in lags:
                ipca_lag = ipca.shift(-lag)
                df_pt = pd.DataFrame({
                    "USD_var": usd_var_clean,
                    "IPCA":    ipca_lag
                }).dropna()
                if len(df_pt) >= 6:
                    c = df_pt["USD_var"].corr(df_pt["IPCA"])
                    corrs.append(round(c, 3))
                else:
                    corrs.append(np.nan)

            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")

            cores_corr = ["#FF4B6E" if c > 0 else "#00D4AA"
                          for c in corrs if not np.isnan(c)]
            valid_lags  = [l for l, c in zip(lags, corrs) if not np.isnan(c)]
            valid_corrs = [c for c in corrs if not np.isnan(c)]

            ax.bar(valid_lags, valid_corrs, color=cores_corr, alpha=0.8, width=0.7)
            ax.axhline(0, color="#555", lw=0.8)
            ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax.tick_params(colors="#AAAAAA", labelsize=9)
            ax.set_xlabel("Defasagem (meses)", color="#AAAAAA", fontsize=9)
            ax.set_ylabel("Correlação (USD var% → IPCA)", color="#AAAAAA", fontsize=9)
            ax.set_xticks(lags)
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            plt.tight_layout()
            st.pyplot(fig); plt.close()

            # Lag de maior correlação
            if valid_corrs:
                max_corr_idx = int(np.argmax(np.abs(valid_corrs)))
                st.caption(
                    f"📌 Maior correlação em **{valid_lags[max_corr_idx]} meses** de defasagem "
                    f"(corr = {valid_corrs[max_corr_idx]:.2f}). "
                    f"Interpreta-se: uma alta do dólar tende a se refletir no IPCA "
                    f"após ~{valid_lags[max_corr_idx]} meses."
                )
        else:
            st.info("Dados de câmbio ou IPCA não disponíveis.")

    with col_g2:
        st.markdown("#### Histórico USD/BRL vs IPCA")
        if not usd.empty and not ipca.empty:
            fig2, ax1 = plt.subplots(figsize=(7, 4))
            fig2.patch.set_facecolor("#0F1117")
            ax1.set_facecolor("#0F1117")

            ax1.plot(usd.index, usd.values,
                     color="#FFB800", lw=2.0, label="USD/BRL")
            ax2 = ax1.twinx()
            ax2.plot(ipca.index, ipca.values,
                     color="#00D4AA", lw=1.5, ls="--",
                     label="IPCA (% a.m.)", alpha=0.85)
            ax2.tick_params(colors="#AAAAAA", labelsize=8)
            ax2.set_facecolor("#0F1117")
            for sp in ax2.spines.values(): sp.set_edgecolor("#333")

            ax1.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax1.tick_params(colors="#AAAAAA", labelsize=9)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax1.spines.values(): sp.set_edgecolor("#333")
            ax1.set_ylabel("R$/USD", color="#FFB800", fontsize=9)
            ax2.set_ylabel("IPCA %", color="#00D4AA", fontsize=9)
            lines1, l1 = ax1.get_legend_handles_labels()
            lines2, l2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1+lines2, l1+l2, fontsize=8,
                       facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig2); plt.close()

    st.markdown("---")


# =============================================================================
# RODAPÉ
# =============================================================================
rodape()
