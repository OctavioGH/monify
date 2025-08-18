import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import core

# === Parámetros ===
RUTA_DATOS = "data/historicos_acciones/"
RUTA_TICKERS = "data/lista_acciones.txt" 

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
    return upper_bb, middle_bb, lower_bb

def calcular_keltner(data, periodos_klt = 20, periodos_atr = 14, mult = 1.5):
    # ATR con TA-Lib
    atr = ta.ATR(
        data['High'].values.astype(np.float64),
        data['Low'].values.astype(np.float64),
        data['Close'].values.astype(np.float64),
        timeperiod=periodos_atr
    )
    atr_ma = ta.SMA(atr, timeperiod=14)

    # Keltner Channels (SMA ± mult * ATR)
    ema = ta.EMA(data['Close'].values.astype(np.float64), timeperiod=periodos_klt)
    upper_kc = ema + mult * atr
    lower_kc = ema - mult * atr

    return upper_kc, ema, lower_kc, atr, atr_ma

def estrategia_clasica(df):
    #print("\n ---------- Estrategia Clásica (SMA21 + RSI14 + MACD) ---------- \n")

    resultado = {
    "ganancia_total" : 0,
    "trade_pos" : 0,
    "trade_neg" : 0,
    "trade_tot" : 0,
    }

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_pos = 0
    trade_neg = 0

    inicio = 26

    for precio, sma21, rsi, macd, signal, obv, obvma in zip(df['Close'].values[26:].astype(np.float64), df['SMA21'].values[26:], df['RSI'].values[26:], df['MACD'].values[26:], df['Signal_Line'].values[26:], df['OBV'].values[26:], df['OBV_10'].values[26:]):

        if precio > sma21 and rsi < 60 and macd > signal and not compre:
            compre = True
            cantidad_compras += 1
            precio_compra = precio
        elif (precio < sma21 or macd < signal) and rsi > 60 and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio - precio_compra)
            if (precio - precio_compra) > 0:
                trade_pos += 1
            else:
                trade_neg += 1

    resultado["ganancia_total"] = ganancia
    resultado["trade_pos"] = trade_pos
    resultado["trade_neg"] = trade_neg
    resultado["trade_tot"] = (trade_pos+trade_neg)

    return resultado

