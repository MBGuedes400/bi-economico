# =============================================================================
# utils/graficos.py — Funções reutilizáveis de visualização
# Todas as funções retornam fig, ax prontos para st.pyplot()
# =============================================================================

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Paleta padrão do projeto
CORES = {
    "primario":   "#00D4FF",
    "secundario": "#FFB800",
    "alerta":     "#FF4B6E",
    "positivo":   "#00D4AA",
    "neutro":     "#AAAAAA",
    "fundo":      "#0F1117",
    "fundo2":     "#1A1D27",
    "borda":      "#333333",
}

CORES_GRUPOS = {
    "Alimentação e bebidas":    "#FF6B6B",
    "Habitação":                "#4ECDC4",
    "Artigos de residência":    "#45B7D1",
    "Vestuário":                "#96CEB4",
    "Transportes":              "#FFEAA7",
    "Saúde e cuidados pessoais":"#DDA0DD",
    "Despesas pessoais":        "#98D8C8",
    "Educação":                 "#F7DC6F",
    "Comunicação":              "#85C1E9",
}

METAS_BCB    = {2019:4.25,2020:4.0,2021:3.75,2022:3.5,2023:3.25,2024:3.0,2025:3.0,2026:3.0}
TOLERANCIA   = 1.5


def _base_fig(w=12, h=5):
    """Cria figura com tema escuro padrão."""
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(CORES["fundo"])
    ax.set_facecolor(CORES["fundo"])
    ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(colors=CORES["neutro"], labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(CORES["borda"])
    return fig, ax


def _legenda(ax, **kwargs):
    """Aplica legenda padrão."""
    ax.legend(
        facecolor=CORES["fundo2"], edgecolor=CORES["borda"],
        labelcolor="#CCC", framealpha=0.9,
        fontsize=8, **kwargs
    )


def grafico_linha_temporal(series_dict, titulo="", ylabel="%",
                           fmt_y="%.1f%%", w=12, h=5):
    """
    Gráfico de linhas temporais para múltiplas séries.
    series_dict: {"Nome": pd.Series, ...}
    """
    fig, ax = _base_fig(w, h)
    for i, (nome, serie) in enumerate(series_dict.items()):
        cor = list(CORES.values())[i % 4]
        s   = serie.dropna()
        ax.plot(s.index, s.values, lw=2.0, label=nome, color=cor)
        if len(s) > 0:
            ax.scatter(s.index[-1], s.iloc[-1], color=cor, s=50, zorder=5)
            ax.annotate(f"  {s.iloc[-1]:.2f}%",
                        xy=(s.index[-1], s.iloc[-1]),
                        xytext=(6,3), textcoords="offset points",
                        color=cor, fontsize=9, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter(fmt_y))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b/%Y"))
    plt.xticks(rotation=30, ha="right")
    ax.set_title(titulo, color="white", fontsize=12, fontweight="bold", pad=14)
    ax.set_ylabel(ylabel, color=CORES["neutro"], fontsize=9)
    _legenda(ax)
    plt.tight_layout()
    return fig, ax


def grafico_ipca_focus(df_ipca, df_focus12, ano_inicio, ano_fim,
                       metas=METAS_BCB, w=12, h=5):
    """IPCA realizado × esperado Focus com banda de incerteza."""
    fig, ax = _base_fig(w, h)
    data_ini = pd.Timestamp(f"{ano_inicio}-01-01")
    data_fim = pd.Timestamp(f"{ano_fim}-12-31")

    # Focus
    if not df_focus12.empty:
        df_f = (df_focus12
                .assign(AM=lambda x: x["Data"].dt.to_period("M"))
                .groupby("AM")
                .agg(Med=("Mediana","median"),
                     Min=("Minimo","min"),
                     Max=("Maximo","max"))
                .reset_index())
        df_f["Data"] = df_f["AM"].dt.to_timestamp()
        df_f = df_f[(df_f["Data"]>=data_ini)&(df_f["Data"]<=data_fim)]
        if not df_f.empty:
            ax.fill_between(df_f["Data"], df_f["Min"], df_f["Max"],
                            color=CORES["secundario"], alpha=0.07,
                            label="Dispersão Focus")
            ax.plot(df_f["Data"], df_f["Med"],
                    color=CORES["secundario"], lw=1.8, ls="--", alpha=0.9,
                    label="IPCA esperado (Focus)")

    # IPCA realizado
    if not df_ipca.empty and "IPCA_acum12m" in df_ipca.columns:
        s = df_ipca["IPCA_acum12m"].dropna()
        s = s[(s.index>=data_ini)&(s.index<=data_fim)]
        if not s.empty:
            ax.plot(s.index, s.values, color=CORES["primario"],
                    lw=2.5, zorder=5, label="IPCA acumulado 12m")
            ax.scatter(s.index[-1], s.iloc[-1],
                       color=CORES["primario"], s=60, zorder=6)
            ax.annotate(f"  {s.iloc[-1]:.2f}%",
                        xy=(s.index[-1], s.iloc[-1]),
                        xytext=(8,4), textcoords="offset points",
                        color=CORES["primario"], fontsize=10, fontweight="bold")

            # Área de surpresa
            if not df_focus12.empty and 'df_f' in dir() and not df_f.empty:
                s_df = s.reset_index()
                s_df.columns = ["Data", "IPCA"]
                mg = pd.merge(s_df, df_f[["Data","Med"]],
                              on="Data", how="inner")
                if not mg.empty:
                    ax.fill_between(mg["Data"], mg["Med"], mg["IPCA"],
                                    where=mg["IPCA"]>mg["Med"],
                                    color=CORES["alerta"], alpha=0.12,
                                    label="Acima do esperado")
                    ax.fill_between(mg["Data"], mg["IPCA"], mg["Med"],
                                    where=mg["IPCA"]<mg["Med"],
                                    color=CORES["primario"], alpha=0.08,
                                    label="Abaixo do esperado")

    # Metas
    for ano in range(ano_inicio, ano_fim+1):
        if ano in metas:
            ini = pd.Timestamp(f"{ano}-01-01")
            fim_a = pd.Timestamp(f"{ano}-12-31")
            ax.hlines(metas[ano], ini, fim_a,
                      colors=CORES["alerta"], lw=1.0, ls=":", alpha=0.7,
                      label="Meta BCB" if ano==ano_inicio else "")
            ax.fill_between([ini,fim_a],
                            metas[ano]-TOLERANCIA, metas[ano]+TOLERANCIA,
                            color=CORES["alerta"], alpha=0.04)

    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b/%Y"))
    plt.xticks(rotation=30, ha="right")
    ax.set_title("IPCA — Realizado × Esperado pelo Mercado (Focus)",
                 color="white", fontsize=12, fontweight="bold", pad=14)
    ax.set_ylabel("Variação acumulada 12m (%)", color=CORES["neutro"], fontsize=9)
    _legenda(ax, ncol=2)
    plt.tight_layout()
    return fig, ax


def grafico_barras_grupos(df_grupos, n_meses=24, w=10, h=5):
    """Barras empilhadas do IPCA por grupo de despesa."""
    if df_grupos.empty:
        return None, None
    df_p = (df_grupos
            .groupby(["Data","Grupo"])["Valor"].mean()
            .reset_index()
            .pivot(index="Data", columns="Grupo", values="Valor")
            .fillna(0)
            .sort_index())
    if len(df_p) > n_meses:
        df_p = df_p.iloc[-n_meses:]

    grupos = df_p.columns.tolist()
    cores  = [CORES_GRUPOS.get(g, "#AAA") for g in grupos]
    larg   = max(8, int(22 - len(df_p)*0.3))

    fig, ax = _base_fig(w, h)
    bp, bn = np.zeros(len(df_p)), np.zeros(len(df_p))
    for i, g in enumerate(grupos):
        vp = df_p[g].clip(lower=0).values
        vn = df_p[g].clip(upper=0).values
        ax.bar(df_p.index, vp, bottom=bp, color=cores[i],
               alpha=0.85, width=larg, label=g)
        ax.bar(df_p.index, vn, bottom=bn, color=cores[i],
               alpha=0.85, width=larg)
        bp += vp; bn += vn

    total = df_p.sum(axis=1)
    ax.plot(df_p.index, total, color="white", lw=2.0,
            marker="o", ms=3, zorder=5, label="IPCA total")
    if len(total) > 0:
        ax.annotate(f" {total.iloc[-1]:.2f}%",
                    xy=(total.index[-1], total.iloc[-1]),
                    xytext=(5,3), textcoords="offset points",
                    color="white", fontsize=9, fontweight="bold")
    ax.axhline(0, color="#555", lw=0.8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b/%y"))
    plt.xticks(rotation=30, ha="right")
    ax.set_title("Decomposição do IPCA por Grupo de Despesa",
                 color="white", fontsize=12, fontweight="bold", pad=14)
    _legenda(ax, ncol=3, loc="upper left")
    plt.tight_layout()
    return fig, ax
