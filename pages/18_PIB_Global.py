# -*- coding: utf-8 -*-
"""
18_PIB_Global.py
BI Econômico Brasileiro — Impeto Gestão e Negócios
Página: PIB Global & Comparativos Internacionais

Fonte primária : World Development Indicators — Banco Mundial (atualizado 02/2026)
                 Arquivo CSV: data/worldbank_data.csv
Indicadores    : GDP growth, GNI/PPP per capita, Inflação, Life expectancy,
                 Exports, Gross capital formation, High-tech exports, FDI
Juros BC       : dados auditados mar/2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import warnings, sys, os

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.layout import sidebar_padrao, CSS_GLOBAL

# ── Estilo ─────────────────────────────────────────────────────────────────────
FUNDO      = "#0E1117"
FUNDO_CARD = "#1E2130"
TEXTO      = "#FAFAFA"
GRID_COLOR = "#2E3347"

def fig_estilo(fig, ax_list=None):
    fig.patch.set_facecolor(FUNDO)
    for ax in (ax_list or fig.axes):
        ax.set_facecolor(FUNDO_CARD)
        ax.tick_params(colors=TEXTO, labelsize=9)
        ax.xaxis.label.set_color(TEXTO)
        ax.yaxis.label.set_color(TEXTO)
        ax.title.set_color(TEXTO)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.6)

# ══════════════════════════════════════════════════════════════════════════════
# PAÍSES
# ══════════════════════════════════════════════════════════════════════════════
PAISES = {
    "BR": {"nome":"Brasil",         "emoji":"🇧🇷","regiao":"América Latina",  "wb_name":"Brazil"},
    "US": {"nome":"EUA",            "emoji":"🇺🇸","regiao":"América do Norte","wb_name":"United States"},
    "CN": {"nome":"China",          "emoji":"🇨🇳","regiao":"Ásia",            "wb_name":"China"},
    "DE": {"nome":"Alemanha",       "emoji":"🇩🇪","regiao":"Europa",          "wb_name":"Germany"},
    "JP": {"nome":"Japão",          "emoji":"🇯🇵","regiao":"Ásia",            "wb_name":"Japan"},
    "IN": {"nome":"Índia",          "emoji":"🇮🇳","regiao":"Ásia",            "wb_name":"India"},
    "GB": {"nome":"Reino Unido",    "emoji":"🇬🇧","regiao":"Europa",          "wb_name":"United Kingdom"},
    "FR": {"nome":"França",         "emoji":"🇫🇷","regiao":"Europa",          "wb_name":"France"},
    "IT": {"nome":"Itália",         "emoji":"🇮🇹","regiao":"Europa",          "wb_name":"Italy"},
    "ES": {"nome":"Espanha",        "emoji":"🇪🇸","regiao":"Europa",          "wb_name":"Spain"},
    "CA": {"nome":"Canadá",         "emoji":"🇨🇦","regiao":"América do Norte","wb_name":"Canada"},
    "AU": {"nome":"Austrália",      "emoji":"🇦🇺","regiao":"Oceania",         "wb_name":"Australia"},
    "KR": {"nome":"Coreia do Sul",  "emoji":"🇰🇷","regiao":"Ásia",            "wb_name":"Korea, Rep."},
    "RU": {"nome":"Rússia",         "emoji":"🇷🇺","regiao":"Europa/Ásia",     "wb_name":"Russian Federation"},
    "MX": {"nome":"México",         "emoji":"🇲🇽","regiao":"América Latina",  "wb_name":"Mexico"},
    "AR": {"nome":"Argentina",      "emoji":"🇦🇷","regiao":"América Latina",  "wb_name":"Argentina"},
    "CL": {"nome":"Chile",          "emoji":"🇨🇱","regiao":"América Latina",  "wb_name":"Chile"},
    "CO": {"nome":"Colômbia",       "emoji":"🇨🇴","regiao":"América Latina",  "wb_name":"Colombia"},
    "ZA": {"nome":"África do Sul",  "emoji":"🇿🇦","regiao":"África",          "wb_name":"South Africa"},
}
PAISES_DEFAULT = ["BR","US","CN","DE","IN","JP","GB","AR","MX"]

CORES = {
    "BR":"#009C3B","US":"#3C3B6E","CN":"#DE2910","DE":"#FFCE00","JP":"#BC002D",
    "IN":"#FF9933","GB":"#012169","FR":"#002395","IT":"#009246","ES":"#C60B1E",
    "CA":"#FF0000","AU":"#00008B","KR":"#003478","RU":"#D52B1E","MX":"#006847",
    "AR":"#74ACDF","CL":"#D52B1E","CO":"#FCD116","ZA":"#007A4D",
}

JUROS_BC = {
    "BR":{"banco":"BCB — Selic",   "taxa":13.25,"tend":"→"},
    "US":{"banco":"Fed Funds",     "taxa": 4.25,"tend":"↓"},
    "CN":{"banco":"PBoC LPR 1a",   "taxa": 3.10,"tend":"↓"},
    "DE":{"banco":"BCE Depo",      "taxa": 2.50,"tend":"↓"},
    "JP":{"banco":"BoJ Policy",    "taxa": 0.50,"tend":"↑"},
    "IN":{"banco":"RBI Repo",      "taxa": 6.25,"tend":"↓"},
    "GB":{"banco":"BoE Bank Rate", "taxa": 4.50,"tend":"↓"},
    "FR":{"banco":"BCE Depo",      "taxa": 2.50,"tend":"↓"},
    "IT":{"banco":"BCE Depo",      "taxa": 2.50,"tend":"↓"},
    "ES":{"banco":"BCE Depo",      "taxa": 2.50,"tend":"↓"},
    "CA":{"banco":"BoC Policy",    "taxa": 2.75,"tend":"↓"},
    "AU":{"banco":"RBA Cash",      "taxa": 4.10,"tend":"↓"},
    "KR":{"banco":"BoK Base",      "taxa": 2.75,"tend":"↓"},
    "RU":{"banco":"CBR Key Rate",  "taxa":21.00,"tend":"→"},
    "MX":{"banco":"Banxico",       "taxa": 9.00,"tend":"↓"},
    "AR":{"banco":"BCRA",          "taxa":29.00,"tend":"↓"},
    "CL":{"banco":"BCCh TPM",      "taxa": 5.00,"tend":"→"},
    "CO":{"banco":"BanRep",        "taxa": 9.25,"tend":"↓"},
    "ZA":{"banco":"SARB Repo",     "taxa": 7.50,"tend":"↓"},
}

# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DO CSV
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400, show_spinner=False)
def carregar_csv() -> pd.DataFrame:
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "data", "worldbank_data.csv")
    try:
        return pd.read_csv(caminho, encoding="latin-1", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def _val(df, indicador, wb_name, ano):
    col = f"{ano} [YR{ano}]"
    row = df[(df["Series Name"] == indicador) & (df["Country Name"] == wb_name)]
    if row.empty: return np.nan
    try:
        v = float(row.iloc[0].get(col, ".."))
        return v if not np.isnan(v) else np.nan
    except: return np.nan

def extrair(df_wb, indicador, paises_sel, ano="2024"):
    return {c: v for c in paises_sel
            if not np.isnan(v := _val(df_wb, indicador, PAISES.get(c,{}).get("wb_name",""), ano))}

def extrair_hist(df_wb, indicador, paises_sel):
    anos_cols = [c for c in df_wb.columns if "YR" in str(c) and "2025" not in c]
    result = {}
    for cod in paises_sel:
        wb = PAISES.get(cod, {}).get("wb_name", "")
        sub = df_wb[(df_wb["Series Name"] == indicador) & (df_wb["Country Name"] == wb)]
        if sub.empty: continue
        row = sub.iloc[0]
        linha = {}
        for col in anos_cols:
            try:
                v = float(row.get(col, ".."))
                if not np.isnan(v):
                    linha[int(col.split()[0])] = v
            except: pass
        if linha: result[cod] = linha
    return pd.DataFrame(result).T

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="PIB Global | BI Econômico", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

def _filtros():
    st.multiselect("Países:", options=list(PAISES.keys()), default=PAISES_DEFAULT,
                   format_func=lambda c: f"{PAISES[c]['emoji']} {PAISES[c]['nome']}",
                   key="paises_sel")
    st.divider()
    st.caption("**Fonte:** World Development Indicators\nBanco Mundial · Atualizado 02/2026")

sidebar_padrao(pagina_atual="PIB_Global", filtros_extra=_filtros)
paises_sel = st.session_state.get("paises_sel", PAISES_DEFAULT) or PAISES_DEFAULT

st.title("🌍 PIB Global — Crescimento e Comparativos Internacionais")
st.caption("World Development Indicators — Banco Mundial · 19 países · Dados até 2024")

st.info("""
**O que este painel mede?**

