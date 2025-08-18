import pandas as pd
import yfinance as yf
import talib as ta
import numpy as np

import pickle
from river import forest

RUTA_MODELO = "data/modelo_trading.pkl"

def analizar_ticker(ticker):

	print("Descargando...")
	# Descargar datos históricos
	data = yf.download(ticker, period="12mo", progress=False, auto_adjust=True)

	print("Analizando...")
	if data.empty:
	    return None

	# Calcular indicadores técnicos
	ultimo_cierre = data['Close'].values[-1,0]
	try:
		precio_actual = yf.Ticker(ticker).info.get('regularMarketPrice')
		if ultimo_cierre == precio_actual:
			ultimo_cierre = data['Close'].values[-2,0]
			#print(f"Ult. Cierre: {ultimo_cierre}")
	except:
		precio_actual = ultimo_cierre

	sma = calcular_sma(data, 21)

	rsi = calcular_rsi(data)

	macd, signal = calcular_macd(data)

	obv, obvma = calcular_obv(data)

	adx = calcular_adx(data)

	upper, middle, lower = calcular_bandas_bollinger(data)

	atr, atr_ma = calcular_atr(data)

	compra_obv = (precio_actual > ultimo_cierre and obv > obvma)
	venta_obv = (precio_actual < ultimo_cierre and obv < obvma)
	
	tolerancia = 0.01
	compra_bollinger = (abs(precio_actual - lower) < (lower*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))
	venta_bollinger = (abs(precio_actual - upper) < (upper*tolerancia)) and upper > middle*(1+(2*tolerancia)) and lower < middle *(1+(2*tolerancia))

	# Determinar señal
	señal = "Mantener"

	# Determinación de compra o venta
	# 4 Indicadores: SMA, MACD, Bollinger, OBV
	if (rsi > 30 and rsi < 60 and adx > 25): 
		señal = "Compra"
	elif (rsi > 70 and adx > 25 and atr > atr_ma):
	    if (precio_actual < sma or macd < signal or venta_obv or venta_bollinger):
	        señal = "Vender"
	
	
	caracteristicas = {
	    "cierre" : data['Close'].values[-1,0],
	    #"maximo" : data['High'].values[-1,0],
	    #"minimo" : data['Low'].values[-1,0],
	    #"volumen" : data['Volume'].values[-1,0],
	    #"cierre_1d" : data['Close'].values[-2,0],
	    #"maximo_1d" : data['High'].values[-2,0],
	    #"minimo_1d" : data['Low'].values[-2,0],
	    #"volumen_1d" : data['Volume'].values[-2,0],
	    #"cierre_2d" : data['Close'].values[-3,0],
	    #"maximo_2d" : data['High'].values[-3,0],
	    #"minimo_2d" : data['Low'].values[-3,0],
	    #"volumen_2d" : data['Volume'].values[-3,0],
	    #"cierre_3d" : data['Close'].values[-4,0],
	    #"maximo_3d" : data['High'].values[-4,0],
	    #"minimo_3d" : data['Low'].values[-4,0],
	    #"volumen_3d" : data['Volume'].values[-4,0],
	    #"cierre_4d" : data['Close'].values[-5,0],
	    #"maximo_4d" : data['High'].values[-5,0],
	    #"minimo_4d" : data['Low'].values[-5,0],
	    #"volumen_4d" : data['Volume'].values[-5,0],
	    #"cierre_5d" : data['Close'].values[-6,0],
	    #"maximo_5d" : data['High'].values[-6,0],
	    #"minimo_5d" : data['Low'].values[-6,0],
	    #"volumen_5d" : data['Volume'].values[-6,0],
	    "sma" : sma,
	    "rsi" : rsi,
	    "adx" : adx,
	    #"atr" : atr,
	    #"atrma" : atr_ma,
	    "obv" : obv,
	    "obvma" : obvma,
	    "macd" : macd,
	    "signal" : signal
	    }

	decision = consultar_modelo(caracteristicas)
	
	mejor_decision = max(decision, key=decision.get)

	if decision[mejor_decision] >= 0.8:
		recomendacion = mejor_decision
	else:
		recomendacion = "Indefinido"

	return {
		'Ticker': ticker,
		'Señal': señal,
		'Modelo' : recomendacion,
		'Comprar(%)' : round(decision['comprar']*100,2),
		'Vender(%)' : round(decision['vender']*100,2),
		'Mantener(%)' : round(decision['mantener']*100,2),
		'Cierre': round(precio_actual, 2),
		'SMA21': (precio_actual > sma),
		'MACD': (True if macd > signal else False),
		'OBV' : compra_obv,
		'Boll' : compra_bollinger

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

def calcular_atr(data):
	atr = ta.ATR(
		data['High'].values[:,0].astype(np.float64),
		data['Low'].values[:,0].astype(np.float64),
		data['Close'].values[:,0].astype(np.float64),
		timeperiod=14
	)
	atr_ma = ta.SMA(atr, timeperiod=14)

	return atr[-1], atr_ma[-1]


def consultar_modelo(caracteristicas):
	prediccion = {}
	try:
		with open(RUTA_MODELO, "rb") as f:
			model = pickle.load(f)
		#prediccion = model.predict_one(caracteristicas)
		prediccion = model.predict_proba_one(caracteristicas)
	except FileNotFoundError:
		print("No hay modelo.")

	return prediccion
