import yfinance as yf
import pandas as pd

def descargar_datos(ruta_datos, ticker, periodo="1y", intervalo="1d"):
    """
    Descarga datos históricos de un ticker desde Yahoo Finance y los guarda en CSV.

    Parámetros:
    ticker (str): Símbolo del activo (ej: 'AAPL', 'TSLA', 'MSFT')
    periodo (str): Periodo de datos (ej: '1y', '6mo', '1d')
    intervalo (str): Intervalo de velas (ej: '1d', '1h', '5m')

    """
    try:
        print(f"📥 Descargando datos de {ticker} desde Yahoo Finance...")
        data = yf.download(ticker, period=periodo, interval=intervalo, auto_adjust = True)

        if data.empty:
            print(f"⚠ No se encontraron datos para {ticker}.")
            return

        ticker = ticker.split('.')[0]
        nombre_archivo = f"{ruta_datos}{ticker}.csv"
        data.to_csv(nombre_archivo)
        print(f"✅ Datos guardados en '{nombre_archivo}'.")

    except Exception as e:
        print(f"❌ Error descargando datos de {ticker}: {e}")

def cargar_csv(ruta_archivo):
    """
    Carga un archivo CSV y lo devuelve como un DataFrame.

    Parámetros:
    nombre_archivo (str): Ruta o nombre del archivo CSV.

    Retorna:
    pd.DataFrame: DataFrame con los datos del CSV.
    """
    try:
        df = pd.read_csv(ruta_archivo)
        #print(f"Archivo '{ruta_archivo}' cargado correctamente.")
        return df
    except FileNotFoundError:
        print(f"El archivo '{ruta_archivo}' no existe.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error al cargar el archivo '{ruta_archivo}': {e}")
        return pd.DataFrame()

