# =============================================================================
# pages/8_Analises_Reais.py — Análises Reais Avançadas
# Blocos: Hiato do Produto · Nowcasting IBC-Br vs PIB · Yield Curve
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

from utils.dados  import get_pib, get_ibcbr, get_juros, get_tesouro_direto, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Análises Reais | BI Econômico",
                   page_icon="🏗️", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
ano_ini, ano_fim = 2010, datetime.today().year
bloco_sel = "Todos"

def _filtros():
    global ano_ini, ano_fim, bloco_sel
    st.markdown("**⚙️ Filtros — Análises Reais**")
    anos = list(range(2005, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2010, datetime.today().year)
    )
    bloco_sel = st.radio(
        "Exibir",
        ["Todos", "Hiato do Produto", "Nowcasting", "Yield Curve"],
        index=0
    )

sidebar_padrao(filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
# Filtrar período
di     = pd.Timestamp(f"{ano_ini}-01-01")
df_fim = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    return df[(df.index >= di) & (df.index <= df_fim)]

# Carregamento sob demanda — só busca o que o bloco selecionado precisa
df_pib    = pd.DataFrame()
df_ibcbr  = pd.DataFrame()
df_juros  = pd.DataFrame()
df_yield  = pd.DataFrame()
df_tesouro = pd.DataFrame()

if bloco_sel in ("Todos", "Hiato do Produto", "Nowcasting"):
    with st.spinner("Carregando IBC-Br..."):
        df_ibcbr = get_ibcbr()

if bloco_sel in ("Todos", "Nowcasting"):
    with st.spinner("Carregando PIB..."):
        df_pib = get_pib()

if bloco_sel in ("Todos", "Yield Curve"):
    with st.spinner("Carregando juros..."):
        df_juros = get_juros()
    with st.spinner("Carregando títulos do Tesouro Direto..."):
        df_tesouro = get_tesouro_direto()
    df_yield = df_juros.copy() if not df_juros.empty else pd.DataFrame()

df_ibcbr_f = filtrar(df_ibcbr)
df_juros_f = filtrar(df_juros)
df_yield_f = filtrar(df_yield)


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🏗️ Análises Reais Avançadas
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Hiato do produto · Nowcasting IBC-Br vs PIB · Yield curve
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# =============================================================================
# BLOCO 1 — HIATO DO PRODUTO (FILTRO HODRICK-PRESCOTT)
# =============================================================================
if bloco_sel in ("Todos", "Hiato do Produto"):
    st.markdown("### 📐 Hiato do Produto")
    st.caption("Diferença entre o PIB efetivo e o PIB potencial estimado via Filtro Hodrick-Prescott (HP)")

    # Usa IBC-Br como proxy mensal do PIB para o filtro HP
    hiato = pd.Series(dtype=float)
    tendencia = pd.Series(dtype=float)
    ibcbr_raw = pd.Series(dtype=float)

    if not df_ibcbr.empty and "IBC_Br" in df_ibcbr.columns:
        try:
            from statsmodels.tsa.filters.hp_filter import hpfilter

            ibcbr_raw = df_ibcbr["IBC_Br"].dropna()
            ibcbr_raw = ibcbr_raw[(ibcbr_raw.index >= di) & (ibcbr_raw.index <= df_fim)]

            if len(ibcbr_raw) >= 24:
                # lambda=129600 para dados mensais (padrão da literatura)
                ciclo, tendencia = hpfilter(ibcbr_raw.values, lamb=129600)
                hiato      = pd.Series(ciclo,     index=ibcbr_raw.index)
                tendencia  = pd.Series(tendencia,  index=ibcbr_raw.index)
        except Exception as e:
            st.warning(f"Erro no filtro HP: {e}")

    col_g1, col_g2 = st.columns([6, 4])

    with col_g1:
        if not hiato.empty:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7),
                                            gridspec_kw={"height_ratios": [3, 2]},
                                            sharex=True)
            fig.patch.set_facecolor("#0F1117")

            # Gráfico superior: IBC-Br vs tendência HP
            ax1.set_facecolor("#0F1117")
            ax1.plot(ibcbr_raw.index, ibcbr_raw.values,
                     color="#00D4FF", lw=1.5, alpha=0.8, label="IBC-Br (efetivo)")
            ax1.plot(tendencia.index, tendencia.values,
                     color="#FFB800", lw=2.0, ls="--", label="Tendência HP (potencial)")
            ax1.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax1.tick_params(colors="#AAAAAA", labelsize=9)
            ax1.set_ylabel("IBC-Br (índice)", color="#AAAAAA", fontsize=9)
            ax1.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            for sp in ax1.spines.values(): sp.set_edgecolor("#333")

            # Gráfico inferior: hiato
            ax2.set_facecolor("#0F1117")
            ax2.fill_between(hiato.index, hiato.values, 0,
                             where=hiato.values >= 0,
                             alpha=0.4, color="#00D4AA", label="Hiato positivo (aquecimento)")
            ax2.fill_between(hiato.index, hiato.values, 0,
                             where=hiato.values < 0,
                             alpha=0.4, color="#FF4B6E", label="Hiato negativo (ociosidade)")
            ax2.plot(hiato.index, hiato.values, color="#FFFFFF", lw=1.0, alpha=0.6)
            ax2.axhline(0, color="#555", lw=0.8)
            ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax2.tick_params(colors="#AAAAAA", labelsize=9)
            ax2.set_ylabel("Hiato (ciclo)", color="#AAAAAA", fontsize=9)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            for sp in ax2.spines.values(): sp.set_edgecolor("#333")

            plt.tight_layout()
            st.pyplot(fig); plt.close()
        else:
            st.info("Dados insuficientes para calcular o hiato do produto.")

    with col_g2:
        st.markdown("#### Interpretação atual")
        if not hiato.empty:
            v_hiato = round(float(hiato.iloc[-1]), 2)
            v_data  = hiato.index[-1].strftime("%b/%Y")

            if v_hiato > 2:
                status = "Economia aquecida"
                desc   = "PIB acima do potencial — pressão inflacionária"
                cor    = "#FF4B6E"
            elif v_hiato > 0:
                status = "Levemente aquecida"
                desc   = "PIB marginalmente acima do potencial"
                cor    = "#FFB800"
            elif v_hiato > -2:
                status = "Próximo ao potencial"
                desc   = "Economia operando perto da capacidade plena"
                cor    = "#00D4AA"
            else:
                status = "Capacidade ociosa"
                desc   = "PIB abaixo do potencial — pressão desinflacionária"
                cor    = "#00D4FF"

            st.metric("Hiato atual", f"{v_hiato:+.2f}", delta=v_data, delta_color="off")
            st.markdown(
                f"<div style='background:#1A1D27;border-left:3px solid {cor};"
                f"border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px'>"
                f"<span style='color:{cor};font-weight:700'>{status}</span><br>"
                f"<span style='color:#AAAAAA;font-size:0.85rem'>{desc}</span></div>",
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption(
                "**Metodologia:** Filtro Hodrick-Prescott com λ=129.600 "
                "(padrão para dados mensais). O IBC-Br é utilizado como "
                "proxy mensal do PIB. Hiato positivo = economia acima do "
                "potencial; negativo = ociosidade."
            )
        else:
            st.info("Dados insuficientes.")

    st.markdown("---")


# =============================================================================
# BLOCO 2 — NOWCASTING: IBC-Br vs PIB
# =============================================================================
if bloco_sel in ("Todos", "Nowcasting"):
    st.markdown("### 🔭 Nowcasting — IBC-Br vs PIB Trimestral")
    st.caption("O IBC-Br do BCB antecipa o PIB do IBGE — correlação e defasagem entre as séries")

    col_g1, col_g2 = st.columns([6, 4])

    with col_g1:
        if not df_ibcbr.empty and "IBC_Br" in df_ibcbr.columns and not df_pib.empty:
            # PIB total trimestral
            df_pib_tot = df_pib[df_pib["Setor"] == "PIB_Total"].copy()
            df_pib_tot = df_pib_tot[(df_pib_tot["Data"] >= di) &
                                     (df_pib_tot["Data"] <= df_fim)].sort_values("Data")

            # IBC-Br acumulado trimestral (média dos 3 meses)
            ibcbr = df_ibcbr["IBC_Br"].dropna()
            ibcbr = ibcbr[(ibcbr.index >= di) & (ibcbr.index <= df_fim)]
            ibcbr_trim = ibcbr.resample("QS").mean()

            fig, ax1 = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor("#0F1117")
            ax1.set_facecolor("#0F1117")

            # PIB var anual
            if len(df_pib_tot) >= 5:
                df_pib_tot = df_pib_tot.set_index("Data")
                pib_var = df_pib_tot["Valor"].pct_change(4) * 100
                ax1.bar(pib_var.index, pib_var.values, width=60,
                        color=["#00D4AA" if v >= 0 else "#FF4B6E"
                               for v in pib_var.fillna(0).values],
                        alpha=0.6, label="PIB var. anual (%)")

            # IBC-Br var anual
            if len(ibcbr_trim) >= 5:
                ibcbr_var = ibcbr_trim.pct_change(4) * 100
                ax1.plot(ibcbr_var.index, ibcbr_var.values,
                         color="#FFB800", lw=2.0, marker="o", ms=4,
                         label="IBC-Br var. anual (%) — trimestral")

            ax1.axhline(0, color="#555", lw=0.8)
            ax1.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax1.tick_params(colors="#AAAAAA", labelsize=9)
            ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            plt.xticks(rotation=30, ha="right")
            for sp in ax1.spines.values(): sp.set_edgecolor("#333")
            ax1.set_ylabel("Variação anual (%)", color="#AAAAAA", fontsize=9)
            ax1.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig); plt.close()
        else:
            st.info("Dados de PIB ou IBC-Br não disponíveis.")

    with col_g2:
        st.markdown("#### Correlação IBC-Br → PIB")

        if not df_ibcbr.empty and not df_pib.empty:
            try:
                df_pib_tot = df_pib[df_pib["Setor"] == "PIB_Total"].copy()
                df_pib_tot = df_pib_tot.set_index("Data").sort_index()
                ibcbr = df_ibcbr["IBC_Br"].dropna()
                ibcbr_trim = ibcbr.resample("QS").mean()
                pib_var    = df_pib_tot["Valor"].pct_change(4) * 100
                ibcbr_var  = ibcbr_trim.pct_change(4) * 100

                corrs = []
                lags  = list(range(0, 5))
                for lag in lags:
                    df_corr = pd.DataFrame({
                        "IBC": ibcbr_var.shift(lag),
                        "PIB": pib_var
                    }).dropna()
                    if len(df_corr) >= 6:
                        corrs.append(round(df_corr["IBC"].corr(df_corr["PIB"]), 3))
                    else:
                        corrs.append(np.nan)

                fig2, ax2 = plt.subplots(figsize=(6, 4))
                fig2.patch.set_facecolor("#0F1117")
                ax2.set_facecolor("#0F1117")
                cores = ["#00D4AA" if c > 0 else "#FF4B6E" for c in corrs if not np.isnan(c)]
                valid = [(l, c) for l, c in zip(lags, corrs) if not np.isnan(c)]
                ax2.bar([v[0] for v in valid], [v[1] for v in valid],
                        color=cores, alpha=0.85, width=0.6)
                ax2.axhline(0, color="#555", lw=0.8)
                ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
                ax2.tick_params(colors="#AAAAAA", labelsize=9)
                ax2.set_xlabel("Defasagem (trimestres)", color="#AAAAAA", fontsize=9)
                ax2.set_ylabel("Correlação", color="#AAAAAA", fontsize=9)
                ax2.set_xticks(lags)
                for sp in ax2.spines.values(): sp.set_edgecolor("#333")
                plt.tight_layout()
                st.pyplot(fig2); plt.close()

                if valid:
                    best = max(valid, key=lambda x: abs(x[1]))
                    st.caption(
                        f"📌 Maior correlação com **{best[0]} trimestre(s)** de defasagem "
                        f"(corr = {best[1]:.2f}). O IBC-Br antecipa o PIB oficial do IBGE."
                    )
            except Exception:
                st.info("Dados insuficientes para calcular correlação.")
        else:
            st.info("Dados não disponíveis.")

    st.markdown("---")


