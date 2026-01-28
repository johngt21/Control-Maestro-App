import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- PASO 1: CONSEGUIR LOS DATOS (EL MERCADO) ---
# Puedes cambiar "BTC-USD" por "EURUSD=X" o "GC=F" (Oro)
ticker = "BTC-USD" 
print(f"Buscando trampas en {ticker}...")
data = yf.download(ticker, period="60d", interval="1h")

# --- PASO 2: LAS 3 MANZANAS (LA LÓGICA) ---

# Manzana 1: Zonas de Liquidez (Donde están los Stops)
data['High_Retail'] = data['High'].shift(1).rolling(window=20).max()
data['Low_Retail'] = data['Low'].shift(1).rolling(window=20).min()

# Manzana 2: Detector de Mentiras (Volumen Relativo - RVOL)
data['Vol_Promedio'] = data['Volume'].rolling(window=20).mean()
data['RVOL'] = data['Volume'] / data['Vol_Promedio']

# Manzana 3: La Huella (Velas Wicky)
# Calculamos la mecha superior e inferior
data['Upper_Wick'] = data['High'] - data[['Open', 'Close']].max(axis=1)
data['Lower_Wick'] = data[['Open', 'Close']].min(axis=1) - data['Low']
data['Body'] = abs(data['Close'] - data['Open'])

# --- PASO 3: ENCONTRAR EL CRIMEN (LA SEÑAL) ---

# Señal de VENTA (Trampa de Toros / Bull Trap)
# 1. El precio rompió el techo anterior (High > High_Retail)
# 2. Hay mucho volumen (RVOL > 1.5)
# 3. La mecha de arriba es grande (Rechazo)
data['Trampa_Alcista'] = (
    (data['High'] > data['High_Retail']) & 
    (data['RVOL'] > 1.5) & 
    (data['Upper_Wick'] > data['Body']) # La mecha es más grande que el cuerpo
)

# Señal de COMPRA (Trampa de Osos / Bear Trap)
# 1. El precio rompió el suelo anterior
# 2. Hay mucho volumen
# 3. La mecha de abajo es grande
data['Trampa_Bajista'] = (
    (data['Low'] < data['Low_Retail']) & 
    (data['RVOL'] > 1.5) & 
    (data['Lower_Wick'] > data['Body'])
)

# --- PASO 4: DIBUJAR EL MAPA (VISUALIZACIÓN) ---

plt.figure(figsize=(14, 7))

# Dibujamos el precio
plt.plot(data.index, data['Close'], label='Precio', color='gray', alpha=0.5)

# Dibujamos las flechas donde tu estrategia detectó trampas
# Flechas ROJAS v hacia abajo (Vender)
trampas_arriba = data[data['Trampa_Alcista']]
plt.scatter(trampas_arriba.index, trampas_arriba['High'], color='red', marker='v', s=100, label='Trampa Retail (Venta)')

# Flechas VERDES ^ hacia arriba (Comprar)
trampas_abajo = data[data['Trampa_Bajista']]
plt.scatter(trampas_abajo.index, trampas_abajo['Low'], color='green', marker='^', s=100, label='Trampa Retail (Compra)')

plt.title(f'Estrategia Anti-Retail en {ticker}: Dónde liquidaron a la gente', fontsize=16)
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

print("Análisis terminado. Si ves flechas, ahí es donde tu estrategia brilló.")
