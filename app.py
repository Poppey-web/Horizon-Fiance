import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import requests

st.set_page_config(page_title="Horizon Finance Pro", layout="wide", initial_sidebar_state="expanded")
DATA_FILE = "portfolio_data.json"

# ============== FONCTIONS DE PRIX ==============

def get_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,solana,polkadot,cardano", "vs_currencies": "usd,eur", "include_24hr_change": "true"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "BTC": {"usd": d.get("bitcoin", {}).get("usd", 0), "eur": d.get("bitcoin", {}).get("eur", 0), "change": d.get("bitcoin", {}).get("usd_24h_change", 0)},
                "ETH": {"usd": d.get("ethereum", {}).get("usd", 0), "eur": d.get("ethereum", {}).get("eur", 0), "change": d.get("ethereum", {}).get("usd_24h_change", 0)},
                "SOL": {"usd": d.get("solana", {}).get("usd", 0), "eur": d.get("solana", {}).get("eur", 0), "change": d.get("solana", {}).get("usd_24h_change", 0)},
                "DOT": {"usd": d.get("polkadot", {}).get("usd", 0), "eur": d.get("polkadot", {}).get("eur", 0), "change": d.get("polkadot", {}).get("usd_24h_change", 0)},
                "ADA": {"usd": d.get("cardano", {}).get("usd", 0), "eur": d.get("cardano", {}).get("eur", 0), "change": d.get("cardano", {}).get("usd_24h_change", 0)},
            }
    except:
        pass
    return None

def get_stock_prices(tickers):
    prices = {}
    try:
        import yfinance as yf
        for ticker in tickers:
            try:
                data = yf.download(ticker, period="1d", interval="15m", progress=False, prepost=True)
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    open_p = float(data['Open'].iloc[0])
                    change = ((price - open_p) / open_p) * 100 if open_p > 0 else 0
                    prices[ticker] = {"price": price, "change": change}
            except:
                continue
    except ImportError:
        st.sidebar.warning("yfinance non installé")
    return prices

def get_forex_rate():
    try:
        import yfinance as yf
        fx = yf.download("EURUSD=X", period="1d", interval="15m", progress=False)
        if not fx.empty:
            return 1 / float(fx['Close'].iloc[-1])
    except:
        pass
    return 0.92

def get_default_data():
    return {
        "bourse": [
            {"nom": "Streamwide", "ticker": "ALSTW.PA", "qty": 8.652555, "prix_achat": 34.69, "secteur": "Tech", "pays": "France", "dividend_yield": 0},
            {"nom": "Chevron", "ticker": "CVX", "qty": 3.415936, "prix_achat": 145.85, "secteur": "Énergie", "pays": "USA", "dividend_yield": 3.8},
            {"nom": "Alphabet (A)", "ticker": "GOOGL", "qty": 1.590988, "prix_achat": 157.77, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.5},
            {"nom": "Nvidia", "ticker": "NVDA", "qty": 2.120073, "prix_achat": 130.22, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.03},
            {"nom": "Total Energie", "ticker": "TTE.PA", "qty": 5.136355, "prix_achat": 54.32, "secteur": "Énergie", "pays": "France", "dividend_yield": 5.2},
            {"nom": "Apple", "ticker": "AAPL", "qty": 1.173637, "prix_achat": 200.25, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.5},
            {"nom": "Riot Platforms", "ticker": "RIOT", "qty": 19.745854, "prix_achat": 12.12, "secteur": "Crypto Mining", "pays": "USA", "dividend_yield": 0},
            {"nom": "Physical Silver", "ticker": "PHAG.L", "qty": 3.587989, "prix_achat": 41.55, "secteur": "Métaux", "pays": "UK", "dividend_yield": 0},
            {"nom": "Microsoft", "ticker": "MSFT", "qty": 0.265737, "prix_achat": 417.79, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.8},
            {"nom": "Prosus", "ticker": "PRX.AS", "qty": 2, "prix_achat": 57.92, "secteur": "Tech", "pays": "Pays-Bas", "dividend_yield": 0},
            {"nom": "Air Liquide", "ticker": "AI.PA", "qty": 0.62586, "prix_achat": 160.00, "secteur": "Industrie", "pays": "France", "dividend_yield": 1.9},
            {"nom": "FTSE EUR", "ticker": "VEUR.AS", "qty": 1.288122, "prix_achat": 52.77, "secteur": "ETF Europe", "pays": "Europe", "dividend_yield": 2.8},
            {"nom": "EURO STOXX 50", "ticker": "MSE.PA", "qty": 2.542464, "prix_achat": 18.50, "secteur": "ETF Europe", "pays": "Europe", "dividend_yield": 3.1},
            {"nom": "Xiaomi", "ticker": "1810.HK", "qty": 9.424083, "prix_achat": 4.77, "secteur": "Tech", "pays": "Chine", "dividend_yield": 0},
            {"nom": "MSCI CHINA", "ticker": "CN1.PA", "qty": 5.536076, "prix_achat": 5.42, "secteur": "ETF Émergents", "pays": "Chine", "dividend_yield": 2.2},
        ],
        "crypto": [
            {"nom": "Ethereum", "ticker": "ETH", "qty": 0.21283369, "prix_achat_usd": 2876.50, "is_staked": True, "staking_value_usd": 656.01, "staking_apy": 1.86, "staking_gains_usd": 23.38},
            {"nom": "Solana", "ticker": "SOL", "qty": 2.23274878, "prix_achat_usd": 129.53, "is_staked": True, "staking_value_usd": 303.05, "staking_apy": 4.13, "staking_gains_usd": 6.38},
            {"nom": "Bitcoin", "ticker": "BTC", "qty": 0.00271222, "prix_achat_usd": 95890.00, "is_staked": False, "staking_value_usd": 0, "staking_apy": 0, "staking_gains_usd": 0},
            {"nom": "Polkadot", "ticker": "DOT", "qty": 17.8306141, "prix_achat_usd": 5.71, "is_staked": True, "staking_value_usd": 37.09, "staking_apy": 8.11, "staking_gains_usd": 8.39},
            {"nom": "Cardano", "ticker": "ADA", "qty": 64.706973, "prix_achat_usd": 1.23, "is_staked": True, "staking_value_usd": 25.20, "staking_apy": 1.52, "staking_gains_usd": 1.49},
        ],
        "crypto_extras": {"disponible_usd": 204.20},
        "dca_orders": [
            {"crypto": "ETH", "nom": "Ethereum", "montant_eur": 20, "frequence_jours": 14, "prochaine_execution": "2026-01-15"},
            {"crypto": "SOL", "nom": "Solana", "montant_eur": 15, "frequence_jours": 14, "prochaine_execution": "2026-01-15"},
            {"crypto": "BTC", "nom": "Bitcoin", "montant_eur": 20, "frequence_jours": 14, "prochaine_execution": "2026-01-15"},
        ],
        "immobilier": {"bricks_bloque": 500, "bricks_libre": 1095, "taux_bloque": 0.085, "taux_libre": 0.04, "royaltiz": 200},
        "historique": {"bourse": [], "crypto": [], "total": []},
        "last_update": None,
        "taux_usd_eur": 0.92
    }

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default = get_default_data()
                for k in default:
                    if k not in data:
                        data[k] = default[k]
                return data
        except:
            return get_default_data()
    return get_default_data()

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_prices(data, force=False):
    last = data.get("last_update")
    if last and not force:
        try:
            if (datetime.now() - datetime.fromisoformat(last)).seconds < 300:
                return data
        except:
            pass
    
    taux = get_forex_rate()
    data["taux_usd_eur"] = taux
    
    crypto_prices = get_crypto_prices()
    if crypto_prices:
        for c in data["crypto"]:
            if c["ticker"] in crypto_prices:
                c["prix_actuel_usd"] = crypto_prices[c["ticker"]]["usd"]
                c["change_24h"] = crypto_prices[c["ticker"]]["change"]
    
    tickers = [p["ticker"] for p in data["bourse"]]
    stock_prices = get_stock_prices(tickers)
    if stock_prices:
        for p in data["bourse"]:
            if p["ticker"] in stock_prices:
                p["prix_actuel"] = stock_prices[p["ticker"]]["price"]
                p["change_24h"] = stock_prices[p["ticker"]]["change"]
    
    data["last_update"] = datetime.now().isoformat()
    return data

