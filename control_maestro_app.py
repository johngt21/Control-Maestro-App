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
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

st.set_page_config(page_title="Control Maestro v4", layout="wide")
st.title("💎 Control Maestro v4: Sistema de Alerta Maestro")

if st.sidebar.button('🔄 REESCANEAR MERCADO'):
    st.rerun()

activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    try:
        df_main = yf.download(ticker, period="30d", interval="1h", progress=False)
        if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
        
        # IA CLUSTERING
        df_main['Ret'] = df_main['Close'].pct_change()
        df_main['Volat'] = df_main['Ret'].rolling(10).std()
        df_clean = df_main.dropna()
        kmeans = KMeans(n_clusters=2, n_init=10).fit(df_clean[['Volat', 'Ret']])
        volat_actual = df_clean['Volat'].iloc[-1]
        es_tendencia = volat_actual > df_clean['Volat'].mean()

        st.subheader(f"📊 {nombre}: {'MODO TENDENCIA' if es_tendencia else 'MODO RANGO'}")

        # GRÁFICOS
        cols = st.columns(3)
        info_conclusiones = {} # Para el resumen final

        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC / BIG MONEY
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            
            # VWAP e Inclinación
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            vwap_subiendo = df['VWAP'].iloc[-1] > df['VWAP'].iloc[-2]
            
            # VSA / DIAMANTE
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            vsa_abs = (df['RVOL'] > 2.0) & (df['Range'] < df['Range'].rolling(20).mean())
            last = df.iloc[-1]
            distancia_muro = abs(last['Close'] - poc_price) / poc_price
            es_diamante = (last['RVOL'] > 1.8) and ( (last['High'] - last[['Open','Close']].max(axis=0) > abs(last['Close']-last['Open'])) or vsa_abs )
            
            # Guardar info para conclusión
            if tf == "5m":
                info_conclusiones = {
                    "diamante": es_diamante,
                    "muro_cerca": distancia_muro < 0.0006,
                    "vwap_up": vwap_subiendo,
                    "poc": poc_price
                }

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.5)
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.5)
                
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d', zorder=20)
                    
                    # ALERTA DE TELEGRAM INTELIGENTE (Solo M5)
                    if tf == "5m":
                        tendencia_txt = "ALCISTA 🟢" if vwap_subiendo else "BAJISTA 🔴"
                        if distancia_muro < 0.0006:
                            msg = f"🔥 *SEÑAL MAESTRA A+*\nInstrumento: {nombre}\nNivel: {poc_price:.2f} (MURO ROJO)\nSetup: Diamante Azul + Absorción\nVWAP: {tendencia_txt}\n_¡Entrada de alta probabilidad!_"
                        else:
                            msg = f"📍 *CONTROL MAESTRO*\nInstrumento: {nombre}\nSetup: Diamante Azul detectado\nVWAP: {tendencia_txt}\nDistancia al Muro: {distancia_muro*100:.2f}%"
                        enviar_telegram(msg)

                ax.set_title(f"TF: {tf}", color="white", fontsize=10)
                ax.tick_params(colors='white', labelsize=8)
                st.pyplot(fig)

        # --- CONCLUSIÓN FINAL ---
        with st.container(border=True):
            st.markdown("### 🔍 Análisis de Control Maestro")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("**🧠 Para Dummies:**")
                tend = "subiendo (Alcista)" if info_conclusiones['vwap_up'] else "bajando (Bajista)"
                if info_conclusiones['diamante'] and info_conclusiones['muro_cerca']:
                    st.success(f"¡ATENCIÓN! El precio está en el muro ({info_conclusiones['poc']:.2f}) y salió un Diamante. La tendencia justa está {tend}. Momento ideal.")
                else:
                    st.write(f"El precio justo está {tend}. Espera a que toque el muro rojo para mayor seguridad.")
            with col_c2:
                st.markdown("**🔬 Para Profesionales:**")
                bias = "BULLISH" if info_conclusiones['vwap_up'] else "BEARISH"
                st.write(f"Bias Intradiario (VWAP): {bias}. POC estacionario en {info_conclusiones['poc']:.2f}. Clustering sugiere {'continuación' if es_tendencia else 'reversión en bordes'}.")

    except Exception as e:
        st.error(f"Error: {e}")
