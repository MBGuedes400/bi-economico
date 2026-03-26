# -*- coding: utf-8 -*-
"""
Home.py — Painel Macroeconômico Brasil
BI Econômico Brasileiro — Impeto Gestão e Negócios
"""

import streamlit as st
import requests
from datetime import datetime
import pytz, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.layout import sidebar_padrao, CSS_GLOBAL, rodape

st.set_page_config(
    page_title="Painel Macro Brasil | Impeto",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
sidebar_padrao(pagina_atual="Home")

# ── CSS da Home ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Estilização do Card como Link */
.card-link {
    display: block;
    background: #1A1D27;
    border: 1px solid #2A2D3A;
    border-radius: 12px;
    padding: 16px 18px 14px;
    margin-bottom: 15px;
    text-decoration: none !important;
    transition: all 0.2s ease-in-out;
    min-height: 140px;
    cursor: pointer;
}
.card-link:hover { 
    border-color: #00D4FF; 
    background: #1E2235; 
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.card-titulo  { font-size: 1.0rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
.card-kpi     { font-size: 1.35rem; font-weight: 800; color: #00D4FF; margin: 4px 0 6px; }
.card-kpi-dev { font-size: 1.0rem; font-weight: 600; color: #555; margin: 4px 0 6px; }
.card-desc    { font-size: 0.77rem; color: #777; line-height: 1.45; }
.secao-titulo {
    font-size: 0.82rem; font-weight: 700; color: #888;
    letter-spacing: 0.1em; text-transform: uppercase;
    margin: 30px 0 10px; padding-bottom: 7px;
    border-bottom: 1px solid #2A2D3A;
}
.badge-novo {
    background: #1E4620; color: #4CAF50;
    font-size: 0.6rem; font-weight: 700;
    padding: 2px 6px; border-radius: 8px;
    margin-left: 7px; vertical-align: middle;
}
.badge-dev {
    background: #2A2000; color: #FF9800;
    font-size: 0.6rem; font-weight: 700;
    padding: 2px 6px; border-radius: 8px;
    margin-left: 7px; vertical-align: middle;
}
.kpi-barra {
    background: #141720; border: 1px solid #2A2D3A;
    border-radius: 8px; padding: 9px 18px;
    font-size: 0.84rem; color: #CCCCCC; margin-bottom: 22px;
}
/* Remove sublinhado padrão de links */
a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)


# ── KPIs ao vivo ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _sgs(cod, n=1):
    try:
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados/ultimos/{n}?formato=json"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        dados = r.json()
        if n == 1:
            return float(dados[0]["valor"])
        return [float(d["valor"]) for d in dados]
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def _ipea(cod, nivel="Brasil"):
    try:
        url = f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{cod}')"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        dados = [x for x in r.json().get("value", []) if x.get("NIVNOME") == nivel]
        return float(sorted(dados, key=lambda x: x["VALDATA"])[-1]["VALVALOR"])
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_kpis():
    k = {}
    k["ipca"]       = _sgs(13522)
    k["selic"]      = _sgs(432)
    k["usd"]        = _sgs(1)
    k["desemprego"] = _sgs(24369)
    ibcbr_13 = _sgs(24363, 13)
    k["ibcbr_var"] = (ibcbr_13[-1] / ibcbr_13[0] - 1) * 100 if ibcbr_13 and len(ibcbr_13) == 13 else None
    m4_mi = _sgs(27813)
    k["m4_tri"] = m4_mi / 1_000_000 if m4_mi else None
    m4_13 = _sgs(27813, 13)
    k["m4_var"] = (m4_13[-1] / m4_13[0] - 1) * 100 if m4_13 and len(m4_13) == 13 else None
    k["inadimp"]   = _sgs(21084)
    k["pobreza"]   = _ipea("PNADCA_TXPNUF")
    k["gini"]      = 0.506
    return k

with st.spinner("Atualizando indicadores ao vivo..."):
    K = carregar_kpis()

def fmt(v, fmt_str):
    if v is None: return "—"
    return fmt_str.format(v)

# ── Cabeçalho ──────────────────────────────────────────────────────────────────
brt = pytz.timezone("America/Sao_Paulo")
agora = datetime.now(brt).strftime("%d/%m/%Y %H:%M")

st.markdown(f"""
<div style='text-align:center;padding:1.8rem 0 0.8rem;'>
  <div style='font-size:2.4rem;'>📊</div>
  <h1 style='font-size:2.1rem;font-weight:800;color:#FFF;margin:.2rem 0;'>
    Painel Macroeconômico Brasil
  </h1>
  <p style='color:#555;font-size:.85rem;margin:0;'>
    Monitoramento econômico integrado · Atualizado em {agora} (horário de Brasília)
  </p>
</div>
""", unsafe_allow_html=True)

partes = []
if K["ipca"]: partes.append(f"<b>IPCA 12m:</b> {K['ipca']:.2f}%")
if K["selic"]: partes.append(f"<b>Selic:</b> {K['selic']:.2f}% a.a.")
if K["usd"]: partes.append(f"<b>Dólar:</b> R$ {K['usd']:.2f}")
if K["desemprego"]: partes.append(f"<b>Desemprego:</b> {K['desemprego']:.1f}%")
if partes:
    st.markdown(f"<div class='kpi-barra'>📡 Ao vivo — {' &nbsp;·&nbsp; '.join(partes)}</div>", unsafe_allow_html=True)


# ── Helper de Card Clicável (HTML Nativo) ─────────────────────────────────────
def card(col, emoji, titulo, kpi_txt, desc, page_file, badge=None):
    badge_html = f"<span class='badge-{badge}'>{badge.upper()}</span>" if badge else ""
    kpi_class = "card-kpi-dev" if (badge == "dev" or kpi_txt in ("—", "Em desenvolvimento")) else "card-kpi"
    
    # Lógica de URL do Streamlit: remove 'pages/', remove números iniciais e '.py'
    # Ex: 'pages/1_Inflacao.py' -> 'Inflacao'
    if page_file and badge != "dev":
        page_name = page_file.replace("pages/", "").replace(".py", "")
        if "_" in page_name:
            page_name = page_name.split("_", 1)[1]
        href = f'href="{page_name}" target="_self"'
    else:
        href = 'style="cursor: default; opacity: 0.6;"'

    html = f"""
    <a {href}>
        <div class="card-link">
            <div class='card-titulo'>{emoji} {titulo}{badge_html}</div>
            <div class='{kpi_class}'>{kpi_txt}</div>
            <div class='card-desc'>{desc}</div>
        </div>
    </a>
    """
    col.markdown(html, unsafe_allow_html=True)


# ── Conteúdo do Painel ────────────────────────────────────────────────────────

# SEÇÃO: MACRO
st.markdown("<div class='secao-titulo'>📈 Indicadores Macroeconômicos</div>", unsafe_allow_html=True)
cols = st.columns(5)
card(cols[0], "📊", "Inflação", fmt(K["ipca"], "{:.2f}% a.a."), "IPCA · Núcleos · Difusão · Decomposição por grupos.", "pages/1_Inflacao.py")
card(cols[1], "🏦", "Juros", fmt(K["selic"], "{:.2f}% a.a."), "Selic meta e efetiva · Curva DI · CDI · Spread bancário.", "pages/2_Juros.py")
card(cols[2], "📈", "Atividade", fmt(K["ibcbr_var"], "{:+.1f}% IBC-Br"), "IBC-Br · PIB trimestral · Índices setoriais.", "pages/3_Atividade.py")
card(cols[3], "👷", "Trabalho", fmt(K["desemprego"], "{:.1f}% desemp."), "Desemprego PNAD · CAGED · Massa salarial.", "pages/4_Mercado_Trabalho.py")
card(cols[4], "🌎", "Externo", fmt(K["usd"], "R$ {:.2f} / USD"), "Balança comercial · Conta corrente · Reservas.", "pages/5_Setor_Externo.py")

# SEÇÃO: ANÁLISES AVANÇADAS
st.markdown("<div class='secao-titulo'>🔬 Análises Avançadas</div>", unsafe_allow_html=True)
cols = st.columns(4)
card(cols[0], "📊", "Comparativos", "Brasil vs mundo", "Brasil vs emergentes · Ranking inflação · Benchmarks.", "pages/6_Comparativos.py")
card(cols[1], "🔬", "Monetárias", fmt(K["m4_tri"], "R$ {:.1f} tri"), "Agregados M1/M2/M4 · Multiplicador · Poupança.", "pages/7_Analises_Monetarias.py")
card(cols[2], "🏗️", "Reais", "Capacidade ociosa", "Indústria · Construção · Capacidade ociosa · Estoques.", "pages/8_Analises_Reais.py")
card(cols[3], "🎯", "Focus", "Projeções vs real", "Projeções do mercado vs realizado · Ranking acertos.", "pages/9_Acuracia_Focus.py")

# SEÇÃO: MERCADO FINANCEIRO
st.markdown("<div class='secao-titulo'>💹 Mercado Financeiro</div>", unsafe_allow_html=True)
cols = st.columns(5)
card(cols[0], "📉", "Ações", "Ibovespa", "Histórico · Top 8 ações · Volatilidade · Prêmio de risco.", "pages/10_Ibovespa.py")
card(cols[1], "💼", "Fundos", "Captação líquida", "Captação por categoria · PL consolidado · Evolução.", "pages/11_Fundos.py")
card(cols[2], "💧", "Liquidez", fmt(K["m4_var"], "{:.1f}% a.a."), "M4 · Poupança · Multiplicador monetário.", "pages/12_Liquidez.py")
card(cols[3], "🏧", "Crédito", fmt(K["inadimp"], "{:.1f}% inad."), "Crédito PF/PJ · Livre vs Direcionado · +90 dias.", "pages/13_Credito.py")
card(cols[4], "🌽", "Commodities", "Base 100", "Soja · Milho · Trigo · Petróleo · Ouro.", "pages/14_Commodities.py")

# SEÇÃO: SETORIAL
st.markdown("<div class='secao-titulo'>🏭 Setorial</div>", unsafe_allow_html=True)
cols = st.columns(3)
card(cols[0], "⚙️", "Indústria", "PIM-PF", "PIM-PF · NUCI · ICEI · Ciclo industrial.", "pages/15_Industria.py")
card(cols[1], "🛒", "Varejo", "PMC", "PMC · ICC FGV · Endividamento familiar CNC.", "pages/16_Comercio.py")
card(cols[2], "🌾", "Agro", "LSPA · VBP", "Safra atual · Top culturas PAM · Balança agrícola.", "pages/17_Agropecuaria.py")

# SEÇÃO: SOCIAL
st.markdown("<div class='secao-titulo'>🫂 Análise Social <span class='badge-novo'>NOVO</span></div>", unsafe_allow_html=True)
cols = st.columns(3)
card(cols[0], "📊", "Diagnóstico", f"Gini: {K['gini']:.3f}", "Gini · Curva de Lorenz · Rendimento · Pobreza.", "pages/20_Social_Diagnostico.py", badge="novo")
card(cols[1], "🗺️", "Vulnerabilidade", "Analfab.: MA 16.1% × SC 2.0%", "6 indicadores por UF · ICV composto · Ranking estadual.", "pages/21_Social_Vulnerabilidade.py", badge="novo")
card(cols[2], "🏛️", "Políticas", "BF: R$ 168.7 bi · MA dep. 9.3%", "Multiplicador Bolsa Família · Fronteira de eficiência alocativa.", "pages/22_Social_Politicas.py", badge="novo")

rodape()