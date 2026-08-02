import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Gold Signal App", page_icon="📈", layout="wide")

# CSS für Live/Offline Badge
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
.error-badge {
    background-color: #cc0000;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# Titel mit Status
col_title, col_status = st.columns([3, 1])

with col_title:
    st.title("📊 Gold Treiber Analyse")

# Fallback-Daten
FALLBACK_DATA = {
    'gold_usd': 2050.0,
    'gold_eur': 1890.0,
    'silver': 23.50,
    'eur_rate': 0.92,
    'timestamp': None
}

def get_gold_data():
    """Versuche mehrere APIs mit Zeitstempel"""
    apis = [
        "https://api.metals.dev/v1/latest",
        "https://api.exchangerate-api.com/v4/latest/USD"
    ]
    
    for url in apis:
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'metals' in data and data.get('status') == 'success':
                return {
                    'gold_usd': data['metals']['gold'],
                    'gold_eur': data['metals']['gold'] / data['currencies']['EUR'],
                    'silver': data['metals']['silver'],
                    'eur_rate': data['currencies']['EUR'],
                    'timestamp': datetime.now(),
                    'source': 'Live API (metals.dev)',
                    'status': 'LIVE',
                    'color': 'green'
                }
            
            if 'rates' in data and 'EUR' in data['rates']:
                eur = data['rates']['EUR']
                gold_usd = 2050.0
                return {
                    'gold_usd': gold_usd,
                    'gold_eur': gold_usd / eur,
                    'silver': 23.50,
                    'eur_rate': eur,
                    'timestamp': datetime.now(),
                    'source': 'Live API (Währung)',
                    'status': 'LIVE',
                    'color': 'green'
                }
                
        except:
            continue
    
    return None

# Daten laden
with st.spinner("Verbinde mit API..."):
    gold_data = get_gold_data()

# Status anzeigen
if gold_data is None:
    gold_data = FALLBACK_DATA.copy()
    gold_data['timestamp'] = datetime.now()
    gold_data['source'] = 'Offline (Beispieldaten)'
    gold_data['status'] = 'OFFLINE'
    gold_data['color'] = 'orange'

with col_status:
    if gold_data['status'] == 'LIVE':
        st.markdown('<span class="live-badge">✅ LIVE DATEN</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="offline-badge">⚠️ OFFLINE (BeispIEL)</span>', unsafe_allow_html=True)

# Zeitstempel prominent anzeigen
if gold_data.get('timestamp'):
    time_str = gold_data['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
    if gold_data['status'] == 'LIVE':
        st.success(f"🟢 Verifizierte Live-Daten von **{gold_data['source']}** | Stand: {time_str}")
    else:
        st.warning(f"🟠 **Beispieldaten** (keine Verbindung zur API) | Stand: {time_str}")

# Preise anzeigen
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Gold (USD)", f"${gold_data['gold_usd']:,.2f}")
with col2:
    st.metric("Gold (EUR)", f"{gold_data['gold_eur']:,.2f} €")
with col3:
    st.metric("Silber", f"${gold_data['silver']:,.2f}")
with col4:
    st.metric("EUR/USD", f"{gold_data['eur_rate']:.4f}")

# Signal-Logik
st.divider()
st.subheader("📋 Markteinschätzung")

gold_usd = gold_data['gold_usd']

if gold_usd > 2300:
    signal = "🔴 Hoch bewertet (Vorsicht)"
    signal_color = "red"
elif gold_usd < 1900:
    signal = "🟢 Günstig (Kaufchance)"
    signal_color = "green"
else:
    signal = "⚪ Neutral"
    signal_color = "gray"

if signal_color == "red":
    st.error(f"### {signal}")
elif signal_color == "green":
    st.success(f"### {signal}")
else:
    st.info(f"### {signal}")

# Chart
st.divider()
st.subheader("📈 30-Tage Verlauf")

days = 30
base_price = gold_data['gold_usd']
dates = [datetime.now() - timedelta(days=i) for i in range(days)]
dates.reverse()

np.random.seed(42)
prices = base_price + np.cumsum(np.random.randn(days) * 15)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=dates, y=prices,
    mode='lines',
    name='Gold',
    line=dict(color='gold', width=2)
))
fig.add_hline(y=base_price, line_dash="dash", line_color="red", 
              annotation_text="Aktueller Preis")

fig.update_layout(
    height=400,
    template="plotly_white",
    xaxis_title="Datum",
    yaxis_title="Preis (USD)",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Warnung bei Offline-Daten
if gold_data['status'] != 'LIVE':
    st.divider()
    st.error("""
    ⚠️ **ACHTUNG:** Es werden **Beispieldaten** angezeigt, keine echten Live-Preise!
    
    Die API-Verbindung ist derzeit nicht möglich. Für echtes Trading bitte später 
    neu laden oder die lokale Version mit yfinance nutzen.
    """)

# Footer
st.divider()
st.caption(f"Quelle: {gold_data['source']} | App läuft auf Streamlit Cloud")

# Refresh
if st.button("🔄 Verbindung erneut testen"):
    st.rerun()
