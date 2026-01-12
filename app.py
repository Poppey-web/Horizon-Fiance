import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import requests

st.set_page_config(page_title="Horizon Finance Pro", layout="wide", initial_sidebar_state="expanded")
DATA_FILE = "portfolio_data.json"

# ============== FONCTIONS UTILITAIRES ==============

def is_market_open():
    """Vérifie si les marchés boursiers sont ouverts (Lun-Ven, 9h-17h30 CET)"""
    now = datetime.now()
    # Weekend = fermé
    if now.weekday() >= 5:  # Samedi=5, Dimanche=6
        return False
    # Horaires d'ouverture (9h00 - 17h30)
    if now.hour < 9 or (now.hour >= 17 and now.minute > 30) or now.hour >= 18:
        return False
    return True

def should_update_stocks(last_update):
    """Détermine si on doit mettre à jour les actions"""
    if not last_update:
        return True
    # On vérifie juste le temps écoulé, pas les heures de marché
    # Le marché est vérifié ailleurs si nécessaire
    try:
        last = datetime.fromisoformat(last_update)
        elapsed = (datetime.now() - last).total_seconds()
        # Mise à jour toutes les 5 minutes max
        return elapsed > 300
    except:
        return True

def should_update_crypto(last_update):
    """MAJ crypto toutes les heures"""
    if not last_update:
        return True
    try:
        last = datetime.fromisoformat(last_update)
        elapsed = (datetime.now() - last).total_seconds()
        return elapsed > 3600  # 1 heure
    except:
        return True

def should_update_immo(last_update):
    """MAJ immobilier tous les mois"""
    if not last_update:
        return True
    try:
        last = datetime.fromisoformat(last_update)
        return (datetime.now() - last).days > 30
    except:
        return True

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
    """Récupère les prix des actions avec gestion robuste des erreurs"""
    prices = {}
    if not tickers:
        return prices
    try:
        import yfinance as yf
        for ticker in tickers:
            try:
                data = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)
                if data.empty:
                    continue
                
                # Gérer le format MultiIndex si présent
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                # S'assurer que 'Close' existe
                if 'Close' not in data.columns:
                    continue
                
                close_prices = data['Close'].dropna()
                if len(close_prices) < 1:
                    continue
                
                price = float(close_prices.iloc[-1])
                if len(close_prices) > 1:
                    prev = float(close_prices.iloc[-2])
                    change = ((price - prev) / prev) * 100 if prev > 0 else 0
                else:
                    change = 0
                
                prices[ticker] = {"price": price, "change": change}
            except Exception as e:
                st.sidebar.warning(f"⚠️ Erreur {ticker}: {str(e)[:30]}")
                continue
    except ImportError:
        st.sidebar.error("⚠️ yfinance non installé: pip install yfinance")
    return prices

def get_forex_rate():
    """Récupère le taux EUR/USD"""
    try:
        import yfinance as yf
        fx = yf.download("EURUSD=X", period="1d", interval="1d", progress=False)
        if not fx.empty:
            # Gérer MultiIndex
            if isinstance(fx.columns, pd.MultiIndex):
                fx.columns = fx.columns.get_level_values(0)
            if 'Close' in fx.columns:
                return 1 / float(fx['Close'].iloc[-1])
    except:
        pass
    return 0.92

def get_etf_comparison_data(tickers, period="1y"):
    """Récupère les données historiques pour comparer des ETF/actions"""
    try:
        import yfinance as yf
        data = {}
        for ticker in tickers:
            try:
                # Télécharger les données historiques
                hist = yf.download(ticker, period=period, interval="1d", progress=False)
                if hist.empty or len(hist) < 2:
                    continue
                
                # Gérer le format MultiIndex si présent
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                
                # Normaliser à 100 pour comparaison
                close_prices = hist['Close'].dropna()
                if len(close_prices) < 2:
                    continue
                    
                start_price = float(close_prices.iloc[0])
                end_price = float(close_prices.iloc[-1])
                
                if start_price <= 0:
                    continue
                
                normalized = (close_prices / start_price) * 100
                perf_total = ((end_price / start_price) - 1) * 100
                
                # Récupérer infos du ticker
                try:
                    ticker_info = yf.Ticker(ticker)
                    info = ticker_info.info
                    name = info.get("shortName") or info.get("longName") or ticker
                    expense_ratio = info.get("annualReportExpenseRatio") or info.get("totalExpenseRatio") or 0
                    div_yield = info.get("dividendYield") or info.get("yield") or 0
                    currency = info.get("currency", "USD")
                    
                    # Limiter les valeurs aberrantes
                    if expense_ratio and expense_ratio > 0.1:  # Max 10%
                        expense_ratio = 0
                    if div_yield and div_yield > 0.2:  # Max 20%
                        div_yield = 0
                except:
                    name = ticker
                    expense_ratio = 0
                    div_yield = 0
                    currency = "USD"
                
                data[ticker] = {
                    "history": normalized.tolist(),
                    "dates": [d.strftime("%Y-%m-%d") for d in close_prices.index],
                    "perf": perf_total,
                    "name": name[:30] if name else ticker,
                    "expense_ratio": expense_ratio if expense_ratio else 0,
                    "dividend_yield": div_yield if div_yield else 0,
                    "current_price": end_price,
                    "currency": currency
                }
            except Exception as e:
                continue
        return data if data else None
    except ImportError:
        return None

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
        "last_update_stocks": None,
        "last_update_crypto": None,
        "last_update_immo": None,
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
    """Met à jour les prix selon les règles d'actualisation"""
    
    # Taux de change
    taux = get_forex_rate()
    data["taux_usd_eur"] = taux
    
    # CRYPTO - toutes les heures (ou force)
    should_crypto = force or should_update_crypto(data.get("last_update_crypto"))
    if should_crypto:
        crypto_prices = get_crypto_prices()
        if crypto_prices:
            for c in data["crypto"]:
                if c["ticker"] in crypto_prices:
                    c["prix_actuel_usd"] = crypto_prices[c["ticker"]]["usd"]
                    c["change_24h"] = crypto_prices[c["ticker"]]["change"]
            data["last_update_crypto"] = datetime.now().isoformat()
    
    # BOURSE - si force=True, on ignore la condition marché ouvert
    should_stocks = force or should_update_stocks(data.get("last_update_stocks"))
    if should_stocks and data["bourse"]:
        tickers = [p["ticker"] for p in data["bourse"]]
        stock_prices = get_stock_prices(tickers)
        if stock_prices:
            updated_count = 0
            for p in data["bourse"]:
                if p["ticker"] in stock_prices:
                    p["prix_actuel"] = stock_prices[p["ticker"]]["price"]
                    p["change_24h"] = stock_prices[p["ticker"]]["change"]
                    updated_count += 1
            if updated_count > 0:
                data["last_update_stocks"] = datetime.now().isoformat()
    
    # IMMOBILIER - tous les mois (intérêts)
    if force or should_update_immo(data.get("last_update_immo")):
        data["last_update_immo"] = datetime.now().isoformat()
    
    return data