O Brasil não cresce em isolamento — seu desempenho é moldado pelo ciclo econômico global.
Este painel compara **crescimento do PIB, renda per capita, inflação, abertura comercial,
investimento, intensidade tecnológica e juros** entre os principais países, situando o
Brasil frente a emergentes, desenvolvidos e vizinhos latino-americanos.

Dados do **World Development Indicators (Banco Mundial)**, atualizados em fevereiro de 2026,
com cobertura de 2016 a 2024 para a maioria dos indicadores.
""")

# ── Carregar ──────────────────────────────────────────────────────────────────
with st.spinner("Carregando World Development Indicators..."):
    df_wb = carregar_csv()

if df_wb.empty:
    st.error("Arquivo `data/worldbank_data.csv` não encontrado. Verifique se o arquivo está na pasta `data/` do projeto.")
    st.stop()

# Extrair todas as séries
cresc24  = extrair(df_wb, "GDP growth (annual %)",                         paises_sel, "2024")
cresc23  = extrair(df_wb, "GDP growth (annual %)",                         paises_sel, "2023")
gni_ppp  = extrair(df_wb, "GNI per capita, PPP (current international $)", paises_sel, "2024")
inflacao = extrair(df_wb, "Inflation, GDP deflator (annual %)",             paises_sel, "2024")
exports  = extrair(df_wb, "Exports of goods and services (% of GDP)",       paises_sel, "2024")
invest   = extrair(df_wb, "Gross capital formation (% of GDP)",             paises_sel, "2024")
hitech   = extrair(df_wb, "High-technology exports (% of manufactured exports)", paises_sel, "2024")
militar  = extrair(df_wb, "Military expenditure (% of GDP)",                paises_sel, "2024")
fdi      = extrair(df_wb, "Foreign direct investment, net inflows (BoP, current US$)", paises_sel, "2024")
le_2023  = extrair(df_wb, "Life expectancy at birth, total (years)",        paises_sel, "2023")
df_hist  = extrair_hist(df_wb, "GDP growth (annual %)",                     paises_sel)

# ── KPIs ──────────────────────────────────────────────────────────────────────
br_c  = cresc24.get("BR")
us_g  = gni_ppp.get("US")
br_g  = gni_ppp.get("BR")
med_c = np.mean(list(cresc24.values())) if cresc24 else None
top   = max(cresc24, key=cresc24.get) if cresc24 else None
bot   = min(cresc24, key=cresc24.get) if cresc24 else None

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🇧🇷 Brasil PIB 2024", f"{br_c:.1f}%" if br_c else "—",
          f"{br_c-med_c:+.1f}pp vs média" if br_c and med_c else None)
c2.metric("📊 Média do grupo",   f"{med_c:.1f}%" if med_c else "—")
if top:
    c3.metric("🏆 Maior crescimento", f"{PAISES[top]['emoji']} {PAISES[top]['nome']}", f"{cresc24[top]:.1f}%")
if bot:
    c4.metric("📉 Menor crescimento", f"{PAISES[bot]['emoji']} {PAISES[bot]['nome']}", f"{cresc24[bot]:.1f}%", delta_color="inverse")
c5.metric("🇧🇷 GNI/cap PPP vs EUA", f"US$ {br_g:,.0f}" if br_g else "—",
          f"{br_g/us_g*100:.0f}% do nível EUA" if br_g and us_g else None)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# ABAS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Crescimento PIB",
    "💰 Renda & Bem-estar",
    "🏗️ Estrutura Econômica",
    "🏦 Juros & Risco",
])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("📈 Crescimento do PIB Real (%) — 2023 vs 2024 e Histórico")

    col_a, col_b = st.columns(2)

    with col_a:
        paises_c = [c for c in paises_sel if c in cresc24]
        df_c = pd.DataFrame({"cod":paises_c,
                              "2024":[cresc24.get(c,np.nan) for c in paises_c],
                              "2023":[cresc23.get(c,np.nan) for c in paises_c],
                              }).dropna(subset=["2024"]).sort_values("2024",ascending=True)
        y = np.arange(len(df_c)); h=0.35
        fig,ax = plt.subplots(figsize=(6, len(df_c)*0.48+0.5))
        fig_estilo(fig,[ax])
        ax.barh(y-h/2, df_c["2023"], h, color="#607D8B", alpha=0.7, label="2023")
        bars24 = ax.barh(y+h/2, df_c["2024"], h,
                         color=[CORES.get(c,"#888") for c in df_c["cod"]], alpha=0.9, label="2024")
        for bar,val in zip(bars24, df_c["2024"]):
            ax.text(val+0.1, bar.get_y()+bar.get_height()/2, f"{val:.1f}%", va="center",fontsize=7.5,color=TEXTO)
        ax.axvline(0,color=TEXTO,lw=0.8,alpha=0.5)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{PAISES[c]['emoji']} {PAISES[c]['nome']}" for c in df_c["cod"]],fontsize=8)
        ax.set_xlabel("Crescimento PIB real (%)",color=TEXTO)
        ax.legend(fontsize=8,facecolor=FUNDO_CARD,labelcolor=TEXTO)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.1f}%"))
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with col_b:
        anos_h = sorted([c for c in df_hist.columns if isinstance(c,int) and c>=2016])
        fig2,ax2 = plt.subplots(figsize=(7,5))
        fig_estilo(fig2,[ax2])
        for cod in paises_sel:
            if cod not in df_hist.index: continue
            vals=[df_hist.loc[cod,a] if a in df_hist.columns else np.nan for a in anos_h]
            ax2.plot(anos_h,vals,color=CORES.get(cod,"#888"),
                     lw=2.5 if cod=="BR" else 1.2,
                     alpha=1.0 if cod=="BR" else 0.65,
                     marker="o",markersize=4 if cod=="BR" else 2.5,
                     label=f"{PAISES[cod]['emoji']} {PAISES[cod]['nome']}")
        ax2.axhline(0,color=TEXTO,lw=0.8,ls="--",alpha=0.4)
        ax2.set_ylabel("Crescimento PIB real (%)",color=TEXTO)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.1f}%"))
        ax2.legend(fontsize=7.5,facecolor=FUNDO_CARD,labelcolor=TEXTO,loc="lower right",ncol=2)
        plt.tight_layout(); st.pyplot(fig2); plt.close()

    br24=cresc24.get("BR",0); de24=cresc24.get("DE",0); in24=cresc24.get("IN",0); ar24=cresc24.get("AR",0)
    st.info(f"""
