import numpy as np
import pandas as pd
from src.fixed_income.engine import metrics, year_fractions, xirr


def analyze(payments, positions, valuation):
    """Call only after input validation. One currency per analysis."""
    if positions.Moneda.nunique() != 1:
        raise ValueError('Analizar una moneda por vez')
    rows = []
    for _, pos in positions.iterrows():
        f = payments[payments.Ticker == pos.Ticker].sort_values('Fecha')
        m = metrics(pos['Market Value'], year_fractions(f.Fecha, valuation), f.Renta, f['Amortización'])
        first = f[f['Flujo Total'] > 0].iloc[0]
        rows.append({**pos.to_dict(), **m, 'Próximo pago': first.Fecha,
                     'Importe próximo pago': first['Flujo Total'], 'Último flujo': f.loc[f['Flujo Total'] > 0, 'Fecha'].max()})
    instruments = pd.DataFrame(rows)
    mv = instruments['Market Value'].sum()
    instruments['Peso'] = instruments['Market Value'] / mv
    instruments['Aporte duration'] = instruments.Peso * instruments.Modified
    summary = {'Market Value': mv, 'TIR ponderada': np.dot(instruments.Peso, instruments.TIR),
               'Portfolio XIRR': xirr(mv, year_fractions(payments.Fecha, valuation), payments['Flujo Total'])}
    for col in ['Macaulay', 'Modified', 'Convexity']:
        summary[col] = np.dot(instruments.Peso, instruments[col])
    principal = payments['Amortización'].sum()
    summary['WAL'] = np.dot(year_fractions(payments.Fecha, valuation), payments['Amortización']) / principal if principal else np.nan
    for col in ['Renta', 'Amortización', 'Flujos']:
        summary[col] = instruments[col].sum()
    return instruments, summary


def ladder(payments, frequency):
    df = payments.copy()
    df['Período'] = df.Fecha.dt.to_period(frequency).astype(str)
    return df.groupby('Período')[['Renta', 'Amortización', 'Flujo Total']].sum()


def issuer_concentration(instruments):
    """Issuer exposure within the selected currency; missing issuers stay visible."""
    df = instruments.copy()
    df['Emisor'] = df.Emisor.fillna('').astype(str).str.strip().replace('', 'Sin emisor informado')
    grouped = df.groupby('Emisor', sort=False).agg(
        **{'Market Value': ('Market Value', 'sum'), 'Peso': ('Peso', 'sum'),
           'Aporte duration': ('Aporte duration', 'sum'),
           'Instrumentos': ('Ticker', lambda x: ', '.join(sorted(x)))})
    return grouped.sort_values('Market Value', ascending=False).reset_index()
