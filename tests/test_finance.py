import numpy as np
import pandas as pd
import pytest
from src.fixed_income.engine import xirr, metrics, year_fractions
from src.portfolio.analytics import analyze, ladder
from src.portfolio.scenarios import scenarios


def test_one_year_zero_coupon():
    m = metrics(100, [1], [0], [110])
    assert m['TIR'] == pytest.approx(.1)
    assert m['Macaulay'] == pytest.approx(1)
    assert m['Modified'] == pytest.approx(1/1.1)
    assert m['Convexity'] == pytest.approx(2/1.1**2)
    assert m['WAL'] == pytest.approx(1)


def test_irregular_and_negative_yields():
    times = np.array([.3,1.7,3.2]); flows = np.array([5,5,105])
    mv = sum(flows / 1.08**times)
    assert xirr(mv, times, flows) == pytest.approx(.08)
    assert xirr(100, [2], [81]) == pytest.approx(-.1)
    assert xirr(100, [1], [100]) == pytest.approx(0, abs=1e-12)


def test_coupon_and_wal_manual():
    m = metrics(100, [1,2], [10,10], [0,100])
    assert m['TIR'] == pytest.approx(.1)
    assert m['Macaulay'] == pytest.approx((10/1.1+2*110/1.1**2)/100)
    assert m['WAL'] == 2
    assert metrics(100, [1,2], [0,0], [50,50])['WAL'] == 1.5
    assert np.isnan(metrics(100, [1], [110], [0])['WAL'])


def test_derivatives():
    t = np.array([.2,1.3,4]); r = np.array([3,3,3]); a = np.array([0,0,100]); y=.07
    pv = lambda rate: np.sum((r+a)/(1+rate)**t)
    mv=pv(y); m=metrics(mv,t,r,a); h=1e-4
    assert m['Modified'] == pytest.approx(-(pv(y+h)-pv(y-h))/(2*h*mv), rel=1e-6)
    assert m['Convexity'] == pytest.approx((pv(y+h)-2*mv+pv(y-h))/(h*h*mv), rel=1e-6)


def test_actual_days_leap_year():
    assert year_fractions(['2025-01-01'], '2024-01-01')[0] == 366/365


@pytest.mark.parametrize('mv,t,c', [(0,[1],[100]),(100,[0],[100]),(100,[1],[-1]),(100,[1],[0]),(100,[1],[float('inf')])])
def test_invalid_xirr(mv,t,c):
    with pytest.raises(ValueError): xirr(mv,t,c)


def test_portfolio_and_scenarios():
    p=pd.DataFrame({'Ticker':['A','B'], 'Fecha':pd.to_datetime(['2027-01-01','2028-01-01']), 'Renta':[0.,0.], 'Amortización':[110.,144.], 'Flujo Total':[110.,144.]})
    v=pd.DataFrame({'Ticker':['A','B'], 'Market Value':[100.,100.], 'Nominal':[100,100], 'Moneda':['USD','USD'], 'Emisor':['A','B']})
    i,s=analyze(p,v,'2026-01-01')
    assert s['TIR ponderada'] == pytest.approx(.15)
    # 200*z² = 110*z + 144, where z=1+y.
    expected=(110+np.sqrt(110**2+4*200*144))/(2*200)-1
    assert s['Portfolio XIRR'] == pytest.approx(expected)
    assert s['Portfolio XIRR'] != pytest.approx(s['TIR ponderada'])
    assert s['Modified'] == pytest.approx(i['Aporte duration'].sum())
    assert s['Macaulay'] == pytest.approx(1.5)
    assert s['WAL'] == pytest.approx((110+2*144)/254)
    assert ladder(p,'Y')['Flujo Total'].sum() == 254
    assert ladder(p,'Q')['Renta'].sum() == 0
    assert ladder(p,'M')['Amortización'].sum() == 254
    sc=scenarios(s).set_index('Shock bps')
    assert sc.loc[100,'ΔP/P duration'] == pytest.approx(-s['Modified']*.01)
    assert sc.loc[100,'ΔP/P convexity'] == pytest.approx(-s['Modified']*.01+.5*s['Convexity']*.01**2)
    v.loc[1,'Moneda']='ARS'
    with pytest.raises(ValueError): analyze(p,v,'2026-01-01')
