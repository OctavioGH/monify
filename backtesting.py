import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import core

# === Parámetros ===
ticker = "AAPL.BA"           # Acción a analizar
start_date = "2020-01-01" # Fecha de inicio del backtest
end_date = "2025-07-01"   # Fecha de fin del backtest
RUTA_DATOS = "data/historicos_acciones/"

def calcular_sma(data, periodos:int):
    return ta.SMA(data['Close'].values.astype(np.float64), timeperiod=periodos)

def calcular_macd(data, periodo_corto = 12, periodo_largo = 26, periodo_señal = 9):
    macd, macd_signal, macdhist = ta.MACD(data['Close'].values.astype(np.float64), periodo_corto, periodo_largo, periodo_señal)
    return macd, macd_signal

def calcular_rsi(data, periodos = 14):
    return ta.RSI(data['Close'].values.astype(np.float64), timeperiod=periodos)

def calcular_obv(data):
    obv = ta.OBV(data['Close'].values.astype(np.float64), data['Volume'].values.astype(np.float64))
    obv_ma = ta.SMA(obv, timeperiod=10)

    return obv, obv_ma

def calcular_adx(data, periodos=14):
    return ta.ADX(data['High'].values.astype(np.float64), data['Low'].values.astype(np.float64), data['Close'].values.astype(np.float64), timeperiod=periodos)

def calcular_bandas_bollinger(data, length=20, mult=2):
    # Bollinger Bands con TA-Lib
    upper_bb, middle_bb, lower_bb = ta.BBANDS(
        data['Close'].values.astype(np.float64),
        timeperiod=length,
        nbdevup=mult,
        nbdevdn=mult,
        matype=0
    )

    """
    # ATR con TA-Lib
    atr = ta.ATR(
        df['High'].values.astype(np.float64),
        df['Low'].values.astype(np.float64),
        df['Close'].values.astype(np.float64),
        timeperiod=length
    )

    # Keltner Channels (SMA ± mult * ATR)
    sma = ta.SMA(df['Close'].values.astype(np.float64), timeperiod=length)
    upper_kc = sma + mult * atr
    lower_kc = sma - mult * atr
    """
    return upper_bb, middle_bb, lower_bb

def probar(df):

    # === Descargar datos de Yahoo Finance ===
    #df = yf.download(ticker, start=start_date, end=end_date, auto_adjust = True)

    # === Calcular SMA 21 ===
    df["SMA21"] = calcular_sma(df, 21)
    #df["SMA50"] = calcular_sma(df, 21)
    #df["SMA200"] = calcular_sma(df, 21)
    df['RSI'] = calcular_rsi(df, 14)

    df['MACD'], df['Signal_Line'] = calcular_macd(df)

    # ================================================================
    # 5. On-Balance Volume (OBV)
    # ================================================================
    df["OBV"], df["OBV_10"] = calcular_obv(df)

    df['upper_bb'], df['middle_bb'], df['lower_bb'] = calcular_bandas_bollinger(df)

    # ================================================================
    # ADX
    # ================================================================
    df['ADX'] = calcular_adx(df)

    #print("\n ---------- Estrategia SMA21 + RSI14 + MACD ---------- \n")

    ganancia_old = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_positivo_old = 0
    trade_negativo_old = 0

    inicio = 26

    for precio, sma21, rsi, macd, signal, obv, obvma in zip(df['Close'].values[26:].astype(np.float64), df['SMA21'].values[26:], df['RSI'].values[26:], df['MACD'].values[26:], df['Signal_Line'].values[26:], df['OBV'].values[26:], df['OBV_10'].values[26:]):

        if precio > sma21 and rsi < 60 and macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio
        elif (precio < sma21 or macd < signal) and rsi > 60 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia_old += (precio - precio_compra)
            if (precio - precio_compra) > 0:
                trade_positivo_old += 1
            else:
                trade_negativo_old += 1

    #print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia_old,2)} ; Trade pos: {trade_positivo_old} ; Trade neg: {trade_negativo_old}")

    #print("\n ---------- Estrategia SMA21 + RSI14 + MACD + OBV10 + ADX---------- \n")

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_positivo = 0
    trade_negativo = 0

    stop_loss = 0
    precio_max = 0

    precio_viejo = float(df['Close'].iloc[inicio])

    tolerancia = 0.01

    simultaneo = 0

    for precio, sma21, rsi, macd, signal, obv, obvma, adx, upper, middle, lower in zip(df['Close'].values[inicio:].astype(np.float64), df['SMA21'].values[inicio:], df['RSI'].values[inicio:], df['MACD'].values[inicio:], df['Signal_Line'].values[inicio:], df['OBV'].values[inicio:], df['OBV_10'].values[inicio:], df['ADX'].values[inicio:], df['upper_bb'].values[inicio:], df['middle_bb'].values[inicio:], df['lower_bb'].values[inicio:]):

        compra_sma = precio > sma21
        compra_macd = macd > signal
        compra_obv = (precio > precio_viejo and obv > obvma)
        compra_rsi = (rsi < 60 and rsi > 30)
        compra_adx = adx > 25
        compra_bollinger = (abs(precio - lower) < (lower*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))
        
        venta_sma = precio < sma21
        venta_macd = macd < signal
        venta_obv = (precio < precio_viejo and obv < obvma)
        venta_rsi = rsi > 70
        venta_adx = adx > 25
        venta_bollinger = (abs(precio - upper) < (upper*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))
        
        if compra_bollinger and venta_bollinger:
            print(f"Precio: {precio} ; Upper: {upper} ; middle: {middle} ; lower: {lower}")
            print(f"Compro: {compra_bollinger} ; Vendo: {venta_bollinger}")
            simultaneo +=1

        if (compra_sma or compra_macd or compra_obv or compra_bollinger) and compra_rsi and compra_adx and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio
        elif (venta_sma or venta_macd or venta_obv or venta_bollinger) and venta_rsi and venta_adx and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio - precio_compra)
            if (precio - precio_compra) > 0:
                trade_positivo += 1
            else:
                trade_negativo += 1

        if compre and precio > precio_max:
            precio_max = precio

        precio_viejo = precio

    #print(f"N° Compras: {cantidad_compras} ; N° Ventas: {cantidad_ventas} ; Ganancias: {round(ganancia,2)} ; Trade pos: {trade_positivo} ; Trade neg: {trade_negativo}")
    #print(f"Simultaneo: {simultaneo}")

    return trade_positivo_old , trade_negativo_old , ganancia_old, trade_positivo , trade_negativo , ganancia

