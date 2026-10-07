"""Independent audit: Decimal bisection, known XIRR benchmark, repricing."""
from decimal import Decimal, localcontext
import numpy as np
import pandas as pd
import pytest
from src.fixed_income.engine import metrics, xirr, year_fractions
from src.portfolio.analytics import analyze


def decimal_yield(mv, days, flows):
    # Direct PV in annual rate, independent of production log-space Brent.
    with localcontext() as ctx:
        ctx.prec = 45
        t = [Decimal(int(d))/Decimal(365) for d in days]
        c = [Decimal(str(v)) for v in flows]
        target = Decimal(str(mv))
        lo, hi = Decimal('-.999999'), Decimal('10')
        for _ in range(180):
            y = (lo+hi)/2
            pv = sum(v/(1+y)**time for time,v in zip(t,c))
            if pv > target: lo=y
            else: hi=y
        return float((lo+hi)/2)


def test_known_excel_xirr_benchmark():
    # Standard XIRR example: initial -10000 on 2008-01-01.
    dates=['2008-03-01','2008-10-30','2009-02-15','2009-04-01']
    result=xirr(10000,year_fractions(dates,'2008-01-01'),[2750,4250,3250,2750])
    assert result == pytest.approx(.373362533518831, abs=1e-10)


@pytest.mark.parametrize('seed', range(12))
def test_independent_decimal_and_derivatives(seed):
    rng=np.random.default_rng(seed)
    days=np.sort(rng.choice(np.arange(20,5000),size=8,replace=False))
    t=days/365
    income=rng.uniform(1,20,8);principal=rng.uniform(0,150,8)
    y=rng.uniform(-.2,.7)
    flows=income+principal
    mv=sum(flows/(1+y)**t)
    m=metrics(mv,t,income,principal)
    assert m['TIR'] == pytest.approx(decimal_yield(mv,days,flows),abs=1e-11)
    assert sum(flows/(1+m['TIR'])**t) == pytest.approx(mv,rel=1e-11)
    pv=lambda rate: sum(flows/(1+rate)**t)
    h=1e-5
    assert m['Modified'] == pytest.approx(-(pv(y+h)-pv(y-h))/(2*h*mv),rel=2e-7)
    assert m['Convexity'] == pytest.approx((pv(y+h)-2*mv+pv(y-h))/(h*h*mv),rel=2e-5)
    # Scaling a position leaves rates and time metrics invariant.
    scaled=metrics(mv*7,t,income*7,principal*7)
    for field in ['TIR','Macaulay','Modified','Convexity','WAL']:
        assert scaled[field] == pytest.approx(m[field],rel=1e-10)


def test_portfolio_parallel_shift_derivatives():
    p=pd.DataFrame({'Ticker':['A','A','B','B'],'Fecha':pd.to_datetime(['2027-01-01','2029-01-01','2028-01-01','2031-01-01']), 'Renta':[5.,5.,8.,8.], 'Amortización':[0.,100.,40.,60.]})
    p['Flujo Total']=p.Renta+p['Amortización']
    v=pd.DataFrame({'Ticker':['A','B'],'Market Value':[98.,110.],'Moneda':['USD','USD']})
    i,s=analyze(p,v,'2026-01-01')
    def value(shift):
        total=0
        for _,row in i.iterrows():
            f=p[p.Ticker==row.Ticker]
            t=year_fractions(f.Fecha,'2026-01-01')
            total+=sum(f['Flujo Total'].to_numpy()/(1+row.TIR+shift)**t)
        return total
    h=1e-5;mv=s['Market Value']
    assert value(0) == pytest.approx(mv,rel=1e-11)
    assert s['Modified'] == pytest.approx(-(value(h)-value(-h))/(2*h*mv),rel=1e-7)
    assert s['Convexity'] == pytest.approx((value(h)-2*value(0)+value(-h))/(h*h*mv),rel=1e-5)
    assert sum(i.Peso) == pytest.approx(1)
