"""Display and export helpers; financial values retain their original precision."""
import pandas as pd
import altair as alt

LABELS = {'Market Value':'Valor de mercado', 'TIR ponderada':'TIR ponderada por valor de mercado',
          'Macaulay':'Duration Macaulay (años)', 'Modified':'Modified duration (años)',
          'WAL':'WAL (años)', 'Convexity':'Convexidad', 'Aporte duration':'Aporte a duration (años)',
          'Flujos':'Flujos futuros', 'Peso':'Peso en cartera'}
PERCENT = {'TIR','Peso','TIR ponderada','Portfolio XIRR','ΔP/P duration','ΔP/P convexity'}
MONEY = {'Market Value','Renta','Amortización','Total','Flujo Total','Flujos','Importe próximo pago','ΔMV duration','ΔMV convexity','Nominal'}
YEARS = {'Macaulay','Modified','WAL','Aporte duration','Convexity'}


def display_table(df):
    df = df.copy()
    formats = {}
    for c in df.columns:
        if c in PERCENT: formats[LABELS.get(c,c)] = '{:.2%}'
        elif c in MONEY: formats[LABELS.get(c,c)] = '{:,.2f}'
        elif c in YEARS: formats[LABELS.get(c,c)] = '{:.2f}'
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime('%d/%m/%Y')
    return df.rename(columns=LABELS).style.format(formats, na_rep='Sin dato')


def horizontal_chart(df, category, value, percent=False):
    return alt.Chart(df).mark_bar().encode(
        y=alt.Y(f'{category}:N', sort='-x', title=None),
        x=alt.X(f'{value}:Q', title=LABELS.get(value,value), axis=alt.Axis(format='.1%' if percent else ',.2f')),
        tooltip=[alt.Tooltip(f'{category}:N'),alt.Tooltip(f'{value}:Q', format='.2%' if percent else ',.2f')])


def sensitivity_chart(df):
    long=df.melt('Shock bps', value_vars=['ΔP/P duration','ΔP/P convexity'], var_name='Aproximación',value_name='Variación')
    return alt.Chart(long).mark_line(point=True).encode(
        x=alt.X('Shock bps:Q', title='Cambio de tasas (bps)', scale=alt.Scale(domain=[-200,200])),
        y=alt.Y('Variación:Q', title='Variación estimada de valor', axis=alt.Axis(format='.1%')),
        color='Aproximación:N', tooltip=['Shock bps', 'Aproximación',alt.Tooltip('Variación:Q',format='.2%')])
