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
        st.text_input("Control Maestro v4 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE": # <--- CAMBIA TU CLAVE AQUÍ
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

# --- 2. CONFIGURACIÓN TELEGRAM ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
    except: pass

st.set_page_config(page_title="Control Maestro v4", layout="wide")
st.title("🎛️ Control Maestro v4")

# --- LEYENDA Y GUÍA RÁPIDA ---
with st.expander("📚 LEYENDA Y GUÍA RÁPIDA"):
    st.markdown("""
    **Simbología del Gráfico (Estilo v3):**
    * **Línea Roja Sólida:** 🚨 **BIG MONEY (POC)**. Donde las instituciones inyectan capital.
    * **Línea Cian Punteada:** VWAP (Precio Justo).
    * **Marcador 📍 (Diamante Naranja):** Trampa detectada.
    
    **Nueva Alerta Inteligente:**
    * Recibirás un mensaje especial si la trampa ocurre **tocando el muro rojo**. Esa es la entrada de mayor confianza.
    """)

if st.sidebar.button('🔄 REESCANEAR MERCADO'):
    st.rerun()

activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    try:
        df_main = yf.download(ticker, period="30d", interval="1h", progress=False)
        if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
        
        # --- IA K-MEANS ---
        df_main['Ret'] = df_main['Close'].pct_change()
        df_main['Volat'] = df_main['Ret'].rolling(10).std()
        df_clean = df_main.dropna()
        kmeans = KMeans(n_clusters=2, n_init=10).fit(df_clean[['Volat', 'Ret']])
        volat_actual = df_clean['Volat'].iloc[-1]
        es_tendencia = volat_actual > df_clean['Volat'].mean()

        # --- PANEL DE VEREDICTO ---
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            st.subheader(f"🚀 {nombre}: {'IR CON TENDENCIA' if es_tendencia else 'BUSCAR TRAMPAS'}")
        with col_v2:
            st.caption(f"IA Status: {'Expansión' if es_tendencia else 'Compresión'}")

        # --- GRÁFICOS ---
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # --- BIG MONEY (Volume Profile) ---
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            vol_profile = df.groupby('price_bin', observed=True)['Volume'].sum()
            poc_bin = vol_profile.idxmax()
            poc_price = (poc_bin.left + poc_bin.right) / 2
            
            # Cálculos Técnicos
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Body'] = abs(df['Close'] - df['Open'])
            df['Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            
            last = df.iloc[-1]
            trampa_activa = (last['RVOL'] > 1.7) and (last['Wick'] > last['Body'])
            
            # Lógica de proximidad al Muro Rojo (dentro de 0.05%)
            toca_muro = abs(last['Close'] - poc_price) / poc_price < 0.0005

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                # Visual v3
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.5)
                ax.axhline(y=poc_price, color='red', linestyle='-', alpha=0.8, linewidth=1.5) # Muro Rojo
                ax.fill_between(df.index, df['VWAP']*1.001, df['VWAP']*0.999, color='cyan', alpha=0.05)
                
                if trampa_activa:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='orange', s=150, marker='d', zorder=10)
                    
                    # ALERTAS TELEGRAM FILTRADAS (Solo M5)
                    if tf == "5m":
                        if toca_muro:
                            enviar_telegram(f"🔥 SEÑAL MAESTRA: {nombre} Trampa detectada TOCANDO EL MURO ROJO ({poc_price:.2f}). ¡Entrada de Alta Probabilidad!")
                        else:
                            enviar_telegram(f"📍 CONTROL MAESTRO: Trampa en {nombre} (M5). Lejos del muro.")

                ax.set_title(f"TF: {tf}", color="white", fontsize=9)
                ax.tick_params(colors='white', labelsize=7)
                for s in ax.spines.values(): s.set_visible(False)
                st.pyplot(fig)
                st.write(f"Muro: **{poc_price:.2f}**")

    except Exception as e:
        st.error(f"Error: {e}")

st.caption(f"Control Maestro v4 | Modo Alerta Big Money Activo")
