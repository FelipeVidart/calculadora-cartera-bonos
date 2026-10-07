# Calculadora de cartera de bonos y ON · V1

Aplicación local Streamlit para flujos determinados, con lectura Excel/CSV, validaciones, análisis individual y por moneda, ladder mensual/trimestral/anual, sensibilidad y exportación Excel.

## Ejecutar

Python 3.12 recomendado:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py
```

En el entorno cloud preparado también puede usarse `/workspace/bond-venv/bin/python`. Ejecutar desde la raíz del proyecto. Cada tarea cloud ya está aislada: utilizar el checkout existente sin crear worktrees salvo pedido explícito.

## Archivos de entrada

- Pagos: `Ticker,Fecha,Renta,Amortización,Total`. Se prefiere hoja `Pagos`; de lo contrario se lee la primera hoja. Importes ya escalados a la posición; Total se recalcula, discrepancias mayores a 0.005 generan aviso. El Total informado se conserva.
- Posiciones: `Ticker,Market Value,Nominal,Moneda,Emisor`. Una fila por ticker. Market Value y moneda son obligatorios para calcular. Nominal y emisor pueden faltar con aviso y se conservan; nominal nunca escala los pagos. Usar MV **dirty** (incluye intereses corridos) en la misma moneda que los flujos.
- `sample_data/posiciones_plantilla.csv`: completar con datos reales para los tickers del adjunto. No contiene precios inventados. `*_demo.csv` contiene datos exclusivamente sintéticos. La interfaz permite probarlos sin cargar archivos.
- Fechas: celdas de fecha Excel o texto ISO AAAA-MM-DD. No se interpretan fechas ambiguas como 01/02/2027 ni seriales numéricos sin formato fecha. Sin horas.
- CSV UTF-8, separador detectado; columnas con coma decimal deben usar delimitador punto y coma o campos entre comillas. Seleccionar decimal en la interfaz. Números de texto sin separadores de miles; los números nativos de Excel se leen directamente.
- Tickers y monedas se respetan, diferenciando mayúsculas; sólo se quitan espacios externos con aviso. Utilizar consistentemente USD, ARS, etc. La moneda de los pagos se atribuye a la posición correspondiente: el usuario debe comprobar esa correspondencia.

Errores bloquean cálculos: vacíos esenciales, parseo ambiguo, negativos, MV ≤ 0, duplicados ticker/fecha en pagos o ticker en posiciones, pagos sin posición, posición sin flujos futuros positivos y moneda faltante. Si dos pagos coinciden legítimamente en ticker y fecha, consolidarlos explícitamente en el origen. No se eliminan duplicados automáticamente. Los pagos con fecha ≤ valuación se excluyen y se avisa por ticker. Falta de amortizaciones produce WAL no definida y aviso.

## Convenciones financieras

`t = días reales / 365` (ACT/365 fijo, también en años bisiestos). Tasas anuales efectivas; dominio y > −1. Se resuelve `MV = Σ CF/(1+y)^t` con búsqueda acotada sobre `log(1+y)` y Brent; flujos no negativos garantizan unicidad. Se utiliza log-sum-exp para estabilidad. No se utiliza IRR periódica. La fecha de valuación determina t=0; el flujo inicial es −MV. No se supone reinversión realizada ni rendimiento garantizado.

- Macaulay: `Σ t·PV / MV`, años.
- Modified: `Macaulay/(1+y)`, sensibilidad a tasa anual efectiva.
- Convexity: `Σ t(t+1)·PV/[MV(1+y)²]`, segunda derivada normalizada respecto de y.
- WAL: `Σ t·amortización / Σ amortización`, años. No usa cupones ni nominal histórico.
- Peso: MV individual / MV total en la moneda seleccionada.
- TIR ponderada: suma de pesos × TIR individual.
- Portfolio XIRR: descuento de todos los flujos agregados contra el MV total; distinta del promedio de TIR.
- Duration y convexity de cartera: promedio por MV de métricas individuales a sus respectivas TIR. Miden desplazamientos paralelos de esas tasas, no la duration calculada a la Portfolio XIRR.
- WAL de cartera: suma de tiempos × amortizaciones / amortizaciones totales, equivalente a ponderar WAL individuales por capital futuro. No se pondera por MV.
- Aporte duration: peso × modified duration individual.

Escenarios ±50/100/200 bps: `ΔP/P ≈ −Dmod·Δy`, y con convexity `+ 0.5·C·Δy²`. Son aproximaciones locales, no proyecciones de precios. Para tasas cercanas a −100% un shock puede exceder el dominio; no constituye un precio revaluado. No incluyen spreads de crédito independientes, defaults, FX ni cambios de flujos. Duration no representa todo el riesgo de crédito.

Las monedas se analizan separadamente; no hay total multimoneda ni conversión implícita. CER, dólar linked, tasa variable, calls, eventos corporativos, descarga de precios y APIs quedan fuera de V1.

## Arquitectura y validación

`src/io`: lectura y parseo; `src/validation`: controles cruzados; `src/fixed_income`: motor independiente; `src/portfolio`: agregación y escenarios; `app.py`: interfaz. Es posible agregar proveedores de precios y generadores de flujos posteriormente sin cambiar las fórmulas centrales.

Tests de bono cero cupón, cupones, pagos irregulares, TIR negativa, año bisiesto, WAL, convexity y duration contra derivadas numéricas, agregación manual, monedas, controles de entrada y recorrido de Streamlit. La inspección del adjunto se documenta en `docs/inspeccion_pagos.md`.

La comparación con calculadoras externas para bonos reales queda pendiente: requiere Market Values y convención equivalente. Al contrastar, registrar fecha, precio dirty, tenencia, moneda, calendario y capitalización; evitar comparar directamente tasas nominales semestrales con tasas efectivas anuales.

Los archivos cargados se procesan en memoria y no se guardan automáticamente. Esta V1 es una herramienta analítica local, sin autenticación ni persistencia de clientes.

## Desplegar en Streamlit Community Cloud

1. Conectar GitHub en https://share.streamlit.io/ y crear una aplicación.
2. Repositorio: `FelipeVidart/calculadora-cartera-bonos`; rama: `main`; archivo principal: `app.py`.
3. En opciones avanzadas elegir Python **3.12**. No se necesitan secrets ni servicios externos.
4. Desplegar y probar primero con la opción **Usar ejemplo sintético**.

La app instala las dependencias desde `requirements.txt`. Para usar datos reales de clientes, configurar acceso restringido y confirmar que el alojamiento está aprobado por la empresa. Esta V1 no incorpora autenticación propia. Los archivos se procesan en memoria, pero se transmiten al servidor que aloja la aplicación.

## Presentación y concentración

La interfaz se organiza en Resumen, Instrumentos, Flujos y Riesgos. Los resultados muestran moneda y fecha de valuación. El resumen incluye valor de mercado, ambas TIR, modified duration y WAL. La vista de emisores suma valor de mercado, peso y aporte a duration, y permite consultar los instrumentos de cada emisor.

Los emisores se agrupan por el nombre informado, quitando espacios externos; no se infieren grupos económicos ni se unifican nombres diferentes automáticamente. Completar nombres consistentemente. Los emisores faltantes aparecen bajo “Sin emisor informado”. Cada agrupación corresponde únicamente a la moneda seleccionada.

El CSV de instrumentos incorpora moneda y fecha de valuación. El Excel incluye hojas Contexto y Emisores, además del detalle existente. Los formatos visuales no redondean los valores utilizados por el motor. La suite actual contiene 32 tests.
