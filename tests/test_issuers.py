import pandas as pd
import pytest
from src.portfolio.analytics import issuer_concentration


def test_issuer_weights_and_duration_reconcile():
    df=pd.DataFrame({'Ticker':['A','B','C','D'], 'Emisor':['Vista','Vista','IRSA',''],
                     'Market Value':[30.,20.,40.,10.], 'Peso':[.3,.2,.4,.1],
                     'Aporte duration':[1.8,.4,2.,.1]})
    result=issuer_concentration(df).set_index('Emisor')
    assert result.loc['Vista','Market Value'] == 50
    assert result.loc['Vista','Peso'] == pytest.approx(.5)
    assert result.loc['Vista','Aporte duration'] == pytest.approx(2.2)
    assert result.loc['Vista','Instrumentos'] == 'A, B'
    assert result.loc['Sin emisor informado','Market Value'] == 10
    assert result.Peso.sum() == pytest.approx(1)
    assert result['Aporte duration'].sum() == pytest.approx(df['Aporte duration'].sum())
    assert df.Emisor.iloc[-1] == ''
