from streamlit.testing.v1 import AppTest


def test_streamlit_demo():
    app=AppTest.from_file('../app.py', default_timeout=30).run()
    assert not app.exception
    app.checkbox[0].check().run()
    assert not app.exception
    assert len(app.metric)==7
    assert app.metric[0].value=='200.00 USD'
    assert len(app.dataframe)>=4
    next(s for s in app.selectbox if s.label == 'Agrupar pagos').select('Trimestre').run()
    assert not app.exception

    assert [tab.label for tab in app.tabs] == ['Resumen','Instrumentos','Flujos','Riesgos','Rebalanceo','Fondos']
    assert any('07/10/2026' in item.value and 'USD' in item.value for item in app.info)
    selector = next(s for s in app.selectbox if s.label == 'Detalle de emisor')
    selector.select('Emisor ficticio B').run()
    assert not app.exception
    assert any('DEMO2' in str(table.value) for table in app.dataframe)


def test_mixed_currency_interface(monkeypatch):
    import src.io.loaders as loaders
    original = loaders.read_table
    def mixed(source, kind, decimal='.'):
        df, issues = original(source, kind, decimal)
        if kind == 'positions':
            df.loc[df.Ticker == 'DEMO2', 'Moneda'] = 'ARS'
            df.loc[df.Ticker == 'DEMO2', 'Moneda MV'] = 'ARS'
            df.loc[df.Ticker == 'DEMO2', 'Market Value'] = 150000.
        return df, issues
    monkeypatch.setattr(loaders, 'read_table', mixed)
    app=AppTest.from_file('../app.py', default_timeout=30).run()
    app.checkbox[0].check().run()
    assert not app.exception
    assert len(app.metric)==0
    next(n for n in app.number_input if n.label=='TC: ARS por USD').set_value(1500.).run()
    next(t for t in app.text_input if t.label=='Fuente del tipo de cambio').set_value('TC sintético').run()
    assert not app.exception
    assert app.metric[0].value=='200.00 USD'
    next(s for s in app.selectbox if s.label=='Moneda de análisis').select('USD').run()
    assert not app.exception
    assert next(m for m in app.metric if m.label=='Valor de mercado').value=='100.00 USD'
    next(n for n in app.number_input if n.label.startswith('Importe a reemplazar')).set_value(0.).run()
    assert not app.exception


def test_add_fixed_income_fund():
    import json
    from pathlib import Path
    cat=json.loads((Path(__file__).parents[1]/'data/fixed_income_funds.json').read_text())
    row=next(r for r in cat['classes'] if r['Moneda']=='USD')
    label=f"{row['Nombre']} · {row['Clase']}"
    app=AppTest.from_file('../app.py',default_timeout=30).run()
    app.checkbox[0].check().run()
    app.multiselect[0].select(label).run()
    assert not app.exception
    next(n for n in app.number_input if n.label=='Valor de mercado de la tenencia').set_value(100.).run()
    assert not app.exception
    assert app.metric[0].value=='300.00 USD'
    assert next(m for m in app.metric if m.label=='Valor de mercado').value=='200.00 USD'
    coverage=next(t.value for t in app.dataframe if 'Cobertura duration' in t.value.columns)
    assert abs(coverage['Cobertura duration'].iloc[0] - 2/3) < 1e-12
    from src.io.loaders import read_table
    from src.portfolio.analytics import analyze
    from datetime import date
    p,_=read_table('sample_data/pagos_demo.csv','payments')
    v,_=read_table('sample_data/posiciones_demo.csv','positions')
    _,summary=analyze(p,v,date(2026,10,7))
    assert next(m for m in app.metric if m.label=='Portfolio XIRR').value==f"{summary['Portfolio XIRR']:.2%}"
