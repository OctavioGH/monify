import yfinance as yf
import pandas as pd

def calcular_rsi(data, periodos=14):
    """Calcula el Índice de Fuerza Relativa (RSI)"""
    delta = data['Close'].diff()
    ganancia = delta.where(delta > 0, 0)
    perdida = -delta.where(delta < 0, 0)
    
    avg_ganancia = ganancia.ewm(alpha=1/periodos, adjust=False).mean()
    avg_perdida = perdida.ewm(alpha=1/periodos, adjust=False).mean()
    
    rs = avg_ganancia / avg_perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analizar_ticker(ticker):
    """Descarga datos y calcula indicadores para un ticker"""
    try:
        # Descargar datos históricos
        data = yf.download(ticker, period="12mo", progress=False, auto_adjust=True)
        
        if data.empty:
            return None
        
        # Calcular indicadores técnicos

        # Medias Móviles (Golden/Death Cross)
        data['SMA21'] = data['Close'].rolling(window=21).mean().fillna(0)
        data['SMA50'] = data['Close'].rolling(window=50).mean().fillna(0)
        data['SMA200'] = data['Close'].rolling(window=200).mean().fillna(0)
        
        # RSI 14 y 21 días
        data['RSI14'] = calcular_rsi(data, 14)
        data['RSI21'] = calcular_rsi(data, 21)

        # EMA50
        data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean().fillna(0)
        
        # Bollinger Bands
        #data['Upper_BB'] = data['SMA21'].values + (2 * (data['Close'].rolling(21).std().values))
        #data['Lower_BB'] = data['SMA21'] - 2 * data['Close'].rolling(21).std()
        
        # MACD
        data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean().fillna(0)
        data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean().fillna(0)
        data['MACD'] = data['EMA12'] - data['EMA26']
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean().fillna(0)

        # Obtener últimos valores
        ultimo_cierre = data['Close'].iloc[-1].item()
        sma21 = data['SMA21'].iloc[-1].item()
        sma50 = data['SMA50'].iloc[-1].item()
        sma200 = data['SMA200'].iloc[-1].item()
        rsi14 = data['RSI14'].iloc[-1].item()
        rsi21 = data['RSI21'].iloc[-1].item()
        macd = data['MACD'].iloc[-1].item()
        signal = data['Signal_Line'].iloc[-1].item()
        
        # Determinar señal
        señal = "Mantener"

        if ultimo_cierre > sma200 and sma21>sma50 and rsi14 < 30 and rsi21 < 40 and macd > signal:
            señal = "Compra fuerte"
        elif ultimo_cierre < sma200 and sma21<sma50 and rsi14 > 60 and rsi21 > 40 and macd < signal:
            señal = "Venta fuerte"
        elif ultimo_cierre > sma21 and rsi14 < 70:
            if rsi14 > 30:
                señal = "Comprar"
            else:
                señal = "Sobreventa - Posible compra"
        elif ultimo_cierre < sma21 and rsi14 > 30:
            if rsi14 < 70:
                señal = "Vender"
            else:
                señal = "Sobrecompra - Posible venta"

        return {
            'Ticker': ticker,
            'Cierre': round(ultimo_cierre, 2),
            'SMA21': round(sma21, 2),
            'SMA50': round(sma50, 2),
            'SMA200': round(sma200, 2),
            'RSI14': round(rsi14, 2),
            'RSI21': round(rsi21, 2),
            'MACD': (True if macd > signal else False),
            'Señal': señal
        }
        
    except Exception as e:
        print(f"Error procesando {ticker}: {str(e)}")
        return None

# Leer tickers desde archivo
print("Iniciando programa...")

archivo_tickers = "config/watchlist.txt"  # Cambia al nombre de tu archivo

try:
    with open(archivo_tickers, 'r') as f:
        tickers = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {archivo_tickers}")
    exit()

# Procesar cada ticker
resultados = []
i = 1

print("Analizando acciones...")

for ticker in tickers:
    print(f"[{i}/{len(tickers)}]Analizando {ticker}")
    i += 1
    if ticker:  # Saltar líneas vacías
        resultado = analizar_ticker(ticker)
        if resultado:
            resultados.append(resultado)

# Mostrar resultados
if resultados:
    df = pd.DataFrame(resultados)
    print("\nResultados del análisis técnico:")
    print(df.to_string(index=False))
else:
    print("No se obtuvieron resultados válidos")