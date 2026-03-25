# =============================================================================
# pages/17_Agropecuaria.py — Setor Agropecuario
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

from utils.dados  import get_lspa, get_pam_culturas, get_agro_indicadores, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Agropecuaria | BI Economico", page_icon="🌾", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2018, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2010, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Periodo", options=anos,
                                         value=(2018, datetime.today().year))
sidebar_padrao(pagina_atual="Agropecuaria", filtros_extra=_filtros)

with st.spinner("Carregando dados agropecuarios..."):
    df_lspa  = get_lspa()
    df_pam, df_pam_hist = get_pam_culturas()
    df_agro  = get_agro_indicadores()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_lf  = filtrar(df_lspa)
df_af  = filtrar(df_agro)

def ultimo_val(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    return round(float(s.iloc[-1]), 2) if not s.empty else None

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
    🌾 Setor Agropecuario
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Safra · Valor Bruto da Producao · Balanca Comercial · Top Culturas
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
# Producao total do ultimo ano disponivel (PAM)
prod_v = None
if not df_pam.empty and "Producao_t" in df_pam.columns:
    _area_s = df_lspa["Area_Plantada"].dropna() if not df_lspa.empty and "Area_Plantada" in df_lspa.columns else None
    prod_v = round(float(_area_s.iloc[-1])/1000, 1) if _area_s is not None and not _area_s.empty else None
area_v    = ultimo_val(df_lspa, "Area_Plantada")
vbp_v     = ultimo_val(df_agro, "VBP")
saldo_v   = ultimo_val(df_agro, "Saldo_Agro")
exp_v     = ultimo_val(df_agro, "Exp_Agro")

prod_12m  = var_12m_col(df_lspa, "Producao")
vbp_12m   = var_12m_col(df_agro, "VBP")
saldo_12m = var_12m_col(df_agro, "Saldo_Agro")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Producao Total (Mi t)",
              f"{prod_v/1000:,.0f}" if prod_v else "—",
              delta=f"{prod_12m:+.1f}% 12m" if prod_12m else None)
with c2:
    st.metric("VBP Agro (R$ bi)",
              f"R$ {vbp_v:,.1f} bi" if vbp_v else "—",
              delta=None)
with c3:
    st.metric("Exportacoes Agro (US$ mi acum.)",
              f"US$ {exp_v:,.0f} mi" if exp_v else "—")
with c4:
    st.metric("Saldo Agro (US$ mi acum.)",
              f"US$ {saldo_v:,.0f} mi" if saldo_v else "—")

# =============================================================================
# BLOCO 1 — SAFRA: PRODUCAO E AREA
# =============================================================================
st.markdown("### 🌱 Safra Agricola — Producao e Area Plantada")
st.caption("Levantamento Sistematico da Producao Agricola (LSPA) · IBGE · Estimativa mensal")

col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Evolucao das principais culturas (Mi toneladas)")
    CORES_CULT = {"Soja":"#00D4AA","Milho":"#FFB800","Cana":"#00D4FF",
                  "Trigo":"#A78BFA","Arroz":"#FF4B6E","Algodao":"#F59E0B"}
    if not df_pam_hist.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        ax2b = ax.twinx()
        for col in ["Soja","Milho","Trigo","Arroz","Algodao"]:
            if col in df_pam_hist.columns:
                s = df_pam_hist[col].dropna() / 1e6
                ax.plot(s.index, s.values, color=CORES_CULT[col], lw=1.8,
                        marker="o", markersize=4, label=col)
        if "Cana" in df_pam_hist.columns:
            s_cana = df_pam_hist["Cana"].dropna() / 1e6
            ax2b.plot(s_cana.index, s_cana.values, color=CORES_CULT["Cana"],
                      lw=1.5, ls="--", marker="s", markersize=3, label="Cana (dir)")
            ax2b.set_ylabel("Cana (Mi t)", color=CORES_CULT["Cana"], fontsize=8)
            ax2b.tick_params(colors="#AAAAAA", labelsize=8)
        ax.set_ylabel("Mi toneladas", color="#AAAAAA", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2b.get_legend_handles_labels()
        ax.legend(lines1+lines2, labels1+labels2, fontsize=7,
                  facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", ncol=3)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados historicos de culturas nao disponiveis.")
with col2:
    st.markdown("#### Area plantada (mil hectares)")
    s_area_raw = df_lspa["Area_Plantada"].dropna() / 1000 if not df_lspa.empty and "Area_Plantada" in df_lspa.columns else None
    s_area_raw = s_area_raw[s_area_raw.index >= dt_ini] if s_area_raw is not None else None
    if s_area_raw is not None and not s_area_raw.empty:
        s2 = s_area_raw
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
        ax2.plot(s2.index, s2.values, color="#FFB800", lw=2)
        ax2.fill_between(s2.index, s2.values, s2.min()*0.98, alpha=0.08, color="#FFB800")
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:,.0f}"))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        ax2.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax2.set_ylabel("Mil hectares", color="#AAAAAA", fontsize=9)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig2); plt.close()

