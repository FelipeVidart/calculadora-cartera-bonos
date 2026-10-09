"""Refresh from the reviewed web export, never from the private master workbook.
Usage: python -m scripts.import_funds_catalog /path/to/web/public/data/funds.json
"""
import json
import sys
from pathlib import Path
from src.portfolio.funds import fixed_income_catalog

if __name__ == '__main__':
    data=json.loads(Path(sys.argv[1]).read_text())
    if data.get('schema_version') != '1.0' or data['meta'].get('synthetic'):
        raise ValueError('Se requiere exportación web real con esquema 1.0')
    result={'meta':data['meta'],'source':'https://github.com/FelipeVidart/plataforma-inversiones', 'classes':fixed_income_catalog(data)}
    target=Path(__file__).parents[1]/'data/fixed_income_funds.json'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(f"Importadas {len(result['classes'])} clases de renta fija")
