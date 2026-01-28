import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v7 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

st.set_page_config(page_title="Control Maestro v7", layout="wide", page_icon="💠")
st.title("🎛️ Control Maestro v7: Niveles de Precisión")

# --- 2. CALCULADORA INDEPENDIENTE (Sidebar) ---
st.sidebar.header("🛡️ CALCULADOR DE LOTES")
balance = st.sidebar.number_input("Capital Cuenta (USD)", value=1000.0)
riesgo_usd = st.sidebar.number_input("Riesgo en esta operación (USD)", value=10.0)
pips_sl = st.sidebar.number_input("Pips de Stop Loss (SL)", min_value=1.0, value=20.0, step=1.0)

def calcular_lotes_final(riesgo, pips, activo):
    if pips == 0: return 0
    if "JPY" in activo:
        return riesgo / (pips * 7.5) 
    else:
        return riesgo / (pips * 10)

# --- 3. DOBLE LEYENDA TÉCNICA ---
col_a, col_b = st.columns(2)
with col_a:
    with st.expander("📚 LEYENDA 1: GUÍA PRÁCTICA DEL ALGORITMO", expanded=True):
        st.markdown("""
        * **VSA (Volume Spread Analysis):** Volumen vs Rango.
        * **Clustering K-Means:** Clasificación de mercado.
        * **POC Dinámico:** El Muro de liquidez real.
        * **VWAP:** El ancla de los bancos.
        """)
with col_b:
    with st.expander("🧠 LEYENDA 2: INTERPRETACIÓN DUMMIES VS PROS", expanded=True):
        st.markdown("""
        **Nivel Dummie:** 🔴 **Muro** (No pasar) | 💠 **Diamante** (Trampa).
        **Nivel Pro:** **Absorción** (Esfuerzo sin resultado) | **Mean Reversion**.
        """)

# --- 4. GUÍA DE ESCENARIOS A+ ---
st.info("🔥 **ESCENARIOS A+:** 1. Rebote en Muro Rojo 🔴 + Diamante 💠 | 2. Regreso al VWAP 🔵 desde extremo + Diamante 💠.")

# --- 5. ANÁLISIS DE MERCADO ---
activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    try:
        # Lote sugerido visible arriba
        lote_sugerido = calcular_lotes_final(riesgo_usd, pips_sl, ticker)
        c1, c2 = st.columns([3, 1])
        c1.subheader(f"📊 {nombre}")
        c2.success(f"**Lote Sugerido: {lote_sugerido:.2f}**")

        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC (Muro Rojo) con cálculo preciso
            bins = 20
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_data = df.groupby('price_bin', observed=True)['Volume'].sum()
            idx_max = poc_data.idxmax()
            poc_price = (idx_max.left + idx_max.right) / 2
            
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante v4
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df
