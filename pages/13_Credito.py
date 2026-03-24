# =============================================================================
# pages/12_Credito.py — Credito & Inadimplencia
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

from utils.dados  import get_credito_sfn, get_juros, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Crédito | BI Econômico", page_icon="🏧", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2019, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2019, datetime.today().year))
sidebar_padrao(pagina_atual="Credito", filtros_extra=_filtros)

with st.spinner("Carregando crédito SFN..."):
    df_c  = get_credito_sfn()
    df_jr = get_juros()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty:
        return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_cf = filtrar(df_c)

def fmt_tri(v):
    if v is None: return "—"
    if v >= 1000: return f"R$ {v/1000:.2f} tri"
    return f"R$ {v:.0f} bi"

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
    🏧 Crédito & Inadimplência
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Operações de crédito SFN · Taxas por modalidade · Inadimplência acima de 90 dias
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
ct_v, ct_d   = ultimo_valor(df_c, "Credito_Total")
pf_v, _      = ultimo_valor(df_c, "Credito_PF")
tx_v, _      = ultimo_valor(df_c, "Taxa_Media_Total")
inad_v, _    = ultimo_valor(df_c, "Inadimplencia_Total")
ct_var       = var_12m(df_c, "Credito_Total")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Crédito Total", fmt_tri(ct_v),
              delta=f"{ct_var:+.1f}% em 12m" if ct_var else (ct_d.strftime("%b/%Y") if ct_d else None),
              delta_color="normal" if ct_var else "off")
with c2:
    st.metric("Crédito PF", fmt_tri(pf_v))
with c3:
    st.metric("Taxa Média Total", f"{tx_v:.1f}% a.a." if tx_v else "—")
with c4:
    st.metric("Inadimplência", f"{inad_v:.1f}%" if inad_v else "—",
              delta="acima de 90 dias", delta_color="off")

st.markdown("---")

# =============================================================================
# ANALISE DIDATICA
# =============================================================================
selic_v, _ = ultimo_valor(df_jr, "Selic_Meta") if not df_jr.empty else (None, None)
inad_pf, _ = ultimo_valor(df_c, "Inadimplencia_PF")
inad_pj, _ = ultimo_valor(df_c, "Inadimplencia_PJ")

if ct_v and tx_v and inad_v:
    spread = round(tx_v - (selic_v or 0), 1) if selic_v else None
    alerta = inad_v > 4.0
    tendencia_inad = ""
    s_inad = df_c["Inadimplencia_Total"].dropna() if not df_c.empty and "Inadimplencia_Total" in df_c.columns else pd.Series()
    if len(s_inad) >= 4:
        tendencia_inad = "em alta" if s_inad.iloc[-1] > s_inad.iloc[-4] else "em queda"

    if alerta:
        st.warning(
            f"**⚠️ Atenção:** inadimplência em {inad_v:.1f}% — acima de 4% requer monitoramento."
        )
    else:
        st.info(
            f"**Inadimplência** em {inad_v:.1f}% — dentro da normalidade histórica (2–4%)."
        )

    st.info(
        f"**Leitura do crédito**\n\n"
        f"O estoque total de crédito do SFN alcança **{fmt_tri(ct_v)}** "
        f"({'crescimento de {:.1f}% em 12m'.format(ct_var) if ct_var else 'variação não calculada'}). "
        f"A taxa média total é de **{tx_v:.1f}% a.a.**"
        + (f", representando **spread de {spread:.1f} p.p.** acima da Selic ({selic_v:.1f}%)" if spread else "") +
        f"\n\nA inadimplência acima de 90 dias está em **{inad_v:.1f}%** {tendencia_inad} "
        f"(PF: {inad_pf:.1f}% · PJ: {inad_pj:.1f}%). "
        f"Spread elevado + inadimplência alta = sinal de **estresse financeiro das famílias e empresas**. "
        f"O BCB monitora esse indicador como termômetro da saúde do sistema financeiro."
    )

st.markdown("---")

