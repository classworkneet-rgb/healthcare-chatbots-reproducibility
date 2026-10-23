"""Public workbook specification derived from the supplied CSVs (standard library only)."""
from __future__ import annotations
import csv, math
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
('Core coding','01_data/coding_revised_core22.csv'),
('Report roster','01_data/full_study_roster26.csv'),
('Extraction','01_data/extraction_revised24.csv'),
('Source checks','01_data/source_verification_v2.csv'),
('Verified endpoints','01_data/verified_endpoints.csv'),
('Claim dispositions','01_data/claim_dispositions18.csv'),
('Worked cases','01_data/claim_evidence_ledger9.csv'),
('Framework comparison','01_data/framework_comparison.csv'),
('Contemporary reports','01_data/currency_evidence.csv'),
('Theory examples','01_data/theory_examples.csv'),
('References','04_outputs/main_reference_crosswalk.csv'),
('Sensitivity','04_outputs/sensitivity_results.csv'),
('Leave one out','04_outputs/leave_one_out.csv'),
('Outcome co-occurrence','04_outputs/outcome_cooccurrence.csv')]
NUMERIC={'year','n','value','number','core_flag','comparative','user_outcome','clinical_outcome','safety_focused_investigation','response_accuracy_benchmark','referral_intention_proxy','health_system_operations','patient_productivity','legacy_service_flag','legacy_safety_flag','legacy_org_flag','denominator','percent','co_measured_n','Year'}
def col(n:int)->str:
 s=''
 while n:n,r=divmod(n-1,26);s=chr(65+r)+s
 return s

def typed(value:str,key:str):
 if value and (key in NUMERIC or key.endswith(('_n','_pct'))):
  try:
   v=float(value)
   return int(v) if v.is_integer() else v
  except ValueError: pass
 return value

