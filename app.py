from datetime import date
from io import BytesIO
import pandas as pd
import streamlit as st
from src.io.loaders import read_table
from src.validation.validators import validate_portfolio
from src.portfolio.analytics import analyze, ladder, issuer_concentration
from src.portfolio.scenarios import scenarios
from src.portfolio.currencies import normalize_positions, consolidate
from src.portfolio.rebalance import simulate
from src.presentation.views import display_table, horizontal_chart, sensitivity_chart

st.set_page_config(page_title='Cartera de bonos', layout='wide')
st.title('Cartera de bonos y ON')
st.caption('V1 · Flujos determinados · ACT/365 fijo · Tasas efectivas anuales')
st.info('El valor de mercado debe incluir intereses corridos. Moneda identifica los pagos; Moneda MV identifica el valor de mercado (opcional: se asume igual a Moneda). Los importes de pagos ya representan la tenencia: no se multiplican por nominal.')
with st.sidebar:
    valuation = st.date_input('Fecha de valuación', date.today(), min_value=date(1900,1,1), max_value=date(2200,1,1))
    decimal = st.selectbox('Separador decimal para números de texto', ['.', ','])
    st.caption('Sin separadores de miles. Fechas: celdas Excel o AAAA-MM-DD. CSV UTF-8.')
    pfile = st.file_uploader('Pagos futuros', type=['xlsx','csv'])
    vfile = st.file_uploader('Posiciones actuales', type=['xlsx','csv'])
    st.download_button('Plantilla de posiciones', 'Ticker,Market Value,Nominal,Moneda,Emisor,Moneda MV\n', 'posiciones.csv', 'text/csv')
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
needs_fx = positions.Moneda.nunique() > 1 or (positions.Moneda != positions['Moneda MV']).any()
fx = 1.0
fx_date = valuation
fx_source = 'No requiere conversión'
base = positions.Moneda.iloc[0]
consolidated = consolidated_issuers = currency_exposure = None
if needs_fx:
    st.subheader('Tipo de cambio para valuación y patrimonio')
    st.caption('Sólo convierte valores actuales. No proyecta el dólar ni convierte pagos futuros. Moneda = moneda de pagos; Moneda MV = moneda del valor ingresado.')
    fx = st.number_input('TC: ARS por USD', min_value=0.0, value=0.0, step=10.0)
    fx_date = st.date_input('Fecha del tipo de cambio', valuation)
    fx_source = st.text_input('Fuente del tipo de cambio', placeholder='Ej.: MEP del broker, cierre de la fecha')
    base = st.selectbox('Moneda base del patrimonio', ['USD','ARS'])
    if fx <= 0 or not fx_source.strip():
        st.info('Ingresá TC positivo y fuente para continuar. No se usa una cotización supuesta automáticamente.')
        st.stop()
    if fx_date != valuation:
        st.warning('La fecha del TC difiere de la valuación; la conversión puede no representar esa fecha.')
    try:
        consolidated, consolidated_issuers, currency_exposure = consolidate(positions, base, fx)
        positions = normalize_positions(positions, fx)
    except ValueError as e:
        st.error(str(e)); st.stop()
else:
    positions['Valor de mercado original'] = positions['Market Value']
    if base in ['USD','ARS']:
        consolidated, consolidated_issuers, currency_exposure = consolidate(positions, base, fx)