def calc_values(data):
    """
    Calcul CORRIGÉ des valeurs :
    - Position de base (investi) = qty × prix_achat
    - Valeur actuelle = qty × prix_actuel
    - Gain = Valeur actuelle - Position de base
    - Performance % = (Gain / Position de base) × 100
    """
    taux = data.get("taux_usd_eur", 0.92)
    
    # BOURSE
    for p in data["bourse"]:
        # Position de base = ce que j'ai payé
        p["position_base"] = p["qty"] * p["prix_achat"]
        
        # Valeur actuelle = prix actuel × quantité
        prix_actuel = p.get("prix_actuel", p["prix_achat"])
        p["valeur_actuelle"] = p["qty"] * prix_actuel
        
        # Gain = différence
        p["gain"] = p["valeur_actuelle"] - p["position_base"]
        
        # Performance en %
        p["perf"] = (p["gain"] / p["position_base"]) * 100 if p["position_base"] > 0 else 0
    
    # CRYPTO
    for c in data["crypto"]:
        # Position de base USD = ce que j'ai payé
        c["position_base_usd"] = c["qty"] * c["prix_achat_usd"]
        
        # Valeur actuelle
        if c.get("is_staked") and c.get("staking_value_usd", 0) > 0:
            # Si staké, utiliser la valeur de staking
            c["valeur_actuelle_usd"] = c["staking_value_usd"]
        else:
            # Sinon calculer avec prix actuel
            prix_actuel = c.get("prix_actuel_usd", c["prix_achat_usd"])
            c["valeur_actuelle_usd"] = c["qty"] * prix_actuel
        
        # Gain USD (incluant les gains de staking)
        c["gain_usd"] = c["valeur_actuelle_usd"] - c["position_base_usd"] + c.get("staking_gains_usd", 0)
        
        # Performance en %
        c["perf"] = (c["gain_usd"] / c["position_base_usd"]) * 100 if c["position_base_usd"] > 0 else 0
        
        # Conversion EUR
        c["position_base_eur"] = c["position_base_usd"] * taux
        c["valeur_actuelle_eur"] = c["valeur_actuelle_usd"] * taux
        c["gain_eur"] = c["gain_usd"] * taux
    
    return data

