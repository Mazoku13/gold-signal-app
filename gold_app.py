import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Gold Live", page_icon="📈", layout="wide")

# ═══════════════════════════════════════════════════
# HIER DEINEN GOLDAPI-KEY EINFÜGEN
API_KEY = "goldapi-e69dff00fae3208222f7b4167faec0e7-io"  # ← HIER ÄNDERN!
# ═══════════════════════════════════════════════════

st.title("📊 Gold Treiber Analyse (Live)")

# CSS für Badges
st.markdown("""
<style>
.live-badge {
    background-color: #00cc00;
    color: white;
    padding: 5px 15px;
    border-radius: 15px;
    font-weight: bold;
}
.warning-badge {
    background-color: #ff9900;
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

def get_data():
    """Holt Gold-Daten und berechnet Schätzungen"""
    
    # Prüfe ob Key eingetragen
    if "DEIN_KEY" in API_KEY or API_KEY == "":
        return {
            'status': 'NO_KEY',
            'gold_usd': 0, 'gold_eur': 0,
            'dxy': 102.5, 'treasury': 4.2, 'eur_rate': 0.92,
            'timestamp': None,
            'source': 'Kein API-Key'
        }
    
    result = {'status': 'LIVE', 'timestamp': datetime.now()}
    
    # 1. ECHTES GOLD von GoldAPI
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": API_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result['gold_usd'] = data.get('price', 2050)
            
            # EUR
            url_eur = "https://www.goldapi.io/api/XAU/EUR"
            response_eur = requests.get(url_eur, headers=headers, timeout=10)
            if response_eur.status_code == 200:
                result['gold_eur'] = response_eur.json().get('price', 1890)
            else:
                result['gold_eur'] = result['gold_usd'] / 0.92
                
            result['source'] = 'GoldAPI.io (Live)'
        else:
            raise Exception("API Fehler")
    except:
        result['status'] = 'ERROR'
        result['gold_usd'] = 2050
        result['gold_eur'] = 1890
        result['source'] = 'Fehler - Beispieldaten'
    
    # 2. DXY-Schätzung aus EUR/USD (einfache API)
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        eur = data['rates']['EUR']
        result['eur_rate'] = eur
        # DXY-Proxy: Annäherung
        result['dxy'] = 100 - ((eur - 0.92) * 50)
    except:
        result['eur_rate'] = 0.92
        result['dxy'] = 102.5
    
    # 3. Zinsen-Schätzung (aktueller Marktdurchschnitt)
    # In Realität 4.0-4.5%, wir nehmen 4.2%
    result['treasury'] = 4.2
    
    return result

# Daten laden
with st.spinner("Lade Daten..."):
    data = get_data()

# Header mit Status
col_title, col_status = st.columns([3, 1])
with col_title:
    st.subheader("Live-Marktdaten")

with col_status:
    if data['status'] == 'LIVE':
        st.markdown('<span class="live-badge">✅ LIVE</span>', unsafe_allow_html=True)
    elif data['status'] == 'NO_KEY':
        st.markdown('<span class="offline-badge">❌ KEIN KEY</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="warning-badge">⚠️ FEHLER</span>', unsafe_allow_html=True)

# Fehlerbehandlung
if data['status'] == 'NO_KEY':
    st.error("""
    ### ❌ Kein API-Key eingetragen!
    
    1. Gehe zu https://www.goldapi.io
    2. Registriere dich (kostenlos)
    3. Kopiere deinen Key
    4. Trage ihn oben im Code ein bei `API_KEY = "goldapi-..."`
    """)
    st.stop()

# Status-Anzeige
if data['status'] == 'LIVE':
    st.success(f"🟢 {data['source']} | {data['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}")
else:
    st.warning(f"🟠 Gold-API nicht erreichbar - Zeige Beispieldaten")

# 5 Metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    change = 0  # Könnte aus API kommen
    st.metric("Gold USD", f"${data['gold_usd']:,.2f}", f"{change:.2f}%")
with col2:
    st.metric("Gold EUR", f"{data['gold_eur']:,.2f} €")
with col3:
    st.metric("DXY", f"{data['dxy']:.2f}")
with col4:
    st.metric("10Y Rendite", f"{data['treasury']:.2f}%")
with col5:
    st.metric("EUR/USD", f"{data['eur_rate']:.4f}")

# ═══════════════════════════════════════════════════
# DIE 4 TREIBER
# ═══════════════════════════════════════════════════

st.divider()
st.subheader("📋 Die 4 Treiber-Analyse")

# Werte extrahieren
gold = data['gold_usd']
dxy = data['dxy']
treasury = data['treasury']

# Treiber 1: Dollar (DXY)
if dxy < 102:
    dxy_signal, dxy_score = "🟢 Schwach (bullish für Gold)", -1
elif dxy > 104:
    dxy_signal, dxy_score = "🔴 Stark (bärish für Gold)", 1
else:
    dxy_signal, dxy_score = "⚪ Neutral", 0

# Treiber 2: Zinsen (10Y)
if treasury < 4.0:
    rate_signal, rate_score = "🟢 Niedrig (bullish für Gold)", -1
elif treasury > 4.5:
    rate_signal, rate_score = "🔴 Hoch (bärish für Gold)", 1
else:
    rate_signal, rate_score = "⚪ Moderat", 0

# Treiber 3: Gold-Preisniveau (Live!)
if gold < 2000:
    trend_signal, trend_score = "🟢 Unterstützungsbereich", -0.5
elif gold > 2200:
    trend_signal, trend_score = "🔴 Widerstandsbereich", 0.5
else:
    trend_signal, trend_score = "⚪ Mittlerer Bereich", 0

# Treiber 4: Gesamt-Score (KORRIGIERT!)
total_score = dxy_score + rate_score + trend_score

# KORRIGIERTE Logik - symmetrisch für alle Werte
if total_score >= 1.5:
    overall_text, overall_color = "🔴 VERKAUFEN", "red"
elif total_score >= 0.5:
    overall_text, overall_color = "🟠 LEICHT VERKAUFEN", "orange"
elif total_score <= -1.5:
    overall_text, overall_color = "🟢 KAUFEN", "green"
elif total_score <= -0.5:
    overall_text, overall_color = "🟡 LEICHT KAUFEN", "blue"
else:
    overall_text, overall_color = "⚪ HALTEN", "gray"

# Anzeige der 4 Treiber
col1, col2 = st.columns(2)

with col1:
    st.write(f"**💵 Dollar (DXY {dxy:.1f}):**")
    st.write(dxy_signal)
    st.caption("Geschätzt aus EUR/USD")
    
    st.write(f"**📈 Zinsen ({treasury:.1f}%):**")
    st.write(rate_signal)
    st.caption("Aktueller Marktdurchschnitt")

with col2:
    st.write(f"**📊 Gold-Preis (${gold:.0f}):**")
    st.write(trend_signal)
    st.caption("✅ ECHT von GoldAPI")
    
    st.write(f"**🎯 Gesamt-Score: {total_score:.1f}**")
    if total_score > 0:
        st.caption("Positiv = Bärish (Gold fällt tendenziell)")
    elif total_score < 0:
        st.caption("Negativ = Bullish (Gold steigt tendenziell)")
    else:
        st.caption("Neutral = Keine klare Richtung")

# Hauptsignal (außerhalb der Spalten, groß)
st.divider()

if overall_color == "green":
    st.success(f"### {overall_text}")
elif overall_color == "red":
    st.error(f"### {overall_text}")
elif overall_color == "orange":
    st.warning(f"### {overall_text}")
elif overall_color == "blue":
    st.info(f"### {overall_text}")
else:
    st.write(f"### {overall_text}")

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

fig.update_layout(
    height=400,
    template="plotly_white",
    xaxis_title="Datum",
    yaxis_title="Preis (USD)",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Legende
st.divider()
st.info("""
📊 **Datenquellen:**
- ✅ **Gold (USD/EUR):** Echt von GoldAPI.io
- ⚠️ **DXY:** Geschätzt aus EUR/USD Wechselkurs
- ⚠️ **Zinsen:** Geschätzter Marktdurchschnitt (~4.2%)
""")

st.caption(f"Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

if st.button("🔄 Neu laden"):
    st.rerun()
