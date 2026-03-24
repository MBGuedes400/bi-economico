# =============================================================================
# pages/19_Cambios.py — Câmbios e Paridade de Poder de Compra
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

from utils.dados  import get_cambio, get_cambios_adicionais, get_ppp_data, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Câmbios & PPP | BI Econômico", page_icon="💱", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2015, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2002, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2015, datetime.today().year))
sidebar_padrao(pagina_atual="Cambios", filtros_extra=_filtros)

with st.spinner("Carregando dados cambiais..."):
    df_fx   = get_cambio()
    df_fxad = get_cambios_adicionais()
    df_ppp  = get_ppp_data()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_fxf   = filtrar(df_fx)
df_fxadf = filtrar(df_fxad)
df_pppf  = filtrar(df_ppp)

CORES_FX = {
    "USD_BRL": "#00D4FF",
    "EUR_BRL": "#FFB800",
    "GBP_BRL": "#A78BFA",
    "CNY_BRL": "#00D4AA",
    "JPY_BRL": "#FF4B6E",
    "CHF_BRL": "#F59E0B",
}

NOMES_FX = {
    "USD_BRL": "Dólar (USD)",
    "EUR_BRL": "Euro (EUR)",
    "GBP_BRL": "Libra (GBP)",
    "CNY_BRL": "Yuan (CNY)",
    "JPY_BRL": "Iene (JPY)",
    "CHF_BRL": "Franco Suíço (CHF)",
}

