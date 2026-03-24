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

sidebar_padrao(pagina_atual="Acuracia_Focus", filtros_extra=_filtros)


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
    if not df_res.empty and "Reservas_USD_bi" in df_res.columns:
        if df_res["Reservas_USD_bi"].dropna().median() > 10000:
            df_res["Reservas_USD_bi"] = df_res["Reservas_USD_bi"] / 1000
    if not df_camb.empty and not df_res.empty:
        df_camb = df_camb.join(df_res, how="outer")


# Mapas definidos APOS sidebar — garante que indicador_sel ja foi atualizado
MAP_REALIZADO = {
    "IPCA":   (df_infl,  "IPCA_acum12m"),
    "Selic":  (df_juros, "Selic_Meta"),
    "C\u00e2mbio": (df_camb, "USD_BRL"),
}
MAP_FOCO_IND = {
    "IPCA":   "IPCA",
    "Selic":  "Selic",
    "C\u00e2mbio": "Cambio",
}
MAP_UNIDADE = {
    "IPCA":   "% a.a.",
    "Selic":  "% a.a.",
    "C\u00e2mbio": "R$/USD",
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
    """Para cada ano de referência, pega a mediana Focus coletada em jan-mar
    e compara com o realizado no final do ano.
    Retorna DataFrame com: Ano, Projetado, Realizado, Erro, Min, Max.
    """
    if df_focus is None or df_focus.empty: return pd.DataFrame()
    if df_real  is None or df_real.empty:  return pd.DataFrame()

    df_ind = df_focus[df_focus["Indicador"] == ind_focus].copy()
    if df_ind.empty: return pd.DataFrame()

    ano_atual = datetime.today().year
    anos_ref  = list(range(ano_atual - anos, ano_atual + 1))

    rows = []
    for ano in anos_ref:
        jan_ini = pd.Timestamp(f"{ano}-01-01")
        jan_fim = pd.Timestamp(f"{ano}-03-31")
        df_jan  = df_ind[
            (df_ind["DataReferencia"] == str(ano)) &
            (df_ind["Data"] >= jan_ini) &
            (df_ind["Data"] <= jan_fim)
        ].dropna(subset=["Mediana"])

        if df_jan.empty:
            continue

        # Pega a projeção mais recente do período jan-mar — um único registro
        ultimo = df_jan.sort_values("Data").iloc[-1]
        proj     = round(float(ultimo["Mediana"]), 2)
        proj_min = round(float(df_jan["Minimo"].dropna().mean()), 2) if "Minimo" in df_jan.columns and df_jan["Minimo"].notna().any() else None
        proj_max = round(float(df_jan["Maximo"].dropna().mean()), 2) if "Maximo" in df_jan.columns and df_jan["Maximo"].notna().any() else None

        # Realizado: último valor do ano na série histórica
        if not isinstance(df_real.index, pd.DatetimeIndex):
            continue
        if col_real not in df_real.columns:
            continue

        s_ano = df_real.loc[df_real.index.year == ano, col_real].dropna()
        if s_ano.empty:
            continue

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

    df_out = pd.DataFrame(rows)
    # Garante um registro por ano (elimina eventuais duplicatas)
    if not df_out.empty:
        df_out = df_out.drop_duplicates(subset=["Ano"]).sort_values("Ano").reset_index(drop=True)
    return df_out


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

    if not df_acur.empty:
        df_plot = df_acur.dropna(subset=["Erro"])
        df_c    = df_plot.copy()

        # Estatísticas para narrativa
        n_anos      = len(df_c)
        n_otimista  = int((df_c["Erro"] > 0.3).sum())
        n_pessimista= int((df_c["Erro"] < -0.3).sum())
        n_neutro    = n_anos - n_otimista - n_pessimista
        erro_med    = round(df_c["Erro"].mean(), 2)
        pior        = df_c.loc[df_c["Erro"].abs().idxmax()]
        dominante   = "otimista" if n_otimista > n_pessimista else ("pessimista" if n_pessimista > n_otimista else "neutro")

        # Legenda textual
        st.markdown(
            "🔴 **Otimista:** projetou **acima** do realizado (erro > +0.3) — "
            "o resultado foi melhor que o esperado.  \n"
            "🟢 **Pessimista:** projetou **abaixo** do realizado (erro < −0.3) — "
            "o resultado foi pior que o esperado.  \n"
            "🟡 **Neutro:** erro dentro de ±0.3 — projeção essencialmente acertada."
        )

        # Gráfico de barras horizontais
        fig2, ax2 = plt.subplots(figsize=(7, max(4, n_anos * 0.7)))
        fig2.patch.set_facecolor("#0F1117")
        ax2.set_facecolor("#0F1117")

        cores = ["#FF4B6E" if e > 0.3 else ("#00D4AA" if e < -0.3 else "#FFB800")
                 for e in df_c["Erro"]]
        ax2.barh(df_c["Ano"].astype(str), df_c["Erro"], color=cores, alpha=0.85)
        ax2.axvline(0, color="#555", lw=0.8)

        for i, (_, row) in enumerate(df_c.iterrows()):
            offset = 0.03 if row["Erro"] >= 0 else -0.03
            ax2.text(row["Erro"] + offset, i, f"{row['Erro']:+.2f}",
                     va="center",
                     ha="left" if row["Erro"] >= 0 else "right",
                     color="#CCC", fontsize=8)

        ax2.grid(True, color="#FFF", alpha=0.05, lw=0.5, axis="x")
        ax2.tick_params(colors="#AAAAAA", labelsize=9)
        for sp in ax2.spines.values(): sp.set_edgecolor("#333")
        ax2.set_xlabel(f"Erro = Projetado − Realizado ({unidade})", color="#AAAAAA", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2); plt.close()

        # Narrativa dinâmica rica
        vies_dir = "otimista" if erro_med > 0 else "pessimista"
        vies_exp = (
            "projetou o valor acima do que se concretizou"
            if erro_med > 0
            else "projetou o valor abaixo do que se concretizou"
        )
        st.markdown(
            f"Na maioria dos anos ({max(n_otimista, n_pessimista, n_neutro)} de {n_anos}), "
            f"o mercado foi **{dominante}** — {vies_exp}. "
            f"O ano com maior distância entre projeção e realidade foi **{int(pior['Ano'])}** "
            f"(erro de **{pior['Erro']:+.2f} {unidade}**): o mercado projetou "
            f"**{pior['Projetado']:.2f}** e o resultado foi **{pior['Realizado']:.2f}**."
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
        df_c     = df_acur.dropna(subset=["Erro"])
        erro_med = round(df_c["Erro"].mean(), 2)
        erro_abs = round(df_c["Erro"].abs().mean(), 2)
        n_otimista   = int((df_c["Erro"] > 0.3).sum())
        n_pessimista = int((df_c["Erro"] < -0.3).sum())
        n_neutro     = len(df_c) - n_otimista - n_pessimista
        pior         = df_c.loc[df_c["Erro"].abs().idxmax()]

        if erro_med > 0.5:
            vies_txt = f"**viés otimista estrutural** (+{erro_med:.2f} {unidade} em média)"
            vies_imp = (f"O mercado projetou sistematicamente **acima do realizado** — "
                        f"subestimou choques de inflação/câmbio/juros.")
        elif erro_med < -0.5:
            vies_txt = f"**viés pessimista estrutural** ({erro_med:.2f} {unidade} em média)"
            vies_imp = (f"O mercado projetou sistematicamente **abaixo do realizado** — "
                        f"superestimou pressões inflacionárias.")
        else:
            vies_txt = f"**sem viés estrutural relevante** (média {erro_med:+.2f} {unidade})"
            vies_imp = "As projeções oscilam em torno do realizado sem tendência clara."

        st.markdown(
            f"No período analisado, as projeções Focus para **{indicador_sel}** apresentam {vies_txt}. "
            f"{vies_imp}\n\n"
            f"**Erro absoluto médio:** {erro_abs:.2f} {unidade}  \n"
            f"**Otimista:** {n_otimista} ano(s) · "
            f"**Pessimista:** {n_pessimista} · "
            f"**Neutro:** {n_neutro}\n\n"
            f"**Maior erro:** {int(pior['Ano'])} — projetou **{pior['Projetado']:.2f}**, "
            f"realizado foi **{pior['Realizado']:.2f}** "
            f"(erro de **{pior['Erro']:+.2f} {unidade}**)."
        )

        st.markdown("---")
        st.markdown("**Por que isso importa?**")
        st.markdown(
            "O **Boletim Focus** agrega projeções de ~130 instituições financeiras "
            "e é o principal insumo do BCB para calibrar a política monetária. "
            "Erros sistemáticos revelam padrões estruturais:\n\n"
            "- **Viés otimista recorrente:** o consenso tende a subestimar choques — "
            "covid, crise hídrica, guerras e deteriorações fiscais costumam surpreender\n"
            "- **Viés pessimista:** ocorre após ciclos de aperto — o mercado superestima "
            "a persistência da inflação quando a política monetária já está funcionando\n"
            "- **Erros grandes em anos específicos:** sinalizam eventos extraordinários "
            "fora do modelo de consenso\n\n"
            "Se o mercado erra sistematicamente para um lado, isso pode indicar "
            "**desancoragem das expectativas** — o que por si só já é um sinal "
            "que o BCB monitora de perto."
        )
    else:
        st.info("Dados insuficientes para análise.")

st.caption("BCB/Focus — mediana das expectativas coletadas em jan/fev do ano de referência · "
           "Realizado = último valor disponível do ano")


# -----------------------------------------------------------------------------
# RODAPÉ
# -----------------------------------------------------------------------------
rodape()
