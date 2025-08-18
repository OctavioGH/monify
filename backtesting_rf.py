import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import core

import pickle
from river import forest
from river import metrics

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
    middle_kc = ta.EMA(data['Close'].values.astype(np.float64), timeperiod=periodos_klt)
    upper_kc = middle_kc + mult * atr
    lower_kc = middle_kc - mult * atr

    return upper_kc, middle_kc, lower_kc, atr, atr_ma


def calcular_metricas(df):

    # ================================================================
    # Simple Moving Average
    # ================================================================
    df["SMA21"] = calcular_sma(df, 21)
    df["SMA50"] = calcular_sma(df, 50)
    df["SMA200"] = calcular_sma(df, 200)

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
    
    df.dropna(inplace=True)

def generar_etiquetas(df, dias):
    
    df['Return'] = df['Close'].pct_change().shift(-dias)

    def create_label(r):
        ganancia = 0.03
        perdida = -0.03
        if r > ganancia:
            return "comprar"  # Buy
        elif r > perdida:
            return "vender"  # Sell
        else:
            return "mantener"  # Hold

    df['Signal'] = df.apply(lambda row: create_label(row['Return']), axis=1)
    df.dropna(inplace=True)

    frecuencias = df['Signal'].value_counts()

    print(f"Frecuencias: {frecuencias}")

if __name__ == "__main__":

    print("Iniciando programa...")

    # ==========================
    # 1. Cargar modelo si existe
    # ==========================
    try:
        with open("modelo_trading.pkl", "rb") as f:
            model = pickle.load(f)
        print("Modelo cargado desde archivo.")
    except FileNotFoundError:
        # Si no existe, creamos un modelo nuevo
        model = forest.ARFClassifier(
            n_models=200,
            max_depth=50,
            seed=42
        )
        print("Creado nuevo modelo.")

    # Métrica para evaluar desempeño
    accuracy = metrics.Accuracy()
    cm = metrics.ConfusionMatrix()

    # ==========================
    # 2. Generar datos mediante backtesting
    # ==========================
    try:
        with open(RUTA_TICKERS, 'r') as f:
            tickers = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {RUTA_TICKERS}")
        exit()

    dict_entradas = []
    salidas = []

    for index, ticker in enumerate(tickers):
        index += 1
        print(f"[{index}/{len(tickers)}]Analizando {ticker}")
        
        nombre_archivo = RUTA_DATOS+ticker.split('.')[0]+'.csv'
        data = core.obtener_datos.cargar_csv(nombre_archivo)
        data = data.drop(index=[0, 1]).reset_index(drop=True)
        data['Close'] = data['Close'].astype(float)
        data['Volume'] = data['Volume'].astype(float)
        data['High'] = data['High'].astype(float)
        data['Low'] = data['Low'].astype(float)
        
        calcular_metricas(data)

        largo = data.shape[0]

        ganancia = 0.05
        perdida = -0.05

        decision = ""
        dias = 5
        for dias in range(5, 6, 5):
            n_comprar = 0
            n_vender = 0
            n_mantener = 0

            lista_caracteristicas = []

            for j in range(26,largo-dias):
                # Toma de decision manual y formacion de caracteristicas
                cambio = (data['Close'].iloc[j+dias] - data['Close'].iloc[j])/data['Close'].iloc[j]
                
                if cambio > ganancia:
                    decision = "comprar"  # Buy
                    n_comprar += 1
                elif cambio < perdida:
                    decision = "vender"  # Sell
                    n_vender += 1
                else:
                    decision = "mantener"  # Hold
                    n_mantener += 1

                caracteristicas = {
                    "cierre" : data['Close'].iloc[j],
                    #"maximo" : data['High'].iloc[j],
                    #"minimo" : data['Low'].iloc[j],
                    #"volumen" : data['Volume'].iloc[j],
                    #"cierre_1d" : data['Close'].iloc[j-1],
                    #"maximo_1d" : data['High'].iloc[j-1],
                    #"minimo_1d" : data['Low'].iloc[j-1],
                    #"volumen_1d" : data['Volume'].iloc[j-1],
                    #"cierre_2d" : data['Close'].iloc[j-2],
                    #"maximo_2d" : data['High'].iloc[j-2],
                    #"minimo_2d" : data['Low'].iloc[j-2],
                    #"volumen_2d" : data['Volume'].iloc[j-2],
                    #"cierre_3d" : data['Close'].iloc[j-3],
                    #"maximo_3d" : data['High'].iloc[j-3],
                    #"minimo_3d" : data['Low'].iloc[j-3],
                    #"volumen_3d" : data['Volume'].iloc[j-3],
                    #"cierre_4d" : data['Close'].iloc[j-4],
                    #"maximo_4d" : data['High'].iloc[j-4],
                    #"minimo_4d" : data['Low'].iloc[j-4],
                    #"volumen_4d" : data['Volume'].iloc[j-4],
                    #"cierre_5d" : data['Close'].iloc[j-5],
                    #"maximo_5d" : data['High'].iloc[j-5],
                    #"minimo_5d" : data['Low'].iloc[j-5],
                    #"volumen_5d" : data['Volume'].iloc[j-5],
                    "sma" : data['SMA21'].iloc[j],
                    "rsi" : data['RSI'].iloc[j],
                    "adx" : data['ADX'].iloc[j],
                    #"atr" : data['ATR'].iloc[j],
                    #"atrma" : data['ATR_MA'].iloc[j],
                    "obv" : data['OBV'].iloc[j],
                    "obvma" : data['OBV_10'].iloc[j],
                    "macd" : data['MACD'].iloc[j],
                    "signal" : data['Signal_Line'].iloc[j],
                    "salida" : decision
                    }

                lista_caracteristicas.append(caracteristicas)
                
            entrenar = False
            n_entrenos = min(n_comprar, n_vender, n_mantener)    
            n_entrenos_compra = 0
            n_entrenos_venta = 0
            n_entrenos_mantener = 0
            n_entrenos_total = 0
            
            print(f"Dias: {dias} | Entreno: {n_entrenos}")

            for caracteristicas in lista_caracteristicas:
                
                decision = caracteristicas['salida']
                caracteristicas.pop('salida')

                match(decision):
                    case 'comprar':
                        if n_entrenos_compra < n_entrenos:
                            n_entrenos_compra += 1
                            entrenar = True
                    case 'vender':
                        if n_entrenos_venta < n_entrenos:
                            n_entrenos_venta += 1
                            entrenar = True
                    case 'mantener':
                        if n_entrenos_mantener < n_entrenos:
                            n_entrenos_mantener += 1
                            entrenar = True
                
                if entrenar:            
                    n_entrenos_total += 1
                    # Predicción automática antes de decidir
                    prediccion = model.predict_one(caracteristicas)

                    # Aprendizaje incremental
                    model.learn_one(caracteristicas, decision)

                    # Actualizar métrica de desempeño
                    if prediccion is not None:
                        accuracy.update(decision, prediccion)
                        cm.update(decision, prediccion)

                    if n_entrenos_total//3 == n_entrenos:  
                        print(f"N. Ent: {n_entrenos_total} ; Real: {decision} ; Predicción: {prediccion} ; Accuarcy: {accuracy.get():.2f}")
                        print(cm)
                    entrenar = False


    # Guardar modelo actualizado
    with open("modelo_trading.pkl", "wb") as f:
        pickle.dump(model, f)