def estrategia_implementada(df):
    
    #print("\n ---------- Estrategia Nueva (SMA21 + RSI14 + MACD + OBV10 + ADX + Bollinger)---------- \n")

    resultado = {
    "ganancia_total" : 0,
    "trade_pos" : 0,
    "trade_neg" : 0,
    "trade_tot" : 0,
    }

    inicio = 26

    ganancia = 0
    compre = False
    precio_compra = 0
    cantidad_compras = 0
    cantidad_ventas = 0
    trade_pos = 0
    trade_neg = 0

    # Variables stop loss
    stop_loss = 0.05
    precio_max = 0
    bloqueo_stop_loss = 0
    BLOQUEO_STOP = 3
    venta_stop_loss = False

    precio_viejo = float(df['Close'].iloc[inicio])

    # Variables bandas Bollinger
    tolerancia = 0.01
    simultaneo = 0

    for precio, sma21, rsi, macd, signal, obv, obvma, adx, upper_bb, middle_bb, lower_bb,  upper_kc, ema, lower_kc, atr, atr_ma in zip(df['Close'].values[inicio:].astype(np.float64), df['SMA21'].values[inicio:], df['RSI'].values[inicio:], df['MACD'].values[inicio:], df['Signal_Line'].values[inicio:], df['OBV'].values[inicio:], df['OBV_10'].values[inicio:], df['ADX'].values[inicio:], df['upper_bb'].values[inicio:], df['middle_bb'].values[inicio:], df['lower_bb'].values[inicio:], df['upper_kc'].values[inicio:], df['middle_kc'].values[inicio:], df['lower_kc'].values[inicio:], df['ATR'].values[inicio:], df['ATR_MA'].values[inicio:]):

        # Condiciones de compra
        compra_rsi = (rsi < 60 and rsi > 30)
        compra_adx = adx > 25
        atr_alto = atr > atr_ma

        compra_sma = (precio > sma21) and compra_rsi and compra_adx
        compra_macd = (macd > signal) and compra_rsi and compra_adx
        compra_obv = (precio > precio_viejo and obv > obvma) and compra_rsi and compra_adx
        compra_bollinger = (abs(precio - lower_bb) < (lower_bb*tolerancia)) and upper_bb > middle_bb*(1+(2*tolerancia)) and lower_bb < middle_bb *(1+(2*tolerancia)) and compra_rsi and compra_adx

        compra_keltner = precio>upper_kc

        # Condiciones de venta
        venta_keltner = precio < lower_kc

        venta_rsi = rsi > 70
        venta_adx = adx > 25
        venta_sma = (precio < sma21) and venta_rsi and venta_adx and atr_alto
        venta_macd = (macd < signal) and venta_rsi and venta_adx and atr_alto
        venta_obv = (precio < precio_viejo and obv < obvma) and venta_rsi and venta_adx and atr_alto
        venta_bollinger = (abs(precio - upper_bb) < (upper_bb*tolerancia)) and upper_bb > middle_bb*(1+(2*tolerancia)) and lower_bb < middle_bb *(1+(2*tolerancia)) and venta_rsi and venta_adx and atr_alto

        # Manejo de stop loss
        if venta_stop_loss:
            bloqueo_stop_loss -= 1
            if bloqueo_stop_loss <= 0:
                venta_stop_loss = False
        elif compre and precio > precio_max:
            precio_max = precio
        elif compre and (precio_max - precio) > (precio_max*stop_loss):
            #print(f"Stop loss {abs(precio_max - precio)/precio} ; compra {precio_compra} ; Max {precio_max} ; precio {precio}")
            venta_stop_loss = True
            bloqueo_stop_loss = BLOQUEO_STOP
        
        # De haber coincidencia en las bandas de bollinger
        if compra_bollinger and venta_bollinger:
            print(f"Precio: {precio} ; upper_bb: {upper_bb} ; middle_bb: {middle_bb} ; lower_bb: {lower_bb}")
            print(f"Compro: {compra_bollinger} ; Vendo: {venta_bollinger}")
            simultaneo +=1

        # Determinación de compra o venta
        if (compra_sma or compra_macd or compra_obv or compra_bollinger) and not compre and not venta_stop_loss:
            compre = True
            cantidad_compras += 1
            precio_compra = precio
            precio_max = precio
        elif (venta_sma or venta_macd or venta_obv or venta_bollinger or (venta_stop_loss and venta_rsi and venta_adx and atr_alto)) and compre:
            compre = False
            cantidad_ventas += 1
            ganancia += (precio - precio_compra)
            if (precio - precio_compra) > 0:
                trade_pos += 1
            else:
                trade_neg += 1

        precio_viejo = precio # Guardo el precio del dia anterior

    resultado["ganancia_total"] = ganancia
    resultado["trade_pos"] = trade_pos
    resultado["trade_neg"] = trade_neg
    resultado["trade_tot"] = (trade_pos+trade_neg)

    return resultado

def estrategia_nueva(df):

    resultado = {
    "ganancia_total" : 0,
    "trade_pos" : 0,
    "trade_neg" : 0,
    "trade_tot" : 0,
    }

    inicio = 26

    compre = False
    precio_compra = 0

    ganancia = 0
    trade_pos = 0
    trade_neg = 0

    for index in range(inicio, df.shape[0]):
        
        # Métricas
        precio = float(df['Close'].loc[index])
        sma = df['SMA21'].loc[index]
        rsi = df['RSI'].loc[index]
        adx = df['ADX'].loc[index]
        macd = df['MACD'].loc[index]
        signal = df['Signal_Line'].loc[index]
        obv = df['OBV'].loc[index]
        obvma = df['OBV_10'].loc[index]
        atr = df['ATR'].loc[index]
        atrma = df['ATR_MA'].loc[index]

        # On-Balance Volume
        compra_obv = True if df['OBV'].loc[index] > df['OBV_10'].loc[index-1] and float(df['Close'].loc[index]) > float(df['Close'].loc[index-1]) else False
        venta_obv = True if df['OBV'].loc[index] < df['OBV_10'].loc[index-1] and float(df['Close'].loc[index]) < float(df['Close'].loc[index-1]) else False

        # Bandas de Bollinger
        upper_bb = df['upper_bb'].loc[index]
        middle_bb = df['middle_bb'].loc[index]
        lower_bb = df['lower_bb'].loc[index]
        
        tolerancia = 0.01
        compra_bollinger = (abs(precio - lower_bb) < (lower_bb*tolerancia)) and upper_bb > middle_bb*(1+(2*tolerancia)) and lower_bb < middle_bb *(1+(2*tolerancia))
        venta_bollinger = (abs(precio - upper_bb) < (upper_bb*tolerancia)) and upper_bb > middle_bb*(1+(2*tolerancia)) and lower_bb < middle_bb *(1+(2*tolerancia))

        # Determinación de compra o venta
        if ((rsi > 30 and rsi < 60) and adx > 25 and not compre):
            if (precio>sma and compra_obv):#if (precio > sma) and (macd > signal and compra_bollinger):
                compre = True
                precio_compra = precio
        elif (rsi > 70 and adx > 25 and atr > atrma and compre):
            if (precio < sma or macd < signal or venta_obv or venta_bollinger):
                compre = False
                ganancia += (precio - precio_compra)
                if (precio - precio_compra) > 0:
                    trade_pos += 1
                else:
                    trade_neg += 1

    resultado["ganancia_total"] = ganancia
    resultado["trade_pos"] = trade_pos
    resultado["trade_neg"] = trade_neg
    resultado["trade_tot"] = (trade_pos+trade_neg)

    return resultado