def ultimo_val(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    return round(float(s.iloc[-1]), 4) if not s.empty else None

def var_12m_col(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    if len(s) < 13: return None
    return round((float(s.iloc[-1]) / float(s.iloc[-13]) - 1) * 100, 1)

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    💱 Câmbios & Paridade de Poder de Compra
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    USD · EUR · GBP · CNY · JPY · CHF · Taxa de Câmbio Real · Desalinhamento PPP
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
usd_v  = ultimo_val(df_fx, "USD_BRL")
eur_v  = ultimo_val(df_fxad, "EUR_BRL") or ultimo_val(df_fx, "EUR_BRL")
gbp_v  = ultimo_val(df_fxad, "GBP_BRL") or ultimo_val(df_fx, "GBP_BRL")
cny_v  = ultimo_val(df_fxad, "CNY_BRL")

usd_12m = var_12m_col(df_fx, "USD_BRL")
eur_12m = var_12m_col(df_fxad, "EUR_BRL")

# PPP KPIs
ppp_atual    = None
misalign_v   = None
rer_v        = None
if not df_ppp.empty:
    s_ppp  = df_ppp["E_ppp"].dropna()
    s_rer  = df_ppp["RER"].dropna()
    s_mis  = df_ppp["misalignment"].dropna()
    if not s_ppp.empty:
        ppp_atual  = round(float(s_ppp.iloc[-1]), 2)
    if not s_rer.empty:
        rer_v      = round(float(s_rer.iloc[-1]), 3)
    if not s_mis.empty:
        misalign_v = round(float(s_mis.iloc[-1]), 3)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("USD/BRL", f"R$ {usd_v:.4f}" if usd_v else "—",
              delta=f"{usd_12m:+.1f}% 12m" if usd_12m else None)
with c2:
    st.metric("EUR/BRL", f"R$ {eur_v:.4f}" if eur_v else "—")
with c3:
    st.metric("GBP/BRL", f"R$ {gbp_v:.4f}" if gbp_v else "—")
with c4:
    st.metric("USD/BRL PPP", f"R$ {ppp_atual:.2f}" if ppp_atual else "—",
              delta="câmbio de equilíbrio" if ppp_atual else None,
              delta_color="off")
with c5:
    if misalign_v is not None:
        sinal_mis = "subvalorizado" if misalign_v > 0 else "sobrevalorizado"
        st.metric("Desalinhamento RER",
                  f"{misalign_v:+.3f}",
                  delta=sinal_mis,
                  delta_color="normal" if misalign_v > 0 else "inverse")
    else:
        st.metric("Desalinhamento RER", "—")

st.markdown("---")

# =============================================================================
# BLOCO 1 — CÂMBIOS MÚLTIPLOS BASE 100
# =============================================================================
st.markdown("### 🌍 Câmbios Múltiplos — Evolução Comparada")
st.caption("Base 100 = primeiro mês do período · Permite comparar valorização/desvalorização relativa do BRL")

col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Evolução base 100")
    # Combinar USD (de df_fx) com outros (de df_fxad)
    df_todos = pd.DataFrame()
    if not df_fxf.empty and "USD_BRL" in df_fxf.columns:
        df_todos["USD_BRL"] = df_fxf["USD_BRL"]
    if not df_fxadf.empty:
        for col in ["EUR_BRL","GBP_BRL","CNY_BRL","JPY_BRL","CHF_BRL"]:
            if col in df_fxadf.columns:
                df_todos[col] = df_fxadf[col]

    if not df_todos.empty:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        for col in df_todos.columns:
            s = df_todos[col].dropna()
            if s.empty or s.iloc[0] == 0: continue
            b100 = s / s.iloc[0] * 100
            ax.plot(b100.index, b100.values,
                    color=CORES_FX.get(col, "#AAA"), lw=1.8,
                    label=NOMES_FX.get(col, col))
        ax.axhline(100, color="#555", lw=0.8, ls="--")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.set_ylabel("Base 100", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=7, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9, ncol=2)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados de câmbio não disponíveis.")

with col2:
    st.markdown("#### Variação 12 meses (%)")
    vars12_fx = {}
    if not df_fx.empty and "USD_BRL" in df_fx.columns:
        v = var_12m_col(df_fx, "USD_BRL")
        if v is not None: vars12_fx["USD_BRL"] = v
    if not df_fxad.empty:
        for col in ["EUR_BRL","GBP_BRL","CNY_BRL","JPY_BRL","CHF_BRL"]:
            v = var_12m_col(df_fxad, col)
            if v is not None: vars12_fx[col] = v

    if vars12_fx:
        ord_v = dict(sorted(vars12_fx.items(), key=lambda x: x[1]))
        fig2, ax2 = plt.subplots(figsize=(6, 4.5))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        nomes = [NOMES_FX.get(k, k) for k in ord_v]
        vals  = list(ord_v.values())
        cors  = ["#FF4B6E" if v >= 0 else "#00D4AA" for v in vals]
        ax2.barh(nomes, vals, color=cors, height=0.6)
        for i, (n, v) in enumerate(zip(nomes, vals)):
            ax2.text(v + (0.2 if v >= 0 else -0.2), i, f"{v:+.1f}%",
                     va="center", ha="left" if v >= 0 else "right",
                     color="#CCC", fontsize=8)
        ax2.axvline(0, color="#555", lw=0.8)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.grid(True, color="#FFF", alpha=0.04, lw=0.5, axis="x")
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        plt.tight_layout(); st.pyplot(fig2); plt.close()

# Narrativa câmbios
if vars12_fx:
    mais_valorizou = min(vars12_fx, key=vars12_fx.get)
    mais_desvalorizou = max(vars12_fx, key=vars12_fx.get)
    txt_usd = ""
    if "USD_BRL" in vars12_fx:
        v = vars12_fx["USD_BRL"]
        if v > 0:
            txt_usd = f"O **dólar subiu {v:+.1f}%** em 12 meses — real mais fraco encarece importações e pressiona o IPCA de bens industrializados. "
        else:
            txt_usd = f"O **dólar caiu {v:+.1f}%** em 12 meses — real mais forte barateia importações e alivia pressão inflacionária. "
    st.info(
        "**Leitura dos câmbios (12 meses):**\n\n"
        + txt_usd
        + f"Entre as moedas monitoradas, o BRL se valorizou mais frente a **{NOMES_FX.get(mais_valorizou, mais_valorizou)}** "
        + f"e se desvalorizou mais frente a **{NOMES_FX.get(mais_desvalorizou, mais_desvalorizou)}**. "
        + "Alta generalizada do dólar globalmente costuma refletir aversão ao risco — capital migra para ativos seguros americanos."
    )

st.markdown("---")

# =============================================================================
# BLOCO 2 — PPP: CÂMBIO NOMINAL vs EQUILÍBRIO
# =============================================================================
st.markdown("### ⚖️ Paridade de Poder de Compra (PPP)")
st.caption("Câmbio de equilíbrio calculado pelo diferencial de inflação Brasil vs EUA · Fonte: BCB/SGS")

if not df_ppp.empty:
    col3, col4 = st.columns([6, 4])

    with col3:
        st.markdown("#### USD/BRL Nominal vs Câmbio PPP")
        st.caption("Linha verde = onde o câmbio 'deveria' estar pela teoria PPP")
        df_pppf2 = filtrar(df_ppp)
        if not df_pppf2.empty:
            fig3, ax3 = plt.subplots(figsize=(10, 4.5))
            fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
            s_e   = df_pppf2["E"].dropna()
            s_ppp = df_pppf2["E_ppp"].dropna()
            idx   = s_e.index.intersection(s_ppp.index)
            if len(idx) > 0:
                ax3.plot(idx, s_e.loc[idx].values,
                         color="#00D4FF", lw=2, label="USD/BRL Nominal")
                ax3.plot(idx, s_ppp.loc[idx].values,
                         color="#00D4AA", lw=2, ls="--", label="Câmbio PPP (equilíbrio)")
                # Área de sub/sobrevalorização
                ax3.fill_between(idx,
                                 s_e.loc[idx].values, s_ppp.loc[idx].values,
                                 where=(s_e.loc[idx].values > s_ppp.loc[idx].values),
                                 alpha=0.12, color="#FF4B6E", label="BRL subvalorizado")
                ax3.fill_between(idx,
                                 s_e.loc[idx].values, s_ppp.loc[idx].values,
                                 where=(s_e.loc[idx].values <= s_ppp.loc[idx].values),
                                 alpha=0.12, color="#00D4AA", label="BRL sobrevalorizado")
            ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R$ {x:.2f}"))
            ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
            ax3.tick_params(colors="#AAAAAA", labelsize=9)
            ax3.legend(fontsize=7, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            for sp in ax3.spines.values(): sp.set_edgecolor("#333")
            plt.xticks(rotation=30, ha="right"); plt.tight_layout()
            st.pyplot(fig3); plt.close()

    with col4:
        st.markdown("#### Taxa de Câmbio Real (RER)")
        st.caption("Câmbio ajustado pelo diferencial de inflação · Linha = média histórica ± 1σ")
        if not df_pppf2.empty and "RER" in df_pppf2.columns:
            s_rer  = df_pppf2["RER"].dropna()
            media  = float(df_ppp["RER"].mean())
            std    = float(df_ppp["RER"].std())
            fig4, ax4 = plt.subplots(figsize=(6, 4.5))
            fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
            ax4.plot(s_rer.index, s_rer.values, color="#A78BFA", lw=2, label="RER")
            ax4.axhline(media,       color="#FFB800", lw=1.2, ls="--", label=f"Média {media:.3f}")
            ax4.axhline(media+std,   color="#FF4B6E", lw=0.8, ls=":",  label=f"+1σ {media+std:.3f}")
            ax4.axhline(media-std,   color="#00D4AA", lw=0.8, ls=":",  label=f"-1σ {media-std:.3f}")
            ax4.fill_between(s_rer.index, media-std, media+std, alpha=0.05, color="#FFB800")
            ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.3f}"))
            ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            ax4.tick_params(colors="#AAAAAA", labelsize=8)
            ax4.grid(True, color="#FFF", alpha=0.04, lw=0.5)
            ax4.legend(fontsize=7, facecolor="#1A1D27", edgecolor="#333",
                       labelcolor="#CCC", framealpha=0.9)
            for sp in ax4.spines.values(): sp.set_edgecolor("#333")
            plt.xticks(rotation=30, ha="right"); plt.tight_layout()
            st.pyplot(fig4); plt.close()

    # Narrativa PPP
    if usd_v and ppp_atual and misalign_v is not None:
        diff_pct = round((usd_v - ppp_atual) / ppp_atual * 100, 1)
        if diff_pct > 5:
            situacao = f"**subvalorizado em {diff_pct:.1f}%** em relação ao equilíbrio PPP"
            implicacao = "o real está barato — exportações brasileiras ficam mais competitivas, mas importações encarecem"
        elif diff_pct < -5:
            situacao = f"**sobrevalorizado em {abs(diff_pct):.1f}%** em relação ao equilíbrio PPP"
            implicacao = "o real está caro — importações ficam baratas, mas exportações perdem competitividade"
        else:
            situacao = "próximo ao equilíbrio PPP"
            implicacao = "câmbio alinhado com os fundamentos de longo prazo"

        st.info(
            f"**Análise PPP:**\n\n"
            f"Com USD/BRL em **R$ {usd_v:.4f}** e câmbio PPP em **R$ {ppp_atual:.2f}**, "
            f"o real está {situacao}. Isso significa que {implicacao}.\n\n"
            f"A **Taxa de Câmbio Real (RER)** em **{rer_v:.3f}** "
            + ("está **acima** da média histórica — real relativamente desvalorizado. " if rer_v and rer_v > float(df_ppp['rer_media'].iloc[-1]) else
               "está **abaixo** da média histórica — real relativamente valorizado. ")
            + "O desalinhamento se reverte historicamente via inflação diferencial ou ajuste nominal do câmbio."
        )

    st.markdown("---")

    # =============================================================================
    # BLOCO 3 — DESALINHAMENTO CAMBIAL
    # =============================================================================
    st.markdown("### 📉 Desalinhamento Cambial")
    st.caption("(+) Real subvalorizado — câmbio acima do equilíbrio · (−) Real sobrevalorizado — câmbio abaixo do equilíbrio")

    if not df_pppf2.empty and "misalignment" in df_pppf2.columns:
        fig5, ax5 = plt.subplots(figsize=(14, 4))
        fig5.patch.set_facecolor("#0F1117"); ax5.set_facecolor("#0F1117")
        s_mis = df_pppf2["misalignment"].dropna()
        std_his = float(df_ppp["rer_std"].iloc[-1])

        ax5.fill_between(s_mis.index, 0, s_mis.values,
                         where=(s_mis.values >= 0),
                         color="#FF4B6E", alpha=0.4, label="Subvalorizado (BRL fraco)")
        ax5.fill_between(s_mis.index, 0, s_mis.values,
                         where=(s_mis.values < 0),
                         color="#00D4AA", alpha=0.4, label="Sobrevalorizado (BRL forte)")
        ax5.plot(s_mis.index, s_mis.values, color="#A78BFA", lw=1.5)
        ax5.axhline(0,           color="#555", lw=1.0, ls="--")
        ax5.axhline(std_his,     color="#FF4B6E", lw=0.7, ls=":", alpha=0.7, label=f"+1σ ({std_his:.3f})")
        ax5.axhline(-std_his,    color="#00D4AA", lw=0.7, ls=":", alpha=0.7, label=f"-1σ (-{std_his:.3f})")
        ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:+.3f}"))
        ax5.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax5.tick_params(colors="#AAAAAA", labelsize=9)
        ax5.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax5.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                   labelcolor="#CCC", framealpha=0.9, loc="upper left")
        for sp in ax5.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig5); plt.close()

        # Narrativa desalinhamento
        if misalign_v is not None:
            meses_desalinhado = 0
            for v in reversed(s_mis.values):
                if (misalign_v > 0 and v > 0) or (misalign_v < 0 and v < 0):
                    meses_desalinhado += 1
                else:
                    break
            extremo = abs(misalign_v) > std_his
            txt_dir = "subvalorizado" if misalign_v > 0 else "sobrevalorizado"
            txt_ext = " — **nível extremo**, fora do intervalo de 1 desvio padrão histórico" if extremo else " — dentro do intervalo histórico normal"
            st.info(
                f"**Desalinhamento atual: {misalign_v:+.3f}** — real **{txt_dir}**{txt_ext}. "
                f"O BRL permanece nessa condição há **{meses_desalinhado} meses consecutivos**.\n\n"
                "Desalinhamentos persistentes tendem a se corrigir: quando o real está muito desvalorizado, "
                "o diferencial de inflação (Brasil > EUA) gradualmente apreciam o câmbio nominal. "
                "Quando está sobrevalorizado, choques externos ou deterioração fiscal costumam forçar a correção."
            )
