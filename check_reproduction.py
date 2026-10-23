#!/usr/bin/env python3
"""One-command offline numerical and workbook reproduction check."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NUMERICAL_OUTPUTS=[
 'results.json','descriptive_counts.csv','sensitivity_results.csv','leave_one_out.csv',
 'outcome_cooccurrence.csv','claim_disposition_counts.csv','verification_coverage.csv','validation_report.txt']
def digest(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args:list[str],name:str)->None:
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONHASHSEED']='0'
    p=subprocess.run([sys.executable,'-B','-S',*args],cwd=ROOT,env=env,text=True,
                     encoding='utf-8',errors='replace',capture_output=True)
    (ROOT/'build'/f'{name}.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode:
        print(p.stdout);print(p.stderr);raise SystemExit(f'FAILED: {name}')
    print(f'{name}: PASS')
def main()->None:
    if sys.version_info<(3,10):raise SystemExit('Python 3.10 or newer is required.')
    (ROOT/'build').mkdir(exist_ok=True)
    run(['03_code/verify_package.py'],'integrity_before')
    expected={n:digest(ROOT/'04_outputs'/n) for n in NUMERICAL_OUTPUTS}
    run(['03_code/reproduce.py'],'numerical_reproduction')
    mismatch=[n for n,h in expected.items() if digest(ROOT/'04_outputs'/n)!=h]
    if mismatch:raise SystemExit('Output mismatch: '+', '.join(mismatch))
    run(['03_code/build_workbook.py','--output','build/Healthcare_Chatbots_Evidence.xlsx'],'workbook_rebuild')
    run(['-m','unittest','discover','-s','03_code','-p','test_*.py','-v'],'tests')
    # Test rebuilt workbook against the same source-derived cell and formula model.
    sys.path.insert(0,str(ROOT/'03_code'))
    from test_release import xlsx_cells
    from workbook_model import build_model
    book=xlsx_cells(ROOT/'build/Healthcare_Chatbots_Evidence.xlsx')
    for model in build_model():
        sheet=book[model['name']]
        for addr,val in model['cells'].items():
            if val not in ('',None) and sheet['cells'].get(addr)!=val:
                raise SystemExit(f'Workbook value mismatch: {model["name"]}!{addr}')
        for addr,formula in model['formulas'].items():
            if sheet['formulas'].get(addr)!=formula:
                raise SystemExit(f'Workbook formula mismatch: {model["name"]}!{addr}')
    run(['03_code/verify_package.py'],'integrity_after')
    report={'status':'PASS','python':platform.python_version(),'platform':platform.system(),
            'numerical_outputs_compared':len(expected),'workbook_sheets':len(book),
            'third_party_packages_required':False,'network_required_for_analysis':False,
            'independent_scientific_validation':False}
    (ROOT/'build/reproduction_status.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPRODUCIBILITY CHECK: PASS')
if __name__=='__main__':main()
