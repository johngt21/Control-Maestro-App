import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Configuracion de pagina - DEBE IR PRIMERO
st.set_page_config(page_title="Control Maestro v9.0", layout="wide", page_icon="🔥")

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

st.title("🎛️ Control Maestro v9.0: ARIMA + GARCH + Analisis Tecnico")

# --- 2. LEYENDA UNICA EXPLICATIVA (PARA DUMMIES) ---
with st.expander("📖 GUIA RAPIDA: Que significa todo esto? (Lee esto primero)", expanded=True):
    st.markdown("""
### 🎯 Este sistema te ayuda a decidir si COMPRAR, VENDER o ESPERAR

| Elemento | Que es | Como usarlo |
|----------|--------|-------------|
| **POC (Linea Roja)** | El precio donde hubo MAS compradores y vendedores. | Si el precio esta cerca, puede rebotar o romper con fuerza. |
| **VWAP (Linea Cyan)** | Precio promedio ponderado por volumen del dia. | Precio ARRIBA = alcista. Precio ABAJO = bajista. |
| **Diamante Azul** | Senal de posible reversion. Hay mucho volumen pero poca volatilidad. | El precio podria cambiar de direccion pronto. |
| **ARIMA** | Modelo que predice el precio futuro basado en patrones pasados. | Flecha verde = sube. Flecha roja = baja. |
| **GARCH** | Mide que tan volatil estara el mercado. | Volatilidad ALTA = peligro. Volatilidad BAJA = mas seguro. |
| **FUEGO MAESTRO** | Senal cuando 5m, 15m y 1H coinciden en la misma direccion. | Esta es la senal mas fuerte! |

---

### ⚡ REGLAS SIMPLES PARA OPERAR:

1. **Si ves FUEGO MAESTRO** -> Considera entrar en esa direccion
2. **Si ARIMA dice SUBE + GARCH bajo** -> Buena oportunidad de COMPRA
3. **Si ARIMA dice BAJA + GARCH bajo** -> Buena oportunidad de VENTA  
4. **Si GARCH es MUY ALTO** -> CUIDADO! Reduce tu riesgo
5. **Si los timeframes no coinciden** -> NO OPERES, espera alineacion

*Recuerda: Ningun sistema es 100% efectivo. Siempre usa stop loss.*
""")

# --- 3. FUNCIONES DE ARIMA Y GARCH ---

# Importar ARIMA y GARCH con manejo de errores
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_DISPONIBLE = True
except ImportError:
    ARIMA_DISPONIBLE = False
    st.warning("⚠️ statsmodels no instalado. ARIMA no disponible. Instala con: pip install statsmodels")

try:
    from arch import arch_model
    GARCH_DISPONIBLE = True
except ImportError:
    GARCH_DISPONIBLE = False
    st.warning("⚠️ arch no instalado. GARCH no disponible. Instala con: pip install arch")

def calcular_arima(precios, periodos_prediccion=5):
    """
    ARIMA: Predice precios futuros basandose en patrones historicos.
    """
    if not ARIMA_DISPONIBLE:
        return None
    try:
        precios_clean = precios.dropna()
        if len(precios_clean) < 30:
            return None
        
        model = ARIMA(precios_clean, order=(2, 1, 2))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periodos_prediccion)
        
        ultimo_precio = float(precios_clean.iloc[-1])
        prediccion_final = float(forecast.iloc[-1])
        
        direccion = "SUBE 📈" if prediccion_final > ultimo_precio else "BAJA 📉"
        cambio_porcentual = ((prediccion_final - ultimo_precio) / ultimo_precio) * 100
        
        return {
            "prediccion": prediccion_final,
            "direccion": direccion,
            "cambio_pct": cambio_porcentual
        }
    except Exception as e:
        return None

def calcular_garch(retornos):
    """
    GARCH: Predice la volatilidad futura del mercado.
    """
    if not GARCH_DISPONIBLE:
        return None
    try:
        retornos_clean = retornos.dropna() * 100
        
        if len(retornos_clean) < 50:
            return None
        
        model = arch_model(retornos_clean, vol='Garch', p=1, q=1, mean='Zero', rescale=False)
        model_fit = model.fit(disp='off', show_warning=False)
        
        forecast = model_fit.forecast(horizon=5)
        volatilidad_predicha = float(np.sqrt(forecast.variance.values[-1, -1]))
        
        volatilidad_historica = float(retornos_clean.std())
        
        if volatilidad_predicha > volatilidad_historica * 1.5:
            nivel = "🔴 MUY ALTA"
        elif volatilidad_predicha > volatilidad_historica:
            nivel = "🟠 ALTA"
        elif volatilidad_predicha > volatilidad_historica * 0.5:
            nivel = "🟢 NORMAL"
        else:
            nivel = "🔵 BAJA"
        
        return {
            "volatilidad": volatilidad_predicha,
            "nivel": nivel
        }
    except Exception as e:
        return None

# --- 4. ANALISIS DE MERCADO ---
activos = {
    "🥇 Oro (Gold)": "GC=F", 
    "💴 Yen (USD/JPY)": "USDJPY=X", 
    "₿ Bitcoin (BTC/USD)": "BTC-USD"
}

