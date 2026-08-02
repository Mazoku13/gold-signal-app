import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Gold Signal App", page_icon="📈", layout="wide")
st.title("📊 Gold Treiber Analyse")

# Kostenlose API für Gold-Preise (kein Key nötig)
def get_gold_data():
    try:
        # Gold-Preis in USD und EUR
        url = "https://api.metals.dev/v1/latest"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'gold_usd': data['metals']['gold'],
                'gold_eur': data['metals']['gold'] / data['currencies']['EUR'],
                'silver': data['metals']['silver'],
                'timestamp': data['timestamp']
            }
    except Exception as e:
        st.error(f"API-Fehler: {e}")
    return None

def get_dxy_data():
    """Ersatz für DXY über EUR/USD"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        eur = data['rates']['EUR']
        # DXY-Proxy: 100 - (EUR/USD * 100) + 50 (Näherung)
        dxy_proxy = 100 - (eur * 100) + 50
        return dxy_proxy, eur
    except:
        return 102.0, 0.92  # Fallback-Werte

# Daten laden
with st.spinner("Lade aktuelle Preise..."):
    gold_data = get_gold_data()
    dxy, eur_rate = get_dxy_data()

if gold_data:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gold (USD)", f"${gold_data['gold_usd']:,.2f}")
    with col2:
        st.metric("Gold (EUR)", f"{gold_data['gold_eur']:,.2f} €")
    with col3:
        st.metric("Silber", f"${gold_data['silver']:,.2f}")
    with col4:
        st.metric("EUR/USD", f"{eur_rate:.4f}")
    
    # Einfache Analyse
    st.divider()
    st.subheader("📋 Markteinschätzung")
    
    # Dummy-Analyse basierend auf Preisniveau
    gold_usd = gold_data['gold_usd']
    
    if gold_usd > 2300:
        signal = "🔴 Hoch bewertet (Vorsicht)"
        color = "red"
    elif gold_usd < 1900:
        signal = "🟢 Günstig (Kaufchance)"
        color = "green"
    else:
        signal = "⚪ Neutral"
        color = "gray"
    
    if color == "red":
        st.error(f"### {signal}")
    elif color == "green":
        st.success(f"### {signal}")
    else:
        st.info(f"### {signal}")
    
    # Einfacher Chart (simulierte 30-Tage Historie als Beispiel)
    st.divider()
    st.subheader("📈 Beispiel-Chart (30 Tage)")
    st.caption("Hinweis: Dies ist eine Demo-Version mit Beispieldaten.")
    
    # Simulierte Daten für Visualisierung
    days = 30
    base_price = gold_data['gold_usd']
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    dates.reverse()
    
    # Zufällige, aber realistische Schwankungen
    np.random.seed(42)
    prices = base_price + np.cumsum(np.random.randn(days) * 10)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        mode='lines',
        name='Gold (Beispieldaten)',
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
    
    # Info
    st.divider()
    st.info("""
    **Hinweis:** Dies ist eine vereinfachte Demo-Version, die auf Streamlit Cloud läuft. 
    Für echte historische Charts und komplexe Analysen nutze die lokale Version mit yfinance.
    """)
    
    st.caption(f"🔄 Aktualisiert: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

else:
    st.error("Konnte keine Daten laden. Bitte später erneut versuchen.")
