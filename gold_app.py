import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Gold Signal App", page_icon="📈", layout="wide")
st.title("📊 Gold Treiber Analyse (USD & EUR)")

@st.cache_data(ttl=300)
def get_data():
    try:
        # Gold in USD
        gold_usd = yf.download("GC=F", period="1mo", interval="1h", progress=False)
        
        # EUR/USD für Umrechnung
        eurusd = yf.download("EURUSD=X", period="1mo", interval="1h", progress=False)
        
        # Dollar Index
        dxy = yf.download("DX-Y.NYB", period="1mo", interval="1d", progress=False)
        
        # 10Y Treasury
        treasury = yf.download("^TNX", period="1mo", interval="1d", progress=False)
        
        return gold_usd, eurusd, dxy, treasury
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return None, None, None, None

def safe_float(value):
    """Hilfsfunktion um Series zu float zu konvertieren"""
    try:
        if isinstance(value, pd.Series):
            return float(value.iloc[0])
        return float(value)
    except:
        return 0.0

def clean_dataframe(df):
    """Bereinigt das DataFrame von String-Werten"""
    if df is None or df.empty:
        return df
    
    # Entferne Zeilen mit Index-Werten die Strings sind (wie 'GC=F')
    df = df[~df.index.astype(str).str.contains('GC=F|Ticker', na=False)]
    
    # Konvertiere alle Spalten zu numerischen Werten
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Entferne NaN Werte
    df = df.dropna()
    
    return df

