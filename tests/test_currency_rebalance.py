import pandas as pd
import pytest
from src.portfolio.currencies import normalize_positions, consolidate
from src.portfolio.rebalance import simulate


def test_currency_conversion_and_consolidation():
    p=pd.DataFrame({'Ticker':['A','B','C'], 'Market Value':[150000.,300000.,100.], 'Moneda':['USD','ARS','USD'], 'Moneda MV':['ARS','ARS','USD'], 'Emisor':['X','X','Y']})
    n=normalize_positions(p,1500)
    assert n['Market Value'].tolist()==[100.,300000.,100.]
    d,e,c=consolidate(p,'USD',1500)
    assert d['Valor consolidado'].tolist()==[100.,200.,100.]
    assert e.set_index('Emisor').loc['X','Peso consolidado']==.75
    assert c.set_index('Moneda').loc['ARS','Peso consolidado']==.5
    d,_,_=consolidate(p,'ARS',1500)
    assert d['Valor consolidado'].sum()==600000
    assert p['Market Value'].iloc[0]==150000
    with pytest.raises(ValueError):normalize_positions(p,0)


def test_rebalance_manual_and_unreachable():
    r=simulate(100,4,20,2,5,7)
    assert r['Duration necesaria de compra']==7
    assert r['Duration simulada']==5
    assert r['Diferencia con objetivo']==0
    assert simulate(100,4,20,2,0,0)['Duration necesaria de compra']<0
    with pytest.raises(ValueError):simulate(100,4,0,2,5,7)
    with pytest.raises(ValueError):simulate(100,4,101,2,5,7)
