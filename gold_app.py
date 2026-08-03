import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Gold Signal App", page_icon="📈", layout="wide")

# CSS für Badges
st.markdown("""
<style>
.live-badge {
    background-color: #00cc00;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
    font-size: 14px;
}
.offline-badge {
    background-color: #ff6600;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# Fallback mit Beispieldaten
FALLBACK_DATA = {
    'gold_usd': 2050.0,
    'gold_eur': 1890.0,
    'silver': 23.50,
    'eur_rate': 0.92,
    'dxy': 102.5,  # Beispiel DXY
    'treasury': 4.2,  # Beispiel 10Y
    'timestamp': None
}

def get_data():
    """Versuche APIs, sonst Fallback"""
    result = FALLBACK_DATA.copy()
    result['status'] = 'OFFLINE'
    result['source'] = 'Beispieldaten (API nicht erreichbar)'
    
    # Versuche Gold API
    try:
        response = requests.get("https://api.metals.dev/v1/latest", timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            result['gold_usd'] = data['metals']['gold']
            result['gold_eur'] = data['metals']['gold'] / data['currencies']['EUR']
            result['silver'] = data['metals']['silver']
            result['eur_rate'] = data['currencies']['EUR']
            result['status'] = 'LIVE'
            result['source'] = 'Live API'
    except:
        pass
    
    # Versuche DXY Proxy
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        data = response.json()
        eur = data['rates']['EUR']
        result['eur_rate'] = eur
        result['dxy'] = 100 - (eur * 100) + 50  # Proxy-Berechnung
    except:
        pass
    
    result['timestamp'] = datetime.now()
    return result

# Daten laden
with st.spinner("Lade Daten..."):
    data = get_data()

# Header mit Status
col_title, col_status = st.columns([3, 1])

with col_title:
    st.title("📊 Gold Treiber Analyse")

with col_status:
    if data['status'] == 'LIVE':
        st.markdown('<span class="live-badge">✅ LIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="offline-badge">⚠️ OFFLINE</span>', unsafe_allow_html=True)

# Status-Info
if data['status'] == 'LIVE':
    st.success(f"🟢 Echte Live-Daten | Stand: {data['timestamp'].strftime('%H:%M:%S')}")
else:
    st.warning(f"🟠 **ACHTUNG:** Beispieldaten werden angezeigt (keine Verbindung zur API)")

# Preise
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Gold (USD)", f"${data['gold_usd']:,.2f}")
with col2:
    st.metric("Gold (EUR)", f"{data['gold_eur']:,.2f} €")
with col3:
    st.metric("Silber", f"${data['silver']:,.2f}")
with col4:
    st.metric("EUR/USD", f"{data['eur_rate']:.4f}")

# Treiber-Analyse (die 4 Kriterien!)
st.divider()
st.subheader("📋 Die 4 Treiber-Analyse")

# 1. Dollar (DXY)
dxy = data['dxy']
if dxy < 102:
    dxy_signal = "🟢 Schwach (bullish für Gold)"
    dxy_score = -1
    dxy_color = "green"
elif dxy > 104:
    dxy_signal = "🔴 Stark (bärish für Gold)"
    dxy_score = 1
    dxy_color = "red"
else:
    dxy_signal = "⚪ Neutral"
    dxy_score = 0
    dxy_color = "gray"

# 2. Zinsen (Treasury)
treasury = data['treasury']
if treasury < 3.5:
    rate_signal = "🟢 Niedrig (bullish für Gold)"
    rate_score = -1
    rate_color = "green"
elif treasury > 4.5:
    rate_signal = "🔴 Hoch (bärish für Gold)"
    rate_score = 1
    rate_color = "red"
else:
    rate_signal = "⚪ Moderat"
    rate_score = 0
    rate_color = "gray"

# 3. Trend (basierend auf Preisniveau)
gold = data['gold_usd']
if gold < 2000:
    trend_signal = "🟢 Unterstützungsniveau"
    trend_score = -0.5
    trend_color = "green"
elif gold > 2200:
    trend_signal = "🔴 Widerstandsniveau"
    trend_score = 0.5
    trend_color = "red"
else:
    trend_signal = "⚪ Mittlerer Bereich"
    trend_score = 0
    trend_color = "gray"

# 4. Gesamt-Score
total_score = dxy_score + rate_score + trend_score

if total_score <= -1.5:
    overall = ("🟢 KAUFEN", "Mehrere bullish Signale", "green")
elif total_score <= -0.5:
    overall = ("🟡 LEICHT KAUFEN", "Tendenz bullish", "lightgreen")
elif total_score >= 1.5:
    overall = ("🔴 VERKAUFEN", "Mehrere bärish Signale", "red")
elif total_score >= 0.5:
    overall = ("🟠 LEICHT VERKAUFEN", "Tendenz bärish", "orange")
else:
    overall = ("⚪ HALTEN", "Keine klare Richtung", "gray")

signal_text, signal_desc, signal_color = overall

# Anzeige der 4 Treiber
col1, col2 = st.columns(2)

with col1:
    st.write(f"**💵 Dollar (DXY {dxy:.1f}):**")
    if dxy_color == "green":
        st.success(dxy_signal)
    elif dxy_color == "red":
        st.error(dxy_signal)
    else:
        st.info(dxy_signal)
    
    st.write(f"**📈 Zinsen (10Y {treasury:.1f}%):**")
    if rate_color == "green":
        st.success(rate_signal)
    elif rate_color == "red":
        st.error(rate_signal)
    else:
        st.info(rate_signal)

with col2:
    st.write(f"**📊 Preisniveau (${gold:.0f}):**")
    if trend_color == "green":
        st.success(trend_signal)
    elif trend_color == "red":
        st.error(trend_signal)
    else:
        st.info(trend_signal)
    
    st.write(f"**🎯 Gesamtsignal (Score: {total_score:.1f}):**")
    if signal_color == "green":
        st.success(f"{signal_text} - {signal_desc}")
    elif signal_color == "red":
        st.error(f"{signal_text} - {signal_desc}")
    elif signal_color == "orange":
        st.warning(f"{signal_text} - {signal_desc}")
    else:
        st.info(f"{signal_text} - {signal_desc}")

# Gesamtes Signal groß
st.divider()
if signal_color == "green":
    st.success(f"### {signal_text}")
elif signal_color == "red":
    st.error(f"### {signal_text}")
elif signal_color == "orange":
    st.warning(f"### {signal_text}")
else:
    st.info(f"### {signal_text}")

# Chart
st.divider()
st.subheader("📈 30-Tage Verlauf (Beispiel)")

days = 30
dates = [datetime.now() - timedelta(days=i) for i in range(days)]
dates.reverse()
np.random.seed(42)
prices = gold + np.cumsum(np.random.randn(days) * 15)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=dates, y=prices,
    mode='lines',
    name='Gold',
    line=dict(color='gold', width=2)
))
fig.add_hline(y=gold, line_dash="dash", line_color="red", annotation_text="Aktuell")
fig.update_layout(height=400, template="plotly_white", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Warnung
if data['status'] != 'LIVE':
    st.divider()
    st.error("""
    ⚠️ **WICHTIG:** Es werden **BEISPIELDATEN** angezeigt!
    
    Die APIs sind derzeit nicht erreichbar. Für echtes Trading nutze die 
    lokale Version mit yfinance auf deinem PC.
    """)

st.caption(f"Quelle: {data['source']} | {data['timestamp'].strftime('%d.%m.%Y %H:%M') if data['timestamp'] else 'Unbekannt'}")

if st.button("🔄 Neu laden"):
    st.rerun()
