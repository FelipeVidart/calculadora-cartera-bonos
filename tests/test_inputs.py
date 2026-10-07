from io import BytesIO, StringIO
import pandas as pd
from openpyxl import Workbook
from src.io.loaders import read_table
from src.validation.validators import validate_portfolio


def csv(text):
    f=StringIO(text);f.name='test.csv';return f


def test_discrepancy_recomputed():
    p,issues=read_table(csv('Ticker,Fecha,Renta,Amortización,Total\nA,2027-01-01,10,100,0\n'),'payments')
    assert p['Flujo Total'].iloc[0] == 110
    assert any(x['Campo']=='Total' for x in issues)


def test_ambiguous_numbers_dates_and_duplicates():
    p,issues=read_table(csv('Ticker;Fecha;Renta;Amortización;Total\nA;01/02/2027;1.000,20;100;110\nA;01/02/2027;10;100;110\n'),'payments')
    assert any(x['Campo']=='Fecha' and x['Nivel']=='error' for x in issues)
    assert any(x['Campo']=='Renta' and x['Nivel']=='error' for x in issues)
    assert any('Duplicado' in x['Mensaje'] for x in issues)


def test_decimal_comma_and_missing_metadata():
    p,i=read_table(csv('Ticker;Market Value;Nominal;Moneda;Emisor\nA;100,25;;;\n'),'positions', ',')
    assert p['Market Value'].iloc[0] == 100.25
    assert any(x['Campo']=='Moneda' and x['Nivel']=='error' for x in i)
    assert any(x['Campo']=='Nominal' and x['Nivel']=='warning' for x in i)


def test_bad_excel_dimension():
    import zipfile
    w=Workbook();s=w.active;s.title='Pagos'
    s.append(['Ticker','Fecha','Renta','Amortización','Total'])
    s.append(['A','2027-01-01',10,100,110]);b=BytesIO();w.save(b)
    out=BytesIO()
    with zipfile.ZipFile(b) as z, zipfile.ZipFile(out,'w') as dst:
        for name in z.namelist():
            data=z.read(name)
            if name=='xl/worksheets/sheet1.xml':data=data.replace(b'ref="A1:E2"',b'ref="A1"')
            dst.writestr(name,data)
    out.seek(0);out.name='test.xlsx'
    p,i=read_table(out,'payments')
    assert len(p)==1 and not i


def test_cross_validation():
    p=pd.DataFrame({'Ticker':['A','B'], 'Fecha':pd.to_datetime(['2026-01-01','2027-01-01']), 'Flujo Total':[100,100], 'Amortización':[100,100]})
    v=pd.DataFrame({'Ticker':['A','C'],'Moneda':['USD','ARS']})
    f,i=validate_portfolio(p,v,'2026-01-01')
    assert len(f)==1
    assert any('excluidos' in x['Mensaje'] for x in i)
    assert any('sin posición' in x['Mensaje'] for x in i)
    assert sum(x['Nivel']=='error' for x in i)==3
