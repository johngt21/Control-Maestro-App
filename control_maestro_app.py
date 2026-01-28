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
        st.text_input("Radar Pro v3.0 - Password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "Controlmaestro17!": # 
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

# --- 2. CONFIGURACIÓN ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
    except: pass

st.set_page_config(page_title="Scanner v3.0", layout="wide")
st.title("🛡️ Scanner de Intención v3.0")

if st.sidebar.button('🔄 ACTUALIZAR SCANNER'):
    st.rerun()

activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

# --- 3. LÓGICA DEL SCANNER ---
for nombre, ticker in activos.items():
    st.markdown(f"---")
    
    # Descarga de datos con corrección para USDJPY
    try:
        df_main = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df_main.empty:
            st.warning(f"Esperando datos de {nombre}...")
            continue
        if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
    except:
        st.error(f"Error de conexión con {nombre}")
        continue

    # --- FILTRO DEFINITIVO (Scanner) ---
    # K-Means para determinar el estado del mercado
    df_main['Ret'] = df_main['Close'].pct_change()
    df_main['Volat'] = df_main['Ret'].rolling(10).std()
    df_clean = df_main.dropna()
    kmeans = KMeans(n_clusters=2, n_init=10).fit(df_clean[['Volat', 'Ret']])
    estado = kmeans.labels_[-1] # 0 o 1
    
    # Determinamos si el mercado está tendencial o comprimido
    avg_volat = df_clean.groupby(kmeans.labels_)['Volat'].mean()
    es_tendencia = (df_clean['Volat'].iloc[-1] > avg_volat.mean())

    if es_tendencia:
        veredicto = f"🚀 El {nombre} está para IR CON LA TENDENCIA"
        color_v = "green"
    else:
        veredicto = f"🪤 El {nombre} está para BUSCAR TRAMPAS"
        color_v = "orange"

    st.subheader(veredicto)

    # --- GRÁFICOS POR TEMPORALIDAD ---
    cols = st.columns(3)
    for idx, (tf, per) in enumerate(tfs.items()):
        df = yf.download(ticker, period=per, interval=tf, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # VWAP e Imán (Perfil de Volumen Simplificado)
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        
        # Detección de Trampa
        df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
        df['Body'] = abs(df['Close'] - df['Open'])
        df['Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        last = df.iloc[-1]
        
        # El "Pin" sustituye a la estrella
        trampa_activa = (last['RVOL'] > 1.7) and (last['Wick'] > last['Body'])

        with cols[idx]:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(df.index, df['Close'], color='white', alpha=0.3)
            ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', label='Precio Justo')
            
            # Mapas de Calor (Sombreado de zonas de volumen)
            ax.fill_between(df.index, df['VWAP']*1.002, df['VWAP']*0.998, color='cyan', alpha=0.1)
            
            if trampa_activa:
                ax.scatter(df.index[-1], df['Close'].iloc[-1], color='orange', s=100, marker='d') # d es un diamante pequeño
                st.toast(f"📍 Señal en {nombre} {tf}", icon="📍")
                if tf == "5m": enviar_telegram(f"📍 ALERTA: Trampa detectada en {nombre} (5m)")
            
            ax.set_title(f"TF: {tf}", color="white")
            ax.set_facecolor('#0e1117')
            fig.patch.set_facecolor('#0e1117')
            ax.tick_params(colors='white')
            st.pyplot(fig)

st.caption(f"Scanner Sincronizado: {time.strftime('%H:%M:%S')}")
