import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v6 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE": # <--- TU CLAVE AQUÍ
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control Maestro v6", layout="wide", page_icon="💠")
st.title("🎛️ Control Maestro v6")

# --- 3. LEYENDAS CLÁSICAS (v4 Style) ---
with st.expander("📚 LEYENDA TÉCNICA Y GUÍA DE ESCENARIOS"):
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown("""
        **Nivel Dummie (Simplicidad):**
        * 🔴 **Muro Rojo:** Precio donde compraron los jefes. Si el precio llega aquí, prepárate.
        * 🔵 **Línea Cian:** El precio 'justo'. El mercado siempre intenta volver a él.
        * 💠 **Diamante Azul:** ¡Atrapados! Alguien intentó mover el mercado y los grandes lo detuvieron.
        """)
    with col_l2:
        st.markdown("""
        **Nivel Pro (Cuantitativo):**
        * **POC (Red):** Point of Control. Zona de máximo volumen y liquidez institucional.
        * **VWAP (Cyan):** Benchmark de ejecución. Define el sesgo del día (Bias).
        * **Absorción:** Detección de anomalías entre Volumen y Rango de precio.
        """)

# --- 4. CALCULADOR DE POSICIÓN (Position Sizer) ---
st.sidebar.header("🛡️ CALCULADOR DE LOTES v6")
capital = st.sidebar.number_input("Capital de la Cuenta (USD)", min_value=10.0, value=1000.0, step=100.0)
arriesgar_usd = st.sidebar.number_input("Dinero a arriesgar en esta operación (USD)", min_value=1.0, value=10.0, step=5.0)

def calcular_lotes_forex(precio_entrada, stop_loss, riesgo_dinero, activo):
    pips_distancia = abs(precio_entrada - stop_loss)
    if pips_distancia == 0: return 0
    
    if "JPY" in activo: # Cálculo para USDJPY
        # 1 lote standard (100k) en USDJPY, un pip (0.01) vale aprox $6.5-$9 dependiendo del precio
        # Simplificación institucional:
        lotes = riesgo_dinero / (pips_distancia * 1000) 
    else: # Cálculo para XAUUSD (Oro)
        # En el Oro, 1 lote = 100 onzas. 1 dólar de movimiento = $100 por lote.
        lotes = riesgo_dinero / (pips_distancia * 100)
    return lotes

# --- 5. ANÁLISIS DE ACTIVOS ---
activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown(f"## 📊 {nombre}")
    try:
        # Gráficos en 3 Temporalidades
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC (Muro Rojo)
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            
            # VWAP (Línea Cian)
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante Azul (v4 Logic)
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 2.0) and (last['Range'] < df['Range'].rolling(20).mean().iloc[-1])

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.4)
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.5)
                
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d', zorder=20)
                
                ax.set_title(f"TF: {tf}", color="white")
                ax.tick_params(colors='gray', labelsize=8)
                st.pyplot(fig)
                
                # Solo mostramos el cálculo en el gráfico de ejecución (5m)
                if tf == "5m":
                    st.write(f"📍 Precio Actual: **{last['Close']:.2f}**")
                    st.write(f"🔴 Muro Rojo (Stop): **{poc_price:.2f}**")
                    
                    lotes_finales = calcular_lotes_forex(last['Close'], poc_price, arriesgar_usd, ticker)
                    
                    with st.container(border=True):
                        st.markdown(f"### 🎯 Lote Sugerido: **{lotes_finales:.2f}**")
                        st.caption(f"Calculado para arriesgar exactamente ${arriesgar_usd} hasta el muro.")

    except Exception as e:
        st.error(f"Error en {nombre}: {e}")

st.caption("Control Maestro v6 | Final Release")
