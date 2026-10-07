"""Spot conversion for valuation only; future payments are never converted."""
import numpy as np


def normalize_positions(positions, ars_per_usd):
    if not np.isfinite(ars_per_usd) or ars_per_usd <= 0:
        raise ValueError('TC debe ser positivo y finito')
    df = positions.copy()
    for col in ['Moneda', 'Moneda MV']:
        if not df[col].isin(['ARS', 'USD']).all():
            raise ValueError('Esta consolidación admite únicamente ARS y USD')
    df['Valor de mercado original'] = df['Market Value']
    df['Market Value'] = [value if source == target else value / ars_per_usd if source == 'ARS' else value * ars_per_usd
                          for value, source, target in zip(df['Market Value'], df['Moneda MV'], df.Moneda)]
    return df


def consolidate(positions, base, ars_per_usd):
    if base not in ['ARS','USD']:
        raise ValueError('Moneda base inválida')
    df = normalize_positions(positions, ars_per_usd)
    df['Valor consolidado'] = [v if m == base else v / ars_per_usd if m == 'ARS' else v * ars_per_usd
                              for v, m in zip(df['Market Value'], df.Moneda)]
    df['Peso consolidado'] = df['Valor consolidado'] / df['Valor consolidado'].sum()
    df['Moneda base'] = base
    df['Emisor'] = df.Emisor.fillna('').astype(str).str.strip().replace('', 'Sin emisor informado')
    issuers = df.groupby('Emisor')[['Valor consolidado','Peso consolidado']].sum().reset_index()
    currencies = df.groupby('Moneda')[['Valor consolidado','Peso consolidado']].sum().reset_index()
    return df, issuers, currencies
