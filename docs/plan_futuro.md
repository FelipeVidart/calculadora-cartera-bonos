# Plan futuro — Calculadora de cartera de bonos y ON

Estado: propuestas para próximas iteraciones; no implementadas por este documento.

## 1. Validación con instrumentos reales

- Comparar un bono bullet y uno amortizable con una calculadora externa.
- Igualar fecha, flujos, moneda, tenencia, precio dirty y convención de tasa antes de comparar.
- Reemplazar el TC ilustrativo de 1.500 ARS/USD por una referencia explícita de la fecha de valuación.
- Confirmar si el Valor Actual de la comitente incluye intereses corridos.

## 2. Presentación y navegación

- Pestañas: Resumen, Instrumentos, Flujos y Riesgos.
- Importes con dos decimales, porcentajes consistentes y fechas sin horas.
- Destacar modified duration y WAL junto a ambas TIR.
- Formatear el eje de sensibilidad como porcentaje.
- Gráficos horizontales, calendario legible y concentración por emisor además de ticker.
- Mantener controles visibles y supuestos accesibles.

## 3. Monedas y patrimonio consolidado

- Separar moneda de cotización, moneda del Market Value y moneda efectiva de los flujos.
- Mantener métricas por moneda: ARS y USD, sin conversión implícita.
- Elegir moneda base para patrimonio consolidado; convertir MV con TC, fuente y fecha explícitos.
- Mostrar pesos y concentración sobre ese patrimonio consolidado.
- No interpretar una conversión del MV actual como una proyección de flujos futuros en USD.
- Separar shocks de tasas ARS, tasas USD y FX.

## 4. Escenarios cambiarios y XIRR en USD

- Usar una trayectoria ARS por USD, con MEP como referencia inicial configurable.
- Convertir cada flujo ARS: flujo USD(t) = flujo ARS(t) / TC(t).
- Convertir el MV inicial a USD y recalcular la XIRR de los flujos convertidos.
- Mantener en USD los pagos de las ON denominadas en USD, aunque coticen en ARS.
- Mostrar el resultado como “XIRR en USD bajo escenario”, separado de las métricas por moneda.
- Primera versión: TC(t) = TC inicial × (1 + devaluación anual efectiva)^t.
- Escenarios configurables: peso más fuerte, base y peso más débil, sin tratarlos como certezas.
- Tabla de sensibilidad cruzando tasas de interés y devaluación, con supuestos compatibles y visibles.
- Alternativas posteriores: inflación argentina/estadounidense y ajuste de tipo de cambio real; REM; futuros de dólar.
- Registrar que REM y futuros pueden referirse al oficial; requieren supuestos adicionales para MEP. Los futuros no son una predicción pura.
- UVA/CER no proyectan automáticamente el dólar: reflejan inflación con rezagos y reglas propias.
- Para bonos indexados, proyectar primero pagos ARS con las condiciones contractuales y luego aplicar el escenario FX. Fuera del motor de flujos determinados de V1.

## 5. Fondos de renta fija

- Incorporar fondos al patrimonio y concentración, aunque no tengan cash flows determinados.
- Input: valor de posición, moneda, categoría, duration informada, fecha y fuente; composición y rendimiento informado cuando estén disponibles.
- Usar modified duration informada para sensibilidad aproximada sólo cuando su definición sea compatible.
- Mostrar cobertura: porcentaje del MV con duration conocida; datos faltantes no equivalen a cero.
- No inventar pagos, WAL ni XIRR a partir de cuotapartes.
- Distinguir TIR de activos subyacentes, rendimiento histórico y retorno futuro de la cuotaparte.

## 6. Rebalanceo hacia duration objetivo

- Calculadora de duration necesaria para la compra: D final = D actual + w × (D compra − D venta).
- Supuesto: reemplazo de igual MV, misma moneda, reinversión completa, sin costos ni aportes/retiros. Duration no equivale a vencimiento.
- Simulador manual de ventas/compras: efectos en duration, TIR, concentración y cash flows.
- Incorporar un universo de candidatos con precios, flujos, moneda, emisor, crédito y liquidez.
- Optimización posterior: alcanzar duration objetivo minimizando operaciones o costos.
- Restricciones: moneda, monto, concentración por emisor, crédito, liquidez, vencimientos y mínimos de negociación.
- No seleccionar instrumentos únicamente por TIR o duration.

## 7. Despliegue para información de clientes

- Demo con datos sintéticos.
- Antes de uso real, alojamiento aprobado por la empresa y acceso restringido.
- Recordar que procesar archivos en memoria no evita su transmisión al servidor.

## Orden sugerido

1. Validación real y presentación.
2. Monedas y consolidación patrimonial.
3. Escenarios FX y sensibilidad conjunta.
4. Fondos con métricas informadas y cobertura visible.
5. Simulador de rebalanceo y luego optimización.

No se asignan fechas ni se presume disponibilidad de proveedores o datos.
