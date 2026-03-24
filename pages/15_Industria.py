# =============================================================================
# pages/15_Industria.py — Setor Industrial
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

from utils.dados  import get_pim_pf, get_industria_indicadores, get_ibcbr, ultimo_valor
from utils.layout import CSS_GLOBAL, rodape, sidebar_padrao

st.set_page_config(page_title="Indústria | BI Econômico", page_icon="🏭", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

ano_ini, ano_fim = 2020, datetime.today().year
def _filtros():
    global ano_ini, ano_fim
    st.markdown("**Filtros**")
    anos = list(range(2015, datetime.today().year + 1))
    ano_ini, ano_fim = st.select_slider("Período", options=anos,
                                         value=(2020, datetime.today().year))
sidebar_padrao(pagina_atual="Industria", filtros_extra=_filtros)

with st.spinner("Carregando dados industriais..."):
    df_pim  = get_pim_pf()
    df_ind  = get_industria_indicadores()
    df_ibc  = get_ibcbr()

dt_ini  = pd.Timestamp(f"{ano_ini}-01-01")
dt_fim_ = pd.Timestamp(f"{ano_fim}-12-31")

def filtrar(df):
    if df is None or df.empty: return df
    df = df.copy(); df.index = pd.to_datetime(df.index)
    return df[(df.index >= dt_ini) & (df.index <= dt_fim_)]

df_pf  = filtrar(df_pim)
df_inf = filtrar(df_ind)
df_ibf = filtrar(df_ibc)

CORES_SETORES = {
    "Extrativa":            "#00D4FF",
    "Transformacao":        "#00D4AA",
    "Alimentos":            "#FFB800",
    "Veiculos":             "#FF4B6E",
    "Maquinas_Equipamentos":"#A78BFA",
    "Metalurgia":           "#F59E0B",
    "Eletronicos":          "#34D399",
    "Farmaceuticos":        "#F87171",
    "Petroleo_Derivados":   "#60A5FA",
    "Minerais_nao_Metalicos":"#FBBF24",
}

NOMES = {
    "Extrativa":            "Extrativa",
    "Transformacao":        "Transformação",
    "Alimentos":            "Alimentos",
    "Veiculos":             "Veículos",
    "Maquinas_Equipamentos":"Máquinas e Equip.",
    "Metalurgia":           "Metalurgia",
    "Eletronicos":          "Eletrônicos",
    "Farmaceuticos":        "Farmacêuticos",
    "Petroleo_Derivados":   "Petróleo/Derivados",
    "Minerais_nao_Metalicos":"Minerais não Met.",
}

SUBSETORES = ["Alimentos","Veiculos","Maquinas_Equipamentos",
              "Metalurgia","Eletronicos","Farmaceuticos",
              "Petroleo_Derivados","Minerais_nao_Metalicos"]

def var_12m(df, col):
    if df is None or df.empty or col not in df.columns: return None
    s = df[col].dropna()
    if len(s) < 13: return None
    return round((s.iloc[-1] / s.iloc[-13] - 1) * 100, 1)

def meses_consecutivos(df, col, direcao="queda"):
    if df is None or df.empty or col not in df.columns: return 0
    s = df[col].dropna().pct_change().dropna()
    if s.empty: return 0
    count = 0
    for v in reversed(s.values):
        if direcao == "queda" and v < 0:
            count += 1
        elif direcao == "expansao" and v > 0:
            count += 1
        else:
            break
    return count

# =============================================================================
# CABECALHO
# =============================================================================
st.markdown("""
<h1 style='text-align:center;color:white;padding:0.5rem 0'>
    🏭 Setor Industrial
</h1>
<p style='text-align:center;color:#AAAAAA;margin-top:-10px;margin-bottom:20px'>
    Produção · Capacidade Instalada · Confiança · Ciclo Setorial
</p>""", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# KPIs
# =============================================================================
nuci_fgv, _ = ultimo_valor(df_ind, "NUCI_FGV")
nuci_cni, _ = ultimo_valor(df_ind, "NUCI_CNI")
icei_v, _   = ultimo_valor(df_ind, "ICEI")
prod_v, _   = ultimo_valor(df_pim, "Transformacao")
var_prod    = var_12m(df_pim, "Transformacao")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Ind. Transformação (índice)",
              f"{prod_v:.1f}" if prod_v else "—",
              delta=f"{var_prod:+.1f}% 12m" if var_prod is not None else None)
with c2:
    nuci_delta = round(nuci_fgv - 80.0, 1) if nuci_fgv else None
    st.metric("NUCI FGV (%)",
              f"{nuci_fgv:.1f}%" if nuci_fgv else "—",
              delta=f"{nuci_delta:+.1f}pp vs 80%" if nuci_delta else None)
with c3:
    st.metric("NUCI CNI (%)",
              f"{nuci_cni:.1f}%" if nuci_cni else "—")
with c4:
    icei_sinal = "expansão" if (icei_v or 0) > 50 else "contração"
    st.metric("ICEI — Confiança",
              f"{icei_v:.1f}" if icei_v else "—",
              delta=icei_sinal if icei_v else None,
              delta_color="normal" if (icei_v or 0) > 50 else "inverse")

st.markdown("---")

# =============================================================================
# BLOCO 1 — PRODUCAO GERAL
# =============================================================================
st.markdown("### 📦 Produção Industrial — Visão Geral")
st.caption("Índice de base fixa sem ajuste sazonal · Base média 2012 = 100 · Fonte: IBGE/PIM-PF")

col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("#### Extrativa vs Transformação")
    if not df_pf.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0F1117"); ax.set_facecolor("#0F1117")
        for col in ["Extrativa", "Transformacao"]:
            if col in df_pf.columns:
                s = df_pf[col].dropna()
                ax.plot(s.index, s.values, color=CORES_SETORES[col], lw=2, label=NOMES[col])
        ax.axhline(100, color="#555", lw=0.8, ls="--", label="Base 2012")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax.tick_params(colors="#AAAAAA", labelsize=9)
        ax.set_ylabel("Índice", color="#AAAAAA", fontsize=9)
        ax.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig); plt.close()
    else:
        st.info("Dados de produção industrial não disponíveis.")

