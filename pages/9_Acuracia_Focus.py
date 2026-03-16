# =============================================================================
# pages/9_Acuracia_Focus.py — Acurácia das Projeções Focus
# Compara o que o mercado projetou 12 meses antes vs o que de fato aconteceu
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

from utils.dados  import get_inflacao, get_juros, get_cambio, get_reservas, \
                         get_focus_anual, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Acurácia Focus | BI Econômico",
                   page_icon="🎯", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
indicador_sel = "IPCA"
anos_janela   = 4

def _filtros():
    global indicador_sel, anos_janela
    st.markdown("**⚙️ Filtros — Acurácia Focus**")
    indicador_sel = st.radio(
        "Indicador",
        ["IPCA", "Selic", "Câmbio"],
        index=0
    )
    anos_janela = st.slider("Anos de histórico", 2, 6, 4)

sidebar_padrao(filtros_extra=_filtros)


# -----------------------------------------------------------------------------
# CARREGAR DADOS
# -----------------------------------------------------------------------------
with st.spinner("Carregando expectativas Focus..."):
    df_fa = get_focus_anual()

with st.spinner("Carregando dados realizados..."):
    df_infl  = get_inflacao()
    df_juros = get_juros()
    df_camb  = get_cambio()
    df_res   = get_reservas()
    # Corrige reservas
    if not df_res.empty and "Reservas_USD_bi" in df_res.columns:
        if df_res["Reservas_USD_bi"].dropna().median() > 10000:
            df_res["Reservas_USD_bi"] = df_res["Reservas_USD_bi"] / 1000
    # Mescla câmbio
    if not df_camb.empty and not df_res.empty:
        df_camb = df_camb.join(df_res, how="outer")


# -----------------------------------------------------------------------------
# MAPEAMENTO: indicador → série realizada
# -----------------------------------------------------------------------------
MAP_REALIZADO = {
    "IPCA":   (df_infl,  "IPCA_acum12m"),
    "Selic":  (df_juros, "Selic_Meta"),
    "Câmbio": (df_camb,  "USD_BRL"),
}
MAP_FOCO_IND = {
    "IPCA":   "IPCA",
    "Selic":  "Selic",
    "Câmbio": "Câmbio",
}
MAP_UNIDADE = {
    "IPCA":   "% a.a.",
    "Selic":  "% a.a.",
    "Câmbio": "R$/USD",
}


