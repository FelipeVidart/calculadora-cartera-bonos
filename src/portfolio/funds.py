"""Catalog adapter. Only explicit fixed-income categories; no inferred cash flows."""
import pandas as pd

ALLOWED = {'Renta fija','Corporativos','Soberanos','Cash'}


def fixed_income_catalog(data):
    rows=[]
    for fund in data['funds']:
        edition=fund.get('selected_edition_id')
        obs=[o for o in data['observations'] if o['edition_id']==edition and o['value_status']=='present' and o.get('entity_scope')=='fund' and (o.get('entity_id') or o.get('entity_ref'))==fund['fund_id']]
        category=next((o['value_text'] for o in obs if o['metric_id']=='asset_class_v1'), '') or ''
        tokens={x.strip() for x in category.split(',')}
        if not tokens or not tokens <= ALLOWED or tokens == {'Cash'} or 'money market' in fund['fund_name'].lower():
            continue
        duration=next((o for o in obs if o['metric_id']=='duration_modified_v1' and o['unit']=='years' and o.get('review_status')=='reviewed'),None)
        reported=next((o for o in obs if o['metric_id']=='duration_unspecified_v1'),None)
        for cls in data['classes']:
            if cls['fund_id']!=fund['fund_id']: continue
            co=[o for o in data['observations'] if o['edition_id']==edition and o['metric_id']=='class_currency_v1' and (o.get('entity_id') or o.get('entity_ref'))==cls['class_id'] and o['value_status']=='present']
            currency=co[0].get('value_text') if len(co)==1 else None
            rows.append({'class_id':cls['class_id'],'fund_id':fund['fund_id'],'Nombre':fund['fund_name'],'Clase':cls['class_label'],
                         'Moneda':currency,'Gestora':fund['manager_name'],'Categoría':category,
                         'Modified':float(duration['value_number']) if duration else None,
                         'Fecha duration':duration.get('effective_date') if duration else None,
                         'Duration publicada':float(reported['value_number']) if reported and reported.get('value_number') else None,
                         'Unidad publicada':reported.get('unit') if reported else None,
                         'Fecha publicada':reported.get('effective_date') if reported else None,
                         'Fuente':(duration or reported or {}).get('source_document_id') or (duration or reported or {}).get('document_id'),
                         'Edición':edition})
    return rows


def duration_coverage(bonds, funds, valuation):
    total=bonds['Market Value'].sum()+funds['Market Value'].sum()
    known=bonds['Market Value'].sum()
    contribution=(bonds['Market Value']*bonds.Modified).sum() if len(bonds) else 0.
    for _, f in funds.iterrows():
        date=pd.to_datetime(f.get('Fecha duration'),errors='coerce')
        if pd.notna(f.get('Modified')) and f.Modified>=0 and pd.notna(date) and date<=pd.Timestamp(valuation) and (pd.Timestamp(valuation)-date).days<=90:
            known+=f['Market Value'];contribution+=f['Market Value']*f.Modified
    return {'Valor total renta fija':total,'Cobertura duration':known/total if total else 0.,
            'Duration porción cubierta':contribution/known if known else None,
            'Aporte conocido sobre total':contribution/total if total else None,
            'Cobertura flujos':bonds['Market Value'].sum()/total if total else 0.}
