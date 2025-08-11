import pandas as pd
import yfinance as yf
import talib as ta
import numpy as np

def analizar_ticker(ticker):
	# Descargar datos históricos
	data = yf.download(ticker, period="12mo", progress=False, auto_adjust=True)

	if data.empty:
	    return None

	# Calcular indicadores técnicos
	ultimo_cierre = data['Close'].values[-1,0]
	precio_actual = yf.Ticker(ticker).info.get('regularMarketPrice')

	if ultimo_cierre == precio_actual:
		ultimo_cierre = data['Close'].values[-2,0]

	sma21 = calcular_sma(data, 21)
	sma50 = calcular_sma(data, 50)
	sma200 = calcular_sma(data, 200)
	rsi = calcular_rsi(data)
	macd, signal = calcular_macd(data)
	obv, obvma = calcular_obv(data)
	adx = calcular_adx(data)
	upper, middle, lower = calcular_bandas_bollinger(data)

	# Determinar señal
	señal = "Mantener"
	tolerancia = 0.01
	compra_sma = precio_actual > sma21
	compra_macd = macd > signal
	compra_obv = (precio_actual > ultimo_cierre and obv > obvma)
	compra_rsi = (rsi < 60 and rsi > 30)
	compra_adx = adx > 25
	compra_bollinger = (abs(precio_actual - lower) < (lower*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))

	venta_sma = precio_actual < sma21
	venta_macd = macd < signal
	venta_obv = (precio_actual < ultimo_cierre and obv < obvma)
	venta_rsi = rsi > 70
	venta_adx = adx > 25
	venta_bollinger = (abs(precio_actual - upper) < (upper*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))

	if (compra_sma or compra_macd or compra_bollinger or compra_obv ) and compra_rsi and compra_adx: #(9,59%)
		señal = "Comprar (3/5)"
		if compra_sma and compra_obv: #(0,00%)
			señal = "Comprar (5/5)"
		elif compra_obv: #(5,73%)
			señal = "Comprar (4/5)"
		elif compra_sma: #(7,81%)
			señal = "Comprar (3,5/5)"

	elif (venta_sma or venta_macd or venta_obv or venta_bollinger) and venta_rsi and venta_adx:
		señal = "Vender"

	return {
		'Ticker': ticker,
		'Señal': señal,
		'Cierre': round(precio_actual, 2),
		'SMA21': round(sma21, 2),
		'SMA50': round(sma50, 2),
		'SMA200': round(sma200, 2),
		'RSI14': round(rsi, 2),
		'MACD': (True if macd > signal else False),
		'ADX' : round(adx, 2)
	}

def calcular_sma(data, periodos:int):
	return ta.SMA(data['Close'].values[:,0], timeperiod=periodos)[-1]

def calcular_macd(data, periodo_corto = 12, periodo_largo = 26, periodo_señal = 9):
	macd, macd_signal, macdhist = ta.MACD(data['Close'].values[:,0], periodo_corto, periodo_largo, periodo_señal)
	return macd[-1], macd_signal[-1]

def calcular_rsi(data, periodos = 14):
	return ta.RSI(data['Close'].values[:,0], timeperiod=periodos)[-1]

def calcular_obv(data):
	obv = ta.OBV(data['Close'].values[:,0].astype(np.float64), data['Volume'].values[:,0].astype(np.float64))
	obv_ma = ta.SMA(obv, timeperiod=10)

	return obv[-1], obv_ma[-1]

def calcular_adx(data, periodos=14):
    return ta.ADX(data['High'].values[:,0], data['Low'].values[:,0], data['Close'].values[:,0], timeperiod=periodos)[-1]

def calcular_bandas_bollinger(data, length=20, mult=2):
    # Bollinger Bands con TA-Lib
	upper_bb, middle_bb, lower_bb = ta.BBANDS(
	    data['Close'].values[:,0],
	    timeperiod=length,
	    nbdevup=mult,
	    nbdevdn=mult,
	    matype=0
	)

	return upper_bb[-1], middle_bb[-1], lower_bb[-1]