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

# --- 2. CONFIGURACIÓN DE RIESGO (v5) ---
st.sidebar.header("🛡️ GESTIÓN DE RIESGO v5")
balance = st.sidebar.number_input("Balance de la Cuenta (USD)", min_value=100.0, value=1000.0, step=100.0)
riesgo_pct = st.sidebar.slider("% de Riesgo por Operación", 0.5, 5.0, 1.0) / 100

def calcular_posicion(entrada, stop_loss, balance, riesgo_dinero):
    distancia = abs(entrada - stop_loss)
    if distancia == 0: return 0
    # Fórmula Quant: Unidades = (Capital * %Riesgo) / Distancia al Stop
    unidades = riesgo_dinero / distancia
    return unidades

# --- 3. CONFIGURACIÓN TELEGRAM ---
TOKEN = "8596067199:AAFhwB6pcrCH5FZTE0fkmvkMApKWIbH3cGI"
CHAT_ID = "759241835"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

st.set_page_config(page_title="Control Maestro v5", layout="wide")
st.title("💎 Control Maestro v5: Risk Management Edition")

# --- LEYENDAS ---
with st.expander("📚 LEYENDA Y HERRAMIENTAS"):
    st.markdown("""
    * 🔴 **Muro Rojo (POC):** Punto de control institucional. Si el precio lo rompe, el escenario A+ se invalida.
    * 🔵 **Cian (VWAP):** Precio promedio de equilibrio.
    * 💠 **Diamante Azul:** Absorción detectada (VSA).
    * 🛡️ **Risk Calculator:** Calcula el lotaje ideal para no quemar la cuenta.
    """)

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
        es_tendencia = df_clean['Volat'].iloc[-1] > df_clean['Volat'].mean()

        st.subheader(f"📊 {nombre}: {'TENDENCIA' if es_tendencia else 'RANGO'}")

        cols = st.columns(3)
        info_final = {}

        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC & VWAP
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            vwap_up = df['VWAP'].iloc[-1] > df['VWAP'].iloc[-2]
            
            # VSA / DIAMANTE
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            es_diamante = (df['RVOL'].iloc[-1] > 1.8) and ((df['High'].iloc[-1] - df[['Open','Close']].iloc[-1].max() > df['Range'].iloc[-1]*0.4) or ((df['RVOL'].iloc[-1]>2) and (df['Range'].iloc[-1]<df['Range'].rolling(20).mean().iloc[-1])))
            
            dist_muro = abs(df['Close'].iloc[-1] - poc_price) / poc_price

            if tf == "5m":
                # CÁLCULO DE RIESGO v5
                dinero_riesgo = balance * riesgo_pct
                posicion = calcular_posicion(df['Close'].iloc[-1], poc_price, balance, dinero_riesgo)
                info_final = {"diamante": es_diamante, "muro": poc_price, "vwap_up": vwap_up, "lotes": posicion, "riesgo": dinero_riesgo}

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.5)
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.5)
                
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d', zorder=20)
                    if tf == "5m":
                        enviar_telegram(f"💎 *ALERTA v5: {nombre}*\nPosición Sugerida: {posicion:.4f} unidades\nStop Loss (Muro): {poc_price:.2f}")

                ax.set_title(f"TF: {tf}", color="white")
                ax.tick_params(colors='white', labelsize=8)
                st.pyplot(fig)

        # --- CONCLUSIÓN v5 CON GESTIÓN ---
        with st.container(border=True):
            st.markdown("### 🔍 Veredicto de Gestión v5")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🛡️ Plan de Trade (Dummies):**")
                if info_final['diamante']:
                    st.success(f"**¡SEÑAL ACTIVA!** Compra/Vende {info_final['lotes']:.4f} unidades. Tu riesgo es de ${info_final['riesgo']:.2f}. Si el precio cruza el Muro Rojo ({info_final['muro']:.2f}), sal de la operación.")
                else:
                    st.write(f"Sin señal clara. Si el diamante aparece, opera máximo {info_final['lotes']:.4f} unidades.")
            with c2:
                st.markdown("**🔬 Métricas Quant (Pros):**")
                st.code(f"Capital en Riesgo: ${info_final['riesgo']:.2f}\nSizing Basado en POC: {info_final['lotes']:.6f}\nInclinación VWAP: {'Alcista' if info_final['vwap_up'] else 'Bajista'}")

    except Exception as e:
        st.error(f"Error: {e}")
