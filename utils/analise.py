# =============================================================================
# utils/analise.py — Geração automática de textos analíticos
# Funções que interpretam os dados e geram texto em markdown
# =============================================================================

from datetime import datetime
import pandas as pd

METAS_BCB  = {2019:4.25,2020:4.0,2021:3.75,2022:3.5,2023:3.25,2024:3.0,2025:3.0,2026:3.0}
TOLERANCIA = 1.5


def analisar_ipca(df_ipca, focus_mediana=None):
    """Gera análise textual automática do IPCA."""
    if df_ipca is None or df_ipca.empty or "IPCA_acum12m" not in df_ipca.columns:
        return "Dados insuficientes para análise."

    s       = df_ipca["IPCA_acum12m"].dropna()
    if s.empty:
        return "Dados insuficientes para análise."

    ipca    = s.iloc[-1]
    mes_ref = s.index[-1].strftime("%b/%Y")
    media   = s.mean()
    pico    = s.max()
    minimo  = s.min()
    mes_p   = s.idxmax().strftime("%b/%Y")
    mes_m   = s.idxmin().strftime("%b/%Y")
    tend    = round(s.iloc[-1] - s.iloc[-3], 2) if len(s) >= 3 else 0

    ano_ref = s.index[-1].year
    meta    = METAS_BCB.get(ano_ref, 3.0)
    teto    = meta + TOLERANCIA

    # Situação vs meta
    if ipca <= meta:
        sit = f"dentro da meta central de {meta:.1f}%"
    elif ipca <= teto:
        sit = f"dentro da banda de tolerância, mas acima da meta de {meta:.1f}%"
    else:
        sit = f"**acima do teto** de {teto:.1f}%, em descumprimento da meta"

    linhas = [
        f"**[IPCA]** Em {mes_ref}, o IPCA acumulado em 12 meses ficou em "
        f"**{ipca:.2f}%** — {sit}."
    ]

    # Surpresa vs Focus
    if focus_mediana is not None:
        surp = round(ipca - focus_mediana, 2)
        if abs(surp) < 0.1:
            linhas.append(
                f"**[Focus]** O resultado ficou em linha com o consenso de "
                f"mercado (mediana: {focus_mediana:.2f}%)."
            )
        elif surp > 0:
            linhas.append(
                f"**[Focus]** O resultado **surpreendeu negativamente** o mercado: "
                f"{surp:+.2f}pp acima da mediana Focus de {focus_mediana:.2f}%."
            )
        else:
            linhas.append(
                f"**[Focus]** O resultado **surpreendeu positivamente**: "
                f"{surp:.2f}pp abaixo da mediana Focus de {focus_mediana:.2f}%."
            )

    # Tendência
    txt_t = ("acelerando" if tend > 0.3
             else "desacelerando" if tend < -0.3
             else "estável")
    linhas.append(
        f"**[Tendência]** A inflação está **{txt_t}** "
        f"({tend:+.2f}pp nos últimos 3 meses)."
    )

    # Contexto histórico
    linhas.append(
        f"**[Período]** No intervalo selecionado: média de {media:.2f}%, "
        f"pico de {pico:.2f}% ({mes_p}) e mínimo de {minimo:.2f}% ({mes_m})."
    )

    return "\n\n".join(linhas)


