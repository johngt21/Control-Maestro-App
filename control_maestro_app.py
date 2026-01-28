import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import requests
import time

# --- 1. CONTRASEÑA SIMPLE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Introduce la contraseña para acceder al Radar", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "Controlmaestro17!": 
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

if not check_password():
    st.stop()

# --- 2. CONFIGURACIÓN DE TELEGRAM ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=params)
    except:
        pass

# --- 3. INTERFAZ ---
st.set_page_config(page_title="Radar Pro v2.0", layout="wide")
st.title("🦅 Radar Institucional de Intención v2.0")

activos = ["GC=F", "USDJPY=X"]
config_tfs = [
    {"tf": "5m", "periodo": "2d"},
    {"tf": "15m", "periodo": "5d"},
    {"tf": "1h", "periodo": "30d"}
]

st.sidebar.header("Opciones")
if st.sidebar.button('🔄 Forzar Actualización'):
    st.rerun()

# --- 4. PROCESAMIENTO ---
for ticker in activos:
    st.markdown(f"## 💎 Instrumento: {ticker}")
    cols = st.columns(3)
    
    for i, conf in enumerate(config_tfs):
        try:
            df = yf.download(ticker, period=conf['periodo'], interval=conf['tf'], progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # --- CÁLCULO VWAP (Precio Justo) ---
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # --- IA: K-MEANS ---
            df['Returns'] = df['Close'].pct_change()
            df['Volatilidad'] = df['Returns'].rolling(10).std()
            df = df.dropna().copy()
            kmeans = KMeans(n_clusters=3, n_init=10, random_state=42).fit(df[['Volatilidad', 'Returns']].values)
            df['Regimen'] = kmeans.labels_
            
            # --- DETECCIÓN DE TRAMPAS (RVOL + Mechas) ---
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Body'] = abs(df['Close'] - df['Open'])
            df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
            
            last = df.iloc[-1]
            es_trampa = (last['RVOL'] > 1.8) and (last['Upper_Wick'] > last['Body'] or last['Lower_Wick'] > last['Body'])
            
            # Alerta Telegram
            if es_trampa and conf['tf'] == "5m":
                enviar_telegram(f"🚨 TRAMPA EN {ticker} (M5). Precio fuera de valor!")

            # --- GRÁFICO PROFESIONAL ---
            with cols[i]:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.plot(df.index, df['Close'], color='black', alpha=0.5, label='Precio')
                ax.plot(df.index, df['VWAP'], color='blue', linestyle='--', alpha=0.7, label='VWAP (Precio Justo)')
                
                if es_trampa:
                    # Dibujamos la estrella naranja de la trampa
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='orange', s=300, marker='*', zorder=5, label='TRAMPA')
                    status = "⚠️ TRAMPA DETECTADA"
                    color_status = "orange"
                else:
                    status = "✅ ESPERA"
                    color_status = "gray"
                
                ax.set_title(f"{conf['tf']} | {status}", color=color_status, fontweight='bold')
                ax.legend(prop={'size': 7})
                st.pyplot(fig)
                
                # Métricas debajo del gráfico
                st.write(f"📊 RVOL: {last['RVOL']:.2f} | VWAP: {last['VWAP']:.2f}")

        except Exception as e:
            st.error(f"Error: {e}")

st.caption(f"Radar Activo | Hora local: {time.strftime('%H:%M:%S')}")