def add_history(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    taux = data.get("taux_usd_eur", 0.92)
    
    total_b = sum(p.get("valeur_actuelle", 0) for p in data["bourse"])
    total_c = sum(c.get("valeur_actuelle_eur", 0) for c in data["crypto"]) + data["crypto_extras"]["disponible_usd"] * taux
    immo = data["immobilier"]
    total_i = immo["bricks_bloque"] + immo["bricks_libre"] + immo["royaltiz"]
    total = total_b + total_c + total_i
    
    for k in ["bourse", "crypto", "total"]:
        if len(data["historique"][k]) > 500:
            data["historique"][k] = data["historique"][k][-400:]
    
    if data["historique"]["total"]:
        if data["historique"]["total"][-1]["date"][:16] == now[:16]:
            return data
    
    data["historique"]["bourse"].append({"date": now, "value": total_b})
    data["historique"]["crypto"].append({"date": now, "value": total_c})
    data["historique"]["total"].append({"date": now, "value": total})
    return data

def analyze_portfolio(data):
    taux = data.get("taux_usd_eur", 0.92)
    total_b = sum(p.get("valeur_actuelle", 0) for p in data["bourse"])
    total_c = sum(c.get("valeur_actuelle_eur", 0) for c in data["crypto"]) + data["crypto_extras"]["disponible_usd"] * taux
    immo = data["immobilier"]
    total_i = immo["bricks_bloque"] + immo["bricks_libre"] + immo["royaltiz"]
    patrimoine = total_b + total_c + total_i
    
    geo = {}
    for p in data["bourse"]:
        geo[p["pays"]] = geo.get(p["pays"], 0) + p.get("valeur_actuelle", 0)
    geo_pct = {k: v/total_b*100 for k, v in geo.items()} if total_b > 0 else {}
    
    sec = {}
    for p in data["bourse"]:
        sec[p["secteur"]] = sec.get(p["secteur"], 0) + p.get("valeur_actuelle", 0)
    sec_pct = {k: v/total_b*100 for k, v in sec.items()} if total_b > 0 else {}
    
    reco = []
    
    usa = geo_pct.get("USA", 0)
    if usa > 50:
        reco.append({"cat": "Géo", "prio": "medium", "icon": "🌍", "title": "Surexposition USA", 
            "detail": f"USA = {usa:.1f}%. Risque de change EUR/USD.",
            "action": "Diversifier vers Europe/Émergents",
            "suggestions": [{"nom": "iShares MSCI Europe", "ticker": "IMEU.AS"}, {"nom": "Amundi MSCI EM", "ticker": "AEEM.PA"}]})
    
    tech = sec_pct.get("Tech", 0)
    if tech > 40:
        reco.append({"cat": "Secteur", "prio": "high", "icon": "💻", "title": "Concentration Tech",
            "detail": f"Tech = {tech:.1f}%. Volatilité élevée.",
            "action": "Diversifier vers Santé, Finance, Consommation",
            "suggestions": [{"nom": "iShares Healthcare", "ticker": "IXJ"}, {"nom": "Sanofi", "ticker": "SAN.PA"}]})
    
    if "Santé" not in sec_pct:
        reco.append({"cat": "Secteur", "prio": "medium", "icon": "🏥", "title": "Absence secteur Santé",
            "detail": "Secteur défensif absent. Croissance structurelle.",
            "action": "Allouer 8-12% au secteur Santé",
            "suggestions": [{"nom": "Johnson & Johnson", "ticker": "JNJ"}, {"nom": "Novo Nordisk", "ticker": "NOVO-B.CO"}]})
    
    crypto_pct = total_c / patrimoine * 100 if patrimoine > 0 else 0
    if crypto_pct > 30:
        reco.append({"cat": "Allocation", "prio": "high", "icon": "⚠️", "title": "Surexposition Crypto",
            "detail": f"Crypto = {crypto_pct:.1f}%. Risque élevé.",
            "action": "Réduire à 20% et réallouer vers ETF",
            "suggestions": [{"nom": "ETF World", "ticker": "CW8.PA"}]})
    
    score = 100 - len([r for r in reco if r["prio"]=="high"])*15 - len([r for r in reco if r["prio"]=="medium"])*8
    
    return {"score": max(0, min(100, score)), "geo_pct": geo_pct, "sec_pct": sec_pct, "reco": reco}

# ============== STYLES CSS CORRIGÉS ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

.stApp { 
    background: linear-gradient(180deg, #0a0a0f 0%, #0d0d14 100%); 
    font-family: 'Inter', sans-serif; 
}

/* HERO SECTION - CORRIGÉ */
.hero-section {
    text-align: center;
    padding: 40px 20px;
    margin-bottom: 30px;
}

.hero-label {
    color: #8E8E93;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 5px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
}

.live-indicator {
    display: inline-flex;
    align-items: center;
    padding: 5px 12px;
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid #4ade80;
    gap: 6px;
}

.live-dot {
    width: 8px;
    height: 8px;
    background: #4ade80;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}

.hero-amount {
    font-size: 72px;
    font-weight: 900;
    color: #ffffff;
    margin: 20px 0;
    line-height: 1;
    letter-spacing: -3px;
}

.hero-perf {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 16px;
    margin-top: 10px;
}

.hero-perf-positive {
    background: linear-gradient(135deg, #1e3a1e 0%, #2d5a2d 100%);
    color: #4ade80;
}

.hero-perf-negative {
    background: linear-gradient(135deg, #3a1e1e 0%, #5a2d2d 100%);
    color: #f87171;
}

/* Section title */
.section-title {
    color: #8E8E93;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 3px;
    margin-bottom: 25px;
    border-bottom: 1px solid #1e1e2e;
    padding-bottom: 10px;
}

/* Cards */
.dash-card {
    background: linear-gradient(145deg, #141420 0%, #1a1a28 100%);
    border-radius: 20px;
    padding: 22px;
    border: 1px solid #252535;
    margin-bottom: 15px;
    transition: all 0.3s;
}

.dash-card:hover {
    transform: translateY(-5px);
    border-color: #4ade80;
}

.dash-card-title {
    color: #6b7280;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

.dash-card-value {
    font-size: 28px;
    font-weight: 800;
    color: #fff;
}

.section-card {
    background: linear-gradient(145deg, #141420 0%, #1a1a28 100%);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid #252535;
    margin-bottom: 20px;
}

.mini-card {
    background: #1c1c28;
    border-radius: 14px;
    padding: 16px;
    border: 1px solid #2a2a3a;
    text-align: center;
}

.mini-title {
    color: #6b7280;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
}

.mini-value {
    color: #fff;
    font-size: 20px;
    font-weight: 700;
    margin-top: 5px;
}

.change-positive { color: #4ade80; }
.change-negative { color: #f87171; }

/* Recommendations */
.reco-card {
    background: linear-gradient(145deg, #141420 0%, #1a1a28 100%);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    transition: all 0.3s;
}

.reco-card:hover { transform: translateX(5px); }
.reco-high { border-left: 4px solid #f87171; }
.reco-medium { border-left: 4px solid #fbbf24; }
.reco-low { border-left: 4px solid #4ade80; }

/* DCA */
.dca-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #2a4a6a;
    margin-bottom: 15px;
}

/* Progress */
.dividend-goal {
    background: linear-gradient(135deg, #0f2a1f 0%, #0a1f15 100%);
    padding: 30px;
    border-radius: 24px;
    border: 2px solid #22543d;
    margin-bottom: 25px;
}

.dividend-progress {
    height: 40px;
    background: #1a1a28;
    border-radius: 20px;
    overflow: hidden;
    margin: 20px 0;
}

.dividend-fill {
    height: 100%;
    background: linear-gradient(90deg, #22c55e 0%, #4ade80 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 700;
}

/* Staking */
.staking-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: linear-gradient(135deg, #1e3a5f 0%, #1a365d 100%);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    color: #60a5fa;
    border: 1px solid #3b82f6;
}

/* Score */
.score-container {
    text-align: center;
    padding: 30px;
    background: linear-gradient(145deg, #141420 0%, #1a1a28 100%);
    border-radius: 24px;
    border: 2px solid;
}

.score-value {
    font-size: 64px;
    font-weight: 900;
}

/* Performer row */
.performer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid #1e1e2e;
}

.performer-row:last-child { border-bottom: none; }

/* Fee cards */
.fee-hero {
    background: linear-gradient(135deg, #2d1f1f 0%, #3d2929 100%);
    padding: 45px;
    border-radius: 28px;
    border: 2px solid #f87171;
    text-align: center;
}

.fee-amount {
    font-size: 72px;
    font-weight: 900;
    color: #f87171;
}

.economy-card {
    background: linear-gradient(135deg, #1f2d1f 0%, #293d29 100%);
    padding: 35px;
    border-radius: 24px;
    border: 2px solid #4ade80;
    text-align: center;
}

/* Chip */
.chip {
    display: inline-block;
    background: #1e1e2e;
    padding: 8px 14px;
    border-radius: 20px;
    margin: 5px;
    font-size: 13px;
    border: 1px solid #2a2a3a;
}

/* Detail info */
.detail-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1e1e2e;
    font-size: 14px;
}

.detail-label { color: #8E8E93; }
.detail-value { color: #ffffff; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============== INIT ==============
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'page' not in st.session_state:
    st.session_state.page = "📊 Dashboard"
if 'force_refresh' not in st.session_state:
    st.session_state.force_refresh = False

data = st.session_state.data
data = update_prices(data, st.session_state.force_refresh)
data = calc_values(data)
data = add_history(data)
save_data(data)
st.session_state.data = data
st.session_state.force_refresh = False

# ============== CALCULS GLOBAUX CORRIGÉS ==============
taux = data.get("taux_usd_eur", 0.92)

# BOURSE
total_bourse_actuel = sum(p.get("valeur_actuelle", 0) for p in data["bourse"])
total_bourse_investi = sum(p.get("position_base", 0) for p in data["bourse"])
gain_bourse = sum(p.get("gain", 0) for p in data["bourse"])

# CRYPTO
total_crypto_actuel = sum(c.get("valeur_actuelle_eur", 0) for c in data["crypto"]) + data["crypto_extras"]["disponible_usd"] * taux
total_crypto_investi = sum(c.get("position_base_eur", 0) for c in data["crypto"])
gain_crypto = sum(c.get("gain_eur", 0) for c in data["crypto"])

# IMMOBILIER
immo = data["immobilier"]
interets_b = immo["bricks_bloque"] * immo["taux_bloque"] * 0.5
interets_l = immo["bricks_libre"] * immo["taux_libre"] / 12 * 6
immo_val = immo["bricks_bloque"] + immo["bricks_libre"] + interets_b + interets_l + immo["royaltiz"]
immo_investi = immo["bricks_bloque"] + immo["bricks_libre"] + immo["royaltiz"]
gain_immo = interets_b + interets_l

# TOTAUX
patrimoine = total_bourse_actuel + total_crypto_actuel + immo_val
total_investi = total_bourse_investi + total_crypto_investi + immo_investi
gain_total = gain_bourse + gain_crypto + gain_immo
perf_globale = (gain_total / total_investi) * 100 if total_investi > 0 else 0

# ============== SIDEBAR ==============
with st.sidebar:
    st.markdown("""<div style='text-align:center; padding:20px 0 30px;'>
        <div style='font-size:2.5em;'>💎</div>
        <div style='font-size:1.1em; font-weight:800; color:#fff;'>HORIZON</div>
        <div style='font-size:0.7em; color:#4ade80;'>FINANCE PRO v4</div>
    </div>""", unsafe_allow_html=True)
    
    pages = ["📊 Dashboard", "📈 Portefeuille", "➕ Gérer", "📉 Courbes", "🎯 Recommandations", "💹 Simulation", "💰 Frais", "💸 Revenus"]
    for p in pages:
        if st.button(p, key=f"nav_{p}", use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()
    
    st.markdown("---")
    last = data.get("last_update", "N/A")
    if last != "N/A":
        try: last = datetime.fromisoformat(last).strftime("%H:%M:%S")
        except: last = "N/A"
    
    st.markdown(f"""<div style='background:#141420; padding:18px; border-radius:16px; border:1px solid #252535;'>
        <div style='color:#6b7280; font-size:11px;'>DERNIÈRE MAJ</div>
        <div style='color:#4ade80; font-size:18px; font-weight:700;'>{last}</div>
        <div style='color:#6b7280; font-size:11px; margin-top:8px;'>USD/EUR: {taux:.4f}</div>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.force_refresh = True
            st.rerun()
    with col2:
        if st.button("🗑️ Reset", use_container_width=True):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.data = get_default_data()
            st.rerun()

# ============== HEADER CORRIGÉ ==============
perf_class = "hero-perf-positive" if gain_total > 0 else "hero-perf-negative"
perf_symbol = "+" if gain_total > 0 else ""

st.markdown(f"""
<div class="hero-section">
    <div class="hero-label">
        PATRIMOINE NET
        <span class="live-indicator">
            <span class="live-dot"></span>
            LIVE
        </span>
    </div>
    <div class="hero-amount">{patrimoine:,.0f} €</div>
    <div class="hero-perf {perf_class}">
        {perf_symbol}{gain_total:,.2f}€ ({perf_symbol}{perf_globale:.2f}%)
    </div>
</div>
""", unsafe_allow_html=True)

# ============== PAGES ==============
view = st.session_state.page

if view == "📊 Dashboard":
    st.markdown('<p class="section-title">📊 TABLEAU DE BORD</p>', unsafe_allow_html=True)
    analysis = analyze_portfolio(data)
    
    # Métriques avec calculs corrigés
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="dash-card"><div class="dash-card-title">💰 INVESTI</div><div class="dash-card-value">{total_investi:,.0f}€</div></div>', unsafe_allow_html=True)
    with col2:
        gc = "change-positive" if gain_total > 0 else "change-negative"
        st.markdown(f'<div class="dash-card"><div class="dash-card-title">📈 GAIN/PERTE</div><div class="dash-card-value {gc}">{perf_symbol}{gain_total:,.2f}€</div></div>', unsafe_allow_html=True)
    with col3:
        sc = "#4ade80" if analysis["score"] >= 70 else "#fbbf24" if analysis["score"] >= 50 else "#f87171"
        st.markdown(f'<div class="dash-card"><div class="dash-card-title">🎯 SCORE</div><div class="dash-card-value" style="color:{sc};">{analysis["score"]}/100</div></div>', unsafe_allow_html=True)
    with col4:
        perf_pct_class = "change-positive" if perf_globale > 0 else "change-negative"
        st.markdown(f'<div class="dash-card"><div class="dash-card-title">📊 PERFORMANCE</div><div class="dash-card-value {perf_pct_class}">{perf_symbol}{perf_globale:.2f}%</div></div>', unsafe_allow_html=True)
    with col5:
        dca = sum(o["montant_eur"] for o in data["dca_orders"]) * 2
        st.markdown(f'<div class="dash-card"><div class="dash-card-title">🔄 DCA/MOIS</div><div class="dash-card-value" style="color:#3b82f6;">{dca}€</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns([2, 1])
    with col1:
        if data["historique"]["total"]:
            st.markdown("#### 📈 Évolution du patrimoine")
            df = pd.DataFrame(data["historique"]["total"][-50:])
            if len(df) > 1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["date"], y=df["value"], mode='lines', fill='tozeroy', line=dict(color='#4ade80', width=2), fillcolor='rgba(74,222,128,0.1)'))
                fig.update_layout(height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#8E8E93'), margin=dict(t=10, b=30, l=50, r=20), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1e1e2e', tickformat=',.0f'))
                st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 🥧 Répartition")
        fig = go.Figure(data=[go.Pie(labels=['Bourse', 'Crypto', 'Immo'], values=[total_bourse_actuel, total_crypto_actuel, immo_val], hole=.7, marker_colors=['#3b82f6', '#f59e0b', '#10b981'], textinfo='percent')])
        fig.update_layout(height=280, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#fff'), showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"), margin=dict(t=10, b=40, l=10, r=10))
        fig.add_annotation(text=f"{patrimoine:,.0f}€", x=0.5, y=0.5, font_size=14, font_color="white", showarrow=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Top/Flop/DCA
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🏆 Top Performers")
        for p in sorted(data["bourse"], key=lambda x: x.get("perf", 0), reverse=True)[:5]:
            c = "#4ade80" if p.get("perf", 0) > 0 else "#f87171"
            st.markdown(f'<div class="performer-row"><span style="color:#fff;">{p["nom"]}</span><span style="color:{c}; font-weight:700;">{p.get("perf", 0):+.1f}%</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("#### 📉 Flop Performers")
        for p in sorted(data["bourse"], key=lambda x: x.get("perf", 0))[:5]:
            c = "#4ade80" if p.get("perf", 0) > 0 else "#f87171"
            st.markdown(f'<div class="performer-row"><span style="color:#fff;">{p["nom"]}</span><span style="color:{c}; font-weight:700;">{p.get("perf", 0):+.1f}%</span></div>', unsafe_allow_html=True)
    with col3:
        st.markdown("#### 🔄 Prochains DCA")
        for o in data["dca_orders"]:
            nd = datetime.strptime(o["prochaine_execution"], "%Y-%m-%d")
            days = (nd - datetime.now()).days
            st.markdown(f'<div class="dca-card"><div style="display:flex; justify-content:space-between;"><span style="color:#fff; font-weight:700;">{o["crypto"]}</span><span style="color:#3b82f6; font-weight:700;">{o["montant_eur"]}€</span></div><div style="color:#4ade80; font-size:13px; margin-top:8px;">{o["prochaine_execution"]} ({days}j)</div></div>', unsafe_allow_html=True)

elif view == "📈 Portefeuille":
    st.markdown('<p class="section-title">📂 PORTEFEUILLE DÉTAILLÉ</p>', unsafe_allow_html=True)
    
    # Résumé global
    st.markdown(f"""
    <div class="section-card">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
            <div>
                <div style="color: #6b7280; font-size: 11px; margin-bottom: 5px;">TOTAL INVESTI</div>
                <div style="color: #fff; font-size: 24px; font-weight: 800;">{total_investi:,.2f}€</div>
            </div>
            <div>
                <div style="color: #6b7280; font-size: 11px; margin-bottom: 5px;">VALEUR ACTUELLE</div>
                <div style="color: #fff; font-size: 24px; font-weight: 800;">{patrimoine:,.2f}€</div>
            </div>
            <div>
                <div style="color: #6b7280; font-size: 11px; margin-bottom: 5px;">GAIN TOTAL</div>
                <div style="color: {'#4ade80' if gain_total > 0 else '#f87171'}; font-size: 24px; font-weight: 800;">{perf_symbol}{gain_total:,.2f}€</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📈 ACTIONS", "₿ CRYPTO", "🏠 IMMO"])
    
    with tabs[0]:
        st.markdown(f"**Investi: {total_bourse_investi:,.2f}€** → **Actuel: {total_bourse_actuel:,.2f}€** • Gain: {'+' if gain_bourse > 0 else ''}{gain_bourse:,.2f}€")
        
        for p in sorted(data["bourse"], key=lambda x: x.get("valeur_actuelle", 0), reverse=True):
            icon = "🟢" if p.get("gain", 0) > 0 else "🔴"
            with st.expander(f"{p['nom']} • {p.get('valeur_actuelle', 0):,.2f}€ {icon} {p.get('perf', 0):+.2f}%"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Position de base (investi)</span><span class="detail-value">{p.get('position_base', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Valeur actuelle</span><span class="detail-value">{p.get('valeur_actuelle', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Gain/Perte</span><span class="detail-value" style="color:{'#4ade80' if p.get('gain', 0) > 0 else '#f87171'};">{p.get('gain', 0):+,.2f}€</span></div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Quantité</span><span class="detail-value">{p['qty']:.6f}</span></div>
                    <div class="detail-row"><span class="detail-label">Prix d'achat</span><span class="detail-value">{p['prix_achat']:.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Prix actuel</span><span class="detail-value">{p.get('prix_actuel', p['prix_achat']):.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Variation 24h</span><span class="detail-value">{p.get('change_24h', 0):+.2f}%</span></div>
                    """, unsafe_allow_html=True)
    
    with tabs[1]:
        staking_gains = sum(c.get("staking_gains_usd", 0) for c in data["crypto"]) * taux
        st.markdown(f"**Investi: {total_crypto_investi:,.2f}€** → **Actuel: {total_crypto_actuel:,.2f}€** • Gain: {'+' if gain_crypto > 0 else ''}{gain_crypto:,.2f}€")
        st.caption(f"💱 USD/EUR: {taux:.4f} • Gains staking inclus: +{staking_gains:,.2f}€")
        
        # Disponible
        dispo_eur = data["crypto_extras"]["disponible_usd"] * taux
        st.markdown(f'<div class="section-card" style="border:1px solid #3b82f6;"><div style="display:flex; justify-content:space-between;"><span style="color:#3b82f6; font-weight:700;">💵 Solde disponible</span><div style="text-align:right;"><div style="color:#fff; font-weight:700;">{dispo_eur:,.2f}€</div><div style="color:#8E8E93; font-size:13px;">{data["crypto_extras"]["disponible_usd"]:.2f}$</div></div></div></div>', unsafe_allow_html=True)
        
        for c in sorted(data["crypto"], key=lambda x: x.get("valeur_actuelle_eur", 0), reverse=True):
            icon = "🟢" if c.get("gain_eur", 0) > 0 else "🔴"
            staked = "🔒" if c.get("is_staked") else ""
            with st.expander(f"{staked} {c['nom']} • {c.get('valeur_actuelle_eur', 0):,.2f}€ {icon} {c.get('perf', 0):+.2f}%"):
                if c.get("is_staked"):
                    st.markdown(f'<span class="staking-badge">🔒 Staké {c.get("staking_apy", 0):.2f}% APY • Gains: +{c.get("staking_gains_usd", 0):.2f}$</span>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Position de base</span><span class="detail-value">{c.get('position_base_eur', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Valeur actuelle</span><span class="detail-value">{c.get('valeur_actuelle_eur', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Gain/Perte</span><span class="detail-value" style="color:{'#4ade80' if c.get('gain_eur', 0) > 0 else '#f87171'};">{c.get('gain_eur', 0):+,.2f}€</span></div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Quantité</span><span class="detail-value">{c['qty']:.8f}</span></div>
                    <div class="detail-row"><span class="detail-label">Prix achat USD</span><span class="detail-value">{c['prix_achat_usd']:.2f}$</span></div>
                    <div class="detail-row"><span class="detail-label">Prix actuel USD</span><span class="detail-value">{c.get('prix_actuel_usd', c['prix_achat_usd']):,.2f}$</span></div>
                    <div class="detail-row"><span class="detail-label">Variation 24h</span><span class="detail-value">{c.get('change_24h', 0):+.2f}%</span></div>
                    """, unsafe_allow_html=True)
        
        st.markdown("### 🔄 DCA programmés")
        for o in data["dca_orders"]:
            nd = datetime.strptime(o["prochaine_execution"], "%Y-%m-%d")
            days = (nd - datetime.now()).days
            st.markdown(f'<div class="dca-card"><div style="display:flex; justify-content:space-between;"><span style="color:#fff; font-weight:700;">{o.get("nom", o["crypto"])}</span><span style="color:#3b82f6; font-weight:700;">{o["montant_eur"]}€ / {o["frequence_jours"]}j</span></div><div style="color:#4ade80; margin-top:10px;">Prochain: {o["prochaine_execution"]} ({days}j)</div></div>', unsafe_allow_html=True)
    
    with tabs[2]:
        st.markdown(f"**Investi: {immo_investi:,.2f}€** → **Actuel: {immo_val:,.2f}€** • Intérêts: +{gain_immo:,.2f}€")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="section-card" style="border:2px solid #10b981;"><div style="color:#10b981; font-weight:700;">🧱 Bricks Bloqué</div><div style="font-size:2em; font-weight:900; color:#fff;">{immo["bricks_bloque"]:,.0f}€</div><div style="color:#4ade80;">+{interets_b:.2f}€ ({immo["taux_bloque"]*100:.1f}%)</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="section-card" style="border:2px solid #3b82f6;"><div style="color:#3b82f6; font-weight:700;">🧱 Bricks Libre</div><div style="font-size:2em; font-weight:900; color:#fff;">{immo["bricks_libre"]:,.0f}€</div><div style="color:#4ade80;">+{interets_l:.2f}€ ({immo["taux_libre"]*100:.1f}%)</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="section-card" style="border:2px solid #8b5cf6;"><div style="color:#8b5cf6; font-weight:700;">👑 Royaltiz</div><div style="font-size:2em; font-weight:900; color:#fff;">{immo["royaltiz"]:,.0f}€</div></div>', unsafe_allow_html=True)

elif view == "➕ Gérer":
    st.markdown('<p class="section-title">➕ GÉRER POSITIONS</p>', unsafe_allow_html=True)
    tabs = st.tabs(["📈 Action", "₿ Crypto", "🔄 DCA", "✏️ Staking", "🗑️ Suppr"])
    
    with tabs[0]:
        with st.form("add_stock"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom*")
                ticker = st.text_input("Ticker*")
                qty = st.number_input("Quantité*", min_value=0.0, format="%.6f")
            with c2:
                prix = st.number_input("Prix achat €*", min_value=0.0)
                secteur = st.selectbox("Secteur", ["Tech", "Énergie", "Finance", "Santé", "Industrie", "ETF Europe", "ETF Émergents", "Métaux", "Autre"])
                pays = st.selectbox("Pays", ["USA", "France", "Europe", "UK", "Chine", "Autre"])
            div = st.number_input("Dividende %", min_value=0.0, max_value=20.0)
            if st.form_submit_button("➕ Ajouter"):
                if nom and ticker and qty > 0 and prix > 0:
                    data["bourse"].append({"nom": nom, "ticker": ticker.upper(), "qty": qty, "prix_achat": prix, "secteur": secteur, "pays": pays, "dividend_yield": div})
                    save_data(data)
                    st.success(f"✅ {nom} ajoutée!")
                    st.rerun()
    
    with tabs[1]:
        with st.form("add_crypto"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom*", key="cn")
                ticker = st.text_input("Ticker*", key="ct")
                qty = st.number_input("Quantité*", min_value=0.0, format="%.8f", key="cq")
            with c2:
                prix = st.number_input("Prix USD*", min_value=0.0, key="cp")
                staked = st.checkbox("Staké?")
                apy = st.number_input("APY %", min_value=0.0, max_value=100.0) if staked else 0
            if st.form_submit_button("➕ Ajouter"):
                if nom and ticker and qty > 0 and prix > 0:
                    data["crypto"].append({"nom": nom, "ticker": ticker.upper(), "qty": qty, "prix_achat_usd": prix, "is_staked": staked, "staking_value_usd": qty*prix, "staking_apy": apy, "staking_gains_usd": 0})
                    save_data(data)
                    st.success(f"✅ {nom} ajoutée!")
                    st.rerun()
    
    with tabs[2]:
        st.markdown("**DCA actuels:**")
        for i, o in enumerate(data["dca_orders"]):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                data["dca_orders"][i]["montant_eur"] = st.number_input(o["crypto"], value=o["montant_eur"], key=f"dca_m_{i}")
            with c2:
                nd = st.date_input("Prochain", value=datetime.strptime(o["prochaine_execution"], "%Y-%m-%d"), key=f"dca_d_{i}")
                data["dca_orders"][i]["prochaine_execution"] = nd.strftime("%Y-%m-%d")
        
        st.markdown("**Disponible USD:**")
        data["crypto_extras"]["disponible_usd"] = st.number_input("USD", value=data["crypto_extras"]["disponible_usd"])
        if st.button("💾 Sauvegarder DCA"):
            save_data(data)
            st.success("Sauvegardé!")
            st.rerun()
    
    with tabs[3]:
        st.markdown("**Valeurs de staking:**")
        for i, c in enumerate(data["crypto"]):
            if c.get("is_staked"):
                st.markdown(f"**{c['nom']}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    c["staking_value_usd"] = st.number_input("Valeur USD", value=c.get("staking_value_usd", 0), key=f"sv_{i}")
                with c2:
                    c["staking_apy"] = st.number_input("APY %", value=c.get("staking_apy", 0), key=f"sa_{i}")
                with c3:
                    c["staking_gains_usd"] = st.number_input("Gains USD", value=c.get("staking_gains_usd", 0), key=f"sg_{i}")
        if st.button("💾 Sauvegarder Staking"):
            save_data(data)
            st.success("Sauvegardé!")
            st.rerun()
    
    with tabs[4]:
        st.warning("⚠️ Irréversible!")
        c1, c2 = st.columns(2)
        with c1:
            for i, p in enumerate(data["bourse"]):
                if st.button(f"🗑️ {p['nom']}", key=f"ds_{i}"):
                    data["bourse"].pop(i)
                    save_data(data)
                    st.rerun()
        with c2:
            for i, c in enumerate(data["crypto"]):
                if st.button(f"🗑️ {c['nom']}", key=f"dc_{i}"):
                    data["crypto"].pop(i)
                    save_data(data)
                    st.rerun()

elif view == "📉 Courbes":
    st.markdown('<p class="section-title">📉 COURBES D\'ÉVOLUTION</p>', unsafe_allow_html=True)
    if not data["historique"]["total"]:
        st.info("📊 Les courbes se construisent au fil du temps. Revenez plus tard!")
    else:
        periode = st.selectbox("Période", ["Tout", "24h", "7 jours", "30 jours"])
        days = {"Tout": None, "24h": 1, "7 jours": 7, "30 jours": 30}[periode]
        
        def filt(h, d):
            if not h or d is None: return h
            cut = datetime.now() - timedelta(days=d)
            return [x for x in h if datetime.strptime(x["date"], "%Y-%m-%d %H:%M") > cut]
        
        st.markdown("### 📈 Patrimoine Total")
        h = filt(data["historique"]["total"], days)
        if h and len(h) > 1:
            df = pd.DataFrame(h)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["value"], mode='lines', fill='tozeroy', line=dict(color='#4ade80', width=2), fillcolor='rgba(74,222,128,0.1)'))
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), margin=dict(t=10, b=30, l=50, r=20), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1e1e2e', tickformat=',.0f'))
            st.plotly_chart(fig, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📊 Bourse")
            hb = filt(data["historique"]["bourse"], days)
            if hb and len(hb) > 1:
                df = pd.DataFrame(hb)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["date"], y=df["value"], mode='lines', line=dict(color='#3b82f6', width=2), fill='tozeroy', fillcolor='rgba(59,130,246,0.1)'))
                fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#8E8E93'), margin=dict(t=10, b=30, l=50, r=10))
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### ₿ Crypto")
            hc = filt(data["historique"]["crypto"], days)
            if hc and len(hc) > 1:
                df = pd.DataFrame(hc)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["date"], y=df["value"], mode='lines', line=dict(color='#f59e0b', width=2), fill='tozeroy', fillcolor='rgba(245,158,11,0.1)'))
                fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#8E8E93'), margin=dict(t=10, b=30, l=50, r=10))
                st.plotly_chart(fig, use_container_width=True)

elif view == "🎯 Recommandations":
    st.markdown('<p class="section-title">🎯 RECOMMANDATIONS PERSONNALISÉES</p>', unsafe_allow_html=True)
    analysis = analyze_portfolio(data)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        sc = analysis["score"]
        col = "#4ade80" if sc >= 70 else "#fbbf24" if sc >= 50 else "#f87171"
        st.markdown(f'<div class="score-container" style="border-color:{col};"><div style="color:#6b7280; font-size:12px;">SCORE DE SANTÉ</div><div class="score-value" style="color:{col};">{sc}/100</div><div style="color:#8E8E93; margin-top:10px;">{len(analysis["reco"])} recommandations</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🌍 Exposition Géographique")
        geo = analysis["geo_pct"]
        if geo:
            fig = go.Figure(go.Bar(x=list(geo.values()), y=list(geo.keys()), orientation='h', marker_color=['#3b82f6' if v < 40 else '#f87171' for v in geo.values()], text=[f"{v:.1f}%" for v in geo.values()], textposition='auto'))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(showgrid=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### 📊 Exposition Sectorielle")
        sec = analysis["sec_pct"]
        if sec:
            fig = go.Figure(go.Bar(x=list(sec.values()), y=list(sec.keys()), orientation='h', marker_color=['#10b981' if v < 30 else '#fbbf24' if v < 50 else '#f87171' for v in sec.values()], text=[f"{v:.1f}%" for v in sec.values()], textposition='auto'))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(showgrid=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 💡 Actions recommandées")
    for r in analysis["reco"]:
        prio_class = f"reco-{r['prio']}"
        prio_label = {"high": "🔴 HAUTE", "medium": "🟡 MOYENNE", "low": "🟢 BASSE"}[r["prio"]]
        st.markdown(f'<div class="reco-card {prio_class}"><div style="display:flex; justify-content:space-between; margin-bottom:15px;"><span style="font-size:1.2em;">{r["icon"]} <strong style="color:#fff;">{r["title"]}</strong></span><span style="font-size:12px; color:#8E8E93;">{prio_label}</span></div><p style="color:#e0e0e0; margin-bottom:15px;">{r["detail"]}</p><p style="color:#4ade80; font-weight:600;">💡 {r["action"]}</p></div>', unsafe_allow_html=True)
        if r.get("suggestions"):
            for s in r["suggestions"]:
                st.markdown(f'<span class="chip"><strong>{s["nom"]}</strong> ({s["ticker"]})</span>', unsafe_allow_html=True)

elif view == "💹 Simulation":
    st.markdown('<p class="section-title">💹 SIMULATEUR DE PROJECTION</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        apport = st.number_input("Apport mensuel €", value=500, step=100)
        rend = st.slider("Rendement annuel %", 0, 20, 8)
    with c2:
        duree = st.slider("Durée (années)", 1, 30, 10)
        capital = st.number_input("Capital initial", value=int(patrimoine), step=1000)
    
    mois = duree * 12
    tm = (1 + rend/100) ** (1/12) - 1
    proj = [capital]
    for _ in range(mois):
        proj.append(proj[-1] * (1 + tm) + apport)
    
    dates = pd.date_range(start=datetime.now(), periods=mois+1, freq='ME')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=proj, mode='lines', fill='tozeroy', line=dict(color='#4ade80', width=3), fillcolor='rgba(74,222,128,0.1)'))
    fig.add_hline(y=100000, line_dash="dash", line_color="#f59e0b", annotation_text="Objectif 100k€")
    fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1e1e2e', tickformat=',.0f'))
    st.plotly_chart(fig, use_container_width=True)
    
    final = proj[-1]
    verse = capital + apport * mois
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valeur finale", f"{final:,.0f}€")
    c2.metric("Total versé", f"{verse:,.0f}€")
    c3.metric("Gains générés", f"{final - verse:,.0f}€")
    for i, v in enumerate(proj):
        if v >= 100000:
            c4.metric("100k€ atteint en", f"{i//12}a {i%12}m")
            break
    else:
        c4.metric("100k€", "Non atteint")

elif view == "💰 Frais":
    st.markdown('<p class="section-title">💰 SCANNER DE FRAIS</p>', unsafe_allow_html=True)
    frais_an = total_bourse_actuel * 0.023
    frais_30 = frais_an * 30 * 1.08
    eco = frais_30 * 0.65
    
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f'<div class="fee-hero"><div style="color:#f87171; letter-spacing:2px; font-size:12px;">COÛT ESTIMÉ SUR 30 ANS</div><div class="fee-amount">{frais_30:,.0f}€</div><p style="color:#fff; margin-top:15px;">Soit {frais_an:,.0f}€/an en moyenne</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="economy-card"><div style="color:#4ade80; font-size:12px;">💡 ÉCONOMIE POSSIBLE</div><div style="font-size:48px; font-weight:900; color:#4ade80; margin:15px 0;">{eco:,.0f}€</div><p style="color:#e0e0e0;">En passant aux ETF bas coût</p></div>', unsafe_allow_html=True)

elif view == "💸 Revenus":
    st.markdown('<p class="section-title">💸 REVENUS PASSIFS</p>', unsafe_allow_html=True)
    
    div_mens = sum(p.get("valeur_actuelle", 0) * p.get("dividend_yield", 0) / 100 / 12 for p in data["bourse"])
    staking_mens = sum(c.get("staking_gains_usd", 0) for c in data["crypto"]) * taux / 6
    immo_mens = gain_immo / 6
    total_passif = div_mens + staking_mens + immo_mens
    objectif = 500
    progress = min(total_passif / objectif * 100, 100)
    
    st.markdown(f'''<div class="dividend-goal">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h2 style="color:#4ade80; margin:0;">🎯 Objectif 500€/mois</h2>
            <span style="background:#22543d; padding:8px 16px; border-radius:12px; color:#4ade80; font-weight:700;">{progress:.1f}%</span>
        </div>
        <div style="font-size:64px; font-weight:900; color:#fff; margin:20px 0;">{total_passif:.2f}€<span style="font-size:24px; color:#6b7280;">/mois</span></div>
        <div class="dividend-progress">
            <div class="dividend-fill" style="width:{progress}%;">{progress:.1f}%</div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="mini-card" style="border:2px solid #3b82f6;"><div style="font-size:24px;">📈</div><div class="mini-value" style="color:#4ade80;">{div_mens:.2f}€</div><div class="mini-title">Dividendes</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mini-card" style="border:2px solid #f59e0b;"><div style="font-size:24px;">⛓️</div><div class="mini-value" style="color:#4ade80;">{staking_mens:.2f}€</div><div class="mini-title">Staking Crypto</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="mini-card" style="border:2px solid #10b981;"><div style="font-size:24px;">🏠</div><div class="mini-value" style="color:#4ade80;">{immo_mens:.2f}€</div><div class="mini-title">Immobilier</div></div>', unsafe_allow_html=True)

# ============== FOOTER ==============
st.markdown("---")
st.markdown(f'''<div style="text-align:center; color:#6b7280; font-size:12px; padding:20px;">
    💎 HORIZON FINANCE PRO v4 • {datetime.now().strftime("%d/%m/%Y %H:%M")} • Taux USD/EUR: {taux:.4f}<br>
    <span style="color:#4a5568;">⚠️ Ces informations ne constituent pas un conseil en investissement</span>
</div>''', unsafe_allow_html=True)