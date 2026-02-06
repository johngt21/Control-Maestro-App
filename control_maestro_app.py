import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model
import warnings
warnings.filterwarnings('ignore')

# --- 1. SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Control Maestro v9.0 - Acceso Restringido", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

def password_entered():
    if st.session_state["password"] == "TU_CLAVE":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else: 
        st.session_state["password_correct"] = False

if not check_password(): 
    st.stop()

st.set_page_config(page_title="Control Maestro v9.0", layout="wide", page_icon="F")
st.title("Control Maestro v9.0: ARIMA + GARCH + Análisis Cuantitativo")

# --- 2. LEYENDA UNICA EXPLICATIVA (PARA DUMMIES) ---
with st.expander("GUIA RAPIDA: Que significa todo esto? (Lee esto primero)", expanded=True):
    st.markdown("""
    ### Este sistema te ayuda a decidir si COMPRAR, VENDER o ESPERAR
    
    **Que hace cada cosa?**
    
    | Elemento | Que es? | Como usarlo? |
    |----------|----------|---------------|
    | **POC (Linea Roja)** | El precio donde hubo MAS compradores y vendedores. | Si el precio esta cerca, puede rebotar o romper con fuerza. |
    | **VWAP (Linea Cyan)** | Precio promedio ponderado por volumen del dia. | Precio ARRIBA = tendencia alcista. Precio ABAJO = tendencia bajista. |
    | **Diamante Azul** | señal de posible reversion. Hay mucho volumen pero poca volatilidad. | Alerta! El precio podria cambiar de direccion pronto. |
    | **ARIMA** | Modelo estadistico que predice el precio futuro basado en patrones pasados. | Flecha verde = sube. Flecha roja = baja. |
    | **GARCH** | Mide que tan loco o volatil estara el mercado. | Volatilidad ALTA = peligro, usa menos dinero. Volatilidad BAJA = mas seguro. |
    | **FUEGO MAESTRO** | Señal especial cuando 5m, 15m y 1H coinciden en la misma direccion. | Esta es la señal mas fuerte. Considera entrar! |
    
    ---
    
    ### REGLAS SIMPLES PARA OPERAR:
    
    1. **Si ves FUEGO MAESTRO** -> Considera entrar en esa direccion
    2. **Si ARIMA dice SUBE + GARCH bajo** -> Buena oportunidad de COMPRA
    3. **Si ARIMA dice BAJA + GARCH bajo** -> Buena oportunidad de VENTA  
    4. **Si GARCH es MUY ALTO** -> CUIDADO! El mercado esta muy volatil, reduce tu riesgo
    5. **Si ves un Diamante** -> El precio podria cambiar de direccion, espera confirmacion
    6. **Si los timeframes no coinciden** -> NO OPERES, espera alineacion
    
    ---
    
    *Recuerda: Ningun sistema es 100% efectivo. Siempre usa stop loss y gestiona tu riesgo.*
    """)

# --- 3. FUNCIONES DE ARIMA Y GARCH ---
@st.cache_data(ttl=300)
def calcular_arima(precios, periodos_prediccion=5):
    """
    ARIMA: Predice precios futuros basandose en patrones historicos.
    Retorna la prediccion y la direccion esperada.
    """
    try:
        model = ARIMA(precios, order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periodos_prediccion)
        
        ultimo_precio = precios.iloc[-1]
        prediccion_final = forecast.iloc[-1]
        
        direccion = "SUBE" if prediccion_final > ultimo_precio else "BAJA"
        cambio_porcentual = ((prediccion_final - ultimo_precio) / ultimo_precio) * 100
        
        return {
            "prediccion": prediccion_final,
            "direccion": direccion,
            "cambio_pct": cambio_porcentual,
            "forecast_series": forecast
        }
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def calcular_garch(retornos):
    """
    GARCH: Predice la volatilidad futura del mercado.
    Volatilidad alta = mas riesgo. Volatilidad baja = mas estable.
    """
    try:
        retornos_clean = retornos.dropna() * 100
        
        if len(retornos_clean) < 30:
            return None
            
        model = arch_model(retornos_clean, vol='Garch', p=1, q=1, rescale=False)
        model_fit = model.fit(disp='off')
        
        forecast = model_fit.forecast(horizon=5)
        volatilidad_predicha = np.sqrt(forecast.variance.values[-1, -1])
        
        volatilidad_historica = retornos_clean.std()
        
        if volatilidad_predicha > volatilidad_historica * 1.5:
            nivel = "MUY ALTA"
            color = "red"
        elif volatilidad_predicha > volatilidad_historica:
            nivel = "ALTA"
            color = "orange"
        elif volatilidad_predicha > volatilidad_historica * 0.5:
            nivel = "NORMAL"
            color = "green"
        else:
            nivel = "BAJA"
            color = "blue"
        
        return {
            "volatilidad": volatilidad_predicha,
            "nivel": nivel,
            "color": color
        }
    except Exception as e:
        return None

