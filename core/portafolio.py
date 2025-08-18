from datetime import datetime
import yfinance as yf
import pandas as pd
import os
import os
import pandas as pd
from datetime import datetime
import yfinance as yf

def inicializar_capital(ruta_capital):
    """Si no existe capital.csv, pedir capital inicial y crearlo."""
    if not os.path.exists(ruta_capital):
        try:
            capital_invertido = float(input("Ingrese su capital invertido: "))
            capital_total = float(input("Ingrese su capital total: "))
            capital_libre = capital_total - capital_invertido
            
            capital = pd.DataFrame([{
            "capital_libre": capital_libre,
            "capital_invertido": capital_invertido,
            "capital_total": capital_total,
            }])
            capital.to_csv(ruta_capital, index=False)

            mostrar_resumen()

        except ValueError:
            print("Entrada inválida.")
            return 1

    return 0

def cargar_transaccion(ruta_transacciones, ruta_portafolio, ruta_capital):
    
    # Defino el tipo de operacion (compra o venta)
    tipo = input("Tipo de operación (compra/venta): ").strip().lower()
    if tipo not in ["compra", "venta"]:
        print("Error: El tipo de operación debe ser 'compra' o 'venta'")
        return

    # Determino el monto, cantidad, y ticker de la operación
    monto = float(input("Monto total de la operación: "))
    cantidad = int(input("Cantidad de acciones: "))
    ticker = input("Ticker de la acción: ").strip().upper()

    # Calculo el PPC de cada acción
    precio_unitario = round(monto / cantidad, 2)

    # Obtengo la fecha en que se realizó la operación
    fecha_input = input("Fecha (DD/MM/YYYY) o vacío para usar ahora: ").strip()
    if fecha_input:
        try:
            fecha = datetime.strptime(fecha_input, "%d/%m/%Y")
        except ValueError:
            print("Formato de fecha inválido, se usará la fecha actual.")
            fecha = datetime.now()
    else:
        fecha = datetime.now()

    # Registro la transacción en el historial
    transaccion = pd.DataFrame([{
        "fecha": fecha.strftime("%d/%m/%Y"),
        "tipo": tipo,
        "monto": monto,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "ticker": ticker
    }])

    if os.path.exists(ruta_transacciones):
        transaccion.to_csv(ruta_transacciones, mode='a', header=False, index=False)
    else:
        transaccion.to_csv(ruta_transacciones, index=False)

    print("Transacción guardada en", ruta_transacciones)


    # Actualizar portafolio
    _actualizar_portafolio(ruta_portafolio, transaccion)

    # Actualizar capital y ganancias
    _actualizar_capital(ruta_capital, ruta_portafolio, transaccion)
    
def _actualizar_capital(ruta_capital, ruta_portafolio, transaccion=None):
    """Actualiza el capital libre, invertido, total y ganancias."""
    capital = pd.read_csv(ruta_capital)
    cuentas = pd.read_csv(ruta_portafolio)

    capital_libre = capital.loc[0, "capital_libre"]
    capital_total = capital.loc[0, "capital_total"]
    capital_invertido = capital.loc[0, "capital_invertido"]

    if transaccion is not None:
        if transaccion.loc[0, "tipo"] == "compra":
            capital_libre -= transaccion.loc[0, "monto"]
        elif transaccion.loc[0, "tipo"] == "venta":
            capital_libre += transaccion.loc[0, "monto"]

    capital_invertido = _valor_actual_portafolio(ruta_portafolio)
    capital_total = capital_libre + capital_invertido

    capital.loc[0, "capital_libre"] = capital_libre
    capital.loc[0, "capital_invertido"] = capital_invertido
    capital.loc[0, "capital_total"] = capital_total

    capital.to_csv(ruta_capital, index=False)
    #print("Capital actualizado:", capital.to_dict(orient="records")[0])

def mostrar_transacciones(ruta_transacciones):
    if not os.path.exists(ruta_transacciones):
        print(f"No existe el archivo {ruta_transacciones}.")
        return

    df = pd.read_csv(ruta_transacciones)
    if df.empty:
        print(f"El archivo {ruta_transacciones} está vacío.")
        return
    else:
        print("\n==================== Historial de transacciones ====================")
        print(df.to_string(index=False))
        print()

