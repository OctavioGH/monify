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
    df["OBV"] = 0  # Primer valor por defecto

    for i in range(1, len(df)):
        if df["Close"].iloc[i].item() > df["Close"].iloc[i - 1].item():
            df.loc[df.index[i], "OBV"] = df["OBV"].iloc[i - 1].item() + df["Volume"].iloc[i].item()
        elif df["Close"].iloc[i].item() < df["Close"].iloc[i - 1].item():
            df.loc[df.index[i], "OBV"] = df["OBV"].iloc[i - 1].item() - df["Volume"].iloc[i].item()
        else:
            df.loc[df.index[i], "OBV"] = df["OBV"].iloc[i - 1].item()

    df["OBV_10"] = df["OBV"].rolling(window=5).mean().fillna(0)

    print("\n ---------- Estrategia SMA21 + RSI14 + MACD ---------- \n")

    ganancia_old = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_positivo_old = 0
    trade_negativo_old = 0

    for precio, sma21, rsi, macd, signal, obv, obvma in zip(df['Close'].values[21:], df['SMA21'].values[21:], df['RSI'].values[21:], df['MACD'].values[26:], df['Signal_Line'].values[26:], df['OBV'].values[26:], df['OBV_10'].values[26:]):

        if precio[0] > sma21 and rsi < 60 and macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif (precio[0] < sma21 or macd < signal) and rsi > 60 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia_old += (precio[0] - precio_compra)
            if (precio[0] - precio_compra) > 0:
                trade_positivo_old += 1
            else:
                trade_negativo_old += 1

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia_old,2)} ; Trade pos: {trade_positivo_old} ; Trade neg: {trade_negativo_old}")

    print("\n ---------- Estrategia SMA21 + RSI14 + MACD + OBV10 ---------- \n")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_positivo = 0
    trade_negativo = 0

    stop_loss = 0
    precio_max = 0

    for precio, sma21, rsi, macd, signal, obv, obvma in zip(df['Close'].values[21:], df['SMA21'].values[21:], df['RSI'].values[21:], df['MACD'].values[26:], df['Signal_Line'].values[26:], df['OBV'].values[26:], df['OBV_10'].values[26:]):

        if precio[0] > sma21 and rsi < 60 and rsi > 30 and macd > signal and obv > obvma and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio[0]
        elif (precio[0] < sma21 or macd < signal) and rsi > 65 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio[0] - precio_compra)
            if (precio[0] - precio_compra) > 0:
                trade_positivo += 1
            else:
                trade_negativo += 1

        if compre and precio[0] > precio_max:
            precio_max = precio[0]

    print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)} ; Trade pos: {trade_positivo} ; Trade neg: {trade_negativo}")
   
    return trade_positivo_old , trade_negativo_old , ganancia_old, trade_positivo , trade_negativo , ganancia

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
trade_pos = 0
trade_neg = 0
ganancia = 0

trade_pos_old = 0
trade_neg_old = 0
ganancia_old = 0

i = 1
for ticker in tickers:
    print(f"\n \n[{i}/{len(tickers)}]Analizando {ticker}")
    i += 1

    trade_pos_old_aux , trade_neg_old_aux , aux_old , trade_pos_aux , trade_neg_aux , aux = probar(ticker)

    trade_pos += trade_pos_aux
    trade_neg += trade_neg_aux
    ganancia += aux

    trade_pos_old += trade_pos_old_aux
    trade_neg_old += trade_neg_old_aux
    ganancia_old += aux_old

print(f"\nGanancia: {round(ganancia,2)} ; Trade pos: {trade_pos} ; Trade neg: {trade_neg} ; Error: {round(trade_neg/(trade_neg+trade_pos)*100,2)}")
print(f"Ganancia old: {round(ganancia_old,2)} ; Trade pos: {trade_pos_old} ; Trade neg: {trade_neg_old} ; Error: {round(trade_neg_old/(trade_neg_old+trade_pos_old)*100,2)}")