def analisar_juro_real(selic, ipca_acum, focus_ipca=None):
    """Analisa o juro real e gera texto interpretativo."""
    if selic is None or ipca_acum is None:
        return "Dados insuficientes."

    juro_real = round(((1 + selic/100) / (1 + ipca_acum/100) - 1) * 100, 2)

    if juro_real > 8:
        nivel = "extremamente restritivo"
        tom = "vermelho"
    elif juro_real > 6:
        nivel = "muito restritivo"
        tom = "vermelho"
    elif juro_real > 3:
        nivel = "restritivo"
        tom = "amarelo"
    elif juro_real > 0:
        nivel = "levemente positivo"
        tom = "verde"
    else:
        nivel = "negativo (expansionista)"
        tom = "verde"

    linhas = [
        f"**[Juro Real Ex-post]** Com Selic de **{selic:.2f}%** e IPCA "
        f"acumulado de **{ipca_acum:.2f}%**, a taxa real de juros está em "
        f"**{juro_real:.2f}% a.a.** — nivel {nivel}."
    ]

    if focus_ipca is not None:
        juro_exante = round(((1 + selic/100) / (1 + focus_ipca/100) - 1) * 100, 2)
        diff = round(juro_real - juro_exante, 2)
        linhas.append(
            f"**[Juro Real Ex-ante]** Usando a expectativa Focus de IPCA "
            f"de **{focus_ipca:.2f}%**, o juro real esperado e de "
            f"**{juro_exante:.2f}% a.a.** — diferenca de {diff:+.2f}pp em relacao "
            f"ao ex-post."
        )

    linhas.append(
        f"**[Contexto]** O juro real brasileiro de {juro_real:.2f}% "
        f"{'esta acima' if juro_real > 6 else 'esta proximo'} da media historica "
        f"de longo prazo do pais (estimada entre 3% e 5% a.a.). "
        f"{'Isso pressiona o credito, o investimento e o crescimento economico.' if juro_real > 6 else 'O nivel atual e compativel com ancoragem das expectativas de inflacao.'}"
    )

    return "\n\n".join(linhas)


def resumo_semana(dados):
    """
    Gera o resumo da semana para a Home.
    dados: dict com últimas leituras de cada indicador
    """
    linhas = [f"### Resumo Econômico — {datetime.today().strftime('%d/%m/%Y')}\n"]

    if dados.get("ipca"):
        linhas.append(f"- **Inflação (IPCA 12m):** {dados['ipca']:.2f}%")
    if dados.get("selic"):
        linhas.append(f"- **Selic:** {dados['selic']:.2f}% a.a.")
    if dados.get("pib"):
        linhas.append(f"- **PIB (último tri):** {dados['pib']:.2f}%")
    if dados.get("desemprego"):
        linhas.append(f"- **Desemprego:** {dados['desemprego']:.1f}%")
    if dados.get("cambio"):
        linhas.append(f"- **Câmbio (USD/BRL):** R$ {dados['cambio']:.2f}")

    return "\n".join(linhas)


# -----------------------------------------------------------------------------
# RESUMO GERAL (para a Home)
# -----------------------------------------------------------------------------
def resumo_geral(df_infl, df_juros, df_cambio, df_pnad, df_focus_anual):
    """Gera resumo executivo para a página Home."""
    from utils.dados import METAS_BCB
    partes = []
    ano    = datetime.today().year

    s = df_infl["IPCA_acum12m"].dropna() if not df_infl.empty and "IPCA_acum12m" in df_infl.columns else None
    v = round(float(s.iloc[-1]), 2) if s is not None and len(s) > 0 else None
    if v:
        meta = METAS_BCB.get(ano, 3.0)
        sit  = "dentro da banda" if v <= meta+1.5 else "acima do teto"
        partes.append(f"**Inflação**: IPCA em {v:.2f}% ({sit} da meta de {meta:.1f}%)")

    s = df_juros["Selic_Meta"].dropna() if not df_juros.empty and "Selic_Meta" in df_juros.columns else None
    v = round(float(s.iloc[-1]), 2) if s is not None and len(s) > 0 else None
    if v:
        partes.append(f"**Selic**: {v:.2f}% a.a.")

    s = df_cambio["USD_BRL"].dropna() if not df_cambio.empty and "USD_BRL" in df_cambio.columns else None
    v = round(float(s.iloc[-1]), 2) if s is not None and len(s) > 0 else None
    if v:
        partes.append(f"**Dólar**: R$ {v:.2f}")

    if df_pnad is not None and not df_pnad.empty and "Taxa_Desocupacao" in df_pnad.columns:
        s = df_pnad["Taxa_Desocupacao"].dropna()
        v = round(float(s.iloc[-1]), 2) if len(s) > 0 else None
        if v:
            partes.append(f"**Desemprego**: {v:.1f}%")

    return " · ".join(partes) if partes else "Carregando dados..."