**Leitura do Ciclo 2024**

**Brasil ({br24:.1f}%)** cresceu acima da média do grupo, sustentado pelo agronegócio, mercado
de trabalho aquecido e demanda interna resiliente — mesmo com a Selic em patamar restritivo.

**Índia ({in24:.1f}%)** e China continuam como principais motores globais. A **Alemanha
({de24:.1f}%)** enfrenta desindustrialização estrutural: encarecimento energético e
perda de competitividade na manufatura pesada.

**Argentina ({ar24:.1f}%)** atravessa ajuste fiscal severo com contração do PIB — reflexo
das reformas em curso para estabilização macroeconômica.
    """)

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("💰 Renda per capita, Inflação e Expectativa de Vida")
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("**GNI per capita PPP (US$ internacionais, 2024)**")
        df_g = pd.DataFrame({"cod":[c for c in paises_sel if c in gni_ppp],
                              "val":[gni_ppp[c] for c in paises_sel if c in gni_ppp],
                              }).sort_values("val",ascending=True)
        fig3,ax3 = plt.subplots(figsize=(6,len(df_g)*0.42+0.5))
        fig_estilo(fig3,[ax3])
        bars_g = ax3.barh([f"{PAISES[c]['emoji']} {PAISES[c]['nome']}" for c in df_g["cod"]],
                           df_g["val"], color=[CORES.get(c,"#888") for c in df_g["cod"]], height=0.7)
        for bar,val,cod in zip(bars_g,df_g["val"],df_g["cod"]):
            bar.set_edgecolor("#FFD700" if cod=="BR" else "none")
            bar.set_linewidth(2 if cod=="BR" else 0)
            ax3.text(val+200,bar.get_y()+bar.get_height()/2,
                     f"US${val:,.0f}",va="center",fontsize=7.5,color=TEXTO)
        ax3.set_xlabel("US$ internacionais (PPP)",color=TEXTO)
        ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"US${v/1000:.0f}k"))
        ax3.set_xlim(0,df_g["val"].max()*1.18)
        plt.tight_layout(); st.pyplot(fig3); plt.close()

    with col_r2:
        st.markdown("**Inflação — Deflator do PIB (%, 2024)**")
        df_i = pd.DataFrame({"cod":[c for c in paises_sel if c in inflacao],
                              "val":[inflacao[c] for c in paises_sel if c in inflacao],
                              }).sort_values("val",ascending=True)
        norm_i = mcolors.Normalize(vmin=0,vmax=min(df_i["val"].max(),25))
        cmap_i = cm.get_cmap("RdYlGn_r")
        fig4,ax4 = plt.subplots(figsize=(6,len(df_i)*0.42+0.5))
        fig_estilo(fig4,[ax4])
        ax4.barh([f"{PAISES[c]['emoji']} {PAISES[c]['nome']}" for c in df_i["cod"]],
                  df_i["val"], height=0.7,
                  color=[cmap_i(norm_i(min(v,25))) for v in df_i["val"]])
        for bar,val in zip(ax4.patches,df_i["val"]):
            ax4.text(val+0.1,bar.get_y()+bar.get_height()/2,
                     f"{val:.1f}%",va="center",fontsize=7.5,color=TEXTO)
        ax4.axvline(2,color="#4CAF50",lw=1,ls="--",alpha=0.8,label="Meta 2%")
        ax4.legend(fontsize=8,facecolor=FUNDO_CARD,labelcolor=TEXTO)
        ax4.set_xlabel("Deflator do PIB (%)",color=TEXTO)
        plt.tight_layout(); st.pyplot(fig4); plt.close()

    if le_2023:
        st.markdown("**Expectativa de Vida ao Nascer (anos, 2023)**")
        df_le = pd.DataFrame({"cod":[c for c in paises_sel if c in le_2023],
                               "val":[le_2023[c] for c in paises_sel if c in le_2023],
                               }).sort_values("val",ascending=True)
        norm_le = mcolors.Normalize(vmin=df_le["val"].min()-1,vmax=df_le["val"].max()+1)
        fig5,ax5 = plt.subplots(figsize=(10,2.8))
        fig_estilo(fig5,[ax5])
        ax5.barh([f"{PAISES[c]['emoji']} {PAISES[c]['nome']}" for c in df_le["cod"]],
                  df_le["val"],height=0.7,
                  color=[cm.get_cmap("RdYlGn")(norm_le(v)) for v in df_le["val"]])
        for bar,val,cod in zip(ax5.patches,df_le["val"],df_le["cod"]):
            ax5.text(val+0.1,bar.get_y()+bar.get_height()/2,
                     f"{val:.1f}",va="center",fontsize=8,color=TEXTO,
                     fontweight="bold" if cod=="BR" else "normal")
        ax5.set_xlabel("Anos",color=TEXTO)
        ax5.set_xlim(df_le["val"].min()-3,df_le["val"].max()+3)
        plt.tight_layout(); st.pyplot(fig5); plt.close()

    br_g_v=gni_ppp.get("BR",0); jp_le=le_2023.get("JP",84); br_le=le_2023.get("BR",75.8); ar_inf=inflacao.get("AR",0)
    st.info(f"""