# =============================================================================
# BLOCO 3 — YIELD CURVE (CURVA DE JUROS) — Tesouro Direto
# =============================================================================
if bloco_sel in ("Todos", "Yield Curve"):
    st.markdown("### 📈 Yield Curve — Estrutura a Termo da Taxa de Juros")
    st.caption("Prefixado (taxa nominal) · IPCA+ (taxa real) · Tesouro Direto — curva invertida sinaliza risco de recessão")

    col_g1, col_g2 = st.columns([6, 4])

    # Prepara dados da yield curve
    df_pre  = pd.DataFrame()
    df_ipca = pd.DataFrame()
    ultima_data = None

    if not df_tesouro.empty:
        df_tesouro["Prazo_Anos"] = (
            (df_tesouro["Data Vencimento"] - df_tesouro["Data Base"]).dt.days / 365
        )
        ultima_data = df_tesouro["Data Base"].max()
        df_hoje = df_tesouro[
            (df_tesouro["Data Base"] == ultima_data) &
            (df_tesouro["Taxa Venda Manha"] > 0)
        ].copy()

        df_pre = (df_hoje[df_hoje["Tipo Titulo"].str.contains("Prefixado")]
                  .groupby("Prazo_Anos")["Taxa Venda Manha"].mean()
                  .reset_index().sort_values("Prazo_Anos"))

        df_ipca = (df_hoje[df_hoje["Tipo Titulo"].str.contains("IPCA")]
                   .groupby("Prazo_Anos")["Taxa Venda Manha"].mean()
                   .reset_index().sort_values("Prazo_Anos"))

    with col_g1:
        if not df_pre.empty or not df_ipca.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")

            if not df_pre.empty:
                ax.plot(df_pre["Prazo_Anos"], df_pre["Taxa Venda Manha"],
                        color="#00D4FF", lw=2.5, marker="o", ms=6,
                        label="Prefixado (taxa nominal)")
            if not df_ipca.empty:
                ax.plot(df_ipca["Prazo_Anos"], df_ipca["Taxa Venda Manha"],
                        color="#FFB800", lw=2.5, marker="o", ms=6,
                        label="IPCA+ (taxa real)")

            ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax.tick_params(colors="#AAAAAA", labelsize=9)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
            ax.set_xlabel("Prazo (anos)", color="#AAAAAA", fontsize=9)
            ax.set_ylabel("Taxa (% a.a.)", color="#AAAAAA", fontsize=9)
            if ultima_data is not None:
                ax.set_title(f"Yield Curve Brasil — {ultima_data.strftime('%d/%m/%Y')}",
                             color="white", fontsize=11, fontweight="bold", pad=10)
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                      labelcolor="#CCC", framealpha=0.9)
            plt.tight_layout()
            st.pyplot(fig); plt.close()
        else:
            st.info("Dados do Tesouro Direto não disponíveis.")

    with col_g2:
        st.markdown("#### Diagnóstico da curva")

        if not df_pre.empty:
            taxa_curta = df_pre.iloc[0]["Taxa Venda Manha"]
            taxa_longa = df_pre.iloc[-1]["Taxa Venda Manha"]
            prazo_curto = round(df_pre.iloc[0]["Prazo_Anos"], 1)
            prazo_longo = round(df_pre.iloc[-1]["Prazo_Anos"], 1)
            spread = round(taxa_longa - taxa_curta, 2)

            st.metric("Spread longo−curto (Prefixado)",
                      f"{spread:+.2f}pp",
                      delta=f"Curto: {taxa_curta:.1f}% · Longo: {taxa_longa:.1f}%",
                      delta_color="off")

            # Forma da curva
            if spread < -0.5:
                forma = "Curva invertida"
                cor   = "#FF4B6E"
                analise = (
                    f"A taxa de **{prazo_curto:.0f} ano(s)** ({taxa_curta:.1f}% a.a.) "
                    f"está **acima** da taxa de **{prazo_longo:.0f} anos** ({taxa_longa:.1f}% a.a.), "
                    f"configurando uma curva invertida. "
                    f"Historicamente, esse padrão antecipa desaceleração econômica — "
                    f"o mercado precifica cortes de juros à frente."
                )
            elif spread > 1.0:
                forma = "Curva normal (inclinada)"
                cor   = "#00D4AA"
                analise = (
                    f"A taxa longa ({taxa_longa:.1f}% a.a. em {prazo_longo:.0f} anos) "
                    f"supera a taxa curta ({taxa_curta:.1f}% a.a. em {prazo_curto:.0f} ano(s)) "
                    f"em **{spread:.2f}pp**. "
                    f"O prêmio de prazo positivo indica que o mercado exige compensação "
                    f"pela incerteza de longo prazo — sinal típico de expectativa de crescimento."
                )
            else:
                forma = "Curva flat"
                cor   = "#FFB800"
                analise = (
                    f"O spread entre o prazo longo ({taxa_longa:.1f}% a.a.) "
                    f"e o curto ({taxa_curta:.1f}% a.a.) é de apenas **{spread:+.2f}pp**, "
                    f"configurando uma curva essencialmente plana. "
                    f"Esse padrão reflete incerteza sobre a trajetória dos juros — "
                    f"o mercado não precifica com clareza afrouxamento nem aperto adicional."
                )

            st.markdown(
                f"<div style='background:#1A1D27;border-left:3px solid {cor};"
                f"border-radius:0 8px 8px 0;padding:12px 14px;margin-top:8px'>"
                f"<span style='color:{cor};font-weight:700;font-size:1rem'>{forma}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown(analise)

        if not df_ipca.empty:
            taxa_real_curta = df_ipca.iloc[0]["Taxa Venda Manha"]
            taxa_real_longa = df_ipca.iloc[-1]["Taxa Venda Manha"]
            prazo_real_longo = round(df_ipca.iloc[-1]["Prazo_Anos"], 0)

            # Juro real: contexto histórico
            if taxa_real_longa > 7:
                nivel_real = "muito elevado — acima da média histórica brasileira (~5-6%)"
                cor_real   = "#FF4B6E"
            elif taxa_real_longa > 5:
                nivel_real = "elevado — ainda restritivo para investimentos de longo prazo"
                cor_real   = "#FFB800"
            else:
                nivel_real = "em patamar mais neutro"
                cor_real   = "#00D4AA"

            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Juro real longo (IPCA+)",
                      f"{taxa_real_longa:.2f}% a.a.",
                      delta=f"Prazo: {prazo_real_longo:.0f} anos · Curto: {taxa_real_curta:.1f}%",
                      delta_color="off")
            st.markdown(
                f"<div style='background:#1A1D27;border-left:3px solid {cor_real};"
                f"border-radius:0 8px 8px 0;padding:10px 14px;margin-top:4px'>"
                f"<span style='color:{cor_real};font-size:0.85rem'>"
                f"O juro real de longo prazo está em {nivel_real}. "
                f"Isso encarece o crédito, comprime o investimento produtivo "
                f"e eleva o custo de rolagem da dívida pública."
                f"</span></div>",
                unsafe_allow_html=True
            )

        st.caption("Fonte: Tesouro Transparente · Atualização diária")

    st.markdown("---")


# =============================================================================
# RODAPÉ
# =============================================================================
rodape()