def _actualizar_portafolio(ruta_portafolio, transaccion):
    # Actualizo el portafolio
    if os.path.exists(ruta_portafolio):
        cuentas = pd.read_csv(ruta_portafolio)
    else:
        cuentas = pd.DataFrame(columns=["ticker", "cantidad", "precio_promedio"])

    ticker = transaccion["ticker"].iloc[0]
    tipo = transaccion["tipo"].iloc[0]
    cantidad = transaccion["cantidad"].iloc[0]
    precio_unitario = transaccion["precio_unitario"].iloc[0]

    # Busco el ticker correspondiente
    if ticker in cuentas["ticker"].values:
        idx = cuentas.index[cuentas["ticker"] == ticker][0]
        # Si lo encuentro, sumo o resto en función de si vendi o compre
        if tipo == "compra":
            cantidad_actual = cuentas.loc[idx, "cantidad"]
            precio_prom_actual = cuentas.loc[idx, "precio_promedio"]

            nuevo_total_acciones = cantidad_actual + cantidad
            nuevo_promedio = ((precio_prom_actual * cantidad_actual) + (precio_unitario * cantidad)) / nuevo_total_acciones

            cuentas.loc[idx, "cantidad"] = nuevo_total_acciones
            cuentas.loc[idx, "precio_promedio"] = nuevo_promedio

        elif tipo == "venta":
            if cuentas.loc[idx, "cantidad"] >= cantidad:
                cuentas.loc[idx, "cantidad"] -= cantidad
                if cuentas.loc[idx, "cantidad"] == 0:
                    cuentas = cuentas.drop(idx)
            else:
                print("Intentas vender más acciones de las que posees.")
    else:
        # Si no lo encuentro, lo agrego
        if tipo == "compra":
            cuentas = pd.concat(
                [cuentas, pd.DataFrame([{
                    "ticker": ticker,
                    "cantidad": cantidad,
                    "precio_promedio": precio_unitario
                }])],
                ignore_index=True
            )
        else:
            print("No puedes vender una acción que no tienes registrada.")

    cuentas.to_csv(ruta_portafolio, index=False)
    print("Cuentas actualizadas en", ruta_portafolio)

def _obtener_portafolio(ruta_portafolio):
    cuentas = None
    if os.path.exists(ruta_portafolio):
        cuentas = pd.read_csv(ruta_portafolio)
    else:
        print("No se encontró el portafolio.")

    return cuentas

def mostrar_resumen_completo(ruta_capital, ruta_portafolio, ruta_transacciones):
    """Muestra un resumen completo de capital y portafolio."""
    if not os.path.exists(ruta_capital):
        print("No existe el archivo de capital.")
        return
    if not os.path.exists(ruta_portafolio):
        print("No existe el archivo de portafolio.")
        return

    # === Cargar capital ===
    _actualizar_capital(ruta_capital, ruta_portafolio)

    cap = pd.read_csv(ruta_capital).iloc[0]
    ganancia = _calcular_ganancia_neta(ruta_transacciones)

    print("\n=============== Capital ===============")
    print(f"Capital Libre:          {cap['capital_libre']:.2f}")
    print(f"Capital Invertido:      {cap['capital_invertido']:.2f}")
    print(f"Capital Total:          {cap['capital_total']:.2f}")
    print(f"Ganancias:              {ganancia:.2f}")

    # === Cargar portafolio ===
    df = pd.read_csv(ruta_portafolio)
    if df.empty:
        print("\nPortafolio vacío.")
        return

    precios = []
    for ticker in df['ticker'].unique():
        try:
            precio_actual = yf.Ticker(ticker+'.BA').info.get('regularMarketPrice')
            if precio_actual is None:
                precio_actual = float('nan')
        except Exception as e:
            print(f"Error obteniendo precio para {ticker}: {e}")
            precio_actual = float('nan')
        precios.append((ticker, precio_actual))

    dict_precios = dict(precios)
    df['precio_actual'] = df['ticker'].map(dict_precios)
    df['valor_actual'] = df['cantidad'] * df['precio_actual']
    df['ganancia_no_realizada'] = df['valor_actual'] - (df['cantidad'] * df['precio_promedio'])
    df['diferencia_pct'] = round( ((df['precio_actual'] - df['precio_promedio']) / df['precio_promedio']) * 100, 2)

    # === Totales de ganancias no realizadas ===
    ganancia_no_realizada_total = df['ganancia_no_realizada'].sum()

    print("\n============================== Portafolio ===================================")
    print(df.to_string(index=False))
    print(f"\nGanancia No Realizada: {ganancia_no_realizada_total:.2f}\n\n")

