from datetime import date
from io import BytesIO
import pandas as pd
import streamlit as st
from src.io.loaders import read_table
from src.validation.validators import validate_portfolio
from src.portfolio.analytics import analyze, ladder, issuer_concentration
from src.portfolio.scenarios import scenarios
from src.presentation.views import display_table, horizontal_chart, sensitivity_chart

st.set_page_config(page_title='Cartera de bonos', layout='wide')
st.title('Cartera de bonos y ON')
st.caption('V1 · Flujos determinados · ACT/365 fijo · Tasas efectivas anuales')
st.info('El valor de mercado debe incluir intereses corridos y estar en la moneda de los flujos. Los importes de pagos ya representan la tenencia: no se multiplican por nominal.')
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
    controls = pd.DataFrame(issues)
    controls['Nivel'] = controls.Nivel.replace({'warning':'Advertencia','error':'Error'})
    controls['Archivo'] = controls.Archivo.replace({'payments':'Pagos','positions':'Posiciones','cartera':'Cartera'})
    controls['Campo'] = controls.Campo.replace({'Market Value':'Valor de mercado'})
    controls['Mensaje'] = controls.Mensaje.str.replace('Market Value', 'valor de mercado', regex=False)
    st.dataframe(controls, hide_index=True)
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
st.info(f"Moneda: {currency} · Fecha de valuación: {valuation:%d/%m/%Y}")
issuers = issuer_concentration(instruments)
sens = scenarios(summary)
resume_tab, instruments_tab, flows_tab, risk_tab = st.tabs(['Resumen', 'Instrumentos', 'Flujos', 'Riesgos'])
with resume_tab:
    st.subheader(f'Resumen de cartera · {currency}')
    cols = st.columns(3)
    cols[0].metric('Valor de mercado', f"{summary['Market Value']:,.2f} {currency}")
    cols[1].metric('TIR ponderada por valor de mercado', f"{summary['TIR ponderada']:.2%}")
    cols[2].metric('Portfolio XIRR', f"{summary['Portfolio XIRR']:.2%}")
    cols = st.columns(2)
    cols[0].metric('Modified duration', f"{summary['Modified']:.2f} años")
    cols[1].metric('WAL', f"{summary['WAL']:.2f} años" if pd.notna(summary['WAL']) else 'Sin dato')
    st.caption('La TIR ponderada promedia tasas individuales; Portfolio XIRR descuenta los flujos agregados contra el valor de mercado total.')
    st.dataframe(display_table(pd.DataFrame([summary])), hide_index=True)
    st.subheader('Concentración por emisor')
    st.caption('Pesos y aportes calculados sobre la cartera de la moneda seleccionada. Los emisores sin informar se muestran juntos; no se infieren grupos económicos.')
    st.dataframe(display_table(issuers), hide_index=True)
    st.altair_chart(horizontal_chart(issuers, 'Emisor', 'Peso', percent=True), use_container_width=True)
    selected_issuer = st.selectbox('Detalle de emisor', issuers.Emisor.tolist())
    names = instruments.Emisor.fillna('').astype(str).str.strip().replace('', 'Sin emisor informado')
    st.dataframe(display_table(instruments.loc[names == selected_issuer, ['Ticker','Market Value','Peso','Modified','Aporte duration']]), hide_index=True)
with instruments_tab:
    st.subheader('Instrumentos')
    st.dataframe(display_table(instruments), hide_index=True)
    exported = instruments.assign(**{'Fecha de valuación': valuation, 'Moneda de análisis': currency})
    st.download_button('Exportar métricas por instrumento', exported.to_csv(index=False).encode('utf-8-sig'), 'instrumentos.csv', 'text/csv')
    st.subheader('Distribución de valor de mercado')
    st.altair_chart(horizontal_chart(instruments, 'Ticker', 'Market Value'), use_container_width=True)
with flows_tab:
    st.subheader('Calendario de pagos')
    frequency = st.selectbox('Agrupar pagos', ['Mes', 'Trimestre', 'Año'])
    agg = ladder(future, {'Mes':'M','Trimestre':'Q','Año':'Y'}[frequency])
    st.dataframe(display_table(agg))
    st.bar_chart(agg[['Renta','Amortización']], stack=True)
    st.subheader('Flujos por año: renta y amortización')
    st.bar_chart(ladder(future, 'Y')[['Renta','Amortización']], stack=True)
with risk_tab:
    st.subheader('Aporte a modified duration por instrumento')
    st.altair_chart(horizontal_chart(instruments, 'Ticker', 'Aporte duration'), use_container_width=True)
    st.subheader('Aporte a modified duration por emisor')
    st.altair_chart(horizontal_chart(issuers, 'Emisor', 'Aporte duration'), use_container_width=True)
    st.subheader('Sensibilidad a tasas')
    st.caption('Aproximación de sensibilidad a desplazamientos paralelos de tasas individuales; no es una proyección de precios.')
    st.dataframe(display_table(sens), hide_index=True)
    st.altair_chart(sensitivity_chart(sens), use_container_width=True)
with st.expander('Supuestos y fórmulas'):
    st.markdown('''**t = días reales / 365**. MV = Σ CF / (1+y)^t; y es anual efectiva, mayor que −100%.

Macaulay = Σ t·PV / MV. Modified = Macaulay / (1+y). Convexity = Σ t(t+1)·PV / [MV·(1+y)²]. WAL = Σ t·amortización / Σ amortización.

Duration y convexity de cartera se ponderan por MV usando las tasas de cada instrumento. WAL de cartera se pondera por amortizaciones futuras, no por MV. Los pagos en o antes de valuación se excluyen explícitamente.

Los escenarios aplican un desplazamiento paralelo de las tasas individuales: ΔP/P ≈ −Dmod·Δy + ½C·Δy². Es una aproximación local de sensibilidad, no una proyección de precio. Cerca de y = −100%, los shocks pueden quedar fuera del dominio financiero.

La TIR no es rendimiento garantizado; supone cumplimiento de los flujos. Duration no mide todo el riesgo de crédito. No se modelan CER, dólar linked, tasa variable, calls, FX ni eventos corporativos.''')
# Export analyzed data; client uploads are kept in memory only.
out = BytesIO()
with pd.ExcelWriter(out, engine='openpyxl') as writer:
    pd.DataFrame([{'Fecha de valuación': pd.Timestamp(valuation), 'Moneda de análisis': currency, 'Convención': 'ACT/365 fijo; tasa efectiva anual'}]).to_excel(writer, sheet_name='Contexto', index=False)
    issuers.to_excel(writer, sheet_name='Emisores', index=False)
    exported.to_excel(writer, sheet_name='Instrumentos', index=False)
    pd.DataFrame([summary]).to_excel(writer, sheet_name='Cartera', index=False)
    future.to_excel(writer, sheet_name='Pagos', index=False)
    sens.to_excel(writer, sheet_name='Escenarios', index=False)
    for name, freq in [('Mes','M'), ('Trimestre','Q'), ('Año','Y')]:
        ladder(future, freq).to_excel(writer, sheet_name=name)
    for sheet in writer.book.worksheets:
        headers = {c.column: c.value for c in sheet[1]}
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                header = headers[cell.column]
                if cell.is_date: cell.number_format = 'DD/MM/YYYY'
                elif header in ['TIR','Peso','TIR ponderada','Portfolio XIRR','ΔP/P duration','ΔP/P convexity']: cell.number_format = '0.00%'
                elif isinstance(cell.value, (int,float)): cell.number_format = '#,##0.00'
st.download_button('Exportar análisis Excel', out.getvalue(), 'analisis.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
