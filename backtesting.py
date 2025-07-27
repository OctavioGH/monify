import yfinance as yf
import pandas as pd
import numpy as np

# === Parámetros ===
ticker = "AAPL"           # Acción a analizar
start_date = "2020-01-01" # Fecha de inicio del backtest
end_date = "2025-07-01"   # Fecha de fin del backtest

def calcular_rsi(df, periodos=14):
    """Calcula el Índice de Fuerza Relativa (RSI)"""
    delta = df['Close'].diff()
    ganancia = delta.where(delta > 0, 0)
    perdida = -delta.where(delta < 0, 0)
    
    avg_ganancia = ganancia.ewm(alpha=1/periodos, adjust=False).mean()
    avg_perdida = perdida.ewm(alpha=1/periodos, adjust=False).mean()
    
    rs = avg_ganancia / avg_perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

def probar(ticker):

    # === Descargar datos de Yahoo Finance ===
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust = True)

    # === Calcular SMA 21 ===
    df["SMA21"] = df["Close"].rolling(window=21).mean().fillna(0)
    df["SMA50"] = df["Close"].rolling(window=50).mean().fillna(0)
    df["SMA200"] = df["Close"].rolling(window=200).mean().fillna(0)
    df['RSI'] = calcular_rsi(df, 14)

    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean().fillna(0)
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean().fillna(0)
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean().fillna(0)

    # ================================================================
    # 5. On-Balance Volume (OBV)
    # ================================================================
    # === Calcular OBV ===
    df["OBV"] = 0
    #df["Direction"] = np.where(df["Close"] > df["Close"].shift(1), 1, np.where(df["Close"] < df["Close"].shift(1), -1, 0))
    df['Direction'] = np.where(df['Close'].values > df['Close'].shift(1).values, 1)
    df['Direction'] = np.where(df['Close'].values < df['Close'].shift(1).values, -1)
    print(df['Direction'])
    
    df["OBV"] = (df["Volume"].values * df["Direction"].values).cumsum()

    # === Suavizar OBV con media móvil ===
    df["OBV_MA"] = df["OBV"].rolling(window=10).mean()

    """
    print(" ---------- Estrategia SMA21 ---------- ")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0

    for precio, sma in zip(df['Close'].values[21:], df['SMA21'].values[21:]):

        #print(f"Precio: {round(precio[0],2)} ; SMA21: {round(sma,2)}")

        if precio[0] > sma and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif precio[0] < sma and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            #print(ganancia)

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)}")

    print(" ---------- Estrategia SMA21 + RSI14 ---------- ")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0

    for precio, sma21, rsi in zip(df['Close'].values[21:], df['SMA21'].values[21:], df['RSI'].values[21:]):

        #print(f"Precio: {round(precio[0],2)} ; SMA21: {round(sma,2)}")

        if precio[0] > sma21 and rsi < 50 and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif precio[0] < sma21 and rsi > 50 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            #print(ganancia)

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)}")

    print(" ---------- Estrategia MACD ---------- ")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0

    for precio, signal, macd in zip(df['Close'].values[26:], df['MACD'].values[26:], df['Signal_Line'].values[26:]):

        #print(f"Precio: {round(precio[0],2)} ; SMA21: {round(sma,2)}")

        if macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif macd < signal and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            #print(ganancia)

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)}")
    """

    print("\n ---------- Estrategia SMA21 + RSI14 + MACD ---------- \n")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0

    for precio, sma21, rsi, macd, signal in zip(df['Close'].values[21:], df['SMA21'].values[21:], df['RSI'].values[21:], df['MACD'].values[26:], df['Signal_Line'].values[26:]):

        #print(f"Precio: {round(precio[0],2)} ; SMA21: {round(sma,2)}")

        if precio[0] > sma21 and rsi < 60 and macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif (precio[0] < sma21 or macd < signal) and rsi > 60 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            #print(ganancia)

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)}")
    """

    print("\n ---------- Estrategia SMA21 + RSI14 + MACD + Stop Loss---------- \n")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    precio_max = 0
    stop_loss = 0.30

    for precio, sma21, rsi, macd, signal in zip(df['Close'].values[21:], df['SMA21'].values[21:], df['RSI'].values[21:], df['MACD'].values[26:], df['Signal_Line'].values[26:]):

        #print(f"Precio: {round(precio[0],2)} ; SMA21: {round(sma,2)}")

        if precio[0] > sma21 and rsi < 60 and macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif (precio[0] < sma21 or macd < signal) and rsi > 60 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            #print(ganancia)

        if compre:
            if precio[0] > precio_max:
                precio_max = precio[0]
            elif (precio_max - precio[0]) > (precio_max*stop_loss):
                #print("Stop_loss")
                compre = False
                cantidad_ventas += 1
                ganancia += (precio[0] - precio_compra)
                precio_max = 0

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)}")

    """

    return ganancia

# Leer tickers desde archivo
print("Iniciando programa...")

archivo_tickers = "config/watchlist.txt"  # Cambia al nombre de tu archivo

try:
    with open(archivo_tickers, 'r') as f:
        tickers = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {archivo_tickers}")
    exit()

print("Analizando acciones...")
ganancia = 0
for ticker in tickers:
    print(f"\n \n Analizando {ticker}")

    ganancia += probar(ticker)

ganancia_prom = (ganancia / len(tickers))

print(f"\n Ganancia total: {ganancia}")
print(f"Ganancia promedio: {ganancia_prom}")