def descargar_datos(tickers):
    for index, ticker in enumerate(tickers):
        index += 1
        print(f"{index}/{len(tickers)} Descargando...")
        core.obtener_datos.descargar_datos(RUTA_DATOS, ticker, '5y')

if __name__ == "__main__":

    print("Iniciando programa...")
    RUTA_TICKERS = "data/lista_acciones.txt"  # Cambia al nombre de tu archivo

    try:
        with open(RUTA_TICKERS, 'r') as f:
            tickers = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {RUTA_TICKERS}")
        exit()

    # descargar_datos(tickers)

    #print("Analizando acciones...")
    trade_pos = 0
    trade_neg = 0
    ganancia = 0

    trade_pos_old = 0
    trade_neg_old = 0
    ganancia_old = 0

    for index, ticker in enumerate(tickers):
        index += 1
        #print(f"\n \n[{index}/{len(tickers)}]Analizando {ticker}")
        
        nombre_archivo = RUTA_DATOS+ticker.split('.')[0]+'.csv'
        data = core.obtener_datos.cargar_csv(nombre_archivo)
        data = data.drop(index=[0, 1]).reset_index(drop=True)

        trade_pos_old_aux , trade_neg_old_aux , aux_old , trade_pos_aux , trade_neg_aux , aux = probar(data)

        trade_pos += trade_pos_aux
        trade_neg += trade_neg_aux
        ganancia += aux

        trade_pos_old += trade_pos_old_aux
        trade_neg_old += trade_neg_old_aux
        ganancia_old += aux_old

    print("---------- Estrategia SMA21 and OBV10 (or MACD or Bollinger) and RSI14 and ADX ----------")
    print(f"Ganancia: {round(ganancia,2)} ; Trade pos: {trade_pos} ; Trade neg: {trade_neg} ; Error: {round(trade_neg/(trade_neg+trade_pos)*100,2)}%")
    print(f"Ganancia old: {round(ganancia_old,2)} ; Trade pos: {trade_pos_old} ; Trade neg: {trade_neg_old} ; Error: {round(trade_neg_old/(trade_neg_old+trade_pos_old)*100,2)}%")
    print(f"Diferencia: {round(ganancia - ganancia_old,2)} ; Dif %: {round((ganancia - ganancia_old)*100/ganancia_old,2)} ; Trade pos: {trade_pos - trade_pos_old} ; Trade neg: {trade_neg - trade_neg_old} ; N Trades: {trade_pos+trade_neg- trade_neg_old - trade_pos_old}")