# Narrativa safra
if not df_lspa.empty and "Producao" in df_lspa.columns:
    s_prod = df_lspa["Producao"].dropna()
    s_area = df_lspa["Area_Plantada"].dropna() if "Area_Plantada" in df_lspa.columns else None
    if len(s_prod) >= 13:
        prod_atual = float(s_prod.iloc[-1]) / 1e6
        prod_ant   = float(s_prod.iloc[-13]) / 1e6
        var_p      = round((prod_atual/prod_ant - 1)*100, 1)
        tend = "crescimento" if var_p > 0 else "reducao"
        txt_area = ""
        if s_area is not None and len(s_area) >= 13:
            area_var = round((float(s_area.iloc[-1])/float(s_area.iloc[-13]) - 1)*100, 1)
            if area_var > 0:
                txt_area = f"A area plantada cresceu **{area_var:+.1f}%**, refletindo expansao da fronteira agricola. "
            else:
                txt_area = f"A area plantada recuou **{area_var:+.1f}%** — ganhos de produtividade sustentam o volume. "
        st.info(
            "**Leitura da safra:**\n\n"
            f"A producao agricola estimada acumula **{var_p:+.1f}%** em 12 meses, "
            f"indicando {tend} em relacao ao ano anterior. " + txt_area +
            "O Brasil e o maior exportador mundial de soja, cafe e acucar, "
            "e o segundo maior de milho — variacao na safra impacta diretamente "
            "a balanca comercial e o nivel de precos de alimentos."
        )

st.markdown("---")

# =============================================================================
# BLOCO 2 — TOP CULTURAS + VBP
# =============================================================================
st.markdown("### 🌽 Principais Culturas e Valor Bruto da Producao")
st.caption("PAM/IBGE: producao em toneladas (ultimo ano) · VBP BCB/SGS 7415: receita bruta do agronegocio")

col3, col4 = st.columns([5, 5])

