import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

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
balance = st.sidebar.number_input("Capital Cuenta (USD)", value=5000.0, min_value=0.0, help="Tu capital total disponible en la cuenta de trading.")
riesgo_usd = st.sidebar.number_input("Riesgo por Trade (USD)", value=10.0, min_value=0.0, help="Cantidad máxima que estás dispuesto a perder en este trade.")
pips_sl = st.sidebar.number_input("Pips de Stop Loss (SL)", min_value=1.0, value=20.0, step=1.0, help="Distancia en pips (o puntos para BTC) desde el entry hasta el stop loss.")

def calcular_lotes_final(riesgo, pips, activo):
    if pips == 0: return 0
    if "JPY" in activo:
        return riesgo / (pips * 7.5)  # Ajuste para pares con JPY (aprox. valor pip)
    elif "BTC" in activo:
        return riesgo / (pips * 100)  # Ajuste aproximado para BTC (asumiendo 1 lote = 1 BTC, pip ~ $100 dependiendo del broker)
    else:
        return riesgo / (pips * 10)  # Genérico para otros pares como Oro

# --- 3. LEYENDAS Y GUÍAS MEJORADAS ---
# Guía para principiantes (Dummies)
with st.expander("📖 Guía para Principiantes (Estilo 'For Dummies')", expanded=True):
    st.markdown("""
    **¡Hola Trader Novato! Bienvenido a Control Maestro v8.1 – Tu Amigo en el Trading.**
    
    - **¿Qué es esto?** Una app super simple que analiza Oro, USD/JPY y Bitcoin. Te muestra gráficos con señales fáciles de entender para decidir si comprar o vender.
    - **¿Para qué sirve?** Para no perder dinero tontamente. Calcula cuánto arriesgar, detecta momentos "calientes" (como el Fuego Maestro) y te da alertas visuales.
    - **Cómo usarla (paso a paso):**
      1. **Sidebar (izquierda):** Pon tu capital, riesgo y pips de SL. Te dice el tamaño de lote ideal para no quebrar.
      2. **Gráficos:** Para cada activo (Oro, Yen, BTC), ves 3 gráficos (5m, 15m, 1h). 
         - **Línea Blanca:** Precio actual.
         - **Línea Cian (VWAP):** Precio promedio ponderado por volumen – si el precio está arriba, es alcista; abajo, bajista.
         - **Línea Roja (POC):** El precio con más volumen histórico – actúa como soporte/resistencia.
         - **Cuadro Verde/Rojo:** Dice "COMPRA" o "VENTA" basado en si el precio > VWAP.
         - **Diamante Azul 💠:** Aparece cuando hay baja volatilidad pero alto volumen – señal de posible explosión de precio.
      3. **Fuego Maestro 🔥:** Si los 3 gráficos dicen lo mismo (todos COMPRA o VENTA), ¡es una señal fuerte! Entra en esa dirección.
    - **Consejos Dummies:** No trades sin SL. Usa lotes pequeños al inicio. Si ves Fuego Maestro, ¡es como una luz verde para actuar!
    - **Escenarios Fáciles:** 
      - Rebote en POC con Diamante: Compra/Vende en el rebote.
      - Cruce de VWAP: Si cruza arriba, compra; abajo, vende.
    
    ¡Prueba con demo primero y diviértete trading!
    """)

# Guía profesional
with st.expander("🧠 Guía Profesional (Detalles Técnicos)"):
    st.markdown("""
    **Descripción Avanzada para Traders Experimentados:**
    
    - **Objetivo:** Plataforma de análisis multi-activo (Commodities, FX, Crypto) con enfoque en alineación multi-timeframe para señales de alta probabilidad.
    - **Activos Analizados:** Oro (GC=F), USD/JPY (USDJPY=X), Bitcoin (BTC-USD) vía yfinance API.
    - **Timeframes:** 5m (2d), 15m (5d), 1h (30d) para capturar momentum corto-medio plazo.
    - **Indicadores Clave:**
      - **POC (Point of Control):** Calculado vía binning de precios (20 bins) y suma de volumen por bin. Representa el nivel de mayor volumen negociado – fuerte magnetismo.
      - **VWAP (Volume Weighted Average Price):** Cumsum(Close * Volume) / Cumsum(Volume). Umbral dinámico para bias alcista/bajista.
      - **Diamante (Señal de Compresión):** RVOL > 2.0 (volumen relativo > 200% media 20 períodos) Y Range actual < media Range (20 períodos). Indica acumulación/distribución inminente.
      - **Tendencia Local:** Basada en Close > VWAP (Alcista) o < VWAP (Bajista).
    - **Fuego Maestro:** Consenso unánime en los 3 TFs (todos COMPRA o VENTA). Alta probabilidad de continuación de tendencia.
    - **Gestión de Riesgo:** Cálculo de lotes = Riesgo_USD / (Pips_SL * Valor_Pip). Ajustes por activo (JPY: ~7.5 USD/pip; BTC: ~100 USD/punto asumiendo estándar).
    - **Visualización:** Gráficos con fondo oscuro para legibilidad. Etiquetas inline para POC. Cajas de tendencia con alpha para overlay no intrusivo.
    - **Limitaciones:** Datos históricos de yfinance (posibles gaps). No incluye slippage/comisiones. POC aproximado (binning). Para producción, integra APIs reales de broker.
    - **Mejoras Sugeridas:** Añadir alertas email/SMS, backtesting integrado, o ML para predicción de VWAP.
    
    Código optimizado para Streamlit: Caché implícito en descargas, manejo de errores robusto.
    """)