**Renda, Preços e Longevidade — O Triângulo do Desenvolvimento**

O GNI per capita em PPP elimina distorções cambiais e compara o poder de compra real.
O **Brasil com US$ {br_g_v:,.0f}** está na faixa intermediária dos emergentes, mas o dado
médio esconde a desigualdade estrutural — a renda da maioria está bem abaixo da média.

**Argentina ({ar_inf:.0f}% de deflator)** ilustra o caso extremo de desancoragem: a indexação
generalizada torna a desinflação estruturalmente difícil mesmo com aperto severo.

**Japão ({jp_le:.1f} anos)** representa o benchmark global de longevidade.
O **Brasil ({br_le:.1f} anos)** recuperou o nível pré-pandemia, mas carrega diferenciais
regionais de até 8 anos entre estados — reflexo direto das desigualdades sociais.
    """)

# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("🏗️ Abertura Comercial, Investimento e Tecnologia (2024)")
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("**Exportações % PIB vs Formação de Capital % PIB**")
        paises_e = [c for c in paises_sel if c in exports and c in invest]
        if paises_e:
            fig6,ax6 = plt.subplots(figsize=(6,5))
            fig_estilo(fig6,[ax6])
            for cod in paises_e:
                ax6.scatter(exports[cod],invest[cod],color=CORES.get(cod,"#888"),s=100,
                            edgecolors="#FFD700" if cod=="BR" else "none",
                            linewidths=2 if cod=="BR" else 0, zorder=5)
                ax6.annotate(f"{PAISES[cod]['emoji']} {cod}",
                             xy=(exports[cod],invest[cod]),xytext=(4,3),
                             textcoords="offset points",fontsize=8,color=TEXTO)
            ax6.axvline(np.mean(list(exports.values())),color="white",lw=0.8,ls=":",alpha=0.4)
            ax6.axhline(np.mean(list(invest.values())),color="white",lw=0.8,ls=":",alpha=0.4)
            ax6.set_xlabel("Exportações (% PIB)",color=TEXTO)
            ax6.set_ylabel("Formação Bruta de Capital (% PIB)",color=TEXTO)
            ax6.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.0f}%"))
            ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.0f}%"))
            plt.tight_layout(); st.pyplot(fig6); plt.close()

    with col_e2:
        st.markdown("**Exportações de Alta Tecnologia (% manufaturas, 2024)**")
        df_ht = pd.DataFrame({"cod":[c for c in paises_sel if c in hitech],
                               "val":[hitech[c] for c in paises_sel if c in hitech],
                               }).sort_values("val",ascending=True)
        norm_ht = mcolors.Normalize(vmin=0,vmax=df_ht["val"].max())
        fig7,ax7 = plt.subplots(figsize=(6,len(df_ht)*0.42+0.5))
        fig_estilo(fig7,[ax7])
        ax7.barh([f"{PAISES[c]['emoji']} {PAISES[c]['nome']}" for c in df_ht["cod"]],
                  df_ht["val"],height=0.7,
                  color=[cm.get_cmap("YlOrRd")(norm_ht(v)) for v in df_ht["val"]])
        for bar,val,cod in zip(ax7.patches,df_ht["val"],df_ht["cod"]):
            ax7.text(val+0.2,bar.get_y()+bar.get_height()/2,
                     f"{val:.1f}%",va="center",fontsize=7.5,color=TEXTO,
                     fontweight="bold" if cod=="BR" else "normal")
        ax7.set_xlabel("% das exportações manufaturadas",color=TEXTO)
        plt.tight_layout(); st.pyplot(fig7); plt.close()

    br_exp=exports.get("BR",0); br_inv=invest.get("BR",0); br_ht=hitech.get("BR",0)
    cn_ht=hitech.get("CN",0); kr_ht=hitech.get("KR",0)
    med_exp=np.mean(list(exports.values())) if exports else 0
    st.info(f"""