with col2:
    st.markdown("#### Variação 12 meses por setor (%)")
    if not df_pim.empty:
        vars12 = {NOMES[c]: var_12m(df_pim, c)
                  for c in CORES_SETORES if c in df_pim.columns and var_12m(df_pim, c) is not None}
        if vars12:
            ord_v = dict(sorted(vars12.items(), key=lambda x: x[1]))
            fig2, ax2 = plt.subplots(figsize=(6, 5))
            fig2.patch.set_facecolor("#0F1117"); ax2.set_facecolor("#0F1117")
            cors = ["#00D4AA" if v >= 0 else "#FF4B6E" for v in ord_v.values()]
            ax2.barh(list(ord_v.keys()), list(ord_v.values()), color=cors, height=0.6)
            for i, (n, v) in enumerate(ord_v.items()):
                ax2.text(v + (0.2 if v >= 0 else -0.2), i, f"{v:+.1f}%",
                         va="center", ha="left" if v >= 0 else "right", color="#CCC", fontsize=8)
            ax2.axvline(0, color="#555", lw=0.8)
            ax2.tick_params(colors="#AAAAAA", labelsize=8)
            ax2.grid(True, color="#FFF", alpha=0.04, lw=0.5, axis="x")
            for sp in ax2.spines.values(): sp.set_edgecolor("#333")
            plt.tight_layout(); st.pyplot(fig2); plt.close()

# Narrativa bloco 1
if df_pim is not None and not df_pim.empty:
    vars12 = {NOMES[c]: var_12m(df_pim, c)
              for c in CORES_SETORES if c in df_pim.columns and var_12m(df_pim, c) is not None}
    if vars12:
        melhor = max(vars12, key=vars12.get)
        pior   = min(vars12, key=vars12.get)
        n_pos  = sum(1 for v in vars12.values() if v > 0)
        n_neg  = sum(1 for v in vars12.values() if v < 0)
        extrat_v = var_12m(df_pim, "Extrativa")
        transf_v = var_12m(df_pim, "Transformacao")
        st.info(
            f"**Leitura da produção industrial (12 meses):**\n\n"
            f"Dos {len(vars12)} segmentos monitorados, **{n_pos} cresceram** e **{n_neg} retraíram**. "
            f"Melhor desempenho: **{melhor}** ({vars12[melhor]:+.1f}%) · "
            f"Pior: **{pior}** ({vars12[pior]:+.1f}%).\n\n"
            + (f"Extrativa ({extrat_v:+.1f}%) e Transformação ({transf_v:+.1f}%) "
               f"{'caminham na mesma direção — ciclo amplo.' if (extrat_v * transf_v > 0) else 'divergem — extrativa pode estar compensando fraqueza na transformação.'} "
               if extrat_v is not None and transf_v is not None else "")
        )