tfs = {"5m": "2d", "15m": "5d", "1h": "30d"}

for nombre, ticker in activos.items():
    st.markdown("---")
    st.subheader(nombre)
    
    consenso_tendencia = [] 

    try:
        # Datos para ARIMA y GARCH (1 hora, 60 dias)
        df_analisis = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df_analisis.columns, pd.MultiIndex):
            df_analisis.columns = df_analisis.columns.get_level_values(0)
        
        if not df_analisis.empty and len(df_analisis) > 50:
            col_arima, col_garch = st.columns(2)
            
            with col_arima:
                resultado_arima = calcular_arima(df_analisis['Close'])
                if resultado_arima:
                    st.metric(
                        label="🔮 ARIMA - Prediccion",
                        value=f"${resultado_arima['prediccion']:.2f}",
                        delta=f"{resultado_arima['cambio_pct']:.2f}% {resultado_arima['direccion']}"
                    )
                else:
                    st.info("🔮 ARIMA: Calculando...")
            
            with col_garch:
                retornos = df_analisis['Close'].pct_change()
                resultado_garch = calcular_garch(retornos)
                if resultado_garch:
                    st.metric(
                        label="📉 GARCH - Volatilidad",
                        value=f"{resultado_garch['volatilidad']:.2f}%",
                        delta=resultado_garch['nivel']
                    )
                else:
                    st.info("📉 GARCH: Calculando...")

        # Graficos por timeframe
        cols = st.columns(3)
        for idx, (tf, per) in enumerate(tfs.items()):
            df = yf.download(ticker, period=per, interval=tf, progress=False)
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            
            if df.empty or len(df) < 10:
                with cols[idx]:
                    st.warning(f"Sin datos para {tf}")
                continue

            # POC (Point of Control)
            try:
                bins = 20
                df['price_bin'] = pd.cut(df['Close'], bins=bins)
                vol_by_bin = df.groupby('price_bin', observed=True)['Volume'].sum()
                poc_idx = vol_by_bin.idxmax()
                poc_price = float((poc_idx.left + poc_idx.right) / 2)
            except:
                poc_price = float(df['Close'].mean())
            
            # VWAP
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # Diamante (alta volumen, baja volatilidad)
            df['RVOL'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['Range'] = df['High'] - df['Low']
            last = df.iloc[-1]
            
            try:
                rvol_val = float(last['RVOL']) if not pd.isna(last['RVOL']) else 0
                range_val = float(last['Range']) if not pd.isna(last['Range']) else 0
                range_mean = float(df['Range'].rolling(20).mean().iloc[-1]) if not pd.isna(df['Range'].rolling(20).mean().iloc[-1]) else range_val
                es_diamante = (rvol_val > 2.0) and (range_val < range_mean)
            except:
                es_diamante = False

            # Determinar tendencia
            tendencia = "NEUTRO"
            color_box = "gray"
            try:
                close_val = float(last['Close'])
                vwap_val = float(last['VWAP'])
                if close_val > vwap_val:
                    tendencia = "COMPRA"
                    color_box = "green"
                    consenso_tendencia.append("COMPRA")
                else:
                    tendencia = "VENTA"
                    color_box = "red"
                    consenso_tendencia.append("VENTA")
            except:
                consenso_tendencia.append("NEUTRO")

            # Graficar
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

                ax.text(0.05, 0.92, tendencia, transform=ax.transAxes, 
                        color='white', fontsize=10, fontweight='bold', 
                        bbox=dict(facecolor=color_box, alpha=0.7, boxstyle='round,pad=0.5'))

                if es_diamante:
                    ax.scatter(df.index[-1], float(df['Close'].iloc[-1]), 
                              color='#00d4ff', s=100, marker='d', 
                              edgecolors='white', zorder=5)

                ax.set_title(f"TF: {tf} | {tendencia}", color="white", fontsize=10)
                ax.tick_params(axis='x', colors='gray', labelsize=6, rotation=45)
                ax.tick_params(axis='y', colors='gray', labelsize=6)
                ax.grid(color='gray', linestyle=':', linewidth=0.2, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        # Conclusion
        st.markdown("##### 🔮 Conclusion del Algoritmo:")
        
        if len(consenso_tendencia) == 3:
            if all(t == "COMPRA" for t in consenso_tendencia):
                st.success("🔥🔥🔥 FUEGO MAESTRO DETECTADO! ALINEACION TOTAL DE COMPRA 🔥🔥🔥")
                st.caption(f"Fuerte presion de compra en {nombre} (5m, 15m, 1h).")
            elif all(t == "VENTA" for t in consenso_tendencia):
                st.error("🧊🧊🧊 VENTA FUERTE CONFIRMADA! ALINEACION TOTAL BAJISTA 🧊🧊🧊")
                st.caption(f"Fuerte presion de venta en {nombre} (5m, 15m, 1h).")
            else:
                st.info("⚖️ MERCADO MIXTO: Los tiempos no coinciden. Espera mejor alineacion.")
        else:
            st.warning("Datos insuficientes para calculo maestro.")

    except Exception as e: 
        st.error(f"Error procesando {nombre}: {e}")

st.markdown("---")
st.caption("Control Maestro v9.0 | ARIMA + GARCH + Analisis Tecnico Institucional")