**Estrutura Econômica — Onde o Brasil Precisa Avançar**

**Abertura comercial:** o Brasil exporta **{br_exp:.1f}% do PIB** — abaixo da média do grupo
({med_exp:.1f}%). Isso reflete uma economia voltada ao mercado interno, com barreiras tarifárias
e custos logísticos que reduzem a competitividade exportadora.

**Investimento:** com **{br_inv:.1f}% do PIB** em formação bruta de capital, o Brasil está aquém
de economias comparáveis. Juros reais elevados encarecem o crédito e comprimem o investimento
privado — o principal gargalo para o crescimento sustentado de longo prazo.

**Tecnologia:** apenas **{br_ht:.1f}%** das manufaturas brasileiras são de alta tecnologia,
contra {cn_ht:.1f}% da China e {kr_ht:.1f}% da Coreia do Sul. A especialização em commodities
vulnerabiliza o país a choques de termos de troca.
    """)

# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("🏦 Juros de Referência — Bancos Centrais (mar/2026)")

    df_j = pd.DataFrame([
        {"cod":c,"nome":PAISES[c]["nome"],"emoji":PAISES[c]["emoji"],
         "banco":JUROS_BC[c]["banco"],"taxa":JUROS_BC[c]["taxa"],"tend":JUROS_BC[c]["tend"]}
        for c in paises_sel if c in JUROS_BC
    ]).sort_values("taxa",ascending=True)

    col_j1, col_j2 = st.columns([1.5,1])

    with col_j1:
        norm_j = mcolors.Normalize(vmin=0,vmax=df_j["taxa"].max())
        cmap_j = cm.get_cmap("RdYlGn_r")
        fig8,ax8 = plt.subplots(figsize=(8,len(df_j)*0.45+0.5))
        fig_estilo(fig8,[ax8])
        bars_j = ax8.barh([f"{r['emoji']} {r['nome']}" for _,r in df_j.iterrows()],
                           df_j["taxa"],height=0.7,
                           color=[cmap_j(norm_j(v)) for v in df_j["taxa"]])
        for bar,(_,row) in zip(bars_j,df_j.iterrows()):
            if row["cod"]=="BR":
                bar.set_edgecolor("#FFD700"); bar.set_linewidth(2)
            ax8.text(row["taxa"]+0.1,bar.get_y()+bar.get_height()/2,
                     f"{row['taxa']:.2f}% {row['tend']}",va="center",fontsize=8.5,color=TEXTO)
        ax8.set_xlabel("Taxa de referência (% a.a.)",color=TEXTO)
        ax8.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f"{v:.1f}%"))
        ax8.set_xlim(0,df_j["taxa"].max()*1.2)
        plt.tight_layout(); st.pyplot(fig8); plt.close()

    with col_j2:
        df_tab=df_j[["emoji","nome","banco","taxa","tend"]].copy()
        df_tab.columns=["","País","Banco Central","Taxa (%)","Tend."]
        df_tab["Taxa (%)"]=df_tab["Taxa (%)"].map(lambda v:f"{v:.2f}%")
        st.dataframe(df_tab,use_container_width=True,hide_index=True,height=480)

    br_j=JUROS_BC.get("BR",{}).get("taxa",13.25); us_j=JUROS_BC.get("US",{}).get("taxa",4.25)
    ru_j=JUROS_BC.get("RU",{}).get("taxa",21.0);  jp_j=JUROS_BC.get("JP",{}).get("taxa",0.50)
    st.info(f"""