st.markdown("---")

# =============================================================================
# BLOCO 2 — SUBSETORES + ALERTAS DE CICLO
# =============================================================================
st.markdown("### 🔄 Subsetores — Ciclo e Desempenho Comparado")
st.caption("Base 100 = primeiro mês do período · Identifica líderes e retardatários do ciclo industrial")

col3, col4 = st.columns([6, 4])

with col3:
    st.markdown("#### Evolução comparada (base 100)")
    if not df_pf.empty:
        fig3, ax3 = plt.subplots(figsize=(10, 4.5))
        fig3.patch.set_facecolor("#0F1117"); ax3.set_facecolor("#0F1117")
        for col in SUBSETORES:
            if col in df_pf.columns:
                s = df_pf[col].dropna()
                if s.empty or s.iloc[0] == 0: continue
                b100 = s / s.iloc[0] * 100
                ax3.plot(b100.index, b100.values, color=CORES_SETORES[col], lw=1.5, label=NOMES[col])
        ax3.axhline(100, color="#555", lw=0.8, ls="--")
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax3.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax3.tick_params(colors="#AAAAAA", labelsize=9)
        ax3.set_ylabel("Base 100", color="#AAAAAA", fontsize=9)
        ax3.legend(fontsize=7, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9, ncol=2)
        for sp in ax3.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig3); plt.close()

with col4:
    st.markdown("#### Alertas de ciclo")
    if not df_pim.empty:
        alertas_queda, alertas_expansao = [], []
        for col in SUBSETORES:
            if col not in df_pim.columns: continue
            m_q = meses_consecutivos(df_pim, col, "queda")
            m_e = meses_consecutivos(df_pim, col, "expansao")
            if m_q >= 3:
                alertas_queda.append((NOMES[col], m_q))
            elif m_e >= 3:
                alertas_expansao.append((NOMES[col], m_e))

        if alertas_queda:
            st.markdown("**⚠️ Em queda consecutiva (3+ meses):**")
            for nome, meses in sorted(alertas_queda, key=lambda x: -x[1]):
                st.markdown(
                    f"<div style='background:#2a1a1a;border-left:3px solid #FF4B6E;"
                    f"padding:6px 10px;border-radius:4px;margin-bottom:4px;font-size:0.85rem'>"
                    f"🔴 <b>{nome}</b> — {meses} meses em queda</div>", unsafe_allow_html=True)

        if alertas_expansao:
            st.markdown("**✅ Em expansão consecutiva (3+ meses):**")
            for nome, meses in sorted(alertas_expansao, key=lambda x: -x[1]):
                st.markdown(
                    f"<div style='background:#1a2a1a;border-left:3px solid #00D4AA;"
                    f"padding:6px 10px;border-radius:4px;margin-bottom:4px;font-size:0.85rem'>"
                    f"🟢 <b>{nome}</b> — {meses} meses em expansão</div>", unsafe_allow_html=True)

        if not alertas_queda and not alertas_expansao:
            st.info("Nenhum setor com tendência clara de 3+ meses consecutivos.")

        st.markdown("**📊 Classificação do ciclo:**")
        ciclo_data = []
        for col in SUBSETORES:
            if col not in df_pim.columns: continue
            v12 = var_12m(df_pim, col)
            m_e = meses_consecutivos(df_pim, col, "expansao")
            if v12 is None: continue
            if v12 > 5 and m_e >= 2:   ciclo = "🚀 Expansão forte"
            elif v12 > 0:               ciclo = "📈 Expansão moderada"
            elif v12 > -5:              ciclo = "📉 Retração leve"
            else:                       ciclo = "🔴 Retração forte"
            ciclo_data.append({"Setor": NOMES[col], "Var 12m": f"{v12:+.1f}%", "Ciclo": ciclo})
        if ciclo_data:
            st.dataframe(pd.DataFrame(ciclo_data), use_container_width=True,
                        hide_index=True, height=min(300, 35 * len(ciclo_data) + 38))

st.markdown("---")

