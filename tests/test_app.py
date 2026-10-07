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

    assert [tab.label for tab in app.tabs] == ['Resumen','Instrumentos','Flujos','Riesgos','Rebalanceo']
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