if positions.Moneda.nunique() > 1:
    st.warning('TIR, duration y sensibilidad se calculan por moneda de pagos. El patrimonio consolidado no tiene una TIR multimoneda.')
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
resume_tab, instruments_tab, flows_tab, risk_tab, rebalance_tab = st.tabs(['Resumen', 'Instrumentos', 'Flujos', 'Riesgos', 'Rebalanceo'])
with resume_tab:
    if consolidated is not None:
        st.subheader(f'Patrimonio consolidado · {base}')
        st.metric('Patrimonio total', f"{consolidated['Valor consolidado'].sum():,.2f} {base}")
        st.caption(f'TC: {fx:,.2f} ARS/USD · Fecha: {fx_date:%d/%m/%Y} · Fuente: {fx_source}' if needs_fx else 'Todas las posiciones están en la misma moneda; no se requiere conversión.')
        st.dataframe(display_table(currency_exposure), hide_index=True)
        st.dataframe(display_table(consolidated_issuers), hide_index=True)
        st.altair_chart(horizontal_chart(consolidated_issuers, 'Emisor', 'Peso consolidado', percent=True), use_container_width=True)
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
with rebalance_tab:
    st.subheader(f'Duration objetivo · {currency}')
    st.caption('Reemplazo de igual valor de mercado, dentro de la moneda seleccionada, reinversión completa y sin costos. La compra es hipotética: no genera TIR ni calendario nuevos. Duration no equivale a vencimiento.')
    sell_ticker = st.selectbox('Instrumento a vender', instruments.Ticker.tolist())
    sale = instruments.loc[instruments.Ticker == sell_ticker].iloc[0]
    amount = st.number_input(f'Importe a reemplazar ({currency})', min_value=0.0, max_value=float(sale['Market Value']), value=float(sale['Market Value']), step=1.0)
    target = st.number_input('Modified duration objetivo (años)', min_value=0.0, value=float(summary['Modified']), step=0.1)
    purchase = st.number_input('Modified duration de compra hipotética (años)', min_value=0.0, value=float(sale.Modified), step=0.1)
    if amount > 0:
        result = simulate(float(summary['Market Value']), float(summary['Modified']), amount, float(sale.Modified), target, purchase)
        st.metric('Duration necesaria de la compra', f"{result['Duration necesaria de compra']:.2f} años")
        if result['Duration necesaria de compra'] < 0:
            st.warning('El objetivo no es alcanzable con esta venta y una compra de duration no negativa. Cambiá el importe o el instrumento vendido.')
        st.dataframe(pd.DataFrame([result]).style.format('{:,.2f}'), hide_index=True)
        st.caption('D final = D actual + (importe reemplazado / valor de cartera) × (D compra − D venta). La venta no puede superar la posición disponible.')
    else:
        st.info('Ingresá un importe de venta mayor que cero para simular.')
with st.expander('Supuestos y fórmulas'):
    st.markdown('''**t = días reales / 365**. MV = Σ CF / (1+y)^t; y es anual efectiva, mayor que −100%.

Macaulay = Σ t·PV / MV. Modified = Macaulay / (1+y). Convexity = Σ t(t+1)·PV / [MV·(1+y)²]. WAL = Σ t·amortización / Σ amortización.

Duration y convexity de cartera se ponderan por MV usando las tasas de cada instrumento. WAL de cartera se pondera por amortizaciones futuras, no por MV. Los pagos en o antes de valuación se excluyen explícitamente.

Los escenarios aplican un desplazamiento paralelo de las tasas individuales: ΔP/P ≈ −Dmod·Δy + ½C·Δy². Es una aproximación local de sensibilidad, no una proyección de precio. Cerca de y = −100%, los shocks pueden quedar fuera del dominio financiero.

La TIR no es rendimiento garantizado; supone cumplimiento de los flujos. Duration no mide todo el riesgo de crédito. No se modelan CER, dólar linked, tasa variable, calls, FX ni eventos corporativos.''')
# Export analyzed data; client uploads are kept in memory only.
out = BytesIO()
with pd.ExcelWriter(out, engine='openpyxl') as writer:
    pd.DataFrame([{'Fecha de valuación': pd.Timestamp(valuation), 'Moneda de análisis': currency, 'Moneda base': base, 'TC ARS/USD': fx if needs_fx else None, 'Fecha TC': pd.Timestamp(fx_date) if needs_fx else None, 'Fuente TC': fx_source, 'Convención': 'ACT/365 fijo; tasa efectiva anual'}]).to_excel(writer, sheet_name='Contexto', index=False)
    if consolidated is not None:
        consolidated.to_excel(writer, sheet_name='Patrimonio', index=False)
        consolidated_issuers.to_excel(writer, sheet_name='Emisores consolidados', index=False)
        currency_exposure.to_excel(writer, sheet_name='Monedas', index=False)
    if amount > 0:
        pd.DataFrame([{**result, 'Instrumento vendido': sell_ticker, 'Moneda': currency, 'Duration venta': float(sale.Modified), 'Duration compra hipotética': purchase}]).to_excel(writer, sheet_name='Rebalanceo', index=False)
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