# =============================================================================
# BLOCO 3 — INDUSTRIA vs PIB + NUCI + ICEI
# =============================================================================
st.markdown("### 📊 Indústria vs Atividade Econômica · Capacidade e Confiança")
st.caption("IBC-Br como proxy mensal do PIB · NUCI = nível de utilização da capacidade instalada")

col5, col6 = st.columns([5, 5])

with col5:
    st.markdown("#### Transformação vs IBC-Br (base 100)")
    st.caption("Indústria lidera ou segue o ciclo econômico?")
    if not df_pf.empty and not df_ibf.empty and "IBC_Br" in df_ibf.columns:
        fig5, ax5 = plt.subplots(figsize=(9, 4))
        fig5.patch.set_facecolor("#0F1117"); ax5.set_facecolor("#0F1117")
        s_t = df_pf["Transformacao"].dropna() if "Transformacao" in df_pf.columns else None
        s_i = df_ibf["IBC_Br"].dropna()
        if s_t is not None and not s_t.empty and not s_i.empty:
            idx = s_t.index.intersection(s_i.index)
            if len(idx) > 0:
                b_t = s_t.loc[idx] / s_t.loc[idx].iloc[0] * 100
                b_i = s_i.loc[idx] / s_i.loc[idx].iloc[0] * 100
                ax5.plot(b_t.index, b_t.values, color="#00D4AA", lw=2, label="Ind. Transformação")
                ax5.plot(b_i.index, b_i.values, color="#FFB800", lw=2, ls="--", label="IBC-Br (proxy PIB)")
                ax5.fill_between(b_t.index, b_t.values, b_i.values,
                                 where=(b_t.values > b_i.values), alpha=0.08, color="#00D4AA")
                ax5.fill_between(b_t.index, b_t.values, b_i.values,
                                 where=(b_t.values <= b_i.values), alpha=0.08, color="#FF4B6E")
                diff = round(float(b_t.iloc[-1] - b_i.iloc[-1]), 1)
        ax5.axhline(100, color="#555", lw=0.8, ls=":")
        ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}"))
        ax5.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax5.grid(True, color="#FFF", alpha=0.05, lw=0.5)
        ax5.tick_params(colors="#AAAAAA", labelsize=9)
        ax5.legend(fontsize=8, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
        for sp in ax5.spines.values(): sp.set_edgecolor("#333")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
        st.pyplot(fig5); plt.close()

        # Narrativa
        try:
            if diff > 3:
                rel = f"Indústria **{diff:.1f}pp acima** do IBC-Br — setor liderando o crescimento."
            elif diff < -3:
                rel = f"Indústria **{abs(diff):.1f}pp abaixo** do IBC-Br — serviços sustentando o PIB."
            else:
                rel = "Indústria e IBC-Br evoluem de forma **alinhada**."
            st.info(
                f"**Indústria vs Atividade Econômica:** {rel}\n\n"
                f"A indústria de transformação é historicamente um **indicador antecedente** do PIB brasileiro — "
                f"variações industriais tendem a preceder o ciclo econômico em 1 a 2 trimestres."
            )
        except Exception:
            pass
    else:
        st.info("Dados do IBC-Br não disponíveis para comparação.")

with col6:
    if not df_inf.empty:
        st.markdown("#### Capacidade Instalada (NUCI)")
        if "NUCI_FGV" in df_inf.columns or "NUCI_CNI" in df_inf.columns:
            fig6, ax6 = plt.subplots(figsize=(9, 2.8))
            fig6.patch.set_facecolor("#0F1117"); ax6.set_facecolor("#0F1117")
            for col, cor, lbl in [("NUCI_FGV","#00D4FF","NUCI FGV"),("NUCI_CNI","#FFB800","NUCI CNI")]:
                if col in df_inf.columns:
                    s = df_inf[col].dropna()
                    ax6.plot(s.index, s.values, color=cor, lw=1.8, label=lbl)
            ax6.axhline(82, color="#FF4B6E", lw=0.8, ls="--", alpha=0.7, label="82% pressão")
            ax6.axhline(78, color="#00D4AA", lw=0.8, ls="--", alpha=0.7, label="78% ociosidade")
            ax6.fill_between(df_inf.index, 78, 82, alpha=0.04, color="#FFB800")
            ax6.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:.0f}%"))
            ax6.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            ax6.tick_params(colors="#AAAAAA", labelsize=8)
            ax6.grid(True, color="#FFF", alpha=0.04, lw=0.5)
            ax6.legend(fontsize=7, facecolor="#1A1D27", edgecolor="#333", labelcolor="#CCC", framealpha=0.9)
            for sp in ax6.spines.values(): sp.set_edgecolor("#333")
            plt.xticks(rotation=30, ha="right"); plt.tight_layout()
            st.pyplot(fig6); plt.close()

        st.markdown("#### ICEI — Confiança do Empresário")
        if "ICEI" in df_inf.columns:
            fig7, ax7 = plt.subplots(figsize=(9, 2.8))
            fig7.patch.set_facecolor("#0F1117"); ax7.set_facecolor("#0F1117")
            s = df_inf["ICEI"].dropna()
            cors_i = ["#00D4AA" if v > 50 else "#FF4B6E" for v in s.values]
            ax7.bar(s.index, s.values, color=cors_i, width=20)
            ax7.axhline(50, color="#555", lw=1.0, ls="--")
            ax7.set_ylabel("ICEI", color="#AAAAAA", fontsize=8)
            ax7.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
            ax7.tick_params(colors="#AAAAAA", labelsize=8)
            ax7.grid(True, color="#FFF", alpha=0.04, lw=0.5)
            for sp in ax7.spines.values(): sp.set_edgecolor("#333")
            plt.xticks(rotation=30, ha="right"); plt.tight_layout()
            st.pyplot(fig7); plt.close()

        if nuci_fgv and icei_v:
            ciclo_n = "pressão sobre custos" if nuci_fgv > 82 else \
                      "ociosidade produtiva" if nuci_fgv < 78 else "equilíbrio operacional"
            conf = "otimistas" if icei_v > 50 else "pessimistas"
            sinal = "favorável para novos investimentos" if icei_v > 50 and nuci_fgv > 80 \
                    else "desfavorável — empresários cautelosos"
            st.info(
                f"**NUCI em {nuci_fgv:.1f}%** → **{ciclo_n}**. "
                f"**ICEI em {icei_v:.1f}** → empresários **{conf}**. "
                f"Ambiente **{sinal}**.\n\n"
                f"NUCI alto + ICEI otimista = momento típico de aceleração de investimentos. "
                f"NUCI baixo + ICEI pessimista = setor em espera, sem expansão de capacidade."
            )

