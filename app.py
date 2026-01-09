import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(page_title="Horizon Finance Pro", layout="wide", initial_sidebar_state="expanded")

# Auto-refresh toutes les 5 minutes (300 secondes)
AUTO_REFRESH_INTERVAL = 300

# Initialiser le compteur de refresh dans session_state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

TAUX_USD_EUR = 0.95

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    .stApp { background: linear-gradient(180deg, #000000 0%, #0a0a0a 100%); font-family: 'Inter', sans-serif; }
    html { scroll-behavior: smooth; }
    .hero-container { text-align: center; padding: 40px 0 10px 0; }
    .total-label { color: #8E8E93; font-size: 0.9em; font-weight: 700; letter-spacing: 4px; }
    .total-amount { font-size: 7.5em !important; font-weight: 900; letter-spacing: -6px; 
                   background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; line-height: 0.8; }
    .perf-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9em; margin-top: 10px; }
    .perf-positive { background: linear-gradient(135deg, #1e3a1e 0%, #2d5a2d 100%); color: #4ade80; }
    .perf-negative { background: linear-gradient(135deg, #3a1e1e 0%, #5a2d2d 100%); color: #f87171; }
    .section-title { color: #8E8E93; font-weight: 700; font-size: 0.85em; letter-spacing: 2px; margin-bottom: 20px; }
    .card-premium { background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%); border: 1px solid #222222; 
                   border-radius: 24px; padding: 25px; margin-bottom: 20px; transition: all 0.3s; }
    .card-premium:hover { transform: translateY(-2px); border-color: #333; }
    .metric-card { background: #1c1c1e; padding: 20px; border-radius: 16px; border: 1px solid #2c2c2e; }
    .news-summary { background: #2c2c2e; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #4ade80; }
    .news-keypoints { color: #4ade80; font-size: 0.85em; font-weight: 600; margin-top: 10px; }
    .fee-hero { background: linear-gradient(135deg, #3a1e1e 0%, #5a2d2d 100%); padding: 40px; 
               border-radius: 24px; border: 2px solid #f87171; text-align: center; margin-bottom: 30px; }
    .fee-amount { font-size: 4em; font-weight: 900; color: #f87171; }
    .fee-card-item { background: linear-gradient(135deg, #1c1c1e 0%, #2a2a2a 100%); padding: 25px; 
                     border-radius: 16px; border: 1px solid #f87171; margin-bottom: 15px; }
    .fee-icon { font-size: 2.5em; margin-bottom: 10px; }
    .fee-value { font-size: 2em; font-weight: 900; color: #f87171; margin: 10px 0; }
    .economy-card { background: linear-gradient(135deg, #1e3a1e 0%, #2d5a2d 100%); padding: 30px; 
                   border-radius: 20px; border: 2px solid #4ade80; text-align: center; }
    .dividend-goal { background: linear-gradient(135deg, #1e3a1e 0%, #153015 100%); padding: 25px; 
                    border-radius: 20px; border: 2px solid #4ade80; margin-bottom: 25px; }
    .dividend-progress { height: 35px; background: #2c2c2e; border-radius: 18px; overflow: hidden; margin: 15px 0; }
    .dividend-fill { height: 100%; background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); 
                    display: flex; align-items: center; justify-content: center; }
    .passive-income-card { background: linear-gradient(135deg, #1e2a3a 0%, #15202b 100%); padding: 25px; 
                          border-radius: 20px; border: 2px solid #3b82f6; }
    .income-breakdown { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
    .income-source { background: #1c1c1e; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #2c2c2e; }
    .income-amount { font-size: 1.8em; font-weight: 900; color: #4ade80; }
    .reco-card { background: #1c1c1e; padding: 20px; border-radius: 16px; border: 1px solid #2c2c2e; margin-bottom: 15px; }
    .live-badge { display: inline-block; padding: 4px 12px; background: #1e3a1e; color: #4ade80; 
                 border-radius: 12px; font-size: 0.75em; font-weight: 700; margin-left: 10px; }
    .live-dot { display: inline-block; width: 8px; height: 8px; background: #4ade80; border-radius: 50%; 
               margin-right: 6px; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    
    /* Dashboard Cards */
    .dash-card { background: linear-gradient(135deg, #1c1c1e 0%, #252525 100%); border-radius: 20px; 
                padding: 20px; border: 1px solid #333; margin-bottom: 15px; transition: all 0.3s; }
    .dash-card:hover { transform: translateY(-3px); border-color: #4ade80; box-shadow: 0 10px 30px rgba(74, 222, 128, 0.1); }
    .dash-card-title { color: #8E8E93; font-size: 0.75em; font-weight: 600; letter-spacing: 1px; margin-bottom: 8px; }
    .dash-card-value { font-size: 1.8em; font-weight: 900; color: #fff; }
    .dash-card-change { font-size: 0.85em; margin-top: 5px; }
    .change-positive { color: #4ade80; }
    .change-negative { color: #f87171; }
    
    /* Mini Cards */
    .mini-card { background: #1c1c1e; border-radius: 12px; padding: 15px; border: 1px solid #2c2c2e; }
    .mini-title { color: #8E8E93; font-size: 0.7em; font-weight: 600; }
    .mini-value { color: #fff; font-size: 1.2em; font-weight: 700; }
    
    /* Section Cards */
    .section-card { background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%); border-radius: 20px; 
                   padding: 25px; border: 1px solid #2c2c2e; margin-bottom: 20px; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .section-link { color: #4ade80; font-size: 0.85em; cursor: pointer; }
    
    /* Progress bars */
    .custom-progress { height: 8px; background: #2c2c2e; border-radius: 4px; overflow: hidden; }
    .custom-progress-fill { height: 100%; border-radius: 4px; }
    
    /* Alert badges */
    .alert-badge { display: inline-block; padding: 4px 10px; border-radius: 8px; font-size: 0.75em; font-weight: 600; }
    .alert-high { background: #3a1e1e; color: #f87171; }
    .alert-medium { background: #3a3a1e; color: #fbbf24; }
    .alert-low { background: #1e3a1e; color: #4ade80; }
    
    /* AI Styles */
    .ai-advisor-container { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                           border-radius: 24px; padding: 30px; border: 2px solid #4a5568; margin-bottom: 20px; }
    .ai-recommendation { background: linear-gradient(135deg, #1c1c1e 0%, #2a2a2a 100%); 
                        padding: 20px; border-radius: 16px; margin: 15px 0; 
                        border: 1px solid #4a5568; transition: all 0.3s; }
    .ai-recommendation:hover { transform: translateX(5px); border-color: #4ade80; }
    .priority-high { border-left: 4px solid #f87171; }
    .priority-medium { border-left: 4px solid #fbbf24; }
    .priority-low { border-left: 4px solid #4ade80; }
    .insight-card { background: linear-gradient(135deg, #1e3a5f 0%, #1a365d 100%); 
                   padding: 20px; border-radius: 16px; margin: 10px 0; border: 1px solid #3182ce; }
    
    /* Fee detail cards */
    .fee-detail-card { background: linear-gradient(135deg, #1c1c1e 0%, #252525 100%); 
                      padding: 28px; border-radius: 20px; border: 1px solid #3a3a3a;
                      transition: all 0.3s ease; margin-bottom: 20px; }
    .fee-detail-card:hover { transform: translateY(-5px); border-color: #f87171; 
                            box-shadow: 0 15px 40px rgba(248, 113, 113, 0.15); }
    
    /* Passive income tips */
    .tip-difficulty { display: inline-block; padding: 4px 10px; border-radius: 8px; font-size: 0.75em; font-weight: 600; }
    .difficulty-easy { background: #1e3a1e; color: #4ade80; }
    .difficulty-medium { background: #3a3a1e; color: #fbbf24; }
    .difficulty-hard { background: #3a1e1e; color: #f87171; }
    
    /* News ticker */
    .news-ticker { background: linear-gradient(90deg, #1e3a1e 0%, #153015 100%); padding: 10px 20px; 
                  border-radius: 12px; margin-bottom: 20px; overflow: hidden; }
    .ticker-content { display: flex; gap: 30px; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    
    /* Quick stats */
    .quick-stat { text-align: center; padding: 15px; }
    .quick-stat-value { font-size: 2em; font-weight: 900; }
    .quick-stat-label { color: #8E8E93; font-size: 0.8em; margin-top: 5px; }
    
    /* Top performers */
    .performer-row { display: flex; justify-content: space-between; align-items: center; 
                    padding: 12px 0; border-bottom: 1px solid #2c2c2e; }
    .performer-row:last-child { border-bottom: none; }
    </style>
""", unsafe_allow_html=True)

# DONNÉES
bourse_positions = [
    {"nom": "Streamwide", "qty": 8.652555, "valeur": 633.37, "perf": 111, "secteur": "Tech", "pays": "France", "dividend_yield": 0},
    {"nom": "Chevron", "qty": 3.415936, "valeur": 466.75, "perf": -6.46, "secteur": "Énergie", "pays": "USA", "dividend_yield": 3.8},
    {"nom": "Alphabet (A)", "qty": 1.590988, "valeur": 444.04, "perf": 77.00, "secteur": "Tech", "pays": "USA", "dividend_yield": 0},
    {"nom": "Nvidia", "qty": 2.120073, "valeur": 336.37, "perf": 21.87, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.03},
    {"nom": "Total Energie", "qty": 5.136355, "valeur": 280.60, "perf": 0.58, "secteur": "Énergie", "pays": "France", "dividend_yield": 5.2},
    {"nom": "Apple", "qty": 1.173637, "valeur": 261.19, "perf": 11.15, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.5},
    {"nom": "Riot Platforms", "qty": 19.745854, "valeur": 256.02, "perf": 7.13, "secteur": "Crypto Mining", "pays": "USA", "dividend_yield": 0},
    {"nom": "Physical Silver", "qty": 3.587989, "valeur": 223.15, "perf": 49.82, "secteur": "Métaux", "pays": "UK", "dividend_yield": 0},
    {"nom": "Microsoft", "qty": 0.265737, "valeur": 108.90, "perf": -1.89, "secteur": "Tech", "pays": "USA", "dividend_yield": 0.8},
    {"nom": "Prosus", "qty": 2, "valeur": 107.64, "perf": -7.08, "secteur": "Tech", "pays": "Pays-Bas", "dividend_yield": 0},
    {"nom": "Air Liquide", "qty": 0.62586, "valeur": 98.07, "perf": -1.93, "secteur": "Industrie", "pays": "France", "dividend_yield": 1.9},
    {"nom": "FTSE EUR", "qty": 1.288122, "valeur": 70.82, "perf": 4.15, "secteur": "ETF", "pays": "Europe", "dividend_yield": 2.8},
    {"nom": "EURO STOXX 50", "qty": 2.542464, "valeur": 48.43, "perf": 3.04, "secteur": "ETF", "pays": "Europe", "dividend_yield": 3.1},
    {"nom": "Xiaomi", "qty": 9.424083, "valeur": 39.69, "perf": -11.80, "secteur": "Tech", "pays": "Chine", "dividend_yield": 0},
    {"nom": "MSCI CHINA", "qty": 5.536076, "valeur": 30.03, "perf": 0.13, "secteur": "ETF", "pays": "Chine", "dividend_yield": 2.2},
]

# Données crypto en USD
crypto_positions_usd = [
    {"nom": "Ethereum", "qty": 0.21283369, "valeur_usd": 663.07, "gain_usd": 51.45, "perf": 8.41, "staking_apy": 2.90},
    {"nom": "Solana", "qty": 2.23274878, "valeur_usd": 310.51, "gain_usd": 21.08, "perf": 7.29, "staking_apy": 0},
    {"nom": "Bitcoin", "qty": 0.00271222, "valeur_usd": 247.31, "gain_usd": -12.96, "perf": -4.98, "staking_apy": 0},
    {"nom": "Polkadot", "qty": 17.8306141, "valeur_usd": 37.45, "gain_usd": -64.34, "perf": -63.11, "staking_apy": 0},
    {"nom": "Cardano", "qty": 64.706973, "valeur_usd": 25.72, "gain_usd": -53.75, "perf": -67.63, "staking_apy": 0},
]

# Conversion USD -> EUR
crypto_positions = []
for crypto in crypto_positions_usd:
    crypto_eur = crypto.copy()
    crypto_eur['valeur_eur'] = crypto['valeur_usd'] * TAUX_USD_EUR
    crypto_eur['gain_eur'] = crypto['gain_usd'] * TAUX_USD_EUR
    crypto_eur['prix_unitaire_eur'] = (crypto['valeur_usd'] / crypto['qty']) * TAUX_USD_EUR if crypto['qty'] > 0 else 0
    crypto_positions.append(crypto_eur)

# Staking en EUR
staking_usd = 1049.53
total_staking_eur = staking_usd * TAUX_USD_EUR
staking_gain_usd = 48.49
staking_gain_eur = staking_gain_usd * TAUX_USD_EUR

bricks_bloque, bricks_libre = 500, 1095
interets_bloque = bricks_bloque * 0.085 * 0.5
interets_libre = bricks_libre * 0.04 / 12 * 6
immo_val = bricks_bloque + bricks_libre + interets_bloque + interets_libre
royaltiz_val = 200

# Calculs globaux
total_bourse = sum(p['valeur'] for p in bourse_positions)
total_crypto_eur = sum(p['valeur_eur'] for p in crypto_positions)
total_crypto = total_crypto_eur + total_staking_eur
patrimoine_total = total_bourse + total_crypto + immo_val + royaltiz_val

total_gain_crypto_eur = sum(p['gain_eur'] for p in crypto_positions) + staking_gain_eur
total_investi_bourse = sum(p['valeur'] / (1 + p['perf']/100) for p in bourse_positions)
total_gain_bourse = total_bourse - total_investi_bourse
total_gain = total_gain_bourse + total_gain_crypto_eur
total_investi = total_investi_bourse + (total_crypto - total_gain_crypto_eur)
perf_globale = (total_gain / total_investi) * 100 if total_investi > 0 else 0

objectif_cible = 100000
objectif_dividendes = 500

# ============== FONCTIONS ==============

def get_news():
    """Actualités financières"""
    return [
        {"titre": "📈 CAC 40 en hausse portée par le luxe", "summary": "Le CAC 40 rebondit de 0,8% grâce aux valeurs du luxe.", 
         "keypoints": ["CAC 40 : +0,8%", "LVMH : +2,3%", "Hermès : +1,9%"], "source": "Bloomberg", "time": "Il y a 2h", "impact": "positif", "secteurs": ["Luxe"]},
        {"titre": "💰 La Fed maintient ses taux directeurs", "summary": "La Fed maintient ses taux entre 4,25% et 4,50%.", 
         "keypoints": ["Taux : 4,25-4,50%", "Inflation : 2,8%"], "source": "Reuters", "time": "Il y a 4h", "impact": "neutre", "secteurs": ["Bancaire"]},
        {"titre": "⚡ Nvidia dépasse les attentes avec l'IA", "summary": "Nvidia annonce des revenus record de 26 milliards de dollars.", 
         "keypoints": ["Revenus : 26 Mds$", "Data centers : +200%"], "source": "CNBC", "time": "Il y a 6h", "impact": "positif", "secteurs": ["Tech"]},
        {"titre": "🛢️ Le pétrole recule sur fond de négociations", "summary": "Les cours du pétrole baissent de 2%.", 
         "keypoints": ["Brent : 78$/baril (-2%)", "WTI : 74$/baril"], "source": "Financial Times", "time": "Il y a 8h", "impact": "négatif", "secteurs": ["Énergie"]},
        {"titre": "🏦 BCE : Lagarde évoque une baisse des taux en juin", "summary": "Christine Lagarde ouvre la porte à une baisse des taux.", 
         "keypoints": ["Baisse possible en juin", "Inflation zone euro : 2,4%"], "source": "Les Échos", "time": "Il y a 10h", "impact": "positif", "secteurs": ["Bancaire"]},
        {"titre": "₿ Bitcoin franchit les 95 000$", "summary": "Le Bitcoin atteint un nouveau record historique.", 
         "keypoints": ["BTC : 95 000$ (+5%)", "ETF : +800M$ d'entrées"], "source": "CoinDesk", "time": "Il y a 12h", "impact": "positif", "secteurs": ["Crypto"]},
        {"titre": "🇨🇳 Chine : stimulus économique massif annoncé", "summary": "Pékin annonce un plan de relance de 500 milliards de yuans.", 
         "keypoints": ["Plan : 500 Mds yuans", "Hang Seng : +3%"], "source": "SCMP", "time": "Il y a 14h", "impact": "positif", "secteurs": ["Chine"]},
        {"titre": "🚗 Tesla annonce une baisse de prix en Europe", "summary": "Tesla réduit les prix de ses Model 3 et Model Y de 5%.", 
         "keypoints": ["Model 3 : -5%", "Model Y : -5%"], "source": "Automotive News", "time": "Il y a 16h", "impact": "neutre", "secteurs": ["Auto"]},
    ]

def calculate_exposure():
    geo, sector = {}, {}
    for p in bourse_positions:
        geo[p['pays']] = geo.get(p['pays'], 0) + p['valeur']
        sector[p['secteur']] = sector.get(p['secteur'], 0) + p['valeur']
    return geo, sector

def calculate_fees():
    frais = {
        "Gestion": {"value": total_bourse * 0.015, "rate": "1.5%", "icon": "💼", "desc": "Frais de gestion annuels"},
        "Transaction": {"value": total_bourse * 0.002, "rate": "0.2%", "icon": "💱", "desc": "Commissions sur ordres"},
        "Performance": {"value": total_bourse * 0.005, "rate": "0.5%", "icon": "📈", "desc": "Frais sur les gains"},
        "Garde": {"value": total_bourse * 0.001, "rate": "0.1%", "icon": "🏦", "desc": "Conservation des titres"},
    }
    annuel = sum([f["value"] for f in frais.values()])
    return frais, annuel, annuel * 30 * 1.08, annuel * 30 * 1.08 * 0.65

def calculate_dividends():
    div_an = sum([p['valeur'] * (p['dividend_yield'] / 100) for p in bourse_positions])
    div_mens = div_an / 12
    stak_mens = total_staking_eur * 0.029 / 12
    immo_mens = (interets_bloque + interets_libre * 2) / 12
    total = div_mens + stak_mens + immo_mens
    manque = max(objectif_dividendes - total, 0)
    return {"actuel": total, "objectif": objectif_dividendes, "manque": manque,
            "progress": min(total / objectif_dividendes * 100, 100),
            "breakdown": {"actions": div_mens, "staking": stak_mens, "immo": immo_mens}}

def generate_passive_income_tips(div_data):
    manque = div_data['manque']
    tips = [
        {"icon": "💰", "title": "Actions dividendes aristocrates", "difficulty": "easy",
         "description": "Investir dans des actions versant des dividendes croissants depuis 25+ ans.",
         "action": f"Capital nécessaire : {manque * 12 / 0.045:,.0f}€ pour +{manque * 0.4:.0f}€/mois",
         "exemples": ["Johnson & Johnson (3.0%)", "Coca-Cola (3.1%)", "P&G (2.5%)"],
         "avantages": ["Revenus stables", "Croissance dividendes"], "risques": ["Rendement modéré"]},
        {"icon": "📊", "title": "ETF Dividendes haut rendement", "difficulty": "easy",
         "description": "Diversification instantanée avec des ETF spécialisés dividendes.",
         "action": f"Investir {manque * 12 / 0.05:,.0f}€ pour +{manque * 0.35:.0f}€/mois",
         "exemples": ["iShares Euro Dividend (4.5%)", "SPDR S&P Dividend (3.8%)"],
         "avantages": ["Diversification auto", "Frais réduits"], "risques": ["Frais de gestion"]},
        {"icon": "🏢", "title": "REITs et Foncières cotées", "difficulty": "medium",
         "description": "Investir dans l'immobilier via des sociétés foncières cotées.",
         "action": f"Allouer {manque * 12 / 0.06:,.0f}€ pour +{manque * 0.25:.0f}€/mois",
         "exemples": ["Realty Income (5.2%)", "Unibail (7.8%)", "Klépierre (6.5%)"],
         "avantages": ["Rendements 5-8%", "Distribution obligatoire"], "risques": ["Sensible aux taux"]},
        {"icon": "⛓️", "title": "Augmenter le staking crypto", "difficulty": "medium",
         "description": "Augmentez votre exposition ETH/SOL stakés.",
         "action": f"Staker {manque * 12 / 0.04:,.0f}€ supplémentaires pour +{manque * 0.15:.0f}€/mois",
         "exemples": ["Ethereum (3-4%)", "Solana (6-8%)", "Polkadot (12%)"],
         "avantages": ["Rendements attractifs", "Sécurisation réseau"], "risques": ["Volatilité crypto"]},
        {"icon": "📜", "title": "Obligations Corporate High Yield", "difficulty": "medium",
         "description": "Investir dans des obligations d'entreprises.",
         "action": f"Allouer {manque * 12 / 0.055:,.0f}€ pour +{manque * 0.2:.0f}€/mois",
         "exemples": ["ETF iShares High Yield (5.5%)", "Obligations Total"],
         "avantages": ["Revenus réguliers", "Moins volatile"], "risques": ["Risque de défaut"]},
        {"icon": "🏗️", "title": "Crowdfunding Immobilier", "difficulty": "medium",
         "description": "Financer des projets immobiliers avec des rendements de 8-12%.",
         "action": f"Investir {manque * 12 / 0.09:,.0f}€ pour +{manque * 0.2:.0f}€/mois",
         "exemples": ["Homunity (9%)", "Fundimmo (10%)", "Anaxago (8.5%)"],
         "avantages": ["Rendements élevés", "Projets tangibles"], "risques": ["Illiquidité"]},
        {"icon": "🧱", "title": "Renforcer position Bricks", "difficulty": "easy",
         "description": f"Vous avez {bricks_bloque + bricks_libre}€ sur Bricks. Augmentez pour plus de revenus.",
         "action": f"Ajouter {manque * 12 / 0.07:,.0f}€ pour +{manque * 0.15:.0f}€/mois",
         "exemples": ["Bricks bloqué (8.5%)", "Bricks libre (4%)"],
         "avantages": ["Simplicité", "Immobilier fractionné"], "risques": ["Plateforme jeune"]},
        {"icon": "📈", "title": "Stratégie Covered Calls", "difficulty": "hard",
         "description": "Vendre des options d'achat sur vos actions pour générer des primes.",
         "action": f"Appliquer sur vos positions US pour +{total_bourse * 0.005:.0f}€/mois",
         "exemples": ["Covered calls sur Apple", "Covered calls sur Nvidia"],
         "avantages": ["Revenus additionnels", "Réduit volatilité"], "risques": ["Limite les gains", "Complexité"]},
        {"icon": "🤝", "title": "Prêts entre particuliers (P2P)", "difficulty": "medium",
         "description": "Prêter à des particuliers ou PME via des plateformes régulées.",
         "action": f"Investir {manque * 12 / 0.08:,.0f}€ pour +{manque * 0.15:.0f}€/mois",
         "exemples": ["October (6-9%)", "Mintos (8-12%)", "PeerBerry (10-12%)"],
         "avantages": ["Rendements attractifs", "Automatisation"], "risques": ["Risque de défaut"]},
        {"icon": "💳", "title": "Optimiser le cash-back", "difficulty": "easy",
         "description": "Maximiser les programmes de cash-back sur vos dépenses courantes.",
         "action": "Potentiel +20-50€/mois selon vos dépenses",
         "exemples": ["Boursorama (3%)", "Revolut Metal (1%)", "iGraal"],
         "avantages": ["Sans effort", "Sur dépenses existantes"], "risques": ["Montants limités"]},
    ]
    return tips

def generate_ai_analysis(patrimoine, bourse, crypto, budget_mensuel):
    ratio_crypto = (crypto / patrimoine) * 100
    ratio_bourse = (bourse / patrimoine) * 100
    geo, sector = calculate_exposure()
    nb_positions = len(bourse_positions) + len(crypto_positions)
    score_diversification = min(nb_positions * 5, 100)
    score_risque = int(ratio_crypto * 0.8 + (100 - score_diversification) * 0.2)
    
    analysis = {
        "score_global": max(0, 100 - score_risque),
        "score_risque": score_risque,
        "score_diversification": score_diversification,
        "ratios": {"crypto": ratio_crypto, "bourse": ratio_bourse},
        "insights": [], "recommendations": [], "alertes": [], "opportunites": []
    }
    
    if ratio_crypto > 35:
        analysis["alertes"].append({
            "priority": "high", "icon": "⚠️", "title": "Surexposition crypto",
            "detail": f"Cryptos = {ratio_crypto:.1f}%. Seuil recommandé : 20-30%.",
            "action": f"Réduire de {ratio_crypto - 30:.0f}%", "impact": "Risque -25%"
        })
    
    tech_exposure = sector.get("Tech", 0) / bourse * 100 if bourse > 0 else 0
    if tech_exposure > 50:
        analysis["alertes"].append({
            "priority": "medium", "icon": "🔧", "title": "Concentration Tech",
            "detail": f"Tech = {tech_exposure:.1f}% du portefeuille actions.",
            "action": "Diversifier vers secteurs défensifs", "impact": "Volatilité -15%"
        })
    
    worst = min(bourse_positions, key=lambda x: x['perf'])
    best = max(bourse_positions, key=lambda x: x['perf'])
    
    if worst['perf'] < -10:
        analysis["alertes"].append({
            "priority": "medium", "icon": "📉", "title": f"Position en difficulté : {worst['nom']}",
            "detail": f"Performance : {worst['perf']:.1f}%",
            "action": "Analyser : renforcer, conserver ou vendre", "impact": "Limiter pertes"
        })
    
    analysis["insights"].append({
        "icon": "🏆", "title": f"Position star : {best['nom']}",
        "detail": f"+{best['perf']:.0f}% • {best['valeur']/bourse*100:.1f}% du portefeuille",
        "suggestion": "Considérer prise de bénéfices partielle (20-30%)"
    })
    
    if budget_mensuel >= 500:
        analysis["recommendations"].append({
            "priority": "high", "icon": "🎯", "title": "Plan DCA recommandé",
            "detail": f"Avec {budget_mensuel}€/mois, objectif 100k€ atteignable.",
            "allocation": {"ETF World": f"{int(budget_mensuel * 0.5)}€", "Dividendes": f"{int(budget_mensuel * 0.3)}€", "Crypto": f"{int(budget_mensuel * 0.2)}€"},
            "impact": f"Patrimoine projeté : {patrimoine + budget_mensuel * 12 * 5 * 1.08:,.0f}€ dans 5 ans"
        })
    
    analysis["opportunites"].append({
        "priority": "medium", "icon": "🚀", "title": "Opportunité IA/Tech",
        "detail": "Le secteur IA est en forte croissance.",
        "action": "Considérer AMD, Microsoft ou ETF IA", "impact": "Exposition megatrend IA"
    })
    
    return analysis

def get_top_performers(positions, n=5, ascending=False):
    sorted_pos = sorted(positions, key=lambda x: x['perf'], reverse=not ascending)
    return sorted_pos[:n]

def calculate_allocation_data():
    return {
        'labels': ['Bourse', 'Crypto', 'Immobilier', 'Autres'],
        'values': [total_bourse, total_crypto, immo_val, royaltiz_val],
        'colors': ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6']
    }

# ============== SIDEBAR ==============

with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    
    # Bouton refresh manuel
    if st.button("🔄 Actualiser maintenant", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.session_state.refresh_count += 1
        st.cache_data.clear()
        st.rerun()
    
    # Timer auto-refresh
    time_since_refresh = (datetime.now() - st.session_state.last_refresh).seconds
    time_until_refresh = max(0, AUTO_REFRESH_INTERVAL - time_since_refresh)
    
    st.markdown(f"""
        <div style='background: #1c1c1e; padding: 15px; border-radius: 12px; margin: 10px 0;'>
            <div style='color: #8E8E93; font-size: 0.75em;'>PROCHAINE MAJ AUTO</div>
            <div style='color: #4ade80; font-size: 1.2em; font-weight: 700;'>{time_until_refresh // 60}:{time_until_refresh % 60:02d}</div>
            <div style='color: #8E8E93; font-size: 0.7em; margin-top: 5px;'>Dernière : {st.session_state.last_refresh.strftime('%H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<small style='color:#8E8E93;'>Taux USD/EUR : {TAUX_USD_EUR}</small>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    view_mode = st.radio("Navigation", [
        "📊 Dashboard", 
        "📈 Portefeuille", 
        "🎯 Simulation", 
        "📰 Actualités", 
        "🧠 Conseiller IA", 
        "💰 Scanner Frais", 
        "💸 Revenus Passifs"
    ])
    
    # Auto-refresh via JavaScript
    if time_until_refresh <= 0:
        st.session_state.last_refresh = datetime.now()
        st.rerun()

# ============== HEADER ==============

perf_class = "perf-positive" if total_gain > 0 else "perf-negative"
perf_symbol = "+" if total_gain > 0 else ""

st.markdown(f"""
    <div class="hero-container">
        <p class="total-label">PATRIMOINE NET <span class="live-badge"><span class="live-dot"></span>LIVE</span></p>
        <p class="total-amount">{patrimoine_total:,.0f} €</p>
        <span class="perf-badge {perf_class}">{perf_symbol}{total_gain:,.2f}€ ({perf_symbol}{perf_globale:.2f}%)</span>
    </div>
""", unsafe_allow_html=True)

# ============== MODES ==============

if view_mode == "📊 Dashboard":
    st.markdown('<p class="section-title">📊 TABLEAU DE BORD COMPLET</p>', unsafe_allow_html=True)
    
    # Ticker d'actualités
    news = get_news()
    ticker_items = " • ".join([f"{n['titre']}" for n in news[:4]])
    st.markdown(f"""
        <div class="news-ticker">
            <div style='display: flex; align-items: center; gap: 15px;'>
                <span style='color: #4ade80; font-weight: 700;'>📰 FLASH</span>
                <span style='color: #e0e0e0; font-size: 0.9em;'>{ticker_items}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Row 1: Métriques principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-title">💰 INVESTI</div>
                <div class="dash-card-value">{total_investi:,.0f}€</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        gain_class = "change-positive" if total_gain > 0 else "change-negative"
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-title">📈 GAIN/PERTE</div>
                <div class="dash-card-value {gain_class}">{perf_symbol}{total_gain:,.0f}€</div>
                <div class="dash-card-change {gain_class}">{perf_symbol}{perf_globale:.2f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-title">📊 POSITIONS</div>
                <div class="dash-card-value">{len(bourse_positions) + len(crypto_positions)}</div>
                <div class="dash-card-change" style="color:#8E8E93;">{len(bourse_positions)} actions • {len(crypto_positions)} cryptos</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        div_data = calculate_dividends()
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-title">💸 REVENUS PASSIFS/MOIS</div>
                <div class="dash-card-value" style="color:#4ade80;">{div_data['actuel']:.2f}€</div>
                <div class="dash-card-change" style="color:#8E8E93;">{div_data['progress']:.0f}% de l'objectif</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        analysis = generate_ai_analysis(patrimoine_total, total_bourse, total_crypto, 500)
        score_color = "#4ade80" if analysis['score_global'] >= 70 else "#fbbf24" if analysis['score_global'] >= 50 else "#f87171"
        st.markdown(f"""
            <div class="dash-card">
                <div class="dash-card-title">🎯 SCORE SANTÉ</div>
                <div class="dash-card-value" style="color:{score_color};">{analysis['score_global']}/100</div>
                <div class="dash-card-change" style="color:#8E8E93;">Risque : {analysis['score_risque']}/100</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 2: Allocation + Top/Flop performers
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("#### 🥧 Allocation du patrimoine")
        alloc = calculate_allocation_data()
        fig = go.Figure(data=[go.Pie(
            labels=alloc['labels'],
            values=alloc['values'],
            hole=.65,
            marker_colors=alloc['colors'],
            textinfo='percent',
            textfont_size=14
        )])
        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=20, b=60, l=20, r=20)
        )
        fig.add_annotation(text=f"{patrimoine_total:,.0f}€", x=0.5, y=0.5, font_size=20, 
                          font_color="white", showarrow=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🏆 Top Performers")
        top_performers = get_top_performers(bourse_positions, 5, ascending=False)
        for p in top_performers:
            color = "#4ade80" if p['perf'] > 0 else "#f87171"
            st.markdown(f"""
                <div class="performer-row">
                    <span style='color:#fff;'>{p['nom']}</span>
                    <span style='color:{color}; font-weight:700;'>+{p['perf']:.0f}%</span>
                </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("#### 📉 Flop Performers")
        flop_performers = get_top_performers(bourse_positions, 5, ascending=True)
        for p in flop_performers:
            color = "#4ade80" if p['perf'] > 0 else "#f87171"
            st.markdown(f"""
                <div class="performer-row">
                    <span style='color:#fff;'>{p['nom']}</span>
                    <span style='color:{color}; font-weight:700;'>{p['perf']:.1f}%</span>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 3: Sections récapitulatives
    col1, col2 = st.columns(2)
    
    with col1:
        # Résumé Portefeuille
        st.markdown("#### 📈 Résumé Portefeuille")
        
        # Bourse
        bourse_gain_pct = (total_gain_bourse / total_investi_bourse * 100) if total_investi_bourse > 0 else 0
        bourse_color = "#4ade80" if bourse_gain_pct > 0 else "#f87171"
        st.markdown(f"""
            <div class="section-card">
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='color: #3b82f6; font-weight: 700;'>📊 BOURSE</div>
                        <div style='font-size: 1.8em; font-weight: 900; color: #fff;'>{total_bourse:,.2f}€</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: {bourse_color}; font-weight: 700;'>{'+' if bourse_gain_pct > 0 else ''}{bourse_gain_pct:.2f}%</div>
                        <div style='color: #8E8E93; font-size: 0.85em;'>{'+' if total_gain_bourse > 0 else ''}{total_gain_bourse:,.2f}€</div>
                    </div>
                </div>
                <div style='margin-top: 15px;'>
                    <div class="custom-progress">
                        <div class="custom-progress-fill" style='width: {total_bourse/patrimoine_total*100}%; background: #3b82f6;'></div>
                    </div>
                    <div style='color: #8E8E93; font-size: 0.75em; margin-top: 5px;'>{total_bourse/patrimoine_total*100:.1f}% du patrimoine • {len(bourse_positions)} positions</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Crypto
        crypto_gain_pct = (total_gain_crypto_eur / (total_crypto - total_gain_crypto_eur) * 100) if (total_crypto - total_gain_crypto_eur) > 0 else 0
        crypto_color = "#4ade80" if crypto_gain_pct > 0 else "#f87171"
        st.markdown(f"""
            <div class="section-card">
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='color: #f59e0b; font-weight: 700;'>₿ CRYPTO</div>
                        <div style='font-size: 1.8em; font-weight: 900; color: #fff;'>{total_crypto:,.2f}€</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: {crypto_color}; font-weight: 700;'>{'+' if crypto_gain_pct > 0 else ''}{crypto_gain_pct:.2f}%</div>
                        <div style='color: #8E8E93; font-size: 0.85em;'>{'+' if total_gain_crypto_eur > 0 else ''}{total_gain_crypto_eur:,.2f}€</div>
                    </div>
                </div>
                <div style='margin-top: 15px;'>
                    <div class="custom-progress">
                        <div class="custom-progress-fill" style='width: {total_crypto/patrimoine_total*100}%; background: #f59e0b;'></div>
                    </div>
                    <div style='color: #8E8E93; font-size: 0.75em; margin-top: 5px;'>{total_crypto/patrimoine_total*100:.1f}% du patrimoine • {len(crypto_positions)} positions + staking</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Immobilier & Autres
        st.markdown(f"""
            <div class="section-card">
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='color: #10b981; font-weight: 700;'>🏠 IMMOBILIER</div>
                        <div style='font-size: 1.8em; font-weight: 900; color: #fff;'>{immo_val:,.2f}€</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: #4ade80; font-weight: 700;'>+{((interets_bloque + interets_libre) / (bricks_bloque + bricks_libre) * 100):.2f}%</div>
                        <div style='color: #8E8E93; font-size: 0.85em;'>+{interets_bloque + interets_libre:.2f}€</div>
                    </div>
                </div>
                <div style='margin-top: 10px; display: flex; gap: 10px;'>
                    <div class="mini-card" style='flex:1;'>
                        <div class="mini-title">BRICKS BLOQUÉ</div>
                        <div class="mini-value">{bricks_bloque}€</div>
                    </div>
                    <div class="mini-card" style='flex:1;'>
                        <div class="mini-title">BRICKS LIBRE</div>
                        <div class="mini-value">{bricks_libre}€</div>
                    </div>
                    <div class="mini-card" style='flex:1;'>
                        <div class="mini-title">ROYALTIZ</div>
                        <div class="mini-value">{royaltiz_val}€</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Résumé Revenus Passifs
        st.markdown("#### 💸 Revenus Passifs")
        st.markdown(f"""
            <div class="section-card" style='border: 2px solid #4ade80;'>
                <div style='text-align: center;'>
                    <div style='color: #8E8E93; font-size: 0.85em;'>REVENUS MENSUELS</div>
                    <div style='font-size: 3em; font-weight: 900; color: #4ade80;'>{div_data['actuel']:.2f}€</div>
                    <div style='color: #8E8E93;'>Objectif : {div_data['objectif']}€/mois</div>
                </div>
                <div class="dividend-progress" style='margin: 20px 0;'>
                    <div class="dividend-fill" style='width:{div_data["progress"]}%;'>
                        <span style='color:#fff; font-weight:700; font-size:0.85em;'>{div_data["progress"]:.1f}%</span>
                    </div>
                </div>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center;'>
                    <div>
                        <div style='color: #3b82f6; font-weight: 700;'>{div_data['breakdown']['actions']:.2f}€</div>
                        <div style='color: #8E8E93; font-size: 0.7em;'>Dividendes</div>
                    </div>
                    <div>
                        <div style='color: #f59e0b; font-weight: 700;'>{div_data['breakdown']['staking']:.2f}€</div>
                        <div style='color: #8E8E93; font-size: 0.7em;'>Staking</div>
                    </div>
                    <div>
                        <div style='color: #10b981; font-weight: 700;'>{div_data['breakdown']['immo']:.2f}€</div>
                        <div style='color: #8E8E93; font-size: 0.7em;'>Immobilier</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Résumé Frais
        st.markdown("#### 💰 Aperçu Frais")
        frais_det, frais_an, frais_30, eco = calculate_fees()
        st.markdown(f"""
            <div class="section-card" style='border: 2px solid #f87171;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='color: #f87171; font-weight: 700;'>FRAIS ANNUELS</div>
                        <div style='font-size: 2em; font-weight: 900; color: #f87171;'>{frais_an:,.0f}€</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: #4ade80; font-weight: 700;'>ÉCONOMIE POSSIBLE</div>
                        <div style='font-size: 1.5em; font-weight: 900; color: #4ade80;'>{eco:,.0f}€</div>
                        <div style='color: #8E8E93; font-size: 0.75em;'>sur 30 ans</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Résumé Conseiller IA
        st.markdown("#### 🧠 Alertes IA")
        if analysis['alertes']:
            for alerte in analysis['alertes'][:3]:
                badge_class = f"alert-{alerte['priority']}"
                st.markdown(f"""
                    <div class="section-card" style='padding: 15px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: #fff;'>{alerte['icon']} {alerte['title']}</span>
                            <span class="alert-badge {badge_class}">{alerte['priority'].upper()}</span>
                        </div>
                        <div style='color: #8E8E93; font-size: 0.85em; margin-top: 8px;'>{alerte['detail']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="section-card" style='padding: 15px; border: 1px solid #4ade80;'>
                    <div style='color: #4ade80; text-align: center;'>✅ Aucune alerte majeure</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Row 4: Graphiques d'exposition
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌍 Exposition Géographique")
        geo, _ = calculate_exposure()
        geo_df = pd.DataFrame([{"Pays": k, "Valeur": v, "Pourcentage": v/total_bourse*100} for k, v in geo.items()])
        geo_df = geo_df.sort_values("Valeur", ascending=True)
        
        fig_geo = go.Figure(go.Bar(
            x=geo_df["Valeur"],
            y=geo_df["Pays"],
            orientation='h',
            marker_color='#3b82f6',
            text=[f"{v:.0f}€ ({p:.1f}%)" for v, p in zip(geo_df["Valeur"], geo_df["Pourcentage"])],
            textposition='auto'
        ))
        fig_geo.update_layout(
            height=250,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(17,17,17,1)',
            font=dict(color='#ffffff'),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_geo, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Exposition Sectorielle")
        _, sector = calculate_exposure()
        sector_df = pd.DataFrame([{"Secteur": k, "Valeur": v, "Pourcentage": v/total_bourse*100} for k, v in sector.items()])
        sector_df = sector_df.sort_values("Valeur", ascending=True)
        
        fig_sector = go.Figure(go.Bar(
            x=sector_df["Valeur"],
            y=sector_df["Secteur"],
            orientation='h',
            marker_color='#10b981',
            text=[f"{v:.0f}€ ({p:.1f}%)" for v, p in zip(sector_df["Valeur"], sector_df["Pourcentage"])],
            textposition='auto'
        ))
        fig_sector.update_layout(
            height=250,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(17,17,17,1)',
            font=dict(color='#ffffff'),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_sector, use_container_width=True)
    
    st.markdown("---")
    
    # Row 5: Projection et objectif
    st.markdown("#### 🎯 Progression vers 100 000€")
    progress_100k = min(patrimoine_total / objectif_cible * 100, 100)
    manque_100k = max(objectif_cible - patrimoine_total, 0)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"""
            <div style='background: #1c1c1e; padding: 20px; border-radius: 16px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                    <span style='color: #fff; font-weight: 700;'>{patrimoine_total:,.0f}€</span>
                    <span style='color: #4ade80; font-weight: 700;'>{objectif_cible:,.0f}€</span>
                </div>
                <div class="dividend-progress">
                    <div class="dividend-fill" style='width:{progress_100k}%; background: linear-gradient(90deg, #3b82f6 0%, #4ade80 100%);'>
                        <span style='color:#fff; font-weight:700;'>{progress_100k:.1f}%</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="mini-card" style='text-align: center;'>
                <div class="mini-title">IL MANQUE</div>
                <div style='font-size: 1.5em; font-weight: 900; color: #f87171;'>{manque_100k:,.0f}€</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        mois_restants = int(manque_100k / 500) if manque_100k > 0 else 0
        st.markdown(f"""
            <div class="mini-card" style='text-align: center;'>
                <div class="mini-title">AVEC 500€/MOIS</div>
                <div style='font-size: 1.5em; font-weight: 900; color: #3b82f6;'>{mois_restants // 12} ans {mois_restants % 12} mois</div>
            </div>
        """, unsafe_allow_html=True)

elif view_mode == "📈 Portefeuille":
    st.markdown('<p class="section-title">📂 Portefeuille détaillé</p>', unsafe_allow_html=True)
    tabs = st.tabs(["📈 ACTIONS", "₿ CRYPTO", "✨ AUTRES"])
    
    with tabs[0]:
        st.markdown(f"**Total : {total_bourse:,.2f}€** • Gain : {'+' if total_gain_bourse > 0 else ''}{total_gain_bourse:,.2f}€")
        for p in sorted(bourse_positions, key=lambda x: x['valeur'], reverse=True):
            inv = p['valeur'] / (1 + p['perf']/100)
            gain = p['valeur'] - inv
            icon = "🟢" if gain > 0 else "🔴"
            with st.expander(f"{p['nom']} • {p['valeur']:.2f}€ {icon} {p['perf']:+.2f}%"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Valeur", f"{p['valeur']:.2f}€")
                col2.metric("Quantité", f"{p['qty']:.4f}")
                col3.metric("Gain", f"{gain:+.2f}€")
                col4.metric("Dividende", f"{p['dividend_yield']:.1f}%")
    
    with tabs[1]:
        st.markdown(f"**Total : {total_crypto:,.2f}€** (USD→EUR) • Gain : {'+' if total_gain_crypto_eur > 0 else ''}{total_gain_crypto_eur:,.2f}€")
        st.caption(f"💱 Taux : 1 USD = {TAUX_USD_EUR} EUR")
        
        with st.expander(f"🔒 Staking ETH • {total_staking_eur:.2f}€ 🟢 +{staking_gain_eur:.2f}€"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Valeur EUR", f"{total_staking_eur:.2f}€")
            col2.metric("Valeur USD", f"{staking_usd:.2f}$")
            col3.metric("Gain EUR", f"+{staking_gain_eur:.2f}€")
        
        for c in sorted(crypto_positions, key=lambda x: x['valeur_eur'], reverse=True):
            icon = "🟢" if c['gain_eur'] > 0 else "🔴"
            with st.expander(f"{c['nom']} • {c['valeur_eur']:.2f}€ {icon} {c['perf']:+.2f}%"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Valeur EUR", f"{c['valeur_eur']:.2f}€")
                col2.metric("Valeur USD", f"{c['valeur_usd']:.2f}$")
                col3.metric("Gain EUR", f"{c['gain_eur']:+.2f}€")
    
    with tabs[2]:
        st.markdown(f"🏠 **Bricks** : {immo_val:.2f}€")
        col1, col2 = st.columns(2)
        col1.metric("Bloqué (8.5%)", f"{bricks_bloque}€", f"+{interets_bloque:.2f}€")
        col2.metric("Libre (4%)", f"{bricks_libre}€", f"+{interets_libre:.2f}€")
        st.markdown(f"👑 **Royaltiz** : {royaltiz_val}€")

elif view_mode == "🎯 Simulation":
    st.markdown('<p class="section-title">🎯 Simulateur de projection</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        apport = st.number_input("Apport mensuel", value=500, step=100)
        rend = st.slider("Rendement annuel (%)", 0, 20, 8)
    with col2:
        duree = st.slider("Durée (années)", 1, 30, 10)
        capital = st.number_input("Capital initial", value=int(patrimoine_total), step=1000)
    
    mois = duree * 12
    taux = (1 + rend/100) ** (1/12) - 1
    proj = [capital]
    for _ in range(mois):
        proj.append(proj[-1] * (1 + taux) + apport)
    
    dates = pd.date_range(start=datetime.now(), periods=mois+1, freq='ME')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=proj, mode='lines', fill='tozeroy', 
                             line=dict(color='#4ade80', width=3), name="Projection"))
    fig.add_hline(y=100000, line_dash="dash", line_color="#f59e0b", annotation_text="Objectif 100k€")
    fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,17,17,1)',
                     font=dict(color='#ffffff'), xaxis_title="Date", yaxis_title="Valeur (€)")
    st.plotly_chart(fig, use_container_width=True)
    
    final = proj[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Valeur finale", f"{final:,.0f}€")
    col2.metric("Total investi", f"{capital + apport * mois:,.0f}€")
    col3.metric("Gains générés", f"{final - capital - apport * mois:,.0f}€")

elif view_mode == "📰 Actualités":
    st.markdown('<p class="section-title">📰 Actualités Marchés</p>', unsafe_allow_html=True)
    
    news_list = get_news()
    st.info(f"📡 {len(news_list)} actualités • MAJ : {datetime.now().strftime('%H:%M')}")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_impact = st.selectbox("Impact", ["Tous", "positif", "négatif", "neutre"])
    with col2:
        filter_source = st.selectbox("Source", ["Toutes"] + list(set(n['source'] for n in news_list)))
    
    filtered = news_list
    if filter_impact != "Tous":
        filtered = [n for n in filtered if n['impact'] == filter_impact]
    if filter_source != "Toutes":
        filtered = [n for n in filtered if n['source'] == filter_source]
    
    for n in filtered:
        impact_color = {"positif": "#4ade80", "négatif": "#f87171", "neutre": "#fbbf24"}.get(n['impact'], "#8E8E93")
        with st.expander(f"{n['titre']}"):
            st.markdown(f"""
                <div class="news-summary">
                    <p style='color:{impact_color}; font-weight:700;'>🤖 Résumé</p>
                    <p style='color:#e0e0e0;'>{n['summary']}</p>
                    <div class="news-keypoints">📌 {' • '.join(n['keypoints'])}</div>
                    <p style='color:#8E8E93; font-size:0.75em; margin-top:10px;'>{n['source']} • {n['time']}</p>
                </div>
            """, unsafe_allow_html=True)

elif view_mode == "🧠 Conseiller IA":
    st.markdown('<p class="section-title">🧠 Conseiller IA Personnel</p>', unsafe_allow_html=True)
    
    budget = st.number_input("💰 Budget mensuel", value=500, step=50)
    profil = st.select_slider("📊 Profil de risque", ["Conservateur", "Modéré", "Dynamique", "Agressif"], value="Modéré")
    
    analysis = generate_ai_analysis(patrimoine_total, total_bourse, total_crypto, budget)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#4ade80" if analysis['score_global'] >= 70 else "#fbbf24" if analysis['score_global'] >= 50 else "#f87171"
        st.markdown(f"""
            <div class="dash-card" style='text-align:center; border:2px solid {color};'>
                <div style='color:#8E8E93;'>SCORE SANTÉ</div>
                <div style='font-size:3em; font-weight:900; color:{color};'>{analysis['score_global']}/100</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="dash-card" style='text-align:center;'>
                <div style='color:#8E8E93;'>DIVERSIFICATION</div>
                <div style='font-size:3em; font-weight:900; color:#3b82f6;'>{analysis['score_diversification']}/100</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        r_color = "#4ade80" if analysis['score_risque'] <= 40 else "#fbbf24" if analysis['score_risque'] <= 60 else "#f87171"
        st.markdown(f"""
            <div class="dash-card" style='text-align:center;'>
                <div style='color:#8E8E93;'>RISQUE</div>
                <div style='font-size:3em; font-weight:900; color:{r_color};'>{analysis['score_risque']}/100</div>
            </div>
        """, unsafe_allow_html=True)
    
    if analysis['alertes']:
        st.markdown("### 🚨 Alertes")
        for a in analysis['alertes']:
            st.markdown(f"""
                <div class="ai-recommendation priority-{a['priority']}">
                    <h4 style='color:#f87171;'>{a['icon']} {a['title']}</h4>
                    <p style='color:#e0e0e0;'>{a['detail']}</p>
                    <p style='color:#4ade80;'>💡 {a['action']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Recommandations")
    for r in analysis['recommendations']:
        with st.expander(f"{r['icon']} {r['title']}", expanded=True):
            st.markdown(f"**{r['detail']}**")
            if 'allocation' in r:
                for k, v in r['allocation'].items():
                    st.markdown(f"- {k} : **{v}**")
            st.success(f"📈 {r['impact']}")

elif view_mode == "💰 Scanner Frais":
    st.markdown('<p class="section-title">💰 Scanner de Frais</p>', unsafe_allow_html=True)
    frais_det, frais_an, frais_30, eco = calculate_fees()
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"""
            <div class="fee-hero">
                <div style='color:#f87171; font-size:0.9em; letter-spacing:2px;'>COÛT TOTAL SUR 30 ANS</div>
                <div class="fee-amount">{frais_30:,.0f}€</div>
                <p style='color:#fff;'>Soit {frais_an:,.0f}€/an</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="economy-card">
                <div style='color:#4ade80;'>💡 ÉCONOMIE POSSIBLE</div>
                <div style='font-size:3em; font-weight:900; color:#4ade80;'>{eco:,.0f}€</div>
                <p style='color:#e0e0e0;'>Avec ETF bas coût</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Détail des frais")
    col1, col2 = st.columns(2)
    for idx, (nom, data) in enumerate(frais_det.items()):
        with col1 if idx % 2 == 0 else col2:
            st.markdown(f"""
                <div class="fee-detail-card">
                    <div style='display:flex; align-items:center; gap:15px;'>
                        <div style='font-size:2em;'>{data['icon']}</div>
                        <div>
                            <h4 style='color:#fff; margin:0;'>{nom}</h4>
                            <p style='color:#8E8E93; font-size:0.85em;'>{data['desc']}</p>
                        </div>
                    </div>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-top:20px;'>
                        <div class="fee-value">{data['value']:,.2f}€</div>
                        <div style='background:#3a1e1e; padding:8px 16px; border-radius:10px;'>
                            <span style='color:#f87171; font-weight:700;'>{data['rate']}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

elif view_mode == "💸 Revenus Passifs":
    st.markdown('<p class="section-title">💸 Objectif 500€/mois</p>', unsafe_allow_html=True)
    div_data = calculate_dividends()
    
    st.markdown(f"""
        <div class="dividend-goal">
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='color:#4ade80; margin:0;'>🎯 Progression</h2>
                <span style='background:#1e3a1e; padding:8px 16px; border-radius:12px; color:#4ade80; font-weight:700;'>{div_data['progress']:.1f}%</span>
            </div>
            <div style='font-size:4em; font-weight:900; color:#fff; margin:20px 0;'>{div_data['actuel']:.2f}€ <span style='font-size:0.4em; color:#8E8E93;'>/ {div_data['objectif']}€</span></div>
            <div class="dividend-progress">
                <div class="dividend-fill" style='width:{div_data["progress"]}%;'>{div_data["progress"]:.1f}%</div>
            </div>
            <p style='color:#f87171; margin-top:15px;'>❌ Il manque {div_data['manque']:.2f}€/mois</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="income-source" style='border:2px solid #3b82f6;'><div style='font-size:2em;'>📈</div><div class="income-amount">{div_data['breakdown']['actions']:.2f}€</div><div style='color:#8E8E93;'>Dividendes</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="income-source" style='border:2px solid #f59e0b;'><div style='font-size:2em;'>⛓️</div><div class="income-amount">{div_data['breakdown']['staking']:.2f}€</div><div style='color:#8E8E93;'>Staking</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="income-source" style='border:2px solid #10b981;'><div style='font-size:2em;'>🏠</div><div class="income-amount">{div_data['breakdown']['immo']:.2f}€</div><div style='color:#8E8E93;'>Immobilier</div></div>""", unsafe_allow_html=True)
    
    st.markdown("### 💡 Stratégies recommandées")
    tips = generate_passive_income_tips(div_data)
    
    filter_diff = st.selectbox("Difficulté", ["Toutes", "Facile", "Moyen", "Difficile"])
    diff_map = {"Facile": "easy", "Moyen": "medium", "Difficile": "hard"}
    if filter_diff != "Toutes":
        tips = [t for t in tips if t['difficulty'] == diff_map[filter_diff]]
    
    for tip in tips:
        diff_label = {"easy": "Facile", "medium": "Moyen", "hard": "Difficile"}[tip['difficulty']]
        with st.expander(f"{tip['icon']} {tip['title']}"):
            st.markdown(f"<span class='tip-difficulty difficulty-{tip['difficulty']}'>{diff_label}</span>", unsafe_allow_html=True)
            st.markdown(f"**{tip['description']}**")
            st.success(f"🎯 {tip['action']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Avantages**")
                for a in tip['avantages']:
                    st.markdown(f"- {a}")
            with col2:
                st.markdown("**⚠️ Risques**")
                for r in tip['risques']:
                    st.markdown(f"- {r}")
            st.info(" • ".join(tip['exemples']))

# ============== FOOTER ==============

st.markdown("---")
st.markdown(f"""
    <div style='text-align:center; color:#8E8E93; font-size:0.8em; padding:20px;'>
        <p>💎 Horizon Finance Pro • Taux USD/EUR : {TAUX_USD_EUR} • MAJ : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>⚠️ Les informations fournies ne constituent pas un conseil en investissement</p>
    </div>
""", unsafe_allow_html=True)