with col3:
    st.markdown("#### Top 10 culturas por producao (toneladas)")
    if not df_pam.empty:
        top10 = df_pam.head(10).copy()
        ano_ref = top10["Ano"].iloc[0] if not top10.empty else ""
        st.caption(f"Referencia: {ano_ref}")
        fig3, ax3 = plt.subplots(figsize=(9, 5))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        cores3 = ["#00D4AA","#FFB800","#00D4FF","#FF4B6E","#A78BFA",
                  "#F59E0B","#34D399","#F87171","#60A5FA","#FBBF24"]
        bars = ax3.barh(top10["Cultura"][::-1],
                        top10["Producao_t"][::-1]/1e6,
                        color=cores3[::-1], height=0.6)
        for bar, val in zip(bars, top10["Producao_t"][::-1]/1e6):
            ax3.text(val + 1, bar.get_y() + bar.get_height()/2,
                     f"{val:,.0f} Mi t", va="center", color="#CCC", fontsize=7.5)
        ax3.set_xlabel("Milhoes de toneladas", color="#AAAAAA", fontsize=8)
        ax3.tick_params(colors="#AAAAAA", labelsize=8)
        ax3.grid(True, color="#FFF", alpha=0.04, lw=0.5, axis="x")
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.tight_layout(); st.pyplot(fig3); plt.close()

        # Narrativa culturas
        lider = top10.iloc[0]
        segundo = top10.iloc[1]
        st.info(
            "**Composicao da producao agricola brasileira:**\n\n"
            f"**{lider['Cultura']}** lidera com **{lider['Producao_t']/1e6:,.0f} milhoes de toneladas**, "
            f"seguida de **{segundo['Cultura']}** com **{segundo['Producao_t']/1e6:,.0f} Mi t**. "
            "Soja e milho juntos representam mais de 70% do volume total colhido e sao "
            "os principais produtos de exportacao do agronegocio brasileiro."
        )
    else:
        st.info("Dados de culturas nao disponiveis.")

with col4:
    st.markdown("#### VBP — Valor Bruto da Producao (R$ bi)")
    if not df_af.empty and "VBP" in df_af.columns:
        s4 = df_af["VBP"].dropna()
        fig4, ax4 = plt.subplots(figsize=(9, 5))
        fig4.patch.set_facecolor("#0F1117"); ax4.set_facecolor("#0F1117")
        ax4.plot(s4.index, s4.values, color="#A78BFA", lw=2)
        ax4.fill_between(s4.index, s4.values, s4.min()*0.98, alpha=0.08, color="#A78BFA")
        ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:,.0f}bi"))
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax4.tick_params(colors="#AAAAAA", labelsize=9)
        ax4.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        for sp in ax4.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig4); plt.close()

        if vbp_v and vbp_12m is not None:
            tend_vbp = "crescimento" if vbp_12m > 0 else "queda"
            st.info(
                f"**VBP em R$ {vbp_v:,.1f} bi**, com {tend_vbp} de **{vbp_12m:+.1f}%** em 12 meses. "
                "O VBP mede a receita bruta do agronegocio — reflete tanto volume produzido "
                "quanto precos recebidos pelo produtor. Alta do dolar amplifica o VBP em reais."
            )
    else:
        st.info("Dados de VBP nao disponiveis.")

st.markdown("---")

# =============================================================================
# BLOCO 3 — BALANCA COMERCIAL AGRO
# =============================================================================
st.markdown("### 🚢 Balanca Comercial do Agronegocio")
st.caption("Exportacoes, importacoes e saldo acumulado em 12 meses · Fonte: MAPA via BCB/SGS · US$ milhoes")

col5, col6 = st.columns([6, 4])

with col5:
    st.markdown("#### Exportacoes e importacoes agro (US$ mi acum. 12m)")
    if not df_af.empty and "Exp_Agro" in df_af.columns:
        fig5, ax5 = plt.subplots(figsize=(10, 4))
        fig5.patch.set_facecolor("#0F1117"); ax5.set_facecolor("#0F1117")
        if "Exp_Agro" in df_af.columns:
            s = df_af["Exp_Agro"].dropna()
            ax5.plot(s.index, s.values, color="#FF4B6E", lw=2, label="Importacoes")
        if "Imp_Agro" in df_af.columns:
            s2 = df_af["Imp_Agro"].dropna()
            ax5.plot(s2.index, s2.values, color="#00D4AA", lw=2, label="Exportacoes")
        ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"US${x/1000:,.0f}bi"))
        ax5.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax5.tick_params(colors="#AAAAAA", labelsize=9)
        ax5.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        ax5.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC")
        for sp in ax5.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig5); plt.close()
    else:
        st.info("Dados de balanca comercial nao disponiveis.")