def calc_values(data):
    taux = data.get("taux_usd_eur", 0.92)
    
    for p in data["bourse"]:
        p["position_base"] = p["qty"] * p["prix_achat"]
        prix_actuel = p.get("prix_actuel", p["prix_achat"])
        p["valeur_actuelle"] = p["qty"] * prix_actuel
        p["gain"] = p["valeur_actuelle"] - p["position_base"]
        p["perf"] = (p["gain"] / p["position_base"]) * 100 if p["position_base"] > 0 else 0
    
    for c in data["crypto"]:
        c["position_base_usd"] = c["qty"] * c["prix_achat_usd"]
        if c.get("is_staked") and c.get("staking_value_usd", 0) > 0:
            c["valeur_actuelle_usd"] = c["staking_value_usd"]
        else:
            prix_actuel = c.get("prix_actuel_usd", c["prix_achat_usd"])
            c["valeur_actuelle_usd"] = c["qty"] * prix_actuel
        c["gain_usd"] = c["valeur_actuelle_usd"] - c["position_base_usd"] + c.get("staking_gains_usd", 0)
        c["perf"] = (c["gain_usd"] / c["position_base_usd"]) * 100 if c["position_base_usd"] > 0 else 0
        c["position_base_eur"] = c["position_base_usd"] * taux
        c["valeur_actuelle_eur"] = c["valeur_actuelle_usd"] * taux
        c["gain_eur"] = c["gain_usd"] * taux
    
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
            "detail": "Secteur défensif absent.",
            "action": "Allouer 8-12% au secteur Santé",
            "suggestions": [{"nom": "Johnson & Johnson", "ticker": "JNJ"}, {"nom": "Novo Nordisk", "ticker": "NOVO-B.CO"}]})
    
    crypto_pct = total_c / patrimoine * 100 if patrimoine > 0 else 0
    if crypto_pct > 30:
        reco.append({"cat": "Allocation", "prio": "high", "icon": "⚠️", "title": "Surexposition Crypto",
            "detail": f"Crypto = {crypto_pct:.1f}%. Risque élevé.",
            "action": "Réduire à 20%",
            "suggestions": [{"nom": "ETF World", "ticker": "CW8.PA"}]})
    
    score = 100 - len([r for r in reco if r["prio"]=="high"])*15 - len([r for r in reco if r["prio"]=="medium"])*8
    return {"score": max(0, min(100, score)), "geo_pct": geo_pct, "sec_pct": sec_pct, "reco": reco}

# ============== STYLES CSS PREMIUM ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Base */
.stApp { 
    background: linear-gradient(135deg, #0a0a0f 0%, #0d0d18 50%, #0a0a12 100%); 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
}

/* Scrollbar premium */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #4ade80 0%, #22c55e 100%); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4ade80; }

/* Hero Section */
.hero-section { 
    text-align: center; 
    padding: 50px 20px; 
    margin-bottom: 40px;
    background: radial-gradient(ellipse at center top, rgba(74, 222, 128, 0.03) 0%, transparent 50%);
}
.hero-label { 
    color: #6b7280; 
    font-size: 13px; 
    font-weight: 600; 
    letter-spacing: 6px; 
    margin-bottom: 20px; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    gap: 20px; 
}
.live-indicator { 
    display: inline-flex; 
    align-items: center; 
    padding: 6px 14px; 
    background: rgba(74, 222, 128, 0.1); 
    color: #4ade80; 
    border-radius: 20px; 
    font-size: 10px; 
    font-weight: 700; 
    letter-spacing: 1px;
    border: 1px solid rgba(74, 222, 128, 0.3); 
    gap: 8px;
    backdrop-filter: blur(10px);
}
.live-dot { 
    width: 6px; 
    height: 6px; 
    background: #4ade80; 
    border-radius: 50%; 
    animation: pulse 2s ease-in-out infinite;
    box-shadow: 0 0 10px #4ade80;
}
.market-closed { 
    background: rgba(251, 191, 36, 0.1); 
    color: #fbbf24; 
    border-color: rgba(251, 191, 36, 0.3); 
}
.market-closed .live-dot {
    background: #fbbf24;
    box-shadow: 0 0 10px #fbbf24;
}
@keyframes pulse { 
    0%, 100% { opacity: 1; transform: scale(1); } 
    50% { opacity: 0.4; transform: scale(0.8); } 
}
.hero-amount { 
    font-size: 80px; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 25px 0; 
    line-height: 1; 
    letter-spacing: -4px;
    text-shadow: 0 0 60px rgba(255,255,255,0.1);
}
.hero-perf { 
    display: inline-block; 
    padding: 14px 28px; 
    border-radius: 30px; 
    font-weight: 700; 
    font-size: 15px; 
    margin-top: 15px;
    backdrop-filter: blur(10px);
}
.hero-perf-positive { 
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(74, 222, 128, 0.1) 100%); 
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.3);
    box-shadow: 0 4px 30px rgba(74, 222, 128, 0.1);
}
.hero-perf-negative { 
    background: linear-gradient(135deg, rgba(248, 113, 113, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%); 
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.3);
    box-shadow: 0 4px 30px rgba(248, 113, 113, 0.1);
}

/* Section Title */
.section-title { 
    color: #4ade80; 
    font-weight: 700; 
    font-size: 11px; 
    letter-spacing: 4px; 
    margin-bottom: 30px; 
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(74, 222, 128, 0.2);
    text-transform: uppercase;
}

/* Cards */
.dash-card { 
    background: linear-gradient(145deg, rgba(20, 20, 32, 0.8) 0%, rgba(26, 26, 40, 0.8) 100%); 
    border-radius: 20px; 
    padding: 24px; 
    border: 1px solid rgba(255,255,255,0.05); 
    margin-bottom: 15px; 
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(20px);
}
.dash-card:hover { 
    transform: translateY(-8px); 
    border-color: rgba(74, 222, 128, 0.5);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 30px rgba(74, 222, 128, 0.1);
}
.dash-card-title { 
    color: #6b7280; 
    font-size: 10px; 
    font-weight: 600; 
    letter-spacing: 2px; 
    margin-bottom: 12px;
    text-transform: uppercase;
}
.dash-card-value { 
    font-size: 26px; 
    font-weight: 800; 
    color: #fff;
    letter-spacing: -1px;
}

.section-card { 
    background: linear-gradient(145deg, rgba(20, 20, 32, 0.9) 0%, rgba(26, 26, 40, 0.9) 100%); 
    border-radius: 24px; 
    padding: 28px; 
    border: 1px solid rgba(255,255,255,0.05); 
    margin-bottom: 20px;
    backdrop-filter: blur(20px);
}

