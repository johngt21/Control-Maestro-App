import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from pmdarima import auto_arima
from arch import arch_model
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control Maestro v8", layout="wide")

# Título solicitado en tus instrucciones previas
st.title("💠 Escáner: Control Maestro v4") 
st.caption("Core Engine: v8 (AI & Statistical Forecast)")

# --- BARRA LATERAL (GESTIÓN) ---
st.sidebar.header("⚙️ Configuración v8")
ticker = st.sidebar.selectbox("Activo", ["GC=F", "USDJPY=X", "BTC-USD"])
periodo = st.sidebar.slider("Días de entrenamiento", 30, 200, 100)

# --- OBTENCIÓN DE DATOS ---
data = yf.download(ticker, period="6mo", interval="1d")
if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
df = data['Close'].dropna()

# --- MODELADO IA (ARIMA + GARCH) ---
st.subheader("🔮 Forecast de Alta Precisión")

with st.spinner("Entrenando modelos ARIMA y GARCH..."):
    # 1. ARIMA (Para la Tendencia/Precio)
    model_arima = auto_arima(df[-periodo:], seasonal=False, error_action='ignore')
    forecast_arima = model_arima.predict(n_periods=5)
    
    # 2. GARCH (Para la Volatilidad/Riesgo)
    # Calculamos retornos para el modelo de volatilidad
    returns = 100 * df[-periodo:].pct_change().dropna()
    model_garch = arch_model(returns, vol='Garch', p=1, q=1)
    res_garch = model_garch.fit(disp='off')
    forecast_vol = res_garch.forecast(horizon=5)
    
# --- VISUALIZACIÓN ---
col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    # Precio Histórico
    fig.add_trace(go.Scatter(x=df[-30:].index, y=df[-30:], name="Histórico", line=dict(color="white")))
    # Predicción
    future_dates = pd.date_range(df.index[-1], periods=6, freq='B')[1:]
    fig.add_trace(go.Scatter(x=future_dates, y=forecast_arima, name="ARIMA Forecast", line=dict(dash='dash', color='cyan')))
    
    fig.update_layout(title=f"Predicción de Tendencia para {ticker}", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("Volatilidad Esperada (GARCH)", f"{forecast_vol.variance.values[-1, -1]**0.5:.2f}%")
    st.write("### Interpretación v8")
    if forecast_arima[-1] > df.iloc[-1]:
        st.success("Tendencia: Alcista (Bullish)")
    else:
        st.error("Tendencia: Bajista (Bearish)")
        
    st.info("El modelo GARCH sugiere que el riesgo de mercado está " + 
            ("ALTO" if forecast_vol.variance.values[-1, -1] > returns.var() else "ESTABLE"))

# --- RECUERDO DE LEYENDAS (De tus chats previos) ---
with st.expander("📚 Leyendas de Control"):
    st.markdown("""
    * **Muro Rojo (POC):** Zona de máxima liquidez.
    * **Diamante Azul:** Atrapados detectados (Volumen + Rango).
    * **v8 AI:** Integración de ARIMA (Precio) y GARCH (Manejo de pánico/volatilidad).
    """)
