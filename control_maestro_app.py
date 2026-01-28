import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from sklearn.cluster import KMeans

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v5 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE": # <--- CAMBIA TU CLAVE AQUÍ
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control Maestro v5", layout="wide", page_icon="💠")
st.title("🎛️ Control Maestro v5")

# --- 3. LEYENDAS CLÁSICAS (v4 Style) ---
with st.expander("📚 LEYENDA TÉCNICA Y GUÍA RÁPIDA"):
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
        * **Win Rate (WR):** Probabilidad estadística basada en los últimos 6 meses.
        """)

# --- 4. GESTIÓN DE RIESGO (Sidebar) ---
st.sidebar.header("🛡️ GESTIÓN DE RIESGO")
balance = st.sidebar.number_input("Balance de la Cuenta (USD)", min_value=100.0, value=1000.0, step=100.0)
riesgo_pct = st.sidebar.slider("% de Riesgo por Operación", 0.5, 3.0, 1.0) / 100
st.sidebar.markdown("---")

def calcular_posicion(entrada, stop_loss, capital_riesgo):
    distancia = abs(entrada - stop_loss)
    return capital_riesgo / distancia if distancia != 0 else 0

# --- 5. LÓGICA DE ANÁLISIS ---
activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown(f"## 📊 {nombre}")
    try:
        # --- SCREENER DE WIN RATE (Histórico 6 meses) ---
        df_wr = yf.download(ticker, period="6mo", interval="1h", progress=False)
        if isinstance(df_wr.columns, pd.MultiIndex): df_wr.columns = df_wr.columns.get_level_values(0)
        
        df_wr['VWAP'] = (df_wr['Close'] * df_wr['Volume']).cumsum() / df_wr['Volume'].cumsum()
        df_wr['RVOL'] = df_wr['Volume'] / df_wr['Volume'].rolling(20).mean()
        df_wr['Signal'] = 0
        df_wr.loc[(df_wr['RVOL'] > 1.7) & (df_wr['Close'] > df_wr['VWAP']), 'Signal'] = 1
        df_wr.loc[(df_wr['RVOL'] > 1.7) & (df_wr['Close'] < df_wr['VWAP']), 'Signal'] = -1
        df_wr['Ret'] = df_wr['Signal'].shift(1) * df_wr['Close'].pct_change()
        
        trades = df_wr[df_wr['Signal'].shift(1) != 0]
        wr = (trades['Ret'] > 0).mean() * 100 if len(trades) > 0 else 0
        pf = trades[trades['Ret'] > 0]['Ret'].sum() / abs(trades[trades['Ret'] < 0]['Ret'].sum() or 1)

        # Métrica de Win Rate en UI
        m1, m2, m3 = st.columns(3)
        m1.metric("Win Rate (6m)", f"{wr:.1f}%")
        m2.metric("Profit Factor", f"{pf:.2f}")
        m3.metric("Señales Detectadas", len(trades))

        # --- ANÁLISIS DE MERCADO (Gráficos) ---
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC & VWAP
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante Azul (v5.1 Optimizada)
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 1.7) and (last['Range'] < df['Range'].rolling(20).mean().iloc[-1])

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                ax.plot(df.index, df['Close'], color='white', alpha=0.3)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.4)
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.5)
                
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d', zorder=20)
                
                ax.set_title(f"TF: {tf}", color="white", fontsize=10)
                ax.tick_params(colors='gray', labelsize=8)
                st.pyplot(fig)
                
                if tf == "5m":
                    st.write(f"POC (Muro): **{poc_price:.2f}**")
                    dinero_riesgo = balance * riesgo_pct
                    lotes = calcular_posicion(last['Close'], poc_price, dinero_riesgo)
                    st.info(f"Sizing Sugerido: **{lotes:.4f}** unidades")

    except Exception as e:
        st.error(f"Error analizando {nombre}: {e}")

st.caption("Control Maestro v5 | Institutional Risk & Win Rate Screener")
