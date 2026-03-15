# =============================================================================
# pages/1_Inflacao.py — Painel de Inflação
# =============================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from datetime import datetime

from utils.dados    import (get_inflacao, get_ipca_grupos,
                             get_focus_inflacao12m, get_focus_anual,
                             ultimo_valor, focus_ultimo, METAS_BCB)
from utils.graficos import grafico_ipca_focus, grafico_barras_grupos
from utils.analise  import analisar_ipca
from utils.layout   import rodape, CSS_GLOBAL

st.set_page_config(page_title="Inflação | BI Econômico",
                   page_icon="📊", layout="wide")

st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    import os as _os
    _logo = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "Imagens", "impeto_Branco.png")
    if _os.path.exists(_logo):
        st.image(_logo, use_container_width=True)

    st.markdown("---")
    st.markdown("**Navegação**")
    st.page_link("Home.py",                      label="🏠  Home")
    st.page_link("pages/1_Inflacao.py",          label="📊  Inflação")
    st.page_link("pages/2_Juros.py",             label="🏦  Juros")
    st.page_link("pages/3_Atividade.py",         label="📈  Atividade Econômica")
    st.page_link("pages/4_Mercado_Trabalho.py",  label="👷  Mercado de Trabalho")
    st.page_link("pages/5_Setor_Externo.py",     label="🌎  Setor Externo")

    st.markdown("---")
    st.markdown("**⚙️ Filtros — Inflação**")
    anos = list(range(2016, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider(
        "Período", options=anos,
        value=(2021, datetime.today().year)
    )
    st.markdown("---")
    indices_sel = st.multiselect(
        "Índices para comparativo",
        ["IPCA","IGPM","INPC","IPC_FIPE","IGP_DI"],
        default=["IPCA","IGPM","INPC"]
    )
    acum12m_toggle = st.toggle("Acumulado 12m", value=True)

    st.markdown("---")
    st.caption("Fonte: BCB/SGS | IBGE/SIDRA | BCB/Focus")
    st.caption("Atualizado automaticamente a cada hora.")


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando dados de inflação..."):
    df_infl   = get_inflacao()
    df_grupos = get_ipca_grupos()
    df_f12    = get_focus_inflacao12m()
    df_fa     = get_focus_anual()

# Filtrar período
di = pd.Timestamp(f"{ano_ini}-01-01")
df = pd.Timestamp(f"{ano_fim}-12-31")
df_infl_f   = df_infl[(df_infl.index >= di) & (df_infl.index <= df)] if not df_infl.empty else df_infl
df_grupos_f = df_grupos[(df_grupos["Data"] >= di) & (df_grupos["Data"] <= df)] if not df_grupos.empty else df_grupos


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    📊 Inflação — Painel de Monitoramento
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    Análise comparativa · Expectativas de mercado · Decomposição por grupos
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
ipca_v, _  = ultimo_valor(df_infl_f, "IPCA_acum12m")
igpm_v, _  = ultimo_valor(df_infl_f, "IGPM_acum12m")
inpc_v, _  = ultimo_valor(df_infl_f, "INPC_acum12m")

foc_med = None
if not df_f12.empty:
    foc = df_f12[df_f12["Indicador"]=="IPCA"].sort_values("Data")
    if len(foc) > 0:
        foc_med = round(float(foc.iloc[-1]["Mediana"]), 2)

surpresa = round(ipca_v - foc_med, 2) if ipca_v and foc_med else None
meta_bcb = METAS_BCB.get(datetime.today().year, 3.0)

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.metric("IPCA 12m",  f"{ipca_v:.2f}%"  if ipca_v  else "—")
with c2: st.metric("IGP-M 12m", f"{igpm_v:.2f}%"  if igpm_v  else "—")
with c3: st.metric("INPC 12m",  f"{inpc_v:.2f}%"  if inpc_v  else "—")
with c4: st.metric("Focus 12m", f"{foc_med:.2f}%" if foc_med else "—",
                   delta="Mediana", delta_color="off")
with c5: st.metric("Surpresa",  f"{surpresa:+.2f}pp" if surpresa else "—",
                   delta_color="off")
st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
col_g1, col_g2 = st.columns([6,4])

with col_g1:
    st.markdown("#### IPCA Realizado × Esperado")
    fig, _ = grafico_ipca_focus(df_infl_f, df_f12, ano_ini, ano_fim)
    st.pyplot(fig); plt.close()

with col_g2:
    st.markdown("#### Decomposição por Grupo")
    fig2, _ = grafico_barras_grupos(df_grupos_f)
    if fig2:
        st.pyplot(fig2); plt.close()
    else:
        st.info("Dados de grupos não disponíveis.")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICO COMPARATIVO DE ÍNDICES (reage ao filtro da sidebar)
# -----------------------------------------------------------------------------
if indices_sel:
    st.markdown("#### Comparativo de Índices Selecionados")

    # Mapeamento de cores por índice
    CORES_IND = {
        "IPCA":    "#00D4FF",
        "IGPM":    "#FFB800",
        "INPC":    "#00D4AA",
        "IPC_FIPE":"#DDA0DD",
        "IGP_DI":  "#F7DC6F",
    }

    sufixo = "_acum12m" if acum12m_toggle else ""

    fig_comp, ax_comp = plt.subplots(figsize=(14, 4))
    fig_comp.patch.set_facecolor("#0F1117")
    ax_comp.set_facecolor("#0F1117")

    for ind in indices_sel:
        col = f"{ind}{sufixo}"
        if col in df_infl_f.columns:
            s = df_infl_f[col].dropna()
            if len(s) > 0:
                ax_comp.plot(s.index, s.values,
                             color=CORES_IND.get(ind, "#AAAAAA"),
                             linewidth=2.0, label=ind)
                # Anotação do último valor
                ax_comp.annotate(
                    f"  {s.iloc[-1]:.2f}%",
                    xy=(s.index[-1], s.iloc[-1]),
                    xytext=(5, 3), textcoords="offset points",
                    color=CORES_IND.get(ind, "#AAAAAA"),
                    fontsize=9, fontweight="bold"
                )

    ax_comp.grid(True, color="#FFF", alpha=0.05, linewidth=0.5)
    ax_comp.tick_params(colors="#AAAAAA", labelsize=9)
    ax_comp.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax_comp.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    plt.xticks(rotation=30, ha="right")
    for sp in ax_comp.spines.values():
        sp.set_edgecolor("#333333")

    titulo_comp = "Acumulado 12 meses (%)" if acum12m_toggle else "Variação mensal (%)"
    ax_comp.set_title(
        f"Comparativo de Índices — {titulo_comp}",
        color="white", fontsize=12, fontweight="bold", pad=12
    )
    ax_comp.legend(
        fontsize=9, facecolor="#1A1D27", edgecolor="#333333",
        labelcolor="#CCC", framealpha=0.9, loc="upper right"
    )
    plt.tight_layout()
    st.pyplot(fig_comp)
    plt.close()
else:
    st.info("Selecione ao menos um índice na sidebar para ver o comparativo.")

st.markdown("---")


# -----------------------------------------------------------------------------
# ANÁLISE + EXPECTATIVAS
# -----------------------------------------------------------------------------
col_t, col_e = st.columns([6,4])

with col_t:
    st.markdown("#### Análise Automática")
    foc_val = None
    if not df_f12.empty:
        foc = df_f12[df_f12["Indicador"]=="IPCA"].sort_values("Data")
        if len(foc) > 0:
            foc_val = round(float(foc.iloc[-1]["Mediana"]), 2)
    texto_analise = analisar_ipca(df_infl_f, foc_val)
    st.markdown(texto_analise)

with col_e:
    st.markdown("#### Expectativas Focus")
    ano_at = datetime.today().year

    def foc_anual(ind, ano):
        if df_fa.empty: return None
        d = df_fa[(df_fa["Indicador"]==ind) &
                  (df_fa["DataReferencia"]==str(ano))]
        if d.empty: return None
        return round(float(d.sort_values("Data").iloc[-1]["Mediana"]), 2)

    c1e, c2e = st.columns(2)
    with c1e:
        v = foc_anual("IPCA", ano_at)
        st.metric(f"IPCA {ano_at}", f"{v:.2f}%" if v else "—",
                  delta=f"Meta: {meta_bcb:.1f}%", delta_color="off")
        v = foc_anual("PIB Total", ano_at)
        st.metric(f"PIB {ano_at}", f"{v:.2f}%" if v else "—",
                  delta="Var. real", delta_color="off")
    with c2e:
        v = foc_anual("Selic", ano_at)
        st.metric(f"Selic {ano_at}", f"{v:.2f}%" if v else "—",
                  delta="Taxa básica", delta_color="off")
        v = foc_anual("Câmbio", ano_at)
        st.metric(f"Câmbio {ano_at}", f"R$ {v:.2f}" if v else "—",
                  delta="USD/BRL", delta_color="off")
    st.caption("BCB/Focus — mediana · última coleta disponível")

st.markdown("---")
rodape()
