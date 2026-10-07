from streamlit.testing.v1 import AppTest


def test_streamlit_demo():
    app=AppTest.from_file('../app.py', default_timeout=30).run()
    assert not app.exception
    app.checkbox[0].check().run()
    assert not app.exception
    assert len(app.metric)==5
    assert app.metric[0].value=='200.00 USD'
    assert len(app.dataframe)>=4
    next(s for s in app.selectbox if s.label == 'Agrupar pagos').select('Trimestre').run()
    assert not app.exception

    assert [tab.label for tab in app.tabs] == ['Resumen','Instrumentos','Flujos','Riesgos']
    assert any('07/10/2026' in item.value and 'USD' in item.value for item in app.info)
    selector = next(s for s in app.selectbox if s.label == 'Detalle de emisor')
    selector.select('Emisor ficticio B').run()
    assert not app.exception
    assert any('DEMO2' in str(table.value) for table in app.dataframe)