**O Mapa dos Juros e o Diferencial Brasileiro**

O **Brasil mantém a Selic em {br_j:.2f}% a.a.** — um dos maiores spreads reais do mundo.
O diferencial frente ao Fed ({us_j:.2f}%) é de **{br_j-us_j:.2f} p.p.**, atraindo capital
externo de curto prazo, mas penalizando o investimento doméstico e elevando o custo da
dívida pública.

**Rússia ({ru_j:.0f}%)** — juros extremamente elevados como resposta à inflação de guerra e
pressão sobre o rublo. **Japão ({jp_j:.2f}%)** normalizando gradualmente após décadas de
taxa zero, com impactos globais no carry trade iene/dólar.

**Tendências:** a maioria dos BCs sinaliza cortes em 2025–2026. O Brasil, na contramão,
reiniciou ciclo de alta por desancoragem das expectativas inflacionárias — reforçando o
prêmio de risco e o custo de capital doméstico.
    """)

# ── Metodologia ───────────────────────────────────────────────────────────────
st.divider()
with st.expander("📋 Metodologia e Fontes"):
    st.markdown("""
    | Indicador | Código WDI | Cobertura |
    |---|---|---|
    | Crescimento PIB real | `NY.GDP.MKTP.KD.ZG` | 2016–2024 |
    | GNI per capita PPP | `NY.GNP.PCAP.PP.CD` | 2016–2024 |
    | Inflação (deflator PIB) | `NY.GDP.DEFL.KD.ZG` | 2016–2024 |
    | Exportações % PIB | `NE.EXP.GNFS.ZS` | 2016–2024 |
    | Formação bruta de capital % PIB | `NE.GDI.TOTL.ZS` | 2016–2024 |
    | Exportações alta tecnologia % | `TX.VAL.TECH.MF.ZS` | 2016–2024 |
    | Expectativa de vida | `SP.DYN.LE00.IN` | até 2023 |
    | Juros de referência | Bancos centrais nacionais | mar/2026 |

    **Fonte dos dados:** World Development Indicators — Banco Mundial (atualizado fev/2026)
    Arquivo: `data/worldbank_data.csv`

    **GNI per capita PPP:** renda nacional bruta per capita em paridade de poder de compra —
    medida mais adequada para comparações internacionais pois elimina distorções cambiais.
    """)