def _valor_actual_portafolio(ruta_portafolio):
    
    """Calcula y devuelve el valor actual del portafolio usando precios de mercado."""
    if not os.path.exists(ruta_portafolio):
        print("No existe el archivo de portafolio.")
        return 0.0

    df = pd.read_csv(ruta_portafolio)
    if df.empty:
        print("El portafolio está vacío.")
        return 0.0

    # Obtener precios actuales
    precios_actuales = {}
    for ticker in df['ticker'].unique():
        try:
            precio_actual = yf.Ticker(ticker + '.BA').info.get('regularMarketPrice')
            if precio_actual is None:
                precio_actual = float('nan')
        except Exception as e:
            print(f"Error obteniendo precio para {ticker}: {e}")
            precio_actual = float('nan')
        precios_actuales[ticker] = precio_actual

    # Calcular valor actual por posición
    df['precio_actual'] = df['ticker'].map(precios_actuales)
    df['valor_actual'] = df['cantidad'] * df['precio_actual']

    valor_total = df['valor_actual'].sum()

    #print(f"Valor Actual del Portafolio: {valor_total:.2f}")
    return valor_total


def _calcular_ganancia_neta(ruta_transacciones):
    """
    Calcula la ganancia neta SOLO de acciones que ya fueron vendidas,
    usando precio de compra promedio y manejando ventas parciales.
    """
    if not os.path.exists(ruta_transacciones):
        print("📂 No existe el archivo de transacciones.")
        return 0.0

    df = pd.read_csv(ruta_transacciones)
    if df.empty:
        print("📂 El historial de transacciones está vacío.")
        return 0.0

    # Asegurar que las transacciones estén en orden cronológico
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df = df.sort_values("fecha")

    portafolio_temp = {}
    ganancia_total = 0.0

    for _, row in df.iterrows():
        tipo = row["tipo"].lower()
        ticker = row["ticker"]
        cantidad = row["cantidad"]
        precio_unitario = row["precio_unitario"]

        if tipo == "compra":
            # Agregar al portafolio temporal o actualizar promedio
            if ticker not in portafolio_temp:
                portafolio_temp[ticker] = {"cantidad": cantidad, "precio_prom": precio_unitario}
            else:
                cant_actual = portafolio_temp[ticker]["cantidad"]
                prom_actual = portafolio_temp[ticker]["precio_prom"]
                nuevo_total = cant_actual + cantidad
                nuevo_prom = ((prom_actual * cant_actual) + (precio_unitario * cantidad)) / nuevo_total
                portafolio_temp[ticker]["cantidad"] = nuevo_total
                portafolio_temp[ticker]["precio_prom"] = nuevo_prom

        elif tipo == "venta":
            if ticker in portafolio_temp and portafolio_temp[ticker]["cantidad"] >= cantidad:
                precio_prom_compra = portafolio_temp[ticker]["precio_prom"]
                costo_base = precio_prom_compra * cantidad
                ingreso_venta = precio_unitario * cantidad
                ganancia_total += (ingreso_venta - costo_base)

                # Reducir cantidad en portafolio
                portafolio_temp[ticker]["cantidad"] -= cantidad
                if portafolio_temp[ticker]["cantidad"] == 0:
                    del portafolio_temp[ticker]
            else:
                print(f"⚠ Venta inválida o sin compras previas para {ticker}.")

    #print(f"💵 Ganancia Realizada: {ganancia_total:.2f}")
    return ganancia_total