# =============================================================================
# LINHA 1 — PF vs PJ (esq) + Inadimplencia (dir)
# =============================================================================
col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Operações de Crédito — PF vs PJ (R$ bi)")
    st.caption("O crédito total é a soma PF + PJ. A composição revela qual segmento puxa o crescimento.")
    if not df_cf.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        for col, cor, lbl in [
            ("Credito_Total", "#00D4FF", "Total"),
            ("Credito_PF",    "#FFB800", "Pessoa Física"),
            ("Credito_PJ",    "#00D4AA", "Pessoa Jurídica"),
        ]:
            if col in df_cf.columns:
                s = df_cf[col].dropna()
                ax.plot(s.index, s.values, color=cor, lw=1.8, label=lbl)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x,_: f"R$ {x/1000:.1f} tri" if x >= 1000 else f"R$ {x:.0f} bi"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig); plt.close()

with col2:
    st.markdown("#### Inadimplência (> 90 dias)")
    st.caption("% de contratos com atraso > 90 dias — principal termômetro de estresse do sistema financeiro.")
    if not df_cf.empty:
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        for col, cor, lbl in [
            ("Inadimplencia_Total", "#FF4B6E", "Total"),
            ("Inadimplencia_PF",    "#FFB800", "Pessoa Física"),
            ("Inadimplencia_PJ",    "#00D4AA", "Pessoa Jurídica"),
        ]:
            if col in df_cf.columns:
                s = df_cf[col].dropna()
                ax2.plot(s.index, s.values, color=cor, lw=1.8, label=lbl)
        ax2.axhline(4.0, color="#FF4B6E", lw=0.8, ls="--", alpha=0.5)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        ax2.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

# Análise dinâmica PF vs PJ
pf_v2, _ = ultimo_valor(df_c, "Credito_PF")
pj_v2, _ = ultimo_valor(df_c, "Credito_PJ")
inad_pf2, _ = ultimo_valor(df_c, "Inadimplencia_PF")
inad_pj2, _ = ultimo_valor(df_c, "Inadimplencia_PJ")
if pf_v2 and pj_v2 and ct_v and inad_pf2 and inad_pj2:
    pf_pct = round(pf_v2 / ct_v * 100, 0)
    pj_pct = round(pj_v2 / ct_v * 100, 0)
    domina = "Pessoa Física" if pf_v2 > pj_v2 else "Pessoa Jurídica"
    st.info(
        f"**Leitura PF vs PJ:** a **{domina}** domina o estoque de crédito "
        f"(PF: {pf_pct:.0f}% · PJ: {pj_pct:.0f}%). "
        f"Inadimplência PF ({inad_pf2:.1f}%) tende a ser maior que PJ ({inad_pj2:.1f}%) — "
        f"pessoas físicas têm menor capacidade de renegociação e mais exposição a crédito rotativo "
        f"(cartão, cheque especial) com taxas acima de 100% a.a.\n\n"
        f"Crescimento do crédito PF acima do PIB estimula consumo no curto prazo, "
        f"mas eleva o endividamento das famílias — monitorado pelo BCB via Relatório de Estabilidade Financeira."
    )

# =============================================================================
# LINHA 2 — Taxas medias + Livre vs Direcionado
# =============================================================================
col3, col4 = st.columns([5, 5])

with col3:
    st.markdown("#### Taxas médias de juros (% a.a.)")
    st.caption("Taxa média das operações de crédito — inclui todas as modalidades")
    if not df_cf.empty:
        fig3, ax3 = plt.subplots(figsize=(9, 4))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        for col, cor, lbl in [
            ("Taxa_Media_Total", "#00D4FF", "Total"),
            ("Taxa_Media_PF",    "#FFB800", "PF livre"),
            ("Taxa_Media_PJ",    "#00D4AA", "PJ livre"),
        ]:
            if col in df_cf.columns:
                s = df_cf[col].dropna()
                ax3.plot(s.index, s.values, color=cor, lw=1.8, label=lbl)
        # Linha Selic como referencia
        if not df_jr.empty and "Selic_Meta" in df_jr.columns:
            s_sel = filtrar(df_jr)["Selic_Meta"].dropna()
            ax3.plot(s_sel.index, s_sel.values, color="#A78BFA",
                     lw=1.2, ls="--", label="Selic Meta")
        ax3.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax3.tick_params(colors="#AAAAAA", labelsize=9)
        ax3.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig3); plt.close()