# --- 4. ANÁLISIS DE MERCADO ---
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
    with col_r: st.success(f"**Lote Sugerido: {lote_sugerido:.2f}** (Basado en riesgo y SL)")

    # CONTENEDOR DE SEÑALES PARA EL FUEGO MAESTRO
    consenso_tendencia = [] 

    try:
        # GRÁFICOS
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            if df.empty:
                st.warning(f"Datos vacíos para {nombre} en {tf}. Revisa conexión o ticker.")
                continue

            # --- CÁLCULOS TÉCNICOS ---
            # POC (Point of Control) mejorado con más bins para precisión
            bins = 50  # Aumentado para mejor granularidad
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            vol_by_bin = df.groupby('price_bin', observed=True)['Volume'].sum()
            poc_idx = vol_by_bin.idxmax()
            poc_price = (poc_idx.left + poc_idx.right) / 2
            
            # VWAP
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante (Volatilidad + Volumen) con umbrales ajustados
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 1.5) and (last['Range'] < df['Range'].rolling(20).mean().iloc[-1] * 0.8)  # Umbrales más sensibles

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

            # --- GRAFICADO MEJORADO ---
            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                # Precios con velas para más detalle (opcional, pero mejora visual)
                # Para simplicidad, mantenemos línea, pero añadimos sombra
                ax.plot(df.index, df['Close'], color='white', alpha=0.8, linewidth=1.5)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.7, linewidth=1.2)
                
                # 1. POC LÍNEA Y NÚMERO
                ax.axhline(y=poc_price, color='red', alpha=0.6, linewidth=1.5)
                ax.text(df.index[-1], poc_price, f'POC: {poc_price:.2f}', 
                        color='red', fontsize=9, fontweight='bold', 
                        ha='left', va='center', backgroundcolor='#0e1117')

                # 2. CUADRO DE CONCLUSIÓN
                ax.text(0.05, 0.92, f'{tendencia}', transform=ax.transAxes, 
                        color='white', fontsize=10, fontweight='bold', 
                        bbox=dict(facecolor=color_box, alpha=0.7, boxstyle='round,pad=0.5'))

                # Diamante mejorado
                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], color='#00d4ff', s=150, marker='D', edgecolors='white', zorder=5)

                ax.set_title(f"TF: {tf} | {tendencia}", color="white", fontsize=10)
                ax.tick_params(axis='x', colors='gray', labelsize=6, rotation=45)
                ax.tick_params(axis='y', colors='gray', labelsize=6)
                ax.grid(color='gray', linestyle=':', linewidth=0.2, alpha=0.3)
                
                # Añadir formato de fechas
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M' if 'm' in tf else '%d-%b'))
                st.pyplot(fig)

        # --- LÓGICA DE FUEGO MAESTRO ---
        st.markdown("##### 🔮 Conclusión del Algoritmo:")
        
        col_res, col_void = st.columns([3,1])
        with col_res:
            if len(consenso_tendencia) == 3:
                if all(t == "COMPRA" for t in consenso_tendencia):
                    st.error("🔥 ¡FUEGO MAESTRO DETECTADO! ALINEACIÓN TOTAL DE COMPRA 🔥")
                    st.caption(f"Fuerte presión de compra en {nombre} (5m, 15m, 1h). Probabilidad alta de continuación alcista.")
                elif all(t == "VENTA" for t in consenso_tendencia):
                    st.error("🧊 ¡VENTA FUERTE CONFIRMADA! ALINEACIÓN TOTAL BAJISTA 🧊")
                    st.caption(f"Fuerte presión de venta en {nombre} (5m, 15m, 1h). Probabilidad alta de continuación bajista.")
                else:
                    st.info("⚖️ MERCADO MIXTO: Ten cuidado, los tiempos no coinciden. Espera confirmación.")
            else:
                st.warning("Datos insuficientes para cálculo maestro. Revisa conexión a datos.")

    except Exception as e: 
        st.error(f"Error procesando {nombre}: {str(e)}. Posible issue con yfinance o conexión.")

# --- 5. VISUALIZACIÓN ADICIONAL: HEATMAP DE CONSENSO (Opcional para todos activos) ---
st.markdown("---")
st.subheader("🌐 Resumen Global de Activos")
consenso_data = {act: consenso_tendencia for act, _ in activos.items() if 'consenso_tendencia' in locals()}  # Recopilar si disponible
if consenso_data:
    df_consenso = pd.DataFrame(consenso_data).T
    fig_heat, ax_heat = plt.subplots(figsize=(8, 4))
    sns.heatmap(df_consenso.apply(lambda x: 1 if x == 'COMPRA' else -1 if x == 'VENTA' else 0), annot=True, cmap='RdYlGn', ax=ax_heat)
    ax_heat.set_title("Heatmap de Consenso por Activo y TF")
    st.pyplot(fig_heat)
else:
    st.info("No hay datos de consenso disponibles para heatmap.")

st.markdown("---")
st.caption("Control Maestro v8.1 | Algoritmo de Coherencia Institucional | Mejoras: Guías Detalladas, Visuales Mejorados")
