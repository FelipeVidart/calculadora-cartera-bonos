import json
import pandas as pd
import pytest
from src.portfolio.funds import duration_coverage, fixed_income_catalog


def test_unknown_duration_does_not_become_zero():
    b=pd.DataFrame({'Market Value':[100.],'Modified':[4.]})
    f=pd.DataFrame({'Market Value':[100.],'Modified':[None], 'Fecha duration':[None]})
    c=duration_coverage(b,f,'2026-10-09')
    assert c['Cobertura duration']==.5
    assert c['Duration porción cubierta']==4
    assert c['Aporte conocido sobre total']==2
    assert c['Cobertura flujos']==.5
    c=duration_coverage(b.iloc[:0],f,'2026-10-09')
    assert c['Duration porción cubierta'] is None


def test_only_recent_known_modified_duration():
    b=pd.DataFrame(columns=['Market Value','Modified'])
    f=pd.DataFrame({'Market Value':[100.,100.,100.],'Modified':[2.,10.,20.], 'Fecha duration':['2026-09-30','2025-01-01','2027-01-01']})
    c=duration_coverage(b,f,'2026-10-09')
    assert c['Cobertura duration']==pytest.approx(1/3)
    assert c['Duration porción cubierta']==2


def test_catalog_filter_and_snapshot():
    data={'funds':[],'classes':[],'observations':[]}
    for i,cat in enumerate(['Renta fija','Corporativos, Cash','Equity','Mixto','Cash','Cash, Soberanos']):
        data['funds'].append({'fund_id':str(i),'fund_name':'Money Market' if i==5 else str(i),'manager_name':'M','selected_edition_id':str(i)})
        data['classes'].append({'fund_id':str(i),'class_id':str(i),'class_label':'A'})
        data['observations'].append({'edition_id':str(i),'value_status':'present','entity_scope':'fund','entity_id':str(i),'metric_id':'asset_class_v1','value_text':cat})
    assert len(fixed_income_catalog(data))==2
    catalog=json.load(open('data/fixed_income_funds.json'))
    assert len(catalog['classes'])==22
    assert all(r['Modified'] is None for r in catalog['classes'])