with col4:
    st.markdown("#### Livre vs Direcionado (R$ bi)")
    st.caption("Crédito livre = taxas de mercado. Direcionado = habitação, rural, BNDES")
    if not df_cf.empty:
        fig4, ax4 = plt.subplots(figsize=(9, 4))
        fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
        for col, cor, lbl in [
            ("Credito_Livre", "#00D4FF", "Livre"),
            ("Credito_Dir",   "#FFB800", "Direcionado"),
        ]:
            if col in df_cf.columns:
                s = df_cf[col].dropna()
                ax4.plot(s.index, s.values, color=cor, lw=1.8, label=lbl)
        ax4.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x,_: f"R$ {x/1000:.1f} tri" if x >= 1000 else f"R$ {x:.0f} bi"))
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax4.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax4.tick_params(colors="#AAAAAA", labelsize=9)
        ax4.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax4.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        st.pyplot(fig4); plt.close()

# Análise spread e livre vs direcionado
tx_pf, _ = ultimo_valor(df_c, "Taxa_Media_PF")
tx_pj, _ = ultimo_valor(df_c, "Taxa_Media_PJ")
cl_v, _  = ultimo_valor(df_c, "Credito_Livre")
cd_v, _  = ultimo_valor(df_c, "Credito_Dir")

if tx_v and selic_v and tx_pf and tx_pj and cl_v and cd_v:
    spread_pf = round(tx_pf - selic_v, 1)
    spread_pj = round(tx_pj - selic_v, 1)
    st.info(
        f"**Leitura das taxas e spread:**\n\n"
        f"Com Selic em **{selic_v:.1f}% a.a.**, o spread médio total é de **{spread:.1f} p.p.** — "
        f"**{spread_pf:.1f} p.p.** para PF e **{spread_pj:.1f} p.p.** para PJ. "
        f"O spread brasileiro é um dos maiores do mundo, reflexo de inadimplência estrutural, "
        f"concentração bancária, compulsório e tributos sobre intermediação financeira.\n\n"
        f"Crédito **livre** (R$ {cl_v:.0f} bi) reage à política monetária: cai com Selic alta, sobe com cortes. "
        f"O **direcionado** (R$ {cd_v:.0f} bi) é menos sensível — por isso habitação e agro "
        f"continuam crescendo mesmo em ciclos de aperto monetário."
    )

st.markdown("---")

# =============================================================================
# ANALISE TECNICA — cards enriquecidos
# =============================================================================
st.markdown("#### Entendendo os indicadores de crédito")
ca, cb, cc = st.columns(3)
with ca:
    st.markdown("""
**📌 Crédito/PIB — onde o Brasil está**

O crédito total representa ~55–60% do PIB brasileiro — bem abaixo de economias desenvolvidas:
- **EUA:** ~200% do PIB
- **Japão:** ~300% do PIB
- **Zona do Euro:** ~100% do PIB

Esse gap indica espaço para crescimento, mas também reflete o alto custo do crédito que inibe a demanda. Expansão sustentada impulsa consumo e investimento; expansão excessiva gera superendividamento e inadimplência futura.
""")
with cb:
    st.markdown("""
**📌 O ciclo crédito–inadimplência**

O crédito e a inadimplência formam um ciclo econômico clássico:

1. **Expansão:** economia aquecida → crédito cresce → inadimplência cai
2. **Pico:** superendividamento das famílias → inadimplência começa a subir
3. **Contração:** bancos restringem crédito → consumo cai → atividade desacelera
4. **Ajuste:** famílias desalavancam → inadimplência estabiliza → crédito retoma

O BCB monitora esse ciclo no **Relatório de Estabilidade Financeira** (semestral) e pode usar instrumentos macroprudenciais para suavizar os excessos.
""")
with cc:
    st.markdown("""
**📌 Por que o spread é tão alto no Brasil**

Spread = taxa cobrada − custo de captação (≈ Selic)

Causas estruturais do spread elevado:
- **Inadimplência alta** → bancos embutem prêmio de risco de todos os clientes
- **Concentração bancária** → poucos grandes bancos com poder de precificação
- **Compulsório** → parte dos depósitos fica retida no BCB sem remuneração
- **Cunha tributária** → IOF, PIS/Cofins sobre intermediação financeira
- **Recuperação judicial lenta** → custo de execução de garantias

Fintechs, Open Finance e concorrência têm pressionado o spread para baixo — mas o processo é lento.
""")

rodape()
