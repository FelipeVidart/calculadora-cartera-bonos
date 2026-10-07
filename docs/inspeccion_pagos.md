# Inspección del archivo adjunto Pagos.xlsx

Inspeccionado antes de implementar. Una hoja: Pagos. 105 filas de datos y cinco columnas: Ticker, Fecha, Renta, Amortización, Total. Tickers: VSCXO (24), PLC7O (22), PN43O (21), IRCPO (17), SBC2O (10), VSCZO (6), RUCEO (5).

Todas las fechas son texto ISO AAAA-MM-DD, desde 2026-10-08 hasta 2038-04-08. Los importes son valores numéricos Excel (enteros o flotantes), hasta tres decimales; formato General. No se observaron vacíos, negativos ni duplicados. Una discrepancia en fila 2: VSCXO, 2026-10-08, Renta 2126.25, Amortización 0, Total informado 0. Se usa 2126.25 para el cálculo y se presenta un aviso.

La dimensión XML de la hoja es A1 aunque hay 106 filas y cinco columnas. El lector openpyxl restablece dimensiones y recorre el contenido real, evitando perder pagos. No se modifica el archivo original.

El archivo no contiene Market Values, monedas, nominales ni emisores. No pueden inferirse precios ni retornos reales a partir de estos pagos sin posiciones. Tampoco acredita por sí solo la completitud de flujos contractuales. No se incorporó el Excel del cliente al repositorio; la plantilla reproduce únicamente los tickers.