.mini-card { 
    background: rgba(28, 28, 40, 0.8); 
    border-radius: 16px; 
    padding: 20px; 
    border: 1px solid rgba(255,255,255,0.05); 
    text-align: center;
    transition: all 0.3s;
}
.mini-card:hover {
    border-color: rgba(74, 222, 128, 0.3);
    transform: scale(1.02);
}
.mini-title { 
    color: #6b7280; 
    font-size: 9px; 
    font-weight: 700; 
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.mini-value { 
    color: #fff; 
    font-size: 22px; 
    font-weight: 800; 
    margin-top: 8px; 
}

.change-positive { color: #4ade80; }
.change-negative { color: #f87171; }

/* Recommendation Cards */
.reco-card { 
    background: linear-gradient(145deg, rgba(20, 20, 32, 0.9) 0%, rgba(26, 26, 40, 0.9) 100%); 
    border-radius: 18px; 
    padding: 22px; 
    margin-bottom: 15px; 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
}
.reco-card:hover { 
    transform: translateX(8px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.reco-high { border-left: 4px solid #f87171; }
.reco-medium { border-left: 4px solid #fbbf24; }
.reco-low { border-left: 4px solid #4ade80; }

/* DCA Card */
.dca-card { 
    background: linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%); 
    border-radius: 18px; 
    padding: 22px; 
    border: 1px solid rgba(59, 130, 246, 0.2); 
    margin-bottom: 15px;
    transition: all 0.3s;
}
.dca-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);
}

/* Dividend Goal */
.dividend-goal { 
    background: linear-gradient(135deg, rgba(15, 42, 31, 0.9) 0%, rgba(10, 31, 21, 0.9) 100%); 
    padding: 35px; 
    border-radius: 28px; 
    border: 1px solid rgba(34, 84, 61, 0.5); 
    margin-bottom: 30px;
    backdrop-filter: blur(10px);
}
.dividend-progress { 
    height: 45px; 
    background: rgba(26, 26, 40, 0.8); 
    border-radius: 23px; 
    overflow: hidden; 
    margin: 25px 0;
    border: 1px solid rgba(255,255,255,0.05);
}
.dividend-fill { 
    height: 100%; 
    background: linear-gradient(90deg, #22c55e 0%, #4ade80 50%, #86efac 100%); 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    color: #000; 
    font-weight: 800;
    font-size: 14px;
    box-shadow: 0 0 20px rgba(74, 222, 128, 0.5);
}

/* Staking Badge */
.staking-badge { 
    display: inline-flex; 
    align-items: center; 
    gap: 6px; 
    background: linear-gradient(135deg, rgba(30, 58, 95, 0.8) 0%, rgba(26, 54, 93, 0.8) 100%); 
    padding: 6px 12px; 
    border-radius: 12px; 
    font-size: 11px; 
    color: #60a5fa; 
    border: 1px solid rgba(59, 130, 246, 0.3);
    font-weight: 600;
}

/* Score Container */
.score-container { 
    text-align: center; 
    padding: 40px; 
    background: linear-gradient(145deg, rgba(20, 20, 32, 0.9) 0%, rgba(26, 26, 40, 0.9) 100%); 
    border-radius: 28px; 
    border: 2px solid;
    backdrop-filter: blur(20px);
}
.score-value { 
    font-size: 72px; 
    font-weight: 900;
    letter-spacing: -3px;
}

/* Performer Row */
.performer-row { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    padding: 16px 0; 
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: all 0.2s;
}
.performer-row:hover {
    background: rgba(255,255,255,0.02);
    padding-left: 10px;
    padding-right: 10px;
    margin: 0 -10px;
    border-radius: 8px;
}
.performer-row:last-child { border-bottom: none; }

/* Fee Cards */
.fee-hero { 
    background: linear-gradient(135deg, rgba(45, 31, 31, 0.9) 0%, rgba(61, 41, 41, 0.9) 100%); 
    padding: 50px; 
    border-radius: 32px; 
    border: 1px solid rgba(248, 113, 113, 0.3); 
    text-align: center;
    backdrop-filter: blur(20px);
}
.fee-amount { 
    font-size: 68px; 
    font-weight: 900; 
    color: #f87171;
    letter-spacing: -3px;
    text-shadow: 0 0 40px rgba(248, 113, 113, 0.3);
}
.economy-card { 
    background: linear-gradient(135deg, rgba(31, 45, 31, 0.9) 0%, rgba(41, 61, 41, 0.9) 100%); 
    padding: 40px; 
    border-radius: 28px; 
    border: 1px solid rgba(74, 222, 128, 0.3); 
    text-align: center;
    backdrop-filter: blur(20px);
}

/* Chip */
.chip { 
    display: inline-block; 
    background: rgba(30, 30, 46, 0.8); 
    padding: 10px 16px; 
    border-radius: 25px; 
    margin: 5px; 
    font-size: 12px; 
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.2s;
    color: #e0e0e0;
}
.chip:hover {
    border-color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
}

/* Detail Row */
.detail-row { 
    display: flex; 
    justify-content: space-between; 
    padding: 12px 0; 
    border-bottom: 1px solid rgba(255,255,255,0.05); 
    font-size: 14px; 
}
.detail-label { color: #6b7280; }
.detail-value { color: #ffffff; font-weight: 600; }

/* Status Badge */
.status-badge { 
    padding: 5px 12px; 
    border-radius: 12px; 
    font-size: 10px; 
    font-weight: 700;
    letter-spacing: 0.5px;
}
.status-open { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.status-closed { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }

/* Streamlit overrides */
.stButton > button {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    color: #fff;
    font-weight: 600;
    transition: all 0.3s;
}
.stButton > button:hover {
    border-color: #4ade80;
    box-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
    transform: translateY(-2px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    border: none;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 30px rgba(74, 222, 128, 0.4);
}

div[data-testid="stMetric"] {
    background: rgba(20, 20, 32, 0.5);
    padding: 15px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(20, 20, 32, 0.8);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.05);
    color: #a0aec0;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    color: #fff;
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(20, 20, 32, 0.8);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# ============== INIT ==============
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.needs_update = True
else:
    st.session_state.needs_update = False

if 'page' not in st.session_state:
    st.session_state.page = "📊 Dashboard"
if 'force_refresh' not in st.session_state:
    st.session_state.force_refresh = False

# Mise à jour des prix
data = st.session_state.data
if st.session_state.force_refresh or st.session_state.needs_update:
    with st.spinner("🔄 Mise à jour des prix..."):
        data = update_prices(data, force=True)
    st.session_state.force_refresh = False
else:
    data = update_prices(data, force=False)

data = calc_values(data)
save_data(data)
st.session_state.data = data

# ============== CALCULS GLOBAUX ==============
taux = data.get("taux_usd_eur", 0.92)
total_bourse_actuel = sum(p.get("valeur_actuelle", 0) for p in data["bourse"])
total_bourse_investi = sum(p.get("position_base", 0) for p in data["bourse"])
gain_bourse = sum(p.get("gain", 0) for p in data["bourse"])

total_crypto_actuel = sum(c.get("valeur_actuelle_eur", 0) for c in data["crypto"]) + data["crypto_extras"]["disponible_usd"] * taux
total_crypto_investi = sum(c.get("position_base_eur", 0) for c in data["crypto"])
gain_crypto = sum(c.get("gain_eur", 0) for c in data["crypto"])

immo = data["immobilier"]
interets_b = immo["bricks_bloque"] * immo["taux_bloque"] * 0.5
interets_l = immo["bricks_libre"] * immo["taux_libre"] / 12 * 6
immo_val = immo["bricks_bloque"] + immo["bricks_libre"] + interets_b + interets_l + immo["royaltiz"]
immo_investi = immo["bricks_bloque"] + immo["bricks_libre"] + immo["royaltiz"]
gain_immo = interets_b + interets_l

patrimoine = total_bourse_actuel + total_crypto_actuel + immo_val
total_investi = total_bourse_investi + total_crypto_investi + immo_investi
gain_total = gain_bourse + gain_crypto + gain_immo
perf_globale = (gain_total / total_investi) * 100 if total_investi > 0 else 0

# ============== SIDEBAR ==============
with st.sidebar:
    st.markdown("""<div style='text-align:center; padding:20px 0 30px;'>
        <div style='font-size:2.5em;'>💎</div>
        <div style='font-size:1.1em; font-weight:800; color:#fff;'>HORIZON</div>
        <div style='font-size:0.7em; color:#4ade80;'>FINANCE PRO v5</div>
    </div>""", unsafe_allow_html=True)
    
    pages = ["📊 Dashboard", "📈 Portefeuille", "➕ Gérer", "🔍 Comparer", "🎯 Recommandations", "💹 Simulation", "💰 Frais", "💸 Revenus"]
    for p in pages:
        if st.button(p, key=f"nav_{p}", use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()
    
    st.markdown("---")
    
    # Status des marchés
    market_open = is_market_open()
    market_status = "OUVERT" if market_open else "FERMÉ"
    market_class = "status-open" if market_open else "status-closed"
    
    st.markdown(f"""<div style='background:#141420; padding:18px; border-radius:16px; border:1px solid #252535; margin-bottom:15px;'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
            <span style='color:#6b7280; font-size:11px;'>MARCHÉ BOURSE</span>
            <span class="status-badge {market_class}">{market_status}</span>
        </div>
        <div style='color:#6b7280; font-size:10px;'>Dernière MAJ: {datetime.fromisoformat(data.get('last_update_stocks', datetime.now().isoformat())).strftime('%d/%m %H:%M') if data.get('last_update_stocks') else 'N/A'}</div>
    </div>""", unsafe_allow_html=True)
    
    # Crypto update
    crypto_update = data.get('last_update_crypto')
    crypto_time = datetime.fromisoformat(crypto_update).strftime('%d/%m %H:%M') if crypto_update else 'N/A'
    st.markdown(f"""<div style='background:#141420; padding:18px; border-radius:16px; border:1px solid #252535;'>
        <div style='color:#6b7280; font-size:11px;'>CRYPTO (MAJ/heure)</div>
        <div style='color:#f59e0b; font-size:14px; font-weight:700;'>{crypto_time}</div>
        <div style='color:#6b7280; font-size:10px; margin-top:8px;'>USD/EUR: {taux:.4f}</div>
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

# ============== HEADER ==============
perf_class = "hero-perf-positive" if gain_total > 0 else "hero-perf-negative"
perf_symbol = "+" if gain_total > 0 else ""
market_indicator = "live-indicator" if is_market_open() else "live-indicator market-closed"
market_text = "LIVE" if is_market_open() else "MARCHÉ FERMÉ"

st.markdown(f"""
<div class="hero-section">
    <div class="hero-label">
        PATRIMOINE NET
        <span class="{market_indicator}">
            <span class="live-dot"></span>
            {market_text}
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
    
    # Répartition
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 🥧 Répartition du patrimoine")
        fig = go.Figure(data=[go.Pie(labels=['Bourse', 'Crypto', 'Immo'], values=[total_bourse_actuel, total_crypto_actuel, immo_val], hole=.7, marker_colors=['#3b82f6', '#f59e0b', '#10b981'], textinfo='percent')])
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#fff'), showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"), margin=dict(t=10, b=40, l=10, r=10))
        fig.add_annotation(text=f"{patrimoine:,.0f}€", x=0.5, y=0.5, font_size=16, font_color="white", showarrow=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Détail par catégorie")
        st.markdown(f"""
        <div class="section-card">
            <div class="detail-row"><span class="detail-label">📈 Bourse</span><span class="detail-value">{total_bourse_actuel:,.2f}€ <span style="color:{'#4ade80' if gain_bourse > 0 else '#f87171'};">({'+' if gain_bourse > 0 else ''}{gain_bourse:,.2f}€)</span></span></div>
            <div class="detail-row"><span class="detail-label">₿ Crypto</span><span class="detail-value">{total_crypto_actuel:,.2f}€ <span style="color:{'#4ade80' if gain_crypto > 0 else '#f87171'};">({'+' if gain_crypto > 0 else ''}{gain_crypto:,.2f}€)</span></span></div>
            <div class="detail-row"><span class="detail-label">🏠 Immobilier</span><span class="detail-value">{immo_val:,.2f}€ <span style="color:#4ade80;">(+{gain_immo:,.2f}€)</span></span></div>
        </div>
        """, unsafe_allow_html=True)
    
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
    
    st.markdown(f"""
    <div class="section-card">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
            <div><div style="color: #6b7280; font-size: 11px;">TOTAL INVESTI</div><div style="color: #fff; font-size: 24px; font-weight: 800;">{total_investi:,.2f}€</div></div>
            <div><div style="color: #6b7280; font-size: 11px;">VALEUR ACTUELLE</div><div style="color: #fff; font-size: 24px; font-weight: 800;">{patrimoine:,.2f}€</div></div>
            <div><div style="color: #6b7280; font-size: 11px;">GAIN TOTAL</div><div style="color: {'#4ade80' if gain_total > 0 else '#f87171'}; font-size: 24px; font-weight: 800;">{perf_symbol}{gain_total:,.2f}€</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📈 ACTIONS", "₿ CRYPTO", "🏠 IMMO"])
    
    with tabs[0]:
        market_status = "🟢 Marché ouvert" if is_market_open() else "🟡 Marché fermé"
        st.markdown(f"**Investi: {total_bourse_investi:,.2f}€** → **Actuel: {total_bourse_actuel:,.2f}€** • {market_status}")
        
        for p in sorted(data["bourse"], key=lambda x: x.get("valeur_actuelle", 0), reverse=True):
            icon = "🟢" if p.get("gain", 0) > 0 else "🔴"
            with st.expander(f"{p['nom']} ({p['ticker']}) • {p.get('valeur_actuelle', 0):,.2f}€ {icon} {p.get('perf', 0):+.2f}%"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Position de base</span><span class="detail-value">{p.get('position_base', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Valeur actuelle</span><span class="detail-value">{p.get('valeur_actuelle', 0):,.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Gain/Perte</span><span class="detail-value" style="color:{'#4ade80' if p.get('gain', 0) > 0 else '#f87171'};">{p.get('gain', 0):+,.2f}€</span></div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="detail-row"><span class="detail-label">Quantité</span><span class="detail-value">{p['qty']:.6f}</span></div>
                    <div class="detail-row"><span class="detail-label">Prix d'achat</span><span class="detail-value">{p['prix_achat']:.2f}€</span></div>
                    <div class="detail-row"><span class="detail-label">Prix actuel</span><span class="detail-value">{p.get('prix_actuel', p['prix_achat']):.2f}€</span></div>
                    """, unsafe_allow_html=True)
    
    with tabs[1]:
        staking_gains = sum(c.get("staking_gains_usd", 0) for c in data["crypto"]) * taux
        st.markdown(f"**Investi: {total_crypto_investi:,.2f}€** → **Actuel: {total_crypto_actuel:,.2f}€** • Gains staking: +{staking_gains:,.2f}€")
        
        dispo_eur = data["crypto_extras"]["disponible_usd"] * taux
        st.markdown(f'<div class="section-card" style="border:1px solid #3b82f6;"><div style="display:flex; justify-content:space-between;"><span style="color:#3b82f6; font-weight:700;">💵 Disponible</span><div style="text-align:right;"><div style="color:#fff; font-weight:700;">{dispo_eur:,.2f}€</div><div style="color:#8E8E93; font-size:13px;">{data["crypto_extras"]["disponible_usd"]:.2f}$</div></div></div></div>', unsafe_allow_html=True)
        
        for c in sorted(data["crypto"], key=lambda x: x.get("valeur_actuelle_eur", 0), reverse=True):
            icon = "🟢" if c.get("gain_eur", 0) > 0 else "🔴"
            staked = "🔒" if c.get("is_staked") else ""
            with st.expander(f"{staked} {c['nom']} • {c.get('valeur_actuelle_eur', 0):,.2f}€ {icon} {c.get('perf', 0):+.2f}%"):
                if c.get("is_staked"):
                    st.markdown(f'<span class="staking-badge">🔒 Staké {c.get("staking_apy", 0):.2f}% APY • +{c.get("staking_gains_usd", 0):.2f}$</span>', unsafe_allow_html=True)
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
                    <div class="detail-row"><span class="detail-label">Prix actuel</span><span class="detail-value">{c.get('prix_actuel_usd', c['prix_achat_usd']):,.2f}$</span></div>
                    <div class="detail-row"><span class="detail-label">Var. 24h</span><span class="detail-value">{c.get('change_24h', 0):+.2f}%</span></div>
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
    tabs = st.tabs(["📈 Action", "₿ Crypto", "🔄 DCA", "✏️ Staking", "🏠 Immo", "🗑️ Suppr"])
    
    with tabs[0]:
        with st.form("add_stock"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom*")
                ticker = st.text_input("Ticker Yahoo Finance*")
                qty = st.number_input("Quantité*", min_value=0.0, format="%.6f")
            with c2:
                prix = st.number_input("Prix achat €*", min_value=0.0)
                secteur = st.selectbox("Secteur", ["Tech", "Énergie", "Finance", "Santé", "Industrie", "ETF Europe", "ETF Émergents", "ETF World", "Métaux", "Autre"])
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
                ticker = st.text_input("Ticker (BTC, ETH...)*", key="ct")
                qty = st.number_input("Quantité*", min_value=0.0, format="%.8f", key="cq")
            with c2:
                prix = st.number_input("Prix achat USD*", min_value=0.0, key="cp")
                staked = st.checkbox("Position stakée?")
                apy = st.number_input("APY %", min_value=0.0, max_value=100.0) if staked else 0
            if st.form_submit_button("➕ Ajouter"):
                if nom and ticker and qty > 0 and prix > 0:
                    data["crypto"].append({"nom": nom, "ticker": ticker.upper(), "qty": qty, "prix_achat_usd": prix, "is_staked": staked, "staking_value_usd": qty*prix, "staking_apy": apy, "staking_gains_usd": 0})
                    save_data(data)
                    st.success(f"✅ {nom} ajoutée!")
                    st.rerun()
    
    with tabs[2]:
        st.markdown("**Ordres DCA:**")
        for i, o in enumerate(data["dca_orders"]):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                data["dca_orders"][i]["montant_eur"] = st.number_input(o["crypto"], value=o["montant_eur"], key=f"dca_m_{i}")
            with c2:
                nd = st.date_input("Prochain", value=datetime.strptime(o["prochaine_execution"], "%Y-%m-%d"), key=f"dca_d_{i}")
                data["dca_orders"][i]["prochaine_execution"] = nd.strftime("%Y-%m-%d")
        st.markdown("**Disponible:**")
        data["crypto_extras"]["disponible_usd"] = st.number_input("USD disponible", value=data["crypto_extras"]["disponible_usd"])
        if st.button("💾 Sauvegarder"):
            save_data(data)
            st.success("Sauvegardé!")
            st.rerun()
    
    with tabs[3]:
        st.markdown("**Valeurs de staking (mettre à jour depuis votre plateforme):**")
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
        st.markdown("**Positions immobilières:**")
        c1, c2 = st.columns(2)
        with c1:
            immo["bricks_bloque"] = st.number_input("Bricks Bloqué €", value=immo["bricks_bloque"])
            immo["taux_bloque"] = st.number_input("Taux Bloqué %", value=immo["taux_bloque"]*100) / 100
        with c2:
            immo["bricks_libre"] = st.number_input("Bricks Libre €", value=immo["bricks_libre"])
            immo["taux_libre"] = st.number_input("Taux Libre %", value=immo["taux_libre"]*100) / 100
        immo["royaltiz"] = st.number_input("Royaltiz €", value=immo["royaltiz"])
        if st.button("💾 Sauvegarder Immo"):
            save_data(data)
            st.success("Sauvegardé!")
            st.rerun()
    
    with tabs[5]:
        st.warning("⚠️ Actions irréversibles!")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Actions:**")
            for i, p in enumerate(data["bourse"]):
                if st.button(f"🗑️ {p['nom']}", key=f"ds_{i}"):
                    data["bourse"].pop(i)
                    save_data(data)
                    st.rerun()
        with c2:
            st.markdown("**Cryptos:**")
            for i, c in enumerate(data["crypto"]):
                if st.button(f"🗑️ {c['nom']}", key=f"dc_{i}"):
                    data["crypto"].pop(i)
                    save_data(data)
                    st.rerun()

elif view == "🔍 Comparer":
    st.markdown('<p class="section-title">🔍 COMPARATEUR ETF & ACTIONS</p>', unsafe_allow_html=True)
    
    # Header élégant
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 20px; padding: 25px; margin-bottom: 25px; border: 1px solid #2a4a6a;">
        <h3 style="color: #4ade80; margin: 0 0 10px 0;">📊 Analysez et comparez vos investissements</h3>
        <p style="color: #a0aec0; margin: 0;">Comparez jusqu'à 5 ETF ou actions pour identifier les meilleures opportunités.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Suggestions populaires avec meilleur design
    st.markdown("##### 💡 Sélection rapide")
    suggestions = {
        "🌍 World": "CW8.PA",
        "🇺🇸 S&P500": "SPY",
        "💻 Nasdaq": "QQQ",
        "🇪🇺 Europe": "MEUD.PA",
        "🌏 Émergents": "AEEM.PA",
        "🏥 Santé": "IXJ"
    }
    
    cols = st.columns(6)
    for i, (name, ticker) in enumerate(suggestions.items()):
        with cols[i]:
            st.button(name, key=f"sug_{ticker}", use_container_width=True)
    
    st.markdown("")
    
    # Zone de saisie améliorée
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tickers_input = st.text_input("🔎 Tickers à comparer", value="CW8.PA, SPY, QQQ", placeholder="Ex: AAPL, MSFT, GOOGL", label_visibility="collapsed")
    with col2:
        period = st.selectbox("Période", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3, label_visibility="collapsed")
    with col3:
        include_portfolio = st.checkbox("+ Mon portfolio", value=False)
    
    if st.button("🚀 Lancer l'analyse", use_container_width=True, type="primary"):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        if include_portfolio:
            portfolio_tickers = [p["ticker"] for p in data["bourse"][:3]]
            tickers = list(dict.fromkeys(tickers + portfolio_tickers))[:5]
        
        if tickers:
            with st.spinner("🔄 Analyse en cours..."):
                comparison_data = get_etf_comparison_data(tickers, period)
            
            if comparison_data and len(comparison_data) > 0:
                st.markdown("---")
                
                # ===== GRAPHIQUE CORRIGÉ =====
                st.markdown("#### 📈 Évolution comparative (Base 100)")
                
                fig = go.Figure()
                colors = ['#4ade80', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6']
                
                for i, (ticker, d) in enumerate(comparison_data.items()):
                    fig.add_trace(go.Scatter(
                        x=d["dates"],
                        y=d["history"],
                        mode='lines',
                        name=f"{d['name'][:20]}",
                        line=dict(color=colors[i % len(colors)], width=3),
                        hovertemplate=f"<b>{d['name'][:20]}</b><br>Date: %{{x}}<br>Valeur: %{{y:.2f}}<extra></extra>"
                    ))
                
                fig.update_layout(
                    height=450,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(20,20,32,0.8)',
                    font=dict(color='#e0e0e0', size=12),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        bgcolor="rgba(20,20,32,0.8)",
                        bordercolor="#2a2a3a",
                        borderwidth=1
                    ),
                    margin=dict(t=60, b=40, l=60, r=20),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.05)',
                        tickfont=dict(size=10)
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.1)',
                        title="Performance (%)",
                        tickformat='.0f'
                    ),
                    hovermode='x unified'
                )
                fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.3)", annotation_text="Base 100", annotation_position="right")
                st.plotly_chart(fig, use_container_width=True)
                
                # ===== TABLEAU COMPARATIF CORRIGÉ =====
                st.markdown("#### 🏆 Classement")
                
                # Trier par performance
                sorted_data = sorted(comparison_data.items(), key=lambda x: x[1]["perf"], reverse=True)
                best_ticker = sorted_data[0][0] if sorted_data else None
                
                # Créer un tableau stylisé
                for rank, (ticker, d) in enumerate(sorted_data, 1):
                    is_winner = rank == 1
                    is_in_portfolio = ticker in [p["ticker"] for p in data["bourse"]]
                    
                    # Couleurs selon le rang
                    if rank == 1:
                        rank_color = "#ffd700"
                        rank_icon = "🥇"
                        border_color = "#4ade80"
                    elif rank == 2:
                        rank_color = "#c0c0c0"
                        rank_icon = "🥈"
                        border_color = "#3b82f6"
                    elif rank == 3:
                        rank_color = "#cd7f32"
                        rank_icon = "🥉"
                        border_color = "#f59e0b"
                    else:
                        rank_color = "#6b7280"
                        rank_icon = f"#{rank}"
                        border_color = "#252535"
                    
                    perf_color = "#4ade80" if d["perf"] > 0 else "#f87171"
                    portfolio_badge = '<span style="background:#3b82f6; color:#fff; padding:3px 8px; border-radius:8px; font-size:10px; margin-left:10px;">📂 PORTFOLIO</span>' if is_in_portfolio else ""
                    
                    # Formater les valeurs
                    ter_display = f"{d['expense_ratio']*100:.2f}%" if d['expense_ratio'] > 0 else "N/A"
                    div_display = f"{d['dividend_yield']*100:.2f}%" if d['dividend_yield'] > 0 else "N/A"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(145deg, #141420 0%, #1a1a28 100%); border-radius: 16px; padding: 20px; margin-bottom: 12px; border-left: 4px solid {border_color}; display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <div style="font-size: 28px; color: {rank_color};">{rank_icon}</div>
                            <div>
                                <div style="color: #fff; font-weight: 700; font-size: 16px;">{d['name'][:30]} {portfolio_badge}</div>
                                <div style="color: #6b7280; font-size: 12px;">{ticker}</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 40px; align-items: center;">
                            <div style="text-align: center;">
                                <div style="color: #6b7280; font-size: 10px; text-transform: uppercase;">Performance</div>
                                <div style="color: {perf_color}; font-size: 20px; font-weight: 800;">{d['perf']:+.2f}%</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="color: #6b7280; font-size: 10px; text-transform: uppercase;">Prix</div>
                                <div style="color: #fff; font-size: 16px; font-weight: 600;">{d['current_price']:.2f} {d['currency']}</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="color: #6b7280; font-size: 10px; text-transform: uppercase;">TER</div>
                                <div style="color: #a0aec0; font-size: 14px;">{ter_display}</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="color: #6b7280; font-size: 10px; text-transform: uppercase;">Dividende</div>
                                <div style="color: #a0aec0; font-size: 14px;">{div_display}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # ===== ANALYSE =====
                st.markdown("---")
                st.markdown("#### 💡 Analyse")
                
                best = sorted_data[0]
                worst = sorted_data[-1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0f2a1f 0%, #1a4030 100%); border-radius: 16px; padding: 20px; border: 1px solid #22543d;">
                        <div style="color: #4ade80; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">🏆 Meilleur choix</div>
                        <div style="color: #fff; font-size: 20px; font-weight: 700;">{best[1]['name'][:25]}</div>
                        <div style="color: #4ade80; font-size: 28px; font-weight: 800; margin-top: 5px;">{best[1]['perf']:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #2a1f1f 0%, #402020 100%); border-radius: 16px; padding: 20px; border: 1px solid #543d3d;">
                        <div style="color: #f87171; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">📉 Moins performant</div>
                        <div style="color: #fff; font-size: 20px; font-weight: 700;">{worst[1]['name'][:25]}</div>
                        <div style="color: #f87171; font-size: 28px; font-weight: 800; margin-top: 5px;">{worst[1]['perf']:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Suggestion si meilleur n'est pas dans portfolio
                portfolio_tickers = [p["ticker"] for p in data["bourse"]]
                if best[0] not in portfolio_tickers:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1a1a3e 0%, #1e2a4a 100%); border-radius: 16px; padding: 20px; margin-top: 15px; border: 1px solid #3b5998;">
                        <div style="color: #60a5fa; font-size: 14px;">💡 <strong>Suggestion:</strong> {best[1]['name']} n'est pas dans votre portefeuille. Avec une performance de {best[1]['perf']:+.2f}%, cela pourrait être un ajout intéressant.</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("❌ Impossible de récupérer les données. Vérifiez les tickers saisis.")
        else:
            st.warning("⚠️ Veuillez entrer au moins un ticker.")

elif view == "🎯 Recommandations":
    st.markdown('<p class="section-title">🎯 RECOMMANDATIONS</p>', unsafe_allow_html=True)
    analysis = analyze_portfolio(data)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        sc = analysis["score"]
        col = "#4ade80" if sc >= 70 else "#fbbf24" if sc >= 50 else "#f87171"
        st.markdown(f'<div class="score-container" style="border-color:{col};"><div style="color:#6b7280; font-size:12px;">SCORE DE SANTÉ</div><div class="score-value" style="color:{col};">{sc}/100</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🌍 Géographie")
        geo = analysis["geo_pct"]
        if geo:
            fig = go.Figure(go.Bar(x=list(geo.values()), y=list(geo.keys()), orientation='h', marker_color=['#3b82f6' if v < 40 else '#f87171' for v in geo.values()], text=[f"{v:.1f}%" for v in geo.values()], textposition='auto'))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(showgrid=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### 📊 Secteurs")
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
    st.markdown('<p class="section-title">💹 SIMULATION</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        apport = st.number_input("Apport mensuel €", value=500, step=100)
        rend = st.slider("Rendement %", 0, 20, 8)
    with c2:
        duree = st.slider("Années", 1, 30, 10)
        capital = st.number_input("Capital initial", value=int(patrimoine), step=1000)
    
    mois = duree * 12
    tm = (1 + rend/100) ** (1/12) - 1
    proj = [capital]
    for _ in range(mois):
        proj.append(proj[-1] * (1 + tm) + apport)
    
    dates = pd.date_range(start=datetime.now(), periods=mois+1, freq='ME')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=proj, mode='lines', fill='tozeroy', line=dict(color='#4ade80', width=3), fillcolor='rgba(74,222,128,0.1)'))
    fig.add_hline(y=100000, line_dash="dash", line_color="#f59e0b", annotation_text="100k€")
    fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,32,1)', font=dict(color='#fff'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1e1e2e', tickformat=',.0f'))
    st.plotly_chart(fig, use_container_width=True)
    
    final = proj[-1]
    verse = capital + apport * mois
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valeur finale", f"{final:,.0f}€")
    c2.metric("Versé", f"{verse:,.0f}€")
    c3.metric("Gains", f"{final - verse:,.0f}€")
    for i, v in enumerate(proj):
        if v >= 100000:
            c4.metric("100k€", f"{i//12}a {i%12}m")
            break
    else:
        c4.metric("100k€", "Non atteint")

elif view == "💰 Frais":
    st.markdown('<p class="section-title">💰 ANALYSEUR DE FRAIS</p>', unsafe_allow_html=True)
    
    # Calculer les frais estimés pour chaque position
    frais_positions = []
    for p in data["bourse"]:
        # Estimer les frais selon le type
        if "ETF" in p.get("secteur", ""):
            ter = 0.002  # 0.20% pour ETF
        elif p.get("secteur") == "Tech":
            ter = 0.0  # Actions individuelles = pas de TER
        else:
            ter = 0.0
        
        frais_annuel = p.get("valeur_actuelle", 0) * ter
        frais_positions.append({
            "nom": p["nom"],
            "ticker": p["ticker"],
            "valeur": p.get("valeur_actuelle", 0),
            "ter": ter,
            "frais_an": frais_annuel,
            "secteur": p.get("secteur", "")
        })
    
    # Frais totaux
    frais_ter_an = sum(f["frais_an"] for f in frais_positions)
    frais_courtage_estim = total_bourse_actuel * 0.001  # 0.1% de spread estimé
    frais_totaux_an = frais_ter_an + frais_courtage_estim
    frais_30_ans = frais_totaux_an * 30 * 1.05  # Avec croissance
    
    # ETF recommandés bas coût
    etf_recommandes = [
        {"nom": "Amundi MSCI World", "ticker": "CW8.PA", "ter": 0.0012, "desc": "World diversifié", "perf_5y": "+85%"},
        {"nom": "Vanguard S&P 500", "ticker": "VUSA.AS", "ter": 0.0007, "desc": "USA grandes caps", "perf_5y": "+95%"},
        {"nom": "iShares Core MSCI Europe", "ticker": "IMEU.AS", "ter": 0.0012, "desc": "Europe diversifié", "perf_5y": "+45%"},
        {"nom": "Amundi MSCI Emerging", "ticker": "AEEM.PA", "ter": 0.0014, "desc": "Marchés émergents", "perf_5y": "+25%"},
        {"nom": "Xtrackers MSCI World", "ticker": "XDWD.DE", "ter": 0.0019, "desc": "World accumulation", "perf_5y": "+82%"},
        {"nom": "Lyxor Nasdaq 100", "ticker": "PUST.PA", "ter": 0.0022, "desc": "Tech US", "perf_5y": "+140%"},
    ]
    
    # Header avec stats principales
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(248, 113, 113, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%); border-radius: 24px; padding: 30px; margin-bottom: 30px; border: 1px solid rgba(248, 113, 113, 0.2);">
        <div style="text-align: center;">
            <div style="color: #f87171; font-size: 11px; letter-spacing: 3px; margin-bottom: 10px;">⚠️ IMPACT DES FRAIS SUR 30 ANS</div>
            <div style="font-size: 64px; font-weight: 900; color: #f87171; letter-spacing: -3px;">""" + f"{frais_30_ans:,.0f}€" + """</div>
            <div style="color: #a0aec0; margin-top: 10px;">Soit """ + f"{frais_totaux_an:,.0f}€" + """/an en moyenne</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3 colonnes de stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(248, 113, 113, 0.3);">
            <div style="font-size: 28px;">📊</div>
            <div class="mini-value" style="color: #f87171;">{frais_ter_an:,.2f}€</div>
            <div class="mini-title">FRAIS DE GESTION/AN</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        ter_moyen = (frais_ter_an / total_bourse_actuel * 100) if total_bourse_actuel > 0 else 0
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(251, 191, 36, 0.3);">
            <div style="font-size: 28px;">📈</div>
            <div class="mini-value" style="color: #fbbf24;">{ter_moyen:.2f}%</div>
            <div class="mini-title">TER MOYEN PONDÉRÉ</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        eco_potentielle = frais_30_ans * 0.6
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(74, 222, 128, 0.3);">
            <div style="font-size: 28px;">💰</div>
            <div class="mini-value" style="color: #4ade80;">{eco_potentielle:,.0f}€</div>
            <div class="mini-title">ÉCONOMIE POSSIBLE</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Analyse de ton portefeuille
    st.markdown("### 🔍 Analyse de ton portefeuille")
    
    # Identifier les positions coûteuses
    actions_indiv = [p for p in data["bourse"] if "ETF" not in p.get("secteur", "")]
    etf_existants = [p for p in data["bourse"] if "ETF" in p.get("secteur", "")]
    
    # Recommandations personnalisées
    recommandations = []
    
    # Check concentration actions individuelles
    total_actions = sum(p.get("valeur_actuelle", 0) for p in actions_indiv)
    pct_actions = (total_actions / total_bourse_actuel * 100) if total_bourse_actuel > 0 else 0
    
    if pct_actions > 60:
        recommandations.append({
            "type": "high",
            "icon": "⚠️",
            "titre": "Forte concentration en actions individuelles",
            "detail": f"{pct_actions:.0f}% de ton portefeuille est en actions individuelles. Les ETF offrent une diversification à moindre coût.",
            "action": "Considère de basculer une partie vers des ETF World ou S&P 500",
            "etf": ["CW8.PA", "VUSA.AS"]
        })
    
    # Check si pas d'ETF World
    has_world = any("World" in p["nom"] or "MSCI" in p["nom"] for p in data["bourse"])
    if not has_world:
        recommandations.append({
            "type": "medium",
            "icon": "🌍",
            "titre": "Absence d'ETF World",
            "detail": "Un ETF World offre une diversification mondiale avec un TER très bas (~0.12-0.20%).",
            "action": "L'ETF CW8.PA (Amundi MSCI World) est éligible PEA avec 0.12% de frais",
            "etf": ["CW8.PA", "XDWD.DE"]
        })
    
    # Check exposition sectorielle
    tech_positions = [p for p in data["bourse"] if p.get("secteur") == "Tech"]
    total_tech = sum(p.get("valeur_actuelle", 0) for p in tech_positions)
    pct_tech = (total_tech / total_bourse_actuel * 100) if total_bourse_actuel > 0 else 0
    
    if pct_tech > 40 and len(tech_positions) > 3:
        recommandations.append({
            "type": "medium",
            "icon": "💻",
            "titre": "Concentration Tech via actions individuelles",
            "detail": f"Tu as {len(tech_positions)} actions tech représentant {pct_tech:.0f}% du portefeuille. Un ETF Nasdaq pourrait simplifier.",
            "action": "Le Lyxor Nasdaq 100 (PUST.PA) offre une exposition tech diversifiée",
            "etf": ["PUST.PA", "QQQ"]
        })
    
    # Afficher les recommandations
    if recommandations:
        for reco in recommandations:
            border_color = "#f87171" if reco["type"] == "high" else "#fbbf24" if reco["type"] == "medium" else "#4ade80"
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, rgba(20, 20, 32, 0.9) 0%, rgba(26, 26, 40, 0.9) 100%); border-radius: 16px; padding: 22px; margin-bottom: 15px; border-left: 4px solid {border_color};">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 24px;">{reco["icon"]}</span>
                    <span style="color: #fff; font-weight: 700; font-size: 16px;">{reco["titre"]}</span>
                </div>
                <p style="color: #a0aec0; margin-bottom: 12px; font-size: 14px;">{reco["detail"]}</p>
                <p style="color: #4ade80; font-weight: 600; font-size: 13px;">💡 {reco["action"]}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Ton portefeuille semble bien optimisé en termes de frais !")
    
    st.markdown("---")
    
    # ETF Recommandés
    st.markdown("### 🏆 ETF à bas coût recommandés")
    st.markdown("<p style='color: #6b7280; margin-bottom: 20px;'>Sélection d'ETF avec les frais les plus compétitifs du marché</p>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    for i, etf in enumerate(etf_recommandes):
        with cols[i % 3]:
            ter_color = "#4ade80" if etf["ter"] < 0.0015 else "#fbbf24" if etf["ter"] < 0.0025 else "#f87171"
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, rgba(20, 20, 32, 0.9) 0%, rgba(26, 26, 40, 0.9) 100%); border-radius: 16px; padding: 20px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div style="color: #fff; font-weight: 700; font-size: 14px;">{etf["nom"]}</div>
                        <div style="color: #6b7280; font-size: 11px;">{etf["ticker"]}</div>
                    </div>
                    <div style="background: {ter_color}20; color: {ter_color}; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: 700;">
                        {etf["ter"]*100:.2f}%
                    </div>
                </div>
                <div style="color: #a0aec0; font-size: 12px; margin-bottom: 8px;">{etf["desc"]}</div>
                <div style="color: #4ade80; font-size: 13px; font-weight: 600;">Perf 5 ans: {etf["perf_5y"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Comparatif frais
    st.markdown("### 📊 Impact des frais sur 30 ans")
    
    # Simulation graphique
    capital_init = total_bourse_actuel if total_bourse_actuel > 0 else 10000
    apport_mensuel = 200
    rendement = 0.07  # 7% annuel
    
    annees = list(range(0, 31))
    
    # Scénario actuel (frais moyens)
    ter_actuel = ter_moyen / 100 if ter_moyen > 0 else 0.02
    values_actuel = []
    val = capital_init
    for a in annees:
        values_actuel.append(val)
        val = val * (1 + rendement - ter_actuel) + apport_mensuel * 12
    
    # Scénario optimisé (0.12% TER)
    ter_opti = 0.0012
    values_opti = []
    val = capital_init
    for a in annees:
        values_opti.append(val)
        val = val * (1 + rendement - ter_opti) + apport_mensuel * 12
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=annees, y=values_opti, mode='lines', name='ETF bas coût (0.12%)',
        line=dict(color='#4ade80', width=3),
        fill='tonexty', fillcolor='rgba(74,222,128,0.1)'
    ))
    fig.add_trace(go.Scatter(
        x=annees, y=values_actuel, mode='lines', name=f'Situation actuelle ({ter_actuel*100:.2f}%)',
        line=dict(color='#f87171', width=3)
    ))
    
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,20,32,0.8)',
        font=dict(color='#e0e0e0'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=50, b=40, l=60, r=20),
        xaxis=dict(title="Années", showgrid=False),
        yaxis=dict(title="Valeur (€)", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickformat=',.0f'),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Différence finale
    diff = values_opti[-1] - values_actuel[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(74, 222, 128, 0.3);">
            <div style="color: #6b7280; font-size: 10px; margin-bottom: 5px;">AVEC ETF BAS COÛT</div>
            <div style="color: #4ade80; font-size: 24px; font-weight: 800;">{values_opti[-1]:,.0f}€</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(248, 113, 113, 0.3);">
            <div style="color: #6b7280; font-size: 10px; margin-bottom: 5px;">SITUATION ACTUELLE</div>
            <div style="color: #f87171; font-size: 24px; font-weight: 800;">{values_actuel[-1]:,.0f}€</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="mini-card" style="border-color: rgba(74, 222, 128, 0.5); background: rgba(74, 222, 128, 0.1);">
            <div style="color: #6b7280; font-size: 10px; margin-bottom: 5px;">💰 ÉCONOMIE</div>
            <div style="color: #4ade80; font-size: 24px; font-weight: 800;">+{diff:,.0f}€</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%); border-radius: 16px; padding: 20px; margin-top: 20px; border: 1px solid rgba(74, 222, 128, 0.2); text-align: center;">
        <p style="color: #4ade80; font-size: 16px; font-weight: 600; margin: 0;">
            💡 En optimisant tes frais, tu pourrais gagner <strong>{diff:,.0f}€</strong> supplémentaires sur 30 ans !
        </p>
    </div>
    """, unsafe_allow_html=True)

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
        <div class="dividend-progress"><div class="dividend-fill" style="width:{progress}%;">{progress:.1f}%</div></div>
    </div>''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="mini-card" style="border:2px solid #3b82f6;"><div style="font-size:24px;">📈</div><div class="mini-value" style="color:#4ade80;">{div_mens:.2f}€</div><div class="mini-title">Dividendes</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="mini-card" style="border:2px solid #f59e0b;"><div style="font-size:24px;">⛓️</div><div class="mini-value" style="color:#4ade80;">{staking_mens:.2f}€</div><div class="mini-title">Staking</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="mini-card" style="border:2px solid #10b981;"><div style="font-size:24px;">🏠</div><div class="mini-value" style="color:#4ade80;">{immo_mens:.2f}€</div><div class="mini-title">Immobilier</div></div>', unsafe_allow_html=True)

# ============== FOOTER ==============
st.markdown("---")
st.markdown(f'''<div style="text-align:center; color:#6b7280; font-size:12px; padding:20px;">
    💎 HORIZON FINANCE PRO v5 • {datetime.now().strftime("%d/%m/%Y %H:%M")}<br>
    <span style="color:#4a5568;">⚠️ Ne constitue pas un conseil en investissement</span>
</div>''', unsafe_allow_html=True)