def probar(df):

    # ================================================================
    # Simple Moving Average
    # ================================================================
    df["SMA21"] = calcular_sma(df, 21)
    #df["SMA50"] = calcular_sma(df, 21)
    #df["SMA200"] = calcular_sma(df, 21)

    # ================================================================
    # Relative Strenght Index
    # ================================================================
    df['RSI'] = calcular_rsi(df, 14)

    # ================================================================
    # Moving Average Convergence Divergence
    # ================================================================
    df['MACD'], df['Signal_Line'] = calcular_macd(df)

    # ================================================================
    # 5. On-Balance Volume (OBV)
    # ================================================================
    df["OBV"], df["OBV_10"] = calcular_obv(df)

    # ================================================================
    # Bandas Bollinger
    # ================================================================
    df['upper_bb'], df['middle_bb'], df['lower_bb'] = calcular_bandas_bollinger(df)

    # ================================================================
    # ADX
    # ================================================================
    df['ADX'] = calcular_adx(df)

    # ================================================================
    # Keltner channels y ATR
    # ================================================================
    df['upper_kc'], df['middle_kc'], df['lower_kc'], df['ATR'], df['ATR_MA'] = calcular_keltner(df)
    
    resultados = []

    resultados.append(estrategia_clasica(df))
    resultados.append(estrategia_implementada(df))
    resultados.append(estrategia_nueva(df))
    
    return resultados

def descargar_datos(tickers):
    for index, ticker in enumerate(tickers):
        index += 1
        print(f"{index}/{len(tickers)} Descargando...")
        core.obtener_datos.descargar_datos(RUTA_DATOS, ticker, '5y')

if __name__ == "__main__":

    #print("Iniciando programa...")

    try:
        with open(RUTA_TICKERS, 'r') as f:
            tickers = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {RUTA_TICKERS}")
        exit()

    # descargar_datos(tickers)
    
    #print("Analizando acciones...")

    resultados = []

    cantidad_estrategias = 3
    resultados = {
        "ganancia_total" : [0] * cantidad_estrategias,
        "trade_pos" : [0] * cantidad_estrategias,
        "trade_neg" : [0] * cantidad_estrategias,
        "trade_tot" : [0] * cantidad_estrategias,
        "error" : [0] * cantidad_estrategias
    }

    for index, ticker in enumerate(tickers):
        index += 1
        #print(f"[{index}/{len(tickers)}]Analizando {ticker}")
        
        nombre_archivo = RUTA_DATOS+ticker.split('.')[0]+'.csv'
        data = core.obtener_datos.cargar_csv(nombre_archivo)
        data = data.drop(index=[0, 1]).reset_index(drop=True)

        respuestas = probar(data)

        for indice, respuesta in enumerate(respuestas):
            resultados["ganancia_total"][indice] += respuesta["ganancia_total"]
            resultados["trade_pos"][indice] += respuesta["trade_pos"]
            resultados["trade_neg"][indice] += respuesta["trade_neg"]
            resultados["trade_tot"][indice] += respuesta["trade_tot"]

    for indice in range(cantidad_estrategias):
        if resultados['trade_tot'][indice] != 0:
            resultados['error'][indice] = round(((resultados['trade_neg'][indice]*100)/resultados['trade_tot'][indice]),2)
        else:
            resultados['error'][indice] = 0
        print(f"Ganancia: {round(resultados['ganancia_total'][indice],2)} ; Trade tot: {resultados['trade_tot'][indice]} ; Trade pos: {resultados['trade_pos'][indice]} ; Trade neg: {resultados['trade_neg'][indice]} ; Error: {resultados['error'][indice]}%")
    
    #print(f"Diferencia: {round(ganancia - ganancia,2)} ; Dif %: {round((ganancia - ganancia)*100/ganancia,2)} ; Trade pos: {trade_pos - trade_pos_old} ; Trade neg: {trade_neg - trade_neg_old} ; N Trades: {trade_pos+trade_neg- trade_neg_old - trade_pos_old}")