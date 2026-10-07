import pandas as pd


def validate_portfolio(payments, positions, valuation):
    issues = []
    def add(level, ticker, message):
        issues.append(dict(Nivel=level, Archivo='cartera', Fila=None, Campo=ticker, Mensaje=message))
    future = payments.loc[payments.Fecha > pd.Timestamp(valuation)].copy()
    old = payments.loc[payments.Fecha <= pd.Timestamp(valuation)]
    for ticker, group in old.groupby('Ticker'):
        add('warning', ticker, f'{len(group)} pagos anteriores o iguales a valuación excluidos')
    for ticker in set(payments.Ticker) - set(positions.Ticker):
        add('error', ticker, 'Pagos sin posición')
    for ticker in set(positions.Ticker):
        f = future[future.Ticker == ticker]
        if f.empty or f['Flujo Total'].sum() <= 0:
            add('error', ticker, 'Posición sin flujos futuros positivos')
        elif f['Amortización'].sum() == 0:
            add('warning', ticker, 'Sin amortización futura: WAL no definida; comprobar completitud')
    if positions.Moneda.nunique() > 1:
        add('warning', 'Moneda', 'Monedas múltiples: métricas por moneda; consolidación patrimonial requiere TC explícito')
    return future, issues
