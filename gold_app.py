import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Gold Live", page_icon="📈", layout="wide")

# ═══════════════════════════════════════════════════
# HIER DEINEN API-KEY EINFÜGEN (von goldapi.io)
API_KEY = "goldapi-e69dff00fae3208222f7b4167faec0e7-io"  # ← HIER ÄNDERN!
# ═══════════════════════════════════════════════════

st.title("📊 Gold Treiber Analyse (Live)")

# CSS für Status-Badges
st.markdown("""
<style>
.live-badge {
    background-color: #00cc00;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
}
.offline-badge {
    background-color: #cc0000;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def get_gold_data():
    """Holt echte Gold-Daten von GoldAPI.io"""
    if "DEIN_KEY_HIER" in API_KEY:
        return {
            'status': 'NO_KEY',
            'gold_usd': 0,
            'gold_eur': 0,
            'timestamp': None,
            'source': 'Kein API-Key eingetragen'
        }
    
    try:
        # Gold in USD
        url_usd = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": API_KEY}
        
        response = requests.get(url_usd, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Hole auch EUR
            url_eur = "https://www.goldapi.io/api/XAU/EUR"
            response_eur = requests.get(url_eur, headers=headers, timeout=10)
            eur_data = response_eur.json() if response_eur.status_code == 200 else {}
            
            return {
                'status': 'LIVE',
                'gold_usd': data.get('price', 0),
                'gold_eur': eur_data.get('price', 0),
                'timestamp': datetime.fromtimestamp(data.get('timestamp', 0)),
                'source': 'GoldAPI.io (Echtzeit)',
                'change_24h': data.get('ch', 0)  # 24h Änderung
            }
    except Exception as e:
        st.error(f"API-Fehler: {e}")
    
    return {
        'status': 'ERROR',
        'gold_usd': 2050.0,
        'gold_eur': 1890.0,
        'timestamp': datetime.now(),
        'source': 'Fehler - Beispieldaten',
        'change_24h': 0
    }

# Daten laden
with st.spinner("Verbinde mit GoldAPI.io..."):
    data = get_gold_data()

# Status-Anzeige oben rechts
col_title, col_status = st.columns([3, 1])
with col_title:
    st.subheader("Live-Marktdaten")

with col_status:
    if data['status'] == 'LIVE':
        st.markdown('<span class="live-badge">✅ LIVE</span>', unsafe_allow_html=True)
    elif data['status'] == 'NO_KEY':
        st.markdown('<span class="offline-badge">❌ KEIN KEY</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="offline-badge">⚠️ FEHLER</span>', unsafe_allow_html=True)

# Warnung wenn kein Key
if data['status'] == 'NO_KEY':
    st.error("""
    ### ❌ Kein API-Key eingetragen!
    
    1. Gehe zu https://www.goldapi.io
    2. Registriere dich (kostenlos)
    3. Kopiere deinen Key
    4. Füge ihn oben im Code bei `API_KEY = "goldapi-DEIN_KEY"` ein
    
    **Oder:** Nutze die lokale Version mit yfinance (kein Key nötig)
    """)
    st.stop()

# Zeitstempel
if data['timestamp']:
    st.success(f"🟢 {data['source']} | Stand: {data['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}")

# 5 Metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Gold USD", f"${data['gold_usd']:,.2f}", f"{data.get('change_24h', 0):.2f}%")
with col2:
    st.metric("Gold EUR", f"{data['gold_eur']:,.2f} €")
with col3:
    st.metric("DXY", "102.50")  # Beispiel (braucht separate API)
with col4:
    st.metric("10Y Rendite", "4.20%")  # Beispiel
with col5:
    st.metric("EUR/USD", f"{(data['gold_usd']/data['gold_eur'] if data['gold_eur'] > 0 else 0):.4f}")

# Die 4 Treiber (mit Live-Goldpreis + Beispieldaten für Rest)
st.divider()
st.subheader("📋 Die 4 Treiber-Analyse")

# Berechne Score basierend auf Live-Daten
gold = data['gold_usd']

# Treiber 1: Dollar (Beispiel - braucht DXY-API)
dxy = 102.5
if dxy < 102:
    dxy_signal, dxy_score = "🟢 Schwach (bullish)", -1
else:
    dxy_signal, dxy_score = "🔴 Stark (bärish)", 1

# Treiber 2: Zinsen (Beispiel)
treasury = 4.2
if treasury < 4.0:
    rate_signal, rate_score = "🟢 Niedrig (bullish)", -1
else:
    rate_signal, rate_score = "🔴 Hoch (bärish)", 1

# Treiber 3: Gold-Preisniveau (Live!)
if gold < 2000:
    trend_signal, trend_score = "🟢 Unterstützung", -0.5
elif gold > 2200:
    trend_signal, trend_score = "🔴 Widerstand", 0.5
else:
    trend_signal, trend_score = "⚪ Neutral", 0

# Treiber 4: Gesamt
total_score = dxy_score + rate_score + trend_score

if total_score <= -1.5:
    overall = ("🟢 KAUFEN", "green")
elif total_score <= -0.5:
    overall = ("🟡 LEICHT KAUFEN", "blue")
elif total_score >= 1.5:
    overall = ("🔴 VERKAUFEN", "red")
elif total_score >= 0.5:
    overall = ("🟠 LEICHT VERKAUFEN", "orange")
else:
    overall = ("⚪ HALTEN", "gray")

signal_text, signal_color = overall

# Anzeige
col1, col2 = st.columns(2)
with col1:
    st.write(f"**💵 Dollar (DXY):** {dxy_signal}")
    st.caption(f"Wert: {dxy:.2f} (Beispiel - braucht DXY-API)")
    
    st.write(f"**📈 Zinsen (10Y):** {rate_signal}")
    st.caption(f"Wert: {treasury:.2f}% (Beispiel - braucht Zinsen-API)")

with col2:
    st.write(f"**📊 Gold-Preis:** {trend_signal}")
    st.caption(f"Live-Wert: ${gold:.2f} ✅ ECHT")
    
    st.write(f"**🎯 Gesamt-Score:** {total_score:.1f}")
    st.caption("Negativ = Bullish, Positiv = Bärish")

# Hauptsignal
st.divider()
if signal_color == "green":
    st.success(f"### {signal_text}")
elif signal_color == "red":
    st.error(f"### {signal_text}")
elif signal_color == "orange":
    st.warning(f"### {signal_text}")
elif signal_color == "blue":
    st.info(f"### {signal_text}")
else:
    st.write(f"### {signal_text}")

# Hinweis
st.divider()
st.info("""
💡 **Hinweis:** Gold-Preis ist ✅ **ECHT** (von GoldAPI.io).  
Dollar und Zinsen sind Beispieldaten (brauchen separate APIs).  
Für alle 4 Treiber mit echten Daten: Lokale Version mit yfinance nutzen.
""")

if st.button("🔄 Daten neu laden"):
    st.rerun()