# --- 4. ANALISIS DE MERCADO ---
activos = {
    "Oro (Gold)": "GC=F", 
    "Yen (USD/JPY)": "USDJPY=X", 
    "Bitcoin (BTC/USD)": "BTC-USD"
}

tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown(f"---")
    st.subheader(f"{nombre}")
    
    consenso_tendencia = [] 

    try:
        df_analisis = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df_analisis.columns, pd.MultiIndex):
            df_analisis.columns = df_analisis.columns.get_level_values(0)
        
        if not df_analisis.empty:
            col_arima, col_garch = st.columns(2)
            
            with col_arima:
                resultado_arima = calcular_arima(df_analisis['Close'])
                if resultado_arima:
                    st.metric(
                        label="ARIMA - Prediccion 5 periodos",
                        value=f"USD {resultado_arima['prediccion']:.2f}",
                        delta=f"{resultado_arima['cambio_pct']:.2f}% {resultado_arima['direccion']}"
                    )
                else:
                    st.warning("ARIMA no disponible")
            
            with col_garch:
                retornos = df_analisis['Close'].pct_change()
                resultado_garch = calcular_garch(retornos)
                if resultado_garch:
                    st.metric(
                        label="GARCH - Volatilidad Esperada",
                        value=f"{resultado_garch['volatilidad']:.2f}%",
                        delta=resultado_garch['nivel']
                    )
                else:
                    st.warning("GARCH no disponible")

        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            
            if df.empty:
                continue

            bins = 20
            df['price_bin'] = pd.cut(df['Close'], bins=bins)
            vol_by_bin = df.groupby('price_bin', observed=True)['Volume'].sum()
            poc_idx = vol_by_bin.idxmax()
            poc_price = (poc_idx.left + poc_idx.right) / 2
            
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            es_diamante = (last['RVOL'] > 2.0) and (last['Range'] < df['Range'].rolling(20).mean().iloc[-1])

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

            with cols[idx]:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                ax.plot(df.index, df['Close'], color='white', alpha=0.5, linewidth=1)
                ax.plot(df.index, df['VWAP'], color='cyan', linestyle='--', alpha=0.6, linewidth=0.8)
                
                ax.axhline(y=poc_price, color='red', alpha=0.6, linewidth=1.5)
                ax.text(df.index[-1], poc_price, f'{poc_price:.2f}', 
                        color='red', fontsize=9, fontweight='bold', 
                        ha='left', va='center', backgroundcolor='#0e1117')

                ax.text(0.05, 0.92, f'{tendencia}', transform=ax.transAxes, 
                        color='white', fontsize=10, fontweight='bold', 
                        bbox=dict(facecolor=color_box, alpha=0.7, boxstyle='round,pad=0.5'))

                if es_diamante:
                    ax.scatter(df.index[-1], df['Close'].iloc[-1], 
                              color='#00d4ff', s=100, marker='d', 
                              edgecolors='white', zorder=5)

                ax.set_title(f"TF: {tf} | {tendencia}", color="white", fontsize=10)
                ax.tick_params(axis='x', colors='gray', labelsize=6, rotation=45)
                ax.tick_params(axis='y', colors='gray', labelsize=6)
                ax.grid(color='gray', linestyle=':', linewidth=0.2, alpha=0.3)
                st.pyplot(fig)
                plt.close(fig)

        st.markdown("##### Conclusion del Algoritmo:")
        
        if len(consenso_tendencia) == 3:
            if all(t == "COMPRA" for t in consenso_tendencia):
                st.error("FUEGO MAESTRO DETECTADO! ALINEACION TOTAL DE COMPRA")
                st.caption(f"Fuerte presion de compra en {nombre} (5m, 15m, 1h).")
            elif all(t == "VENTA" for t in consenso_tendencia):
                st.error("VENTA FUERTE CONFIRMADA! ALINEACION TOTAL BAJISTA")
                st.caption(f"Fuerte presion de venta en {nombre} (5m, 15m, 1h).")
            else:
                st.info("MERCADO MIXTO: Los tiempos no coinciden. Espera mejor alineacion.")
        else:
            st.warning("Datos insuficientes para calculo maestro.")

    except Exception as e: 
        st.error(f"Error procesando {nombre}: {e}")

st.markdown("---")
st.caption("Control Maestro v9.0 | ARIMA + GARCH + Análisis Cuantitativo Institucional")

