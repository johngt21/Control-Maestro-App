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
    if st.session_state["password"] == "Controlmaestro17!": # 
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
with st.expander("📚 LEYENDA Y GUÍA RÁPIDA DEL TRIPLE RADAR"):
    st.markdown("""
    **Simbología del Gráfico:**
    * **Línea Cian Punteada:** VWAP (Precio Justo). Es el imán del mercado.
    * **Sombreado Cian (Neon):** Zona de Valor / Mapa de Calor de volumen.
    * **Marcador 📍 (Diamante Naranja):** Trampa detectada por volumen relativo (RVOL).
    
    **Guía del Triple Radar:**
    1.  **H1 (Tendencia):** Define el sesgo del día.
    2.  **M15 (Confirmación):** Busca si el precio se aleja del VWAP.
    3.  **M5 (Entrada):** Aquí es donde recibes la alerta en **Telegram**. Si ves el 📍, es tu gatillo.
    """)

if st.sidebar.button('🔄 REESCANEAR MERCADO'):
    st.rerun()

activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    try:
        # Descarga para lógica de IA (1h)
        df_main = yf.download(ticker, period="30d", interval="1h", progress=False)
        if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
        
        # --- LÓGICA IA (Clustering K-Means) ---
        df_main['Ret'] = df_main['Close'].pct_change()
        df_main['Volat'] = df_main['Ret'].rolling(10).std()
        df_clean = df_main.dropna()
        kmeans = KMeans(n_clusters=2, n_init=10).fit(df_clean[['Volat', 'Ret']])
        
        volat_actual = df_clean['Volat'].iloc[-1]
        volat_media = df_clean['Volat'].mean()
        es_tendencia = volat_actual > volat_media

        # --- PANEL DE VEREDICTO ---
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            if es_tendencia:
                st.subheader(f"🚀 {nombre}: IR CON LA TENDENCIA")
            else:
                st.subheader(f"🪤 {nombre}: BUSCAR TRAMPAS")
        
        with col_v2:
            with st.container(border=True):
                st.write("**¿Por qué la IA dice esto?**")
                if es_tendencia:
                    st.caption(f"Volatilidad ({volat_actual:.4f}) ALTA. El mercado tiene fuerza direccional.")
                else:
                    st.caption(f"Volatilidad ({volat_actual:.4f}) BAJA. El precio está en zona de engaño.")

        # --- GRÁFICOS (Estética v3) ---
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Cálculos técnicos
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Body'] = abs(df['Close'] - df['Open'])
            df['Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            
            last = df.iloc[-1]
            trampa_activa = (last['RVOL'] > 1.7) and (last['Wick'] > last['Body'])

            with cols[idx]:
                # Configuración de estilo profesional oscuro
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                # Gráfica de precio suavizada (v3 style)
                ax.plot(df.index, df['Close'], color='white', alpha=0.4, linewidth=1.5)
                
                # VWAP e "Imán" Neón
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.8, label='VWAP')
                ax.fill_between(df.index, df['VWAP']*1.002, df['VWAP']*0.998, color='cyan', alpha=0.1)
                
                # Diamante de Trampa (📍)
                if trampa_activa:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='orange', s=150, marker='d', zorder=5)
                    st.toast(f"📍 Trampa en {nombre} ({tf})", icon="📍")
                    if tf == "5m": enviar_telegram(f"📍 CONTROL MAESTRO: Trampa detectada en {nombre} (M5)")
                
                # Refinamiento de ejes
                ax.set_title(f"Temporalidad: {tf}", color="white", fontsize=10, fontweight='bold')
                ax.tick_params(colors='white', labelsize=8)
                for spine in ax.spines.values():
                    spine.set_visible(False)
                ax.grid(color='white', alpha=0.05)
                
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Error procesando {nombre}: {e}")

st.caption(f"Control Maestro v4 | Sincronizado: {time.strftime('%H:%M:%S')}")
