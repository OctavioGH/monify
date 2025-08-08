import pandas as pd
import yfinance as yf

def analizar_ticker(ticker):
    # Descargar datos históricos
    data = yf.download(ticker, period="12mo", progress=False, auto_adjust=True)
    
    if data.empty:
        return None
    
    # Calcular indicadores técnicos
    ultimo_cierre = data['Close'].iloc[-1].item()
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
	return data['Close'].rolling(window=periodos).mean().fillna(0).iloc[-1].item()

def calcular_macd(data, periodo_largo = 26, periodo_corto = 12, periodo_señal = 9):
	data['ema_corto'] = data['Close'].ewm(span=periodo_corto, adjust=False).mean().fillna(0)
	data['ema_largo'] = data['Close'].ewm(span=periodo_largo, adjust=False).mean().fillna(0)
	data['macd'] = data['ema_corto'] - data['ema_largo']
	data['linea_señal'] = data['macd'].ewm(span=periodo_señal, adjust=False).mean().fillna(0)

	return data['macd'].iloc[-1].item(), data['linea_señal'].iloc[-1].item()

def calcular_rsi(data, periodos = 14):
	"""Calcula el Índice de Fuerza Relativa (RSI)"""
	delta = data['Close'].diff()
	ganancia = delta.where(delta > 0, 0)
	perdida = -delta.where(delta < 0, 0)

	avg_ganancia = ganancia.ewm(alpha=1/periodos, adjust=False).mean()
	avg_perdida = perdida.ewm(alpha=1/periodos, adjust=False).mean()

	rs = avg_ganancia / avg_perdida
	rsi = 100 - (100 / (1 + rs))

	return rsi.iloc[-1].item()

def calcular_obv(data):
	# On-Balance Volume (OBV)
	data["OBV"] = 0  # Primer valor por defecto

	for i in range(1, len(data)):
	    if data["Close"].iloc[i].item() > data["Close"].iloc[i - 1].item():
	        data.loc[data.index[i], "OBV"] = data["OBV"].iloc[i - 1].item() + data["Volume"].iloc[i].item()
	    elif data["Close"].iloc[i].item() < data["Close"].iloc[i - 1].item():
	        data.loc[data.index[i], "OBV"] = data["OBV"].iloc[i - 1].item() - data["Volume"].iloc[i].item()
	    else:
	        data.loc[data.index[i], "OBV"] = data["OBV"].iloc[i - 1].item()

	data["OBV_10"] = data["OBV"].rolling(window=10).mean().fillna(0)

	return data['OBV'].iloc[-1].item(), data['OBV_10'].iloc[-1].item()