# -----------------------------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------------------------
st.markdown(f"""
<h1 style='text-align:center; color:white; padding:0.5rem 0;'>
    🎯 Acurácia das Projeções Focus
</h1>
<p style='text-align:center; color:#AAAAAA; margin-top:-10px; margin-bottom:20px;'>
    O que o mercado projetou 12 meses antes vs o que de fato aconteceu · IPCA · Selic · Câmbio
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# -----------------------------------------------------------------------------
# MONTA SÉRIE DE PROJEÇÕES vs REALIZADO
# -----------------------------------------------------------------------------
def montar_serie_acuracia(df_focus, ind_focus, df_real, col_real, anos=4):
    """
    Para cada ano de referência disponível no Focus, pega a mediana
    projetada no início do ano (jan) e compara com o realizado no final (dez).
    Retorna DataFrame com colunas: Ano, Projetado, Realizado, Erro, Min, Max.
    """
    if df_focus is None or df_focus.empty: return pd.DataFrame()
    if df_real  is None or df_real.empty:  return pd.DataFrame()

    df_ind = df_focus[df_focus["Indicador"] == ind_focus].copy()
    if df_ind.empty: return pd.DataFrame()

    ano_atual = datetime.today().year
    anos_ref  = list(range(ano_atual - anos, ano_atual + 1))

    rows = []
    for ano in anos_ref:
        # Projeção: mediana Focus coletada em janeiro do ano (±2 meses)
        jan_ini = pd.Timestamp(f"{ano}-01-01")
        jan_fim = pd.Timestamp(f"{ano}-03-31")
        df_jan  = df_ind[
            (df_ind["DataReferencia"] == str(ano)) &
            (df_ind["Data"] >= jan_ini) &
            (df_ind["Data"] <= jan_fim)
        ].dropna(subset=["Mediana"])

        if df_jan.empty:
            continue

        proj     = round(float(df_jan.sort_values("Data").iloc[-1]["Mediana"]), 2)
        proj_min = round(float(df_jan["Minimo"].dropna().mean()),  2) if "Minimo" in df_jan else None
        proj_max = round(float(df_jan["Maximo"].dropna().mean()),  2) if "Maximo" in df_jan else None

        # Realizado: último valor disponível do ano
        if isinstance(df_real.index, pd.DatetimeIndex):
            df_ano = df_real[
                (df_real.index.year == ano) & (col_real in df_real.columns)
            ]
        else:
            continue

        if df_ano.empty or col_real not in df_ano.columns:
            continue

        s_ano = df_ano[col_real].dropna()
        if s_ano.empty: continue

        realizado = round(float(s_ano.iloc[-1]), 2)
        erro      = round(proj - realizado, 2)

        rows.append({
            "Ano":       ano,
            "Projetado": proj,
            "Realizado": realizado,
            "Erro":      erro,
            "Min":       proj_min,
            "Max":       proj_max,
        })

    return pd.DataFrame(rows)


ind_focus = MAP_FOCO_IND[indicador_sel]
df_real_src, col_real = MAP_REALIZADO[indicador_sel]
unidade = MAP_UNIDADE[indicador_sel]

df_acur = montar_serie_acuracia(df_fa, ind_focus, df_real_src, col_real, anos=anos_janela)


# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------
if not df_acur.empty:
    df_completo = df_acur.dropna(subset=["Projetado", "Realizado"])

    erro_medio = round(df_completo["Erro"].mean(), 2) if not df_completo.empty else None
    erro_abs   = round(df_completo["Erro"].abs().mean(), 2) if not df_completo.empty else None
    vies       = "otimista (projetou acima)" if (erro_medio or 0) > 0 else "pessimista (projetou abaixo)"
    ano_pior   = df_completo.loc[df_completo["Erro"].abs().idxmax(), "Ano"] if not df_completo.empty else None
    pior_erro  = df_completo.loc[df_completo["Erro"].abs().idxmax(), "Erro"] if not df_completo.empty else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Erro médio (viés)",
                  f"{erro_medio:+.2f} {unidade}" if erro_medio is not None else "—",
                  delta=vies, delta_color="off")
    with c2:
        st.metric("Erro absoluto médio",
                  f"{erro_abs:.2f} {unidade}" if erro_abs is not None else "—",
                  delta="MAE — desvio médio", delta_color="off")
    with c3:
        st.metric("Pior projeção",
                  f"{ano_pior}" if ano_pior else "—",
                  delta=f"Erro: {pior_erro:+.2f}" if pior_erro is not None else None,
                  delta_color="off")
    with c4:
        v_atual, _ = ultimo_valor(df_real_src, col_real)
        v_proj     = None
        if not df_fa.empty:
            ano_at = datetime.today().year
            f = df_fa[(df_fa["Indicador"] == ind_focus) &
                      (df_fa["DataReferencia"] == str(ano_at))]
            if not f.empty:
                v_proj = round(float(f.sort_values("Data").iloc[-1]["Mediana"]), 2)
        st.metric(f"Projeção Focus {datetime.today().year}",
                  f"{v_proj:.2f} {unidade}" if v_proj else "—",
                  delta=f"Realizado atual: {v_atual:.2f}" if v_atual else None,
                  delta_color="off")

st.markdown("---")


# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
col_g1, col_g2 = st.columns([6, 4])

with col_g1:
    st.markdown(f"#### {indicador_sel} — Projeção Focus (jan) vs Realizado (dez)")

    if not df_acur.empty and len(df_acur) >= 2:
        df_plot = df_acur.dropna(subset=["Projetado", "Realizado"])

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0F1117")
        ax.set_facecolor("#0F1117")

        anos_x = df_plot["Ano"].values

        # Banda de dispersão (min/max)
        if df_plot["Min"].notna().any() and df_plot["Max"].notna().any():
            ax.fill_between(anos_x,
                            df_plot["Min"].fillna(df_plot["Projetado"]),
                            df_plot["Max"].fillna(df_plot["Projetado"]),
                            alpha=0.15, color="#FFB800",
                            label="Dispersão (min/max analistas)")

        ax.plot(anos_x, df_plot["Projetado"], color="#FFB800",
                lw=2.0, marker="o", ms=7, ls="--",
                label="Projetado Focus (início do ano)")
        ax.plot(anos_x, df_plot["Realizado"], color="#00D4FF",
                lw=2.5, marker="o", ms=7,
                label="Realizado")

        # Anotações dos erros
        for _, row in df_plot.iterrows():
            erro = row["Erro"]
            cor_e = "#FF4B6E" if abs(erro) > 1.5 else "#AAAAAA"
            ax.annotate(f"{erro:+.1f}",
                        xy=(row["Ano"], row["Projetado"]),
                        xytext=(0, 12), textcoords="offset points",
                        color=cor_e, fontsize=8, ha="center", fontweight="bold")

        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.set_xticks(anos_x)
        ax.set_xticklabels([str(a) for a in anos_x], color="#AAAAAA")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.set_ylabel(unidade, color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333",
                  labelcolor="#CCC", framealpha=0.9)
        plt.tight_layout()
        st.pyplot(fig); plt.close()
        st.caption("Números sobre a linha tracejada = erro da projeção (projetado − realizado). "
                   "Vermelho = erro > 1.5pp.")
    else:
        st.info("Dados insuficientes para plotar.")

with col_g2:
    st.markdown("#### Como o mercado errou?")
    st.caption(
        "🔴 **Otimista:** projetou **acima** do realizado (erro > +0.3) — "
        "o resultado foi melhor que o esperado. "
        "🟢 **Pessimista:** projetou **abaixo** do realizado (erro < −0.3) — "
        "o resultado foi pior que o esperado. "
        "🟡 **Neutro:** erro dentro de ±0.3 — projeção essencialmente acertada."
    )

    if not df_acur.empty:
        df_plot = df_acur.dropna(subset=["Erro"])

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        cores = ["#FF4B6E" if e > 0.3 else ("#00D4AA" if e < -0.3 else "#FFB800")
                 for e in df_plot["Erro"]]
        ax2.barh(df_plot["Ano"].astype(str), df_plot["Erro"],
                 color=cores, alpha=0.85)
        ax2.axvline(0, color="#555", lw=0.8)

        for i, (_, row) in enumerate(df_plot.iterrows()):
            ax2.text(row["Erro"] + (0.05 if row["Erro"] >= 0 else -0.05),
                     i, f"{row['Erro']:+.2f}",
                     va="center", ha="left" if row["Erro"] >= 0 else "right",
                     color="#AAAAAA", fontsize=8)

        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5, axis="x")
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        ax2.set_xlabel(f"Erro = Projetado − Realizado ({unidade})", color="#AAAAAA", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

        # Texto dinâmico
        if not df_plot.empty:
            n_otim = (df_plot["Erro"] > 0.3).sum()
            n_pess = (df_plot["Erro"] < -0.3).sum()
            maior_erro = df_plot.loc[df_plot["Erro"].abs().idxmax()]

            if n_otim > n_pess:
                direcao = f"Na maioria dos anos ({n_otim} de {len(df_plot)}), o mercado foi **otimista** — projetou {indicador_sel} mais alto do que o que se concretizou."
            elif n_pess > n_otim:
                direcao = f"Na maioria dos anos ({n_pess} de {len(df_plot)}), o mercado foi **pessimista** — projetou {indicador_sel} mais baixo do que o realizado."
            else:
                direcao = f"Os erros se distribuíram de forma equilibrada entre anos otimistas e pessimistas."

            st.markdown(
                f"{direcao} "
                f"O ano com maior distância entre projeção e realidade foi **{int(maior_erro['Ano'])}** "
                f"(erro de **{maior_erro['Erro']:+.2f} {unidade}**): o mercado projetou "
                f"**{maior_erro['Projetado']:.2f}** e o resultado foi **{maior_erro['Realizado']:.2f}**."
            )
    else:
        st.info("Dados insuficientes.")

st.markdown("---")


# -----------------------------------------------------------------------------
# TABELA RESUMO + ANÁLISE
# -----------------------------------------------------------------------------
col_t, col_e = st.columns([5, 5])

with col_t:
    st.markdown("#### Tabela de Acurácia")

    if not df_acur.empty:
        df_tab = df_acur.copy()
        df_tab["Erro abs."] = df_tab["Erro"].abs().round(2)
        df_tab["Viés"] = df_tab["Erro"].apply(
            lambda e: "Otimista ↑" if e > 0.3 else ("Pessimista ↓" if e < -0.3 else "Neutro →")
        )
        df_tab = df_tab[["Ano", "Projetado", "Realizado", "Erro", "Erro abs.", "Viés"]]
        df_tab.columns = ["Ano", f"Proj. ({unidade})", f"Real. ({unidade})",
                          "Erro", "Erro abs.", "Viés"]
        st.dataframe(df_tab, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados disponíveis.")

with col_e:
    st.markdown("#### Análise Automática")

    if not df_acur.empty and not df_acur.dropna(subset=["Erro"]).empty:
        df_c = df_acur.dropna(subset=["Erro"])
        erro_med = round(df_c["Erro"].mean(), 2)
        erro_abs = round(df_c["Erro"].abs().mean(), 2)
        n_otimista  = (df_c["Erro"] > 0.3).sum()
        n_pessimista = (df_c["Erro"] < -0.3).sum()
        n_neutro    = len(df_c) - n_otimista - n_pessimista
        pior        = df_c.loc[df_c["Erro"].abs().idxmax()]

        # Viés estrutural
        if erro_med > 0.5:
            vies_txt = f"**viés otimista estrutural** (+{erro_med:.2f} {unidade} em média)"
            vies_imp = "O mercado sistematicamente subestima a inflação/juros/câmbio — as projeções tendem a ser menores que o realizado."
        elif erro_med < -0.5:
            vies_txt = f"**viés pessimista estrutural** ({erro_med:.2f} {unidade} em média)"
            vies_imp = "O mercado sistematicamente superestima — as projeções tendem a ser maiores que o realizado."
        else:
            vies_txt = f"**sem viés estrutural relevante** (média {erro_med:+.2f} {unidade})"
            vies_imp = "As projeções oscilam em torno do realizado sem tendência clara de erro."

        st.markdown(
            f"No período analisado, as projeções Focus para **{indicador_sel}** apresentam {vies_txt}. "
            f"{vies_imp}\n\n"
            f"O erro absoluto médio foi de **{erro_abs:.2f} {unidade}**, "
            f"com **{n_otimista}** ano(s) de projeção otimista, "
            f"**{n_pessimista}** pessimista(s) e **{n_neutro}** neutro(s).\n\n"
            f"O maior erro ocorreu em **{int(pior['Ano'])}**, quando o mercado projetou "
            f"**{pior['Projetado']:.2f}** e o realizado foi **{pior['Realizado']:.2f}** "
            f"(erro de **{pior['Erro']:+.2f} {unidade}**)."
        )
    else:
        st.info("Dados insuficientes para análise.")

st.caption("BCB/Focus — mediana das expectativas coletadas em jan/fev do ano de referência · "
           "Realizado = último valor disponível do ano")


# -----------------------------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------------------------
rodape()