def analyze_data(gold_usd, eurusd, dxy, treasury):
    results = {}
    
    # Bereinige Daten
    gold_usd = clean_dataframe(gold_usd)
    eurusd = clean_dataframe(eurusd)
    
    # Gold USD Analyse
    if gold_usd is not None and not gold_usd.empty:
        current_gold_usd = safe_float(gold_usd['Close'].iloc[-1])
        gold_24h_usd = safe_float(gold_usd['Close'].iloc[-24]) if len(gold_usd) > 24 else safe_float(gold_usd['Close'].iloc[0])
        gold_change_usd = ((current_gold_usd - gold_24h_usd) / gold_24h_usd) * 100
        
        results['gold_price_usd'] = current_gold_usd
        results['gold_change_usd'] = gold_change_usd
        results['gold_df'] = gold_usd  # Für Chart
    else:
        results['gold_price_usd'] = 0
        results['gold_change_usd'] = 0
        results['gold_df'] = None
    
    # Gold EUR berechnen (USD / EURUSD)
    if results['gold_price_usd'] > 0 and eurusd is not None and not eurusd.empty:
        current_eurusd = safe_float(eurusd['Close'].iloc[-1])
        eurusd_24h = safe_float(eurusd['Close'].iloc[-24]) if len(eurusd) > 24 else current_eurusd
        
        if current_eurusd > 0:
            # Gold in EUR = Gold in USD / EURUSD
            current_gold_eur = current_gold_usd / current_eurusd
            gold_24h_eur = (gold_24h_usd / eurusd_24h) if eurusd_24h > 0 else current_gold_eur
            gold_change_eur = ((current_gold_eur - gold_24h_eur) / gold_24h_eur) * 100
            
            results['gold_price_eur'] = current_gold_eur
            results['gold_change_eur'] = gold_change_eur
        else:
            results['gold_price_eur'] = 0
            results['gold_change_eur'] = 0
    else:
        results['gold_price_eur'] = 0
        results['gold_change_eur'] = 0
    
    # Dollar Analyse
    if dxy is not None and not dxy.empty and len(dxy) > 5:
        current_dxy = safe_float(dxy['Close'].iloc[-1])
        dxy_ma20 = safe_float(dxy['Close'].rolling(20).mean().iloc[-1])
        dxy_week = safe_float(dxy['Close'].iloc[-5])
        dxy_change = ((current_dxy - dxy_week) / dxy_week) * 100
        
        results['dxy'] = current_dxy
        results['dxy_change'] = dxy_change
        
        if current_dxy < dxy_ma20 * 0.995:
            results['dxy_signal'] = "🟢 Schwach (bullish für Gold)"
            results['dxy_score'] = -1
        elif current_dxy > dxy_ma20 * 1.005:
            results['dxy_signal'] = "🔴 Stark (bärish für Gold)"
            results['dxy_score'] = 1
        else:
            results['dxy_signal'] = "⚪ Neutral"
            results['dxy_score'] = 0
    else:
        results['dxy_signal'] = "⚪ Keine Daten"
        results['dxy_score'] = 0
        results['dxy'] = 0
        results['dxy_change'] = 0
    
    # Zinsen Analyse
    if treasury is not None and not treasury.empty and len(treasury) > 5:
        current_rate = safe_float(treasury['Close'].iloc[-1])
        rate_week = safe_float(treasury['Close'].iloc[-5])
        rate_change = ((current_rate - rate_week) / rate_week) * 100
        
        results['rate'] = current_rate
        results['rate_change'] = rate_change
        
        if rate_change < -3:
            results['rate_signal'] = "🟢 Gefallen (bullish für Gold)"
            results['rate_score'] = -1
        elif rate_change > 3:
            results['rate_signal'] = "🔴 Gestiegen (bärish für Gold)"
            results['rate_score'] = 1
        else:
            results['rate_signal'] = "⚪ Stabil"
            results['rate_score'] = 0
    else:
        results['rate_signal'] = "⚪ Keine Daten"
        results['rate_score'] = 0
        results['rate'] = 0
        results['rate_change'] = 0
    
    # Trend Analyse
    if gold_usd is not None and not gold_usd.empty and len(gold_usd) > 20:
        current = safe_float(gold_usd['Close'].iloc[-1])
        ma20 = safe_float(gold_usd['Close'].rolling(20).mean().iloc[-1])
        
        if current > ma20:
            results['trend_signal'] = "🟢 Über MA20"
            results['trend_score'] = -0.5
        else:
            results['trend_signal'] = "🔴 Unter MA20"
            results['trend_score'] = 0.5
    else:
        results['trend_signal'] = "⚪ Keine Daten"
        results['trend_score'] = 0
    
    # Gesamt-Signal
    total_score = results['dxy_score'] + results['rate_score'] + results['trend_score']
    
    if total_score <= -1.5:
        results['signal'] = "🟢 KAUFEN"
        results['signal_desc'] = "Mehrere bullish Treiber aktiv"
        results['color'] = "green"
    elif total_score <= -0.5:
        results['signal'] = "🟡 LEICHT KAUFEN"
        results['signal_desc'] = "Bullish Tendenz"
        results['color'] = "lightgreen"
    elif total_score >= 1.5:
        results['signal'] = "🔴 VERKAUFEN"
        results['signal_desc'] = "Mehrere bärish Treiber aktiv"
        results['color'] = "red"
    elif total_score >= 0.5:
        results['signal'] = "🟠 LEICHT VERKAUFEN"
        results['signal_desc'] = "Bärish Tendenz"
        results['color'] = "orange"
    else:
        results['signal'] = "⚪ HALTEN"
        results['signal_desc'] = "Keine klare Richtung"
        results['color'] = "gray"
    
    results['total_score'] = total_score
    return results

