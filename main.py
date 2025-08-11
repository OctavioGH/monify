import yfinance as yf
import pandas as pd
import core
import os

RUTA_TICKERS = "data/lista_acciones.txt"
RUTA_TRANSACCIONES = "data/historial_transacciones.csv"
RUTA_PORTAFOLIO = "data/portafolio.csv"

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def analizar_acciones():
    
    with open(RUTA_TICKERS, 'r') as f:
        tickers = [line.strip() for line in f.readlines()]

    resultados = []

    print("Analizando acciones...")

    for index, ticker in enumerate(tickers):
        index += 1
        
        print(f"[{index}/{len(tickers)}]Analizando {ticker}")
        
        if ticker:
            resultado = core.metricas.analizar_ticker(ticker)
            if resultado:
                resultados.append(resultado)

    if resultados:
        data = pd.DataFrame(resultados).sort_values(by='Señal', ascending=True)
        print("\n--------------- Resultados del análisis técnico: ---------------\n")
        print(data.to_string(index=False))
        print()
    else:
        print("No se obtuvieron resultados válidos")

if __name__ == "__main__":
    
    clear()

    salir = False
    
    while not salir:
        print("========== MONIFY ==========")
        print("1 - Cargar transacción")
        print("2 - Mostrar portafolio")
        print("3 - Mostrar transacciones")
        print("4 - Analizar acciones")
        print("5 - Salir")
        opcion = input("Selecciona una opción: ").strip()

        match(opcion):
            case "1":
                core.portafolio.cargar_transaccion(RUTA_TRANSACCIONES, RUTA_PORTAFOLIO)
            case "2":
                core.portafolio.mostrar_archivo(RUTA_PORTAFOLIO)
            case "3":
                core.portafolio.mostrar_archivo(RUTA_TRANSACCIONES)
            case "4":
                analizar_acciones()
            case "5":
                salir = True
            case _:
                print("Opción no válida")

    clear()