import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from sklearn.cluster import KMeans
import time

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v5 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

# --- 2. GESTIÓN DE RIESGO ---
st.sidebar.header("🛡️ GESTIÓN DE RIESGO v5")
balance = st.sidebar.number_input("Balance de la Cuenta (USD)", min_value=100.0, value=1000.0)
riesgo_pct = st.sidebar.slider("% de Riesgo por Operación", 0.5, 5.0, 1.0) / 100

def calcular_posicion(entrada, stop_loss, balance, riesgo_dinero):
    distancia = abs(entrada - stop_loss)
    return riesgo_dinero / distancia if distancia != 0 else 0

# --- 3. CONFIGURACIÓN TELEGRAM ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

st.set_page_config(page_title="Control Maestro v4", layout="wide")
st.title("💎 Control Maestro v5")

# --- LEYENDAS (Tus Favoritas) ---
with st.expander("📚 LEYENDA Y GUÍA RÁPIDA"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Nivel Dummie (Simplicidad):**
        * 🔴 **Muro Rojo:** Precio donde compraron los jefes.
        * 🔵 **Línea Cian:** El precio 'justo' (Imán).
        * 💠 **Diamante Azul:** Aviso de que los jefes están atrapando gente.
        """)
    with col2:
        st.markdown("""
        **Nivel Pro (Cuantitativo):**
        * **POC (Red):** Punto de mayor liquidez institucional.
        * **VWAP (Cyan):** Precio promedio ponderado por volumen.
        * **VSA:** Detección de absorción institucional.
        """)

# --- LÓGICA DE ACTIVOS ---
activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    try:
        df_main = yf.download(ticker, period="30d", interval="1h", progress=False)
        if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
        
        # IA STATUS
        volat = df_main['Close'].pct_change().rolling(10).std().iloc[-1]
        es_tendencia = volat > df_main['Close'].pct_change().rolling(10).std().mean()
        st.subheader(f"📊 {nombre}: {'MODO TENDENCIA' if es_tendencia else 'MODO RANGO'}")

        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC & VWAP
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # DIAMANTE
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 1.8) and ((last['High'] - last[['Open','Close']].max() > last['Range']*0.4) or ((last['RVOL']>2) and (last['Range']<df['Range'].rolling(20).mean().iloc[-1])))

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.5)
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.5)
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d')
                ax.set_title(f"TF: {tf}", color="white")
                ax.tick_params(colors='white', labelsize=8)
                st.pyplot(fig)
                
                if tf == "5m":
                    posicion = calcular_posicion(last['Close'], poc_price, balance, balance*riesgo_pct)
                    st
