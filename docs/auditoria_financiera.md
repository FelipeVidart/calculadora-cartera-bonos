# Auditoría del motor financiero

Se ejecutaron 31 tests: los 17 iniciales y 14 adicionales de auditoría. No se detectaron discrepancias en las fórmulas bajo ACT/365 fijo y tasas efectivas anuales.

Verificaciones adicionales:

- Ejemplo conocido de Excel XIRR: inversión 10000 el 2008-01-01, cobros 2750 el 2008-03-01, 4250 el 2008-10-30, 3250 el 2009-02-15 y 2750 el 2009-04-01. Resultado 37.3362533518831%, tolerancia absoluta de tasa 1e-10. Se contrasta con el valor de referencia; no se ejecutó Excel durante esta auditoría.
- Doce calendarios irregulares: búsqueda por bisección directa en la tasa usando Decimal con 45 dígitos, independiente del Brent en logaritmos de producción. Tolerancia absoluta de tasa 1e-11.
- Reconciliación: el valor presente a la TIR recuperada reproduce el MV, tolerancia relativa 1e-11.
- Modified duration y convexity contra primeras y segundas derivadas numéricas del valor presente, tanto individuales como a nivel cartera.
- Invariancia de TIR, durations, convexity y WAL al multiplicar toda la posición por siete.

Caso manual: MV 100, pagos 10 a un año y 110 a dos años (renta 10 cada año y amortización 100 al final). TIR 10%; Macaulay 1.9090909091 años; modified 1.7355371901; convexity 4.6581517656; WAL 2 años; renta 20; amortización 100; flujos 120.

Caso de cartera: MV 100 con cobro 110 a un año y MV 100 con cobro 144 a dos años. TIR individuales 10% y 20%; promedio ponderado 15%; Portfolio XIRR 16.6978138746%.

## Alcance y pendientes

Esta evidencia valida el motor dentro de sus supuestos; no certifica calendarios, precios ni métricas contractuales de bonos reales. Es necesario contrastar al menos un bullet y un amortizable con una fuente externa, utilizando idénticos flujos, fecha, moneda, intereses corridos y convención de tasa. No se dispone aún del archivo de posiciones reales.

El descuento usa MV dirty de la tenencia y pagos ya escalados. Excluye fechas iguales o anteriores a valuación. No ajusta días hábiles, impuestos, costos, incumplimientos, calls ni indexaciones. La moneda del flujo se atribuye desde posiciones, porque Pagos.xlsx no la incluye. El usuario debe verificar esa correspondencia.

Duration y convexity de cartera son ponderaciones por MV de métricas a las TIR individuales. Su interpretación es un desplazamiento paralelo de esas tasas. No son las derivadas de una cartera descontada a una única Portfolio XIRR. WAL se pondera por capital futuro, no MV.

Los escenarios son aproximaciones Taylor; no se ofrecen como revaluaciones exactas. Cerca de tasas de −100%, los shocks pueden exceder el dominio. El motor requiere flujos no negativos y no admite múltiples raíces propias de flujos con cambios de signo.
