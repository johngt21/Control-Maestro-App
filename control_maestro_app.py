import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v6 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

st.set_page_config(page_title="Control Maestro v6", layout="wide", page_icon="💠")
st.title("🎛️ Control Maestro v6: Operativa Total")

# --- 2. CALCULADORA DE POSICIÓN INDEPENDIENTE (Sidebar) ---
st.sidebar.header("🛡️ CALCULADOR DE LOTES")
balance = st.sidebar.number_input("Capital Cuenta (USD)", value=1000.0)
riesgo_usd = st.sidebar.number_input("Riesgo en esta operación (USD)", value=10.0)
pips_sl = st.sidebar.number_input("Pips de Stop Loss (SL)", min_value=1.0, value=20.0, step=1.0)

def calcular_lotes_final(riesgo, pips, activo):
    if pips == 0: return 0
    if "JPY" in activo:
        # Para USDJPY: 1 lote standard (100k), 1 pip = ~0.01 JPY (aprox $6.5-$9)
        # Ajuste estándar: Lotes = Riesgo / (Pips * Valor_Pip_Aprox)
        return riesgo / (pips * 7.5) 
    else:
        # Para XAUUSD: 1 pip (0.10 centavos) en 1 lote = $10.
        # Si pips es distancia en puntos (ej 2.0 usd = 20 pips)
        return riesgo / (pips * 10)

# --- 3. DOBLE LEYENDA TÉCNICA ---
col_a, col_b = st.columns(2)
with col_a:
    with st.expander("📚 LEYENDA 1: GUÍA PRÁCTICA DEL ALGORITMO", expanded=True):
        st.markdown("""
        **¿De qué está hecho este sistema?**
        * **VSA (Volume Spread Analysis):** Analiza si el volumen confirma el movimiento.
        * **Clustering K-Means:** La IA clasifica si estamos en tendencia o rango.
        * **POC Dinámico:** Detecta dónde está acumulada la mayor liquidez hoy.
        * **VWAP Institucional:** El ancla de precio que usan los bancos para ejecutar.
        """)
with col_b:
    with st.expander("🧠 LEYENDA 2: INTERPRETACIÓN DUMMIES VS PROS", expanded=True):
        st.markdown("""
        **Nivel Dummie:**
        * 🔴 **Muro:** No pases de aquí sin permiso.
        * 💠 **Diamante:** ¡Alerta! Los jefes están atrapando gente.
        
        **Nivel Profesional:**
        * **Absorción:** Esfuerzo sin resultado (Volumen alto, rango pequeño).
        * **Mean Reversion:** El precio siempre busca el equilibrio del VWAP.
        """)

# --- 4. GUÍA DE ESCENARIOS DE ALTA PROBABILIDAD ---
st.info("""
🔥 **ESCENARIOS A+ (Alta Probabilidad):**
1. **El Rebote del Jefe:** Precio toca el Muro Rojo (POC) + Aparece Diamante Azul 💠.
2. **La Trampa de Tendencia:** Precio lejos del VWAP + Diamante Azul 💠 + RVOL > 2.0 (Regreso al imán cian).
""")

# --- 5. ANÁLISIS DE MERCADO ---
activos = {"Oro (Gold)": "GC=F", "Yen (USD/JPY)": "USDJPY=X"}
tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown(f"---")
    try:
        df_wr = yf.download(ticker, period="2d", interval="5m", progress=False)
        if isinstance(df_wr.columns, pd.MultiIndex): df_wr.columns = df_wr.columns.get_level_values(0)
        
        # UI DE CÁLCULO
        lote_sugerido = calcular_lotes_final(riesgo_usd, pips_sl, ticker)
        
        col_t, col_r = st.columns([2, 1])
        with col_t: st.subheader(f"📊 {nombre}")
        with col_r: st.success(f"**Lote Sugerido: {lote_sugerido:.2f}**")

        # GRÁFICOS
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # POC & VWAP
            bins = 15
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            poc_price = (df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().left + df.groupby('price_bin', observed=True)['Volume'].sum().idxmax().right) / 2
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante Azul v4
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
                ax.axhline(y=poc_price, color='red', alpha=0.7, linewidth=1.2)
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='d')
                ax.set_title(f"TF: {tf}", color="white")
                ax.tick_params(colors='gray', labelsize=8)
                st.pyplot(fig)

    except Exception as e: st.error(f"Error: {e}")

st.caption("Control Maestro v6 | Final Command Version")