with col6:
    st.markdown("#### Saldo agro acumulado 12m (US$ mi)")
    if not df_af.empty and "Saldo_Agro" in df_af.columns:
        s6 = df_af["Saldo_Agro"].dropna()
        fig6, ax6 = plt.subplots(figsize=(6, 4))
        fig6.patch.set_facecolor("#0F1117"); ax6.set_facecolor("#0F1117")
        cors6 = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in s6.values]
        ax6.bar(s6.index, s6.values/1000, color=cors6, width=20)
        ax6.axhline(0, color="#555", lw=0.8)
        ax6.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"US${x:,.0f}bi"))
        ax6.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax6.tick_params(colors="#AAAAAA", labelsize=8)
        ax6.grid(True, color="#FFF", alpha=0.04, lw=0.5)
        for sp in ax6.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig6); plt.close()

# Narrativa balanca
if exp_v and saldo_v:
    imp_v = ultimo_val(df_agro, "Imp_Agro")
    cobert = round(exp_v / imp_v * 100, 1) if imp_v else None
    txt_cob = f"As exportacoes cobrem **{cobert:.0f}%** das importacoes. " if cobert else ""
    st.info(
        "**Leitura da balanca comercial do agro:**\n\n"
        f"O saldo acumulado de **US$ {saldo_v/1000:,.1f} bi** em 12 meses mostra que o agronegocio "
        f"e o principal gerador de superavit comercial do Brasil. " + txt_cob +
        "O agronegocio representa mais de 50% das exportacoes totais do pais — "
        "o nivel do dolar amplifica diretamente a receita em reais dos exportadores."
    )

st.markdown("---")

# =============================================================================
# CARDS DIDATICOS
# =============================================================================
st.markdown("#### Como interpretar estes indicadores")
ca, cb, cc = st.columns(3)

with ca:
    prod_txt = f"{prod_v/1e6:,.0f} Mi t" if prod_v else "—"
    st.markdown(
        "**🌱 LSPA e PAM — Safra e Culturas**\n\n"
        "O LSPA (IBGE) e o levantamento mensal da safra — estima producao antes da colheita. "
        "O PAM consolida os dados anuais definitivos por cultura e municipio.\n\n"
        "**Por que importa:**\n"
        "- Safra recorde → exportacoes maiores → real mais forte\n"
        "- Safra fraca → escassez → alta nos precos de alimentos → pressao no IPCA\n"
        "- Clima e pragas sao os principais riscos de curto prazo\n\n"
        f"Producao estimada atual: **{prod_txt}**"
    )

with cb:
    vbp_txt = f"R$ {vbp_v:,.1f} bi" if vbp_v else "—"
    st.markdown(
        "**💰 VBP — Valor Bruto da Producao**\n\n"
        "O VBP mede a receita bruta total do setor agropecuario. "
        "Diferente do volume fisico, captura o efeito dos precos recebidos.\n\n"
        "**Drivers do VBP:**\n"
        "- Volume da safra (clima, insumos, area plantada)\n"
        "- Precos internacionais das commodities\n"
        "- Taxa de cambio (dolar alto = VBP maior em reais)\n\n"
        f"VBP atual: **{vbp_txt}**\n\n"
        "Alta do VBP com dolar forte pode mascarar queda de volume fisico."
    )

with cc:
    saldo_txt = f"US$ {saldo_v/1000:,.1f} bi" if saldo_v else "—"
    st.markdown(
        "**🚢 Balanca Comercial Agro**\n\n"
        "O agronegocio e o pilar do superavit comercial brasileiro. "
        "Um saldo positivo expressivo financia importacoes industriais e "
        "sustenta as reservas internacionais.\n\n"
        "**Como o agro afeta o cambio:**\n"
        "- Safra recorde → mais exportacoes → oferta de dolares sobe → real se valoriza\n"
        "- Exportadores vendem dolares antecipando colheita → pressao sobre o USD/BRL\n"
        "- Concentracao sazonal: maior fluxo de mar a jun (colheita soja/milho)\n\n"
        f"Saldo acumulado 12m: **{saldo_txt}**"
    )

rodape()