def read(rel):
 with (ROOT/rel).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def build_model():
 sheets=[]
 for name,rel in SOURCES:
  with (ROOT/rel).open(encoding='utf-8-sig',newline='') as f:
   rr=list(csv.reader(f))
  heads=rr[0]; raw=rr[1:];body=[[typed(v,k) for k,v in zip(heads,row)] for row in raw]
  cells={};styles={};heights={1:30,2:34,3:9,4:44};widths={}
  end=col(len(heads));merges=[f'A1:{end}1',f'A2:{end}2']
  cells['A1']=name;styles['A1']=1
  cells['A2']=f'Source: {rel}. Report-level evidence; source-access limits and analytic roles are retained.';styles['A2']=2
  for j,h in enumerate(heads,1):
   c=col(j)
   w=12 if h in {'study_id','Study ID','record_id','case_id','assessment_id','year','Year','n','number'} else (16 if h in NUMERIC or h.endswith(('_flag','_n','_pct')) else 42 if any(x in h.lower() for x in ['scope','rationale','claim','finding','interpretation','sample','population','note','verification']) else 36)
   widths[j]=w;cells[c+'4']=h;styles[c+'4']=3
  for i,(row,rraw) in enumerate(zip(body,raw),5):
   maxlines=1
   for j,v in enumerate(row,1):
    a=f'{col(j)}{i}';cells[a]=v;styles[a]=5 if isinstance(v,(int,float)) else 4
    maxlines=max(maxlines,math.ceil(len(str(v))/max(8,widths[j]-3))+str(v).count('\n'))
   heights[i]=min(330,max(32,maxlines*13+8))
  sheets.append({'name':name,'cells':cells,'styles':styles,'formulas':{},'merges':merges,'widths':widths,'heights':heights,'freeze_rows':4,'freeze_columns':1,'autofilter':f'A4:{end}{4+len(raw)}','headers':heads,'nrows':len(raw)})
 byname={s['name']:s for s in sheets}
 core=read(SOURCES[0][1]);claims=read('01_data/claim_dispositions18.csv');audit=read('01_data/source_verification_v2.csv')
 sc={'name':'Summary','cells':{},'styles':{},'formulas':{},'merges':['A1:G1','A2:G3','E16:G16','E17:G20','A23:G23','A24:G27','A29:G30'],'widths':{1:36,2:11,3:28,4:3,5:38,6:11,7:14},'heights':{i:32 for i in range(1,31)},'freeze_rows':5,'freeze_columns':0,'autofilter':None}
 c=sc['cells'];st=sc['styles'];f=sc['formulas']
 def put(addr,val,style=4,formula=None):
  c[addr]=val;st[addr]=style
  if formula:f[addr]=formula
 put('A1','Healthcare chatbot evidence — analytical summary',1)
 put('A2',(ROOT/'02_methods/TITLE.txt').read_text(encoding='utf-8').strip(),2)
 for addr,text in [('A5','Historical analytical set'),('B5','Count'),('C5','Share'),('E5','Claim-level disposition'),('F5','Count'),('G5','Share'),('A16','Targeted source checks'),('B16','Count'),('C16','Access / scope'),('E16','Reading guide'),('A23','Interpretive boundary')]:put(addr,text,3)
 n=len(core);end=4+n
 fields=[('Healthcare-specific reports',None),('User measures','user_outcome'),('Clinical measures','clinical_outcome'),('Referral-safety proxy','safety_focused_investigation'),('Health-system operations','health_system_operations'),('Patient productivity','patient_productivity'),('Intervention-comparison family','comparative'),('Mental health and well-being','domain')]
 for row,(label,field) in enumerate(fields,6):
  put(f'A{row}',label)
  if field is None:v=n;fo=f"COUNTA('Core coding'!A5:A{end})"
  elif field=='domain':v=sum(x[field]=='Mental health and well-being' for x in core);cc=col(byname['Core coding']['headers'].index(field)+1);fo=f'COUNTIF(\'Core coding\'!{cc}5:{cc}{end},"Mental health and well-being")'
  else:v=sum(int(x[field]) for x in core);cc=col(byname['Core coding']['headers'].index(field)+1);fo=f"SUM('Core coding'!{cc}5:{cc}{end})"
  put(f'B{row}',v,5,fo);put(f'C{row}',v/n,6,f'B{row}/$B$6')
 for row,label in enumerate(['Supported within tested conditions','Supported with qualifications','Not established','Not assessed'],6):
  put(f'E{row}',label);put(f'F{row}',sum(x['disposition']==label for x in claims),5,f"COUNTIF('Claim dispositions'!$E$5:$E$22,E{row})");put(f'G{row}',sum(x['disposition']==label for x in claims)/len(claims),6,f'F{row}/$F$10')
 put('E10','Total specified claims');put('F10',len(claims),5,"COUNTA('Claim dispositions'!A5:A22)")
 put('E11','Worked cases');put('F11',len(read('01_data/claim_evidence_ledger9.csv')),5,"COUNTA('Worked cases'!A5:A13)")
 for row,label,note,val,fo in [
 (17,'Historical reports','Field-specific source checks; not duplicate human appraisal',22,'+'.join(f'COUNTIF(\'Source checks\'!$A$5:$A$33,"S{i:02d}")' for i in range(1,25) if i not in [6,7])),
 (18,'Contemporary examples','Outside historical denominators',4,'+'.join(f'COUNTIF(\'Source checks\'!$A$5:$A$33,"U{i:02d}")' for i in range(1,5))),
 (19,'Established frameworks','Proctor, NASSS, NICE',3,'B20-B17-B18'),
 (20,'All source-check records','Different access levels',len(audit),"COUNTA('Source checks'!A5:A33)")]:
  put(f'A{row}',label);put(f'B{row}',val,5,fo);put(f'C{row}',note)
 put('E17','Use the report and claim sheets to trace measured endpoints, sources, interpretation boundaries, and the next evidence needed. Unknown fields are not zero and observations are not automatically causal effects.',2)
 put('A24','Counts describe a fixed, non-exhaustive report corpus. Source checks are field-specific and were not duplicated by independent human reviewers. Sensitivity labels are not formal risk-of-bias ratings. The proposed worksheet is not independently validated. CSV data and analytical scripts are authoritative; workbook reproduction uses only the Python standard library.',7)
 put('A29','Reproduce: python 03_code/reproduce.py | Rebuild workbook: python 03_code/build_workbook.py | Tests: python -m unittest discover -s 03_code -p "test_*.py" -v',2)
 sc['heights'].update({1:32,2:26,3:26,4:9,16:44,17:45,18:45,19:45,20:45,21:9,22:9,23:30,28:9,29:24,30:24})
 return [sc]+sheets