# Haupt-Programm
try:
    with st.spinner("Lade Daten..."):
        gold_usd, eurusd, dxy, treasury = get_data()
    
    if gold_usd is None or gold_usd.empty:
        st.error("Keine Daten verfügbar")
    else:
        results = analyze_data(gold_usd, eurusd, dxy, treasury)
        
        # Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Gold (USD)", f"${results['gold_price_usd']:.2f}", f"{results['gold_change_usd']:+.2f}%")
        col2.metric("Gold (EUR)", f"{results['gold_price_eur']:.2f} €", f"{results['gold_change_eur']:+.2f}%")
        col3.metric("DXY", f"{results['dxy']:.2f}", f"{results['dxy_change']:+.2f}%")
        col4.metric("10Y Rendite", f"{results['rate']:.2f}%", f"{results['rate_change']:+.2f}%")
        col5.metric("Gesamt-Score", f"{results['total_score']:.1f}", "Negativ=Bullish")
        
        # Signal
        st.divider()
        if results['color'] == "green":
            st.success(f"### {results['signal']}\n{results['signal_desc']}")
        elif results['color'] == "red":
            st.error(f"### {results['signal']}\n{results['signal_desc']}")
        elif results['color'] == "orange":
            st.warning(f"### {results['signal']}\n{results['signal_desc']}")
        elif results['color'] == "lightgreen":
            st.info(f"### {results['signal']}\n{results['signal_desc']}")
        else:
            st.write(f"### {results['signal']}\n{results['signal_desc']}")
        
        # Details
        st.divider()
        st.subheader("📋 Detaillierte Treiber-Analyse")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**💵 Dollar (DXY):**")
            st.write(results['dxy_signal'])
            st.caption("Ein schwacher Dollar ist gut für Gold")
            
            st.write(f"**📈 Zinsen (10Y Treasury):**")
            st.write(results['rate_signal'])
            st.caption("Fallende Zinsen unterstützen Gold")
        
        with col2:
            st.write(f"**📊 Technischer Trend:**")
            st.write(results['trend_signal'])
            st.caption("Basiert auf dem 20-Tage-Durchschnitt")
            
            st.write(f"**🎯 Gesamtsignal:**")
            if results['color'] == "green":
                st.success(f"{results['signal']} - {results['signal_desc']}")
            elif results['color'] == "red":
                st.error(f"{results['signal']} - {results['signal_desc']}")
            elif results['color'] == "orange":
                st.warning(f"{results['signal']} - {results['signal_desc']}")
            else:
                st.info(f"{results['signal']} - {results['signal_desc']}")
            st.caption(f"Aktueller Score: {results['total_score']:.1f}")
        
        # Chart - korrigiert
        if results['gold_df'] is not None and not results['gold_df'].empty:
            st.divider()
            st.subheader("📈 Gold Chart (30 Tage)")
            
            try:
                # Extrahiere Daten sicher
                df = results['gold_df'].copy()
                
                # Erstelle Listen für den Chart
                dates = df.index.tolist()
                opens = [safe_float(x) for x in df['Open']]
                highs = [safe_float(x) for x in df['High']]
                lows = [safe_float(x) for x in df['Low']]
                closes = [safe_float(x) for x in df['Close']]
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=dates,
                    open=opens,
                    high=highs,
                    low=lows,
                    close=closes,
                    name='Gold (USD)'
                ))
                
                # MA20 berechnen
                if len(closes) >= 20:
                    closes_series = pd.Series(closes)
                    ma20 = closes_series.rolling(20).mean()
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=ma20.tolist(),
                        mode='lines',
                        name='MA20',
                        line=dict(color='orange', width=2)
                    ))
                
                fig.update_layout(
                    height=500, 
                    template="plotly_white", 
                    xaxis_rangeslider_visible=False,
                    title="Gold in USD",
                    yaxis_title="Preis (USD)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as chart_error:
                st.error(f"Chart-Fehler: {chart_error}")
                st.info("Daten werden trotzdem angezeigt")
        
        # Footer
        st.divider()
        st.caption(f"🔄 Aktualisiert: {datetime.now().strftime('%d.%m.%Y %H:%M')} | ⚠️ Nur zu Bildungszwecken")
        
        if st.button("🔄 Aktualisieren"):
            st.rerun()

except Exception as e:
    st.error(f"Fehler: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.info("Bitte Seite neu laden")