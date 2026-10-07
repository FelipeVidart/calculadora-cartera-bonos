from streamlit.testing.v1 import AppTest


def test_streamlit_demo():
    app=AppTest.from_file('../app.py', default_timeout=30).run()
    assert not app.exception
    app.checkbox[0].check().run()
    assert not app.exception
    assert len(app.metric)==3
    assert app.metric[0].value=='200.00'
    assert len(app.dataframe)>=4
    next(s for s in app.selectbox if s.label == 'Agrupar pagos').select('Trimestre').run()
    assert not app.exception
