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
    ultimo_cierre = precio_actual = yf.Ticker(ticker).info.get('regularMarketPrice')
    sma21 = calcular_sma(data, 21)
    sma50 = calcular_sma(data, 50)
    sma200 = calcular_sma(data, 200)
    rsi = calcular_rsi(data)
    macd, signal = calcular_macd(data)
    obv, obvma = calcular_obv(data)
    
    # Determinar señal
    señal = "Mantener"

    if ultimo_cierre > sma21 and rsi < 60 and rsi > 30 and macd > signal and obv > obvma and sma21 > sma50 and sma50 > sma200:
        señal = "Comprar"
    elif (ultimo_cierre < sma21 or macd < signal) and rsi > 65:
        señal = "Vender"

    return {
        'Ticker': ticker,
        'Cierre': round(ultimo_cierre, 2),
        'SMA21': round(sma21, 2),
        'SMA50': round(sma50, 2),
        'SMA200': round(sma200, 2),
        'RSI14': round(rsi, 2),
        'MACD': (True if macd > signal else False),
        'Señal': señal
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

def calculate_adx(data, periodos=14):
    return ta.ADX(data['High'].values[:,0], data['Low'].values[:,0], data['Close'].values[:,0], timeperiod=periodos)[-1]

def squeeze_momentum(data):
	# Bollinger Bands (usualmente 20 periodos, 2 desviaciones)
	upper_bb, middle_bb, lower_bb = ta.BBANDS(data['Close'].values[:,0], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

	# Keltner Channels (usualmente 20 periodos, factor 1.5)
	# Keltner Channel central = EMA(20)
	ema20 = ta.EMA(data['Close'].values[:,0], timeperiod=20)
	atr = ta.ATR(data['High'].values[:,0], data['Low'].values[:,0], data['Close'].values[:,0], timeperiod=20)
	upper_kc = ema20 + 1.5 * atr
	lower_kc = ema20 - 1.5 * atr

	# Condición squeeze: Bollinger Bands dentro de Keltner Channels
	squeeze_on = (lower_bb > lower_kc) & (upper_bb < upper_kc)

	# Momentum: usar MACD histograma como proxy
	macd, macdsignal, macdhist = ta.MACD(data['Close'].values[:,0], fastperiod=12, slowperiod=26, signalperiod=9)

	# Squeeze momentum = macd histograma * (1 o -1 según squeeze_on)
	squeeze_momentum_val = np.where(squeeze_on, macdhist, 0)

	#df['squeeze_on'] = squeeze_on
	#df['squeeze_momentum'] = squeeze_momentum_val

	return squeeze_on[-1], squeeze_momentum_val[-1]
