import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import requests
import time

# --- CONFIGURACIÓN ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=params)
    except:
        pass

st.set_page_config(page_title="Radar Institucional", layout="wide")
st.title("🦅 Radar de Intención v1.0")

activos = ["GC=F", "USDJPY=X"]
config_tfs = [
    {"tf": "5m", "periodo": "2d"},
    {"tf": "15m", "periodo": "5d"},
    {"tf": "1h", "periodo": "30d"}
]

if st.button('🔄 ACTUALIZAR DATOS'):
    st.rerun()

for ticker in activos:
    st.subheader(f"📊 {ticker}")
    cols = st.columns(3)
    
    for i, conf in enumerate(config_tfs):
        try:
            # Descarga de datos
            df = yf.download(ticker, period=conf['periodo'], interval=conf['tf'], progress=False)
            if df.empty: continue
            
            # Limpiar columnas MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Cálculos de IA
            df['Returns'] = df['Close'].pct_change()
            df['Volatilidad'] = df['Returns'].rolling(10).std()
            df = df.dropna().copy()
            
            X = df[['Volatilidad', 'Returns']].values
            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
            df['Regimen'] = kmeans.labels_
            
            # Lógica de detección
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
            df['Body'] = abs(df['Close'] - df['Open'])
            
            last = df.iloc[-1]
            es_trampa = (last['RVOL'] > 1.8) and (last['Upper_Wick'] > last['Body'] or last['Lower_Wick'] > last['Body'])
            
            # Gráfico
            with cols[i]:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.plot(df.index, df['Close'], color='black', alpha=0.6)
                
                status = "ESPERA"
                if es_trampa:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='orange', s=250, marker='*')
                    status = "🪤 TRAMPA"
                    if conf['tf'] == "5m":
                        enviar_telegram(f"🚨 TRAMPA en {ticker} ({conf['tf']})")
                
                ax.set_title(f"{conf['tf']} | {status}", fontsize=12, fontweight='bold')
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Error en {ticker} {conf['tf']}: {e}")

st.caption(f"Actualizado a las {time.strftime('%H:%M:%S')}")