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
    if st.session_state["password"] == "TU_CLAVE":
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

st.set_page_config(page_title="Control Maestro v4", layout="wide")
st.title("💎 Control Maestro v4: Quant Edition")

# --- LEYENDAS Y POTENCIAL ---
with st.expander("📚 LEYENDA TÉCNICA (Dummies & Pros)"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Para Dummies (Explicación Simple):**
        * **Muro Rojo:** Donde los dueños del dinero compraron mucho. No cruzar sin permiso.
        * **Línea Cian:** El precio 'justo'. Si el precio está lejos, va a volver como un imán.
        * **Diamante Azul 💠:** ¡Cuidado! Alguien intentó engañar al mercado y lo atraparon.
        """)
    with col2:
        st.markdown("""
        **Para Profesionales (Explicación Quant):**
        * **POC (Point of Control):** High Volume Node. Nivel de máxima liquidez institucional.
        * **VWAP:** Benchmark institucional de ejecución.
        * **VSA (Effort vs Result):** Algoritmo que detecta absorción institucional mediante la divergencia entre el rango de la vela y el volumen relativo.
        """)

with st.expander("🔥 GUÍA DE ESCENARIOS A+ (Máxima Probabilidad)"):
    st.markdown("""
    **Escenario 1: El Rebote del Muro (Reversión)**
    1. El precio toca el **Muro Rojo (POC)**.
    2. Aparece un **Diamante Azul 💠**.
    3. El precio está fuera de la zona cian (Sobre-extensión).
    *Resultado:* Entrada inmediata hacia el VWAP.
    
    **Escenario 2: El Engaño en Tendencia**
    1. La IA dice: **IR CON TENDENCIA**.
    2. El precio hace un retroceso al **Muro Rojo**.
    3. Aparece el **Diamante Azul**.
    *Resultado:* Continuación de tendencia con stop muy corto.
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
        
        # --- IA QUANT ---
        df_main['Ret'] = df_main['Close'].pct_change()
        df_main['Volat'] = df_main['Ret'].rolling(10).std()
        df_clean = df_main.dropna()
        kmeans = KMeans(n_clusters=2, n_init=10).fit(df_clean[['Volat', 'Ret']])
        volat_actual = df_clean['Volat'].iloc[-1]
        es_tendencia = volat_actual > df_clean['Volat'].mean()

        # --- PANEL DE VEREDICTO ---
        st.subheader(f"📊 {nombre}: {'ALTA VOLATILIDAD / TENDENCIA' if es_tendencia else 'BAJA VOLATILIDAD / RANGO'}")

        # --- GRÁFICOS ---
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # --- BIG MONEY (POC) ---
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            
            # --- VSA (Detección Quant de Instituciones) ---
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            # Anomalía: Mucho volumen, poco movimiento (Absorción)
            df['VSA_Anomalia'] = (df['RVOL'] > 2.0) & (df['Range'] < df['Range'].rolling(20).mean())
            
            last = df.iloc[-1]
            toca_muro = abs(last['Close'] - poc_price) / poc_price < 0.0006
            # Señal: VSA o Trampa clásica
            es_diamante = (last['RVOL'] > 1.8) and ( (last['High'] - last[['Open','Close']].max(axis=0) > abs(last['Close']-last['Open'])) or last['VSA_Anomalia'] )

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                ax.plot(df.index, df['Close'], color='white', alpha=0.2, linewidth=1)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.4)
                ax.axhline(y=poc_price, color='red', alpha=0.6, linewidth=1.2)
                
                if es_diamante:
                    # AZUL DIAMANTE
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=180, marker='d', zorder=15)
                    if tf == "5m":
                        status_muro = "⚠️ SOBRE EL MURO" if toca_muro else "fuera de zona"
                        enviar_telegram(f"💎 DIAMANTE AZUL: {nombre} ({tf}) {status_muro}. Muro: {poc_price:.2f}")

                ax.set_title(f"{tf}", color="white", fontsize=10)
                ax.axis('off') # Diseño ultra limpio
                st.pyplot(fig)
                st.write(f"POC: {poc_price:.2f}")

    except Exception as e:
        st.error(f"Error: {e}")

st.caption(f"Control Maestro v4 | Quant VSA & Big Money Detector")
