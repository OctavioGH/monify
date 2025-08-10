from datetime import datetime
import yfinance as yf
import pandas as pd
import os

def cargar_transaccion(ruta_transacciones, ruta_portafolio):
    tipo = input("Tipo de operación (compra/venta): ").strip().lower()
    if tipo not in ["compra", "venta"]:
        print("Error: El tipo de operación debe ser 'compra' o 'venta'")
        return

    monto = float(input("Monto total de la operación: "))
    cantidad = int(input("Cantidad de acciones: "))
    ticker = input("Ticker de la acción: ").strip().upper()

    precio_unitario = monto / cantidad

    fecha_input = input("¿Deseas especificar la fecha? (YYYY-MM-DD HH:MM) o deja vacío para usar ahora: ").strip()
    if fecha_input:
        try:
            fecha = datetime.strptime(fecha_input, "%d/%m/%Y")
        except ValueError:
            print("Formato de fecha inválido, se usará la fecha actual.")
            fecha = datetime.now()
    else:
        fecha = datetime.now()

    # Guardar en transacciones.csv
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

    print("✅ Transacción guardada en", ruta_transacciones)

    # Actualizar cuentas.csv
    if os.path.exists(ruta_portafolio):
        cuentas = pd.read_csv(ruta_portafolio)
    else:
        cuentas = pd.DataFrame(columns=["ticker", "cantidad", "precio_promedio"])

    if ticker in cuentas["ticker"].values:
        idx = cuentas.index[cuentas["ticker"] == ticker][0]
        if tipo == "compra":
            cantidad_actual = cuentas.loc[idx, "cantidad"]
            precio_prom_actual = cuentas.loc[idx, "precio_promedio"]

            # Calcular nuevo promedio ponderado
            nuevo_total_acciones = cantidad_actual + cantidad
            nuevo_promedio = ((precio_prom_actual * cantidad_actual) + (precio_unitario * cantidad)) / nuevo_total_acciones

            cuentas.loc[idx, "cantidad"] = nuevo_total_acciones
            cuentas.loc[idx, "precio_promedio"] = nuevo_promedio

        elif tipo == "venta":
            if cuentas.loc[idx, "cantidad"] >= cantidad:
                cuentas.loc[idx, "cantidad"] -= cantidad
                if cuentas.loc[idx, "cantidad"] == 0:
                    cuentas = cuentas.drop(idx)  # eliminar si ya no queda nada
            else:
                print("⚠ Advertencia: Intentas vender más acciones de las que posees.")
    else:
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
            print("⚠ No puedes vender una acción que no tienes registrada.")

    cuentas.to_csv(ruta_portafolio, index=False)
    print("✅ Cuentas actualizadas en", ruta_portafolio)

def mostrar_archivo(nombre_archivo):
    """Muestra por consola el contenido de un archivo CSV si existe."""
    if not os.path.exists(nombre_archivo):
        print(f"📂 No existe el archivo {nombre_archivo}.")
        return

    df = pd.read_csv(nombre_archivo)
    if df.empty:
        print(f"📂 El archivo {nombre_archivo} está vacío.")
        return
    else:
        titulo = "Historial de transacciones"
        if "portafolio" in nombre_archivo:
            titulo = "Portafolio"
            # Obtener precios actuales para cada ticker
            precios = []
            
            for ticker in df['ticker'].unique():
                try:
                    precio_actual = yf.Ticker(ticker+'.BA').info.get('regularMarketPrice')
                    if precio_actual is None:
                        precio_actual = float('nan')  # Por si no hay precio disponible
                except Exception as e:
                    print(f"Error obteniendo precio para {ticker}: {e}")
                    precio_actual = float('nan')
                precios.append((ticker, precio_actual))

            # Crear un diccionario para mapear ticker -> precio
            dict_precios = dict(precios)

            # Crear nueva columna con el precio más reciente
            df['precio_actual'] = df['ticker'].map(dict_precios)
            
            # Calcular diferencia porcentual
            df['diferencia_pct'] = round(((df['precio_actual'] - df['precio_promedio']) / df['precio_promedio']) * 100, 2)

        print(f"\n{titulo}")
        print(df.to_string(index=False))
        print()
