import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd

# 1. CONFIGURATION VISUELLE & ESPACEMENT
st.set_page_config(page_title="Horizon Finance", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #000000; font-family: 'Inter', sans-serif; }
    
    /* ESPACEMENT ENTRE SECTIONS */
    .section-spacer { margin-top: 60px; }
    
    /* PATRIMOINE HERO */
    .hero-container { text-align: center; padding: 40px 0 10px 0; }
    .total-label { color: #8E8E93; font-size: 0.9em; font-weight: 700; letter-spacing: 4px; }
    .total-amount { font-size: 7.5em !important; font-weight: 900; letter-spacing: -6px; color: #ffffff; margin: 0; line-height: 0.8; }
    
    /* CARTES ET BLOCS */
    .section-title { color: #8E8E93; font-weight: 700; font-size: 0.85em; letter-spacing: 2px; margin-bottom: 20px; text-transform: uppercase; }
    .card-premium { background: #111111; border: 1px solid #222222; border-radius: 24px; padding: 25px; }
    
    /* CONSEILLER */
    .advice-row { display: flex; justify-content: space-between; margin-top: 20px; gap: 15px; }
    .advice-item { background: #1c1c1e; padding: 15px; border-radius: 16px; flex: 1; text-align: center; border: 1px solid #2c2c2e; }
    .advice-val { font-weight: 800; color: #ffffff; font-size: 1.2em; }
    .advice-lab { color: #8E8E93; font-size: 0.7em; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9em; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DONNÉES
tickers_map = {
    "Streamwide": "ALSTW.PA", "Chevron": "CVX", "Alphabet (A)": "GOOGL", "Nvidia": "NVDA",
    "Total Energie": "TTE.PA", "Apple": "AAPL", "Riot Platforms": "RIOT", "Physical Silver": "PHAG.L",
    "Microsoft": "MSFT", "Prosus": "PRX.AS", "Air Liquide": "AI.PA", "FTSE EUR": "VEUR.AS",
    "XIAOMI": "1810.HK", "MSCI CHINA": "ICHA.AS", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Bitcoin": "BTC-USD"
}

bourse_data = [
    {"nom": "Streamwide", "valeur": 629.91, "perf": "+109.97%"}, {"nom": "Chevron", "valeur": 454.73, "perf": "-8.87%"},
    {"nom": "Alphabet (A)", "valeur": 438.71, "perf": "+74.88%"}, {"nom": "Nvidia", "valeur": 343.03, "perf": "+24.29%"},
    {"nom": "Total Energie", "valeur": 276.39, "perf": "-0.92%"}, {"nom": "Apple", "valeur": 261.78, "perf": "+11.40%"},
    {"nom": "Riot Platforms", "valeur": 255.12, "perf": "+6.75%"}, {"nom": "Physical Silver", "valeur": 230.75, "perf": "+54.92%"},
    {"nom": "Microsoft", "valeur": 109.98, "perf": "-0.92%"}, {"nom": "Prosus", "valeur": 108.18, "perf": "-6.61%"},
    {"nom": "Air Liquide", "valeur": 97.87, "perf": "-2.13%"}, {"nom": "FTSE EUR", "valeur": 70.89, "perf": "+4.24%"},
    {"nom": "XIAOMI", "valeur": 39.44, "perf": "-12.35%"}, {"nom": "MSCI CHINA", "valeur": 29.93, "perf": "-0.21%"},
]
crypto_data = [{"nom": "Ethereum", "valeur": 672.20, "perf": "+9.73%"}, {"nom": "Solana", "valeur": 304.01, "perf": "+4.92%"}, {"nom": "Bitcoin", "valeur": 246.96, "perf": "-5.20%"}]
total_bourse = sum(d['valeur'] for d in bourse_data)
total_crypto = sum(d['valeur'] for d in crypto_data)
immo_val, royaltiz_val = 1595, 200
patrimoine_total = total_bourse + total_crypto + immo_val + royaltiz_val
objectif_cible = 100000

# 3. HEADER HERO
st.markdown(f"""
    <div class="hero-container">
        <p class="total-label">PATRIMOINE NET</p>
        <p class="total-amount">{patrimoine_total:,.0f} €</p>
    </div>
    """, unsafe_allow_html=True)

# 4. SECTION STRATÉGIE
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-title">🎯 Stratégie & Objectif</p>', unsafe_allow_html=True)
prog = min(patrimoine_total / objectif_cible, 1.0)
st.markdown(f"""
    <div class="card-premium">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="color:#8E8E93; font-weight:700; font-size:0.75em;">PROGRESSION VERS 100K€</span>
            <span style="color:#ffffff; font-weight:900;">{prog*100:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.progress(prog)

# CONSEILLER
st.write("")
budget = st.number_input("💸 Budget d'investissement mensuel (€)", value=500)
st.markdown(f"""
    <div class="advice-row">
        <div class="advice-item"><div class="advice-lab">📈 Bourse (50%)</div><div class="advice-val">{budget*0.5:.0f}€</div></div>
        <div class="advice-item"><div class="advice-lab">₿ Crypto (30%)</div><div class="advice-val">{budget*0.3:.0f}€</div></div>
        <div class="advice-item"><div class="advice-lab">🏠 Immo (20%)</div><div class="advice-val">{budget*0.2:.0f}€</div></div>
    </div>
""", unsafe_allow_html=True)

# 5. SECTION ANALYSE
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-title">📊 Analyse de l\'Allocation</p>', unsafe_allow_html=True)
col_chart, col_leg = st.columns([1.5, 1])

with col_chart:
    fig = go.Figure(data=[go.Pie(labels=['Bourse', 'Crypto', 'Immo', 'Royaltiz'], 
                                 values=[total_bourse, total_crypto, immo_val, royaltiz_val], 
                                 hole=.85, marker_colors=['#ffffff', '#444444', '#222222', '#666666'])])
    fig.update_layout(showlegend=False, height=220, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col_leg:
    st.markdown(f"""
        <div style="margin-top:40px;">
            <p style="color:#ffffff; font-size:0.85em; margin-bottom:8px;">⚪ Bourse : <b>{total_bourse/patrimoine_total*100:.1f}%</b></p>
            <p style="color:#8E8E93; font-size:0.85em; margin-bottom:8px;">⚫ Crypto : <b>{total_crypto/patrimoine_total*100:.1f}%</b></p>
            <p style="color:#444444; font-size:0.85em;">🟤 Immo : <b>{immo_val/patrimoine_total*100:.1f}%</b></p>
        </div>
    """, unsafe_allow_html=True)

# 6. SECTION DÉTAILS
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-title">📂 Détails du Portefeuille</p>', unsafe_allow_html=True)
tabs = st.tabs(["📈 ACTIONS", "₿ CRYPTO", "✨ AUTRES"])

def plot_spark(ticker):
    try:
        data = yf.download(ticker, period="1d", interval="15m", progress=False)
        if not data.empty:
            fig = go.Figure(go.Scatter(x=data.index, y=data['Close'], line=dict(color='#ffffff', width=2)))
            fig.update_layout(height=80, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

with tabs[0]:
    for d in bourse_data:
        with st.expander(f"{d['nom']}  •  {d['valeur']:.2f}€"):
            plot_spark(tickers_map.get(d['nom']))

with tabs[1]:
    for c in crypto_data:
        with st.expander(f"{c['nom']}  •  {c['valeur']:.2f}€"):
            plot_spark(tickers_map.get(c['nom']))

with tabs[2]:
    st.markdown(f'<div class="card-premium" style="margin-bottom:15px;">🏠 Bricks Immobilier : {immo_val} €</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card-premium">👑 Royaltiz (Vinicius) : {royaltiz_val} €</div>', unsafe_allow_html=True)