else:
    st.info("Dados para análise PPP não disponíveis. Verifique a conexão com o BCB.")

st.markdown("---")

# =============================================================================
# CARDS DIDÁTICOS
# =============================================================================
st.markdown("#### Como interpretar estes indicadores")
ca, cb, cc = st.columns(3)

usd_txt = f"R$ {usd_v:.4f}" if usd_v else "—"
ppp_txt = f"R$ {ppp_atual:.2f}" if ppp_atual else "—"
mis_txt = f"{misalign_v:+.3f}" if misalign_v is not None else "—"

with ca:
    st.markdown(
        "**💱 Câmbio Nominal e Múltiplos**\n\n"
        "O câmbio nominal mede quantos reais compram 1 unidade da moeda estrangeira. "
        "Monitorar múltiplas moedas revela se a desvalorização do BRL é generalizada "
        "(dólar global forte) ou específica ao Brasil.\n\n"
        "**Impactos de um real fraco:**\n"
        "- Exportações mais competitivas\n"
        "- Importações encarecem → pressão no IPCA\n"
        "- Dívida externa fica mais cara\n"
        "- Fuga de capital estrangeiro\n\n"
        f"USD/BRL atual: **{usd_txt}**"
    )

with cb:
    st.markdown(
        "**⚖️ Paridade de Poder de Compra (PPP)**\n\n"
        "A teoria PPP diz que o câmbio de equilíbrio é aquele que iguala o poder de compra "
        "entre dois países. Se a inflação brasileira supera a americana, o real tende a se "
        "desvalorizar para compensar.\n\n"
        "**Fórmula:** E_PPP = E₀ × (P_Brasil / P_EUA)\n\n"
        f"Câmbio nominal: **{usd_txt}**\n\n"
        f"Câmbio PPP: **{ppp_txt}**\n\n"
        "Se nominal > PPP → real subvalorizado. Se nominal < PPP → real sobrevalorizado."
    )

with cc:
    std_txt = f"{float(df_ppp['rer_std'].iloc[-1]):.3f}" if not df_ppp.empty else "—"
    st.markdown(
        "**📉 Taxa de Câmbio Real e Desalinhamento**\n\n"
        "A Taxa de Câmbio Real (RER) remove o efeito da inflação do câmbio nominal. "
        "É a medida mais precisa de competitividade.\n\n"
        "**Desalinhamento** = RER atual − RER média histórica\n\n"
        f"Desalinhamento atual: **{mis_txt}**\n\n"
        f"Intervalo histórico ±1σ: **±{std_txt}**\n\n"
        "Desalinhamentos além de ±1σ indicam condição extrema que historicamente "
        "tende a se reverter nos meses seguintes."
    )

rodape()