st.markdown("---")

# =============================================================================
# CARDS DIDÁTICOS
# =============================================================================
st.markdown("#### Como interpretar estes indicadores")
ca, cb, cc = st.columns(3)

with ca:
    st.markdown("""
**🏭 PIM-PF — Produção Industrial**

Mede o **volume físico** produzido pela indústria (IBGE) — sem efeito de preços. Base 2012 = 100.

**Setores cíclicos vs defensivos:**
- Veículos e Máquinas reagem forte ao crédito e investimento
- Alimentos e Farmacêuticos são resilientes — demanda essencial
- Petróleo/Derivados segue preço internacional e câmbio

Quedas consecutivas em setores cíclicos antecipam desaceleração do PIB.
""")

with cb:
    zona = "pressão" if nuci_fgv and nuci_fgv > 82 else \
           "ociosidade" if nuci_fgv and nuci_fgv < 78 else "equilíbrio"
    nuci_txt = f"{nuci_fgv:.1f}%" if nuci_fgv else "—"
    st.markdown(f"""
**⚙️ NUCI — Capacidade Instalada**

Mede quanto do parque industrial está efetivamente em uso.

- Acima de 82% → pressão sobre custos, risco inflacionário
- Entre 78% e 82% → zona neutra, operação eficiente
- Abaixo de 78% → ociosidade, baixo incentivo a investir

Com NUCI em {nuci_txt}, indústria em zona de **{zona}**. O BCB monitora esse canal na calibração da Selic.
""")

with cc:
    icei_txt = f"{icei_v:.1f}" if icei_v else "—"
    humor = "otimistas" if icei_v and icei_v > 50 else "pessimistas"
    st.markdown(f"""
**📊 ICEI e Comparativo com PIB**

O ICEI (CNI) mede expectativas dos industriais. Acima de 50 = otimismo. É **indicador antecedente** — empresários otimistas tendem a contratar e investir nos meses seguintes.

Com ICEI em {icei_txt}, os industriais estão **{humor}**.

**Indústria vs IBC-Br:** quando a indústria lidera o IBC-Br, a atividade econômica tende a acelerar. Quando fica abaixo, o crescimento está sendo puxado por serviços.
""")

rodape()
