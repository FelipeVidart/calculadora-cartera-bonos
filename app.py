from datetime import date
from io import BytesIO
import pandas as pd
import streamlit as st
from src.io.loaders import read_table
from src.validation.validators import validate_portfolio
from src.portfolio.analytics import analyze, ladder
from src.portfolio.scenarios import scenarios

st.set_page_config(page_title='Cartera de bonos', layout='wide')
st.title('Cartera de bonos y ON')
st.caption('V1 · Flujos determinados · ACT/365 fijo · Tasas efectivas anuales')
st.info('Market Value debe incluir intereses corridos y estar en la moneda de los flujos. Los importes de pagos ya representan la tenencia: no se multiplican por nominal.')
with st.sidebar:
    valuation = st.date_input('Fecha de valuación', date.today(), min_value=date(1900,1,1), max_value=date(2200,1,1))
    decimal = st.selectbox('Separador decimal para números de texto', ['.', ','])
    st.caption('Sin separadores de miles. Fechas: celdas Excel o AAAA-MM-DD. CSV UTF-8.')
    pfile = st.file_uploader('Pagos futuros', type=['xlsx','csv'])
    vfile = st.file_uploader('Posiciones actuales', type=['xlsx','csv'])
    st.download_button('Plantilla de posiciones', 'Ticker,Market Value,Nominal,Moneda,Emisor\n', 'posiciones.csv', 'text/csv')
    demo = st.checkbox('Usar ejemplo sintético', value=False)
if demo:
    pfile, vfile = 'sample_data/pagos_demo.csv', 'sample_data/posiciones_demo.csv'
    valuation = date(2026,10,7)
    st.warning('Ejemplo ficticio; no representa valores de mercado ni la cartera del cliente.')
if not pfile or not vfile:
    st.write('Cargá ambos archivos para analizar la cartera. Podés probar el ejemplo sintético.')
    st.stop()
try:
    payments, pi = read_table(pfile, 'payments', decimal)
    positions, vi = read_table(vfile, 'positions', decimal)
    future, ci = validate_portfolio(payments, positions, valuation)
except Exception as e:
    st.error(f'No se pudo leer el archivo: {e}')
    st.stop()
issues = pi + vi + ci
if issues:
    st.subheader('Controles de datos')
    st.dataframe(pd.DataFrame(issues), hide_index=True)
if any(x['Nivel'] == 'error' for x in issues):
    st.error('Corregí los errores en los archivos antes de calcular.')
    st.stop()
if positions.Moneda.nunique() > 1:
    st.warning('No se suman monedas distintas. Cada análisis usa sólo la moneda seleccionada.')
currency = st.selectbox('Moneda de análisis', sorted(positions.Moneda.unique()))
positions = positions[positions.Moneda == currency]
future = future[future.Ticker.isin(positions.Ticker)]
try:
    instruments, summary = analyze(future, positions, valuation)
except ValueError as e:
    st.error(f'No se pudo calcular: {e}')
    st.stop()
st.subheader(f'Resumen de cartera · {currency}')
cols = st.columns(3)
cols[0].metric('Market Value', f"{summary['Market Value']:,.2f}")
cols[1].metric('TIR ponderada por MV', f"{summary['TIR ponderada']:.2%}")
cols[2].metric('Portfolio XIRR', f"{summary['Portfolio XIRR']:.2%}")
st.caption('La TIR ponderada promedia tasas individuales; Portfolio XIRR descuenta los flujos agregados contra el MV total.')
st.dataframe(pd.DataFrame([summary]), hide_index=True)
st.subheader('Instrumentos')
st.dataframe(instruments, hide_index=True, column_config={c: st.column_config.NumberColumn(c, format='percent') for c in ['TIR','Peso']})
st.download_button('Exportar métricas por instrumento', instruments.to_csv(index=False).encode('utf-8-sig'), 'instrumentos.csv', 'text/csv')
st.subheader('Cash-flow ladder')
frequency = st.selectbox('Agrupar pagos', ['Mes', 'Trimestre', 'Año'])
agg = ladder(future, {'Mes':'M','Trimestre':'Q','Año':'Y'}[frequency])
st.dataframe(agg)
st.bar_chart(agg[['Renta','Amortización']], stack=True)
st.subheader('Flujos por año: renta y amortización')
st.bar_chart(ladder(future, 'Y')[['Renta','Amortización']], stack=True)
st.subheader('Distribución de Market Value')
st.bar_chart(instruments.set_index('Ticker')[['Market Value']])
st.subheader('Aporte a modified duration')
st.bar_chart(instruments.set_index('Ticker')[['Aporte duration']])
st.subheader('Sensibilidad a tasas')
sens = scenarios(summary)
st.dataframe(sens, hide_index=True, column_config={c:st.column_config.NumberColumn(c, format='percent') for c in ['ΔP/P duration','ΔP/P convexity']})
st.line_chart(sens.set_index('Shock bps')[['ΔP/P duration','ΔP/P convexity']])
with st.expander('Supuestos y fórmulas'):
    st.markdown('''**t = días reales / 365**. MV = Σ CF / (1+y)^t; y es anual efectiva, mayor que −100%.

Macaulay = Σ t·PV / MV. Modified = Macaulay / (1+y). Convexity = Σ t(t+1)·PV / [MV·(1+y)²]. WAL = Σ t·amortización / Σ amortización.

Duration y convexity de cartera se ponderan por MV usando las tasas de cada instrumento. WAL de cartera se pondera por amortizaciones futuras, no por MV. Los pagos en o antes de valuación se excluyen explícitamente.

Los escenarios aplican un desplazamiento paralelo de las tasas individuales: ΔP/P ≈ −Dmod·Δy + ½C·Δy². Es una aproximación local de sensibilidad, no una proyección de precio. Cerca de y = −100%, los shocks pueden quedar fuera del dominio financiero.

La TIR no es rendimiento garantizado; supone cumplimiento de los flujos. Duration no mide todo el riesgo de crédito. No se modelan CER, dólar linked, tasa variable, calls, FX ni eventos corporativos.''')
# Export analyzed data; client uploads are kept in memory only.
out = BytesIO()
with pd.ExcelWriter(out, engine='openpyxl') as writer:
    instruments.to_excel(writer, sheet_name='Instrumentos', index=False)
    pd.DataFrame([summary]).to_excel(writer, sheet_name='Cartera', index=False)
    future.to_excel(writer, sheet_name='Pagos', index=False)
    sens.to_excel(writer, sheet_name='Escenarios', index=False)
    for name, freq in [('Mes','M'), ('Trimestre','Q'), ('Año','Y')]:
        ladder(future, freq).to_excel(writer, sheet_name=name)
st.download_button('Exportar análisis Excel', out.getvalue(), 'analisis.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
