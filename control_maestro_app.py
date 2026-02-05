import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v8.1 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: st.session_state["password_correct"] = False

if not check_password(): st.stop()

st.set_page_config(page_title="Control Maestro v8.1", layout="wide", page_icon="🔥")
st.title("🎛️ Control Maestro v8.1: Fuego Maestro + BTC")

# --- 2. CALCULADORA DE POSICIÓN (Sidebar) ---
st.sidebar.header("🛡️ GESTIÓN DE RIESGO")
balance = st.sidebar.number_input("Capital Cuenta (USD)", value=1000.0)
riesgo_usd = st.sidebar.number_input("Riesgo por Trade (USD)", value=10.0)
pips_sl = st.sidebar.number_input("Pips de Stop Loss (SL)", min_value=1.0, value=20.0, step=1.0)

def calcular_lotes_final(riesgo, pips, activo):
    if pips == 0: return 0
    if "JPY" in activo:
        return riesgo / (pips * 7.5) 
    else:
        # Nota: Para BTC verifica si tu broker usa 1 lote = 1 BTC.
        # Si es así, la fórmula genérica aplica razonablemente bien para distancias en USD.
        return riesgo / (pips * 10)

# --- 3. LEYENDAS Y GUÍAS ---
col_a, col_b = st.columns(2)
with col_a:
    with st.expander("🔥 LEYENDA: SEÑALES ALGORÍTMICAS", expanded=True):
        st.markdown("""
        * **POC (Etiqueta Roja):** Precio exacto donde hubo más volumen. Es un imán o un muro.
        * **Cuadro COMPRA/VENTA:** Diagnóstico de la IA para ese timeframe específico.
        * **🔥 FUEGO MAESTRO:** Señal especial que aparece solo si los 3 gráficos (5m, 15m, 1H) se alinean en la misma dirección.
        """)
with col_b:
    with st.expander("💎 ESCENARIOS DE ALTA PROBABILIDAD", expanded=True):
        st.markdown("""
        1. **Fuego Maestro:** Si ves el botón de fuego abajo de los gráficos, entra en esa dirección sin dudar.
        2. **Rebote Técnico:** El precio toca el número rojo (POC) y aparece un Diamante Azul 💠.
        3. **Ruptura de VWAP:** El precio cruza la línea cian con fuerza y el cuadro cambia de color.
        """)

# --- 4. ANÁLISIS DE MERCADO ---
# AQUI SE AGREGÓ BITCOIN
activos = {
    "Oro (Gold)": "GC=F", 
    "Yen (USD/JPY)": "USDJPY=X", 
    "Bitcoin (BTC)": "BTC-USD"
}

tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown(f"---")
    
    # UI DE CÁLCULO
    lote_sugerido = calcular_lotes_final(riesgo_usd, pips_sl, ticker)
    col_t, col_r = st.columns([2, 1])
    with col_t: st.subheader(f"📊 {nombre}")
    with col_r: st.success(f"**Lote Sugerido: {lote_sugerido:.2f}**")

    # CONTENEDOR DE SEÑALES PARA EL FUEGO MAESTRO
    consenso_tendencia = [] 

    try:
        # GRÁFICOS
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            if df.empty:
                continue

            # --- CÁLCULOS TÉCNICOS ---
            # POC (Point of Control)
            bins = 20
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            vol_by_bin = df.groupby('price_bin', observed=True)['Volume'].sum()
            poc_idx = vol_by_bin.idxmax()
            poc_price = (poc_idx.left + poc_idx.right) / 2
            
            # VWAP
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante (Volatilidad + Volumen)
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 2.0) and (last['Range'] < df['Range'].rolling(20).mean().iloc[-1])

            # DETERMINAR TENDENCIA LOCAL
            tendencia = "NEUTRO"
            color_box = "gray"
            if last['Close'] > last['VWAP']:
                tendencia = "COMPRA"
                color_box = "green"
                consenso_tendencia.append("COMPRA")
            else:
                tendencia = "VENTA"
                color_box = "red"
                consenso_tendencia.append("VENTA")

            # --- GRAFICADO ---
            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                # Precios y VWAP
                ax.plot(df.index, df['Close'], color='white', alpha=0.5, linewidth=1)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.6, linewidth=0.8)
                
                # 1. POC LÍNEA Y NÚMERO
                ax.axhline(y=poc_price, color='red', alpha=0.6, linewidth=1.5)
                ax.text(df.index[-1], poc_price, f'{poc_price:.2f}', 
                        color='red', fontsize=9, fontweight='bold', 
                        ha='left', va='center', backgroundcolor='#0e1117')

                # 2. CUADRO DE CONCLUSIÓN
                ax.text(0.05, 0.92, f'{tendencia}', transform=ax.transAxes, 
                        color='white', fontsize=10, fontweight='bold', 
                        bbox=dict(facecolor=color_box, alpha=0.7, boxstyle='round,pad=0.5'))

                # Diamante
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=100, marker='d', edgecolors='white', zorder=5)

                ax.set_title(f"TF: {tf} | {tendencia}", color="white", fontsize=10)
                ax.tick_params(axis='x', colors='gray', labelsize=6, rotation=45)
                ax.tick_params(axis='y', colors='gray', labelsize=6)
                ax.grid(color='gray', linestyle=':', linewidth=0.2, alpha=0.3)
                st.pyplot(fig)

        # --- LÓGICA DE FUEGO MAESTRO ---
        st.markdown("##### 🔮 Conclusión del Algoritmo:")
        
        col_res, col_void = st.columns([3,1])
        with col_res:
            if len(consenso_tendencia) == 3:
                if all(t == "COMPRA" for t in consenso_tendencia):
                    st.error("🔥🔥🔥 ¡FUEGO MAESTRO DETECTADO! ALINEACIÓN TOTAL DE COMPRA 🔥🔥🔥")
                    st.caption(f"Fuerte presión de compra en {nombre} (5m, 15m, 1h).")
                elif all(t == "VENTA" for t in consenso_tendencia):
                    st.error("🧊🧊🧊 ¡VENTA FUERTE CONFIRMADA! ALINEACIÓN TOTAL BAJISTA 🧊🧊🧊")
                    st.caption(f"Fuerte presión de venta en {nombre} (5m, 15m, 1h).")
                else:
                    st.info("⚖️ MERCADO MIXTO: Ten cuidado, los tiempos no coinciden.")
            else:
                st.warning("Datos insuficientes para cálculo maestro.")

    except Exception as e: 
        st.error(f"Error procesando {nombre}: {e}")

st.markdown("---")
st.caption("Control Maestro v8.1 | Algoritmo de Coherencia Institucional")
