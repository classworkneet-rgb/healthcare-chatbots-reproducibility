"""Offline release checks. These test file integrity and consistency, not study validity."""
import unittest,csv,re,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from workbook_model import ROOT,build_model
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def xlsx_cells(path):
 with zipfile.ZipFile(path) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   ss=[''.join(i.itertext()) for i in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  rel={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  out={}
  for sh in ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets',N):
   target=rel[sh.attrib['{'+N['r']+'}id']]
   target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   cells={};formulas={}
   for c in ET.fromstring(z.read(target)).findall('.//s:sheetData/s:row/s:c',N):
    addr=c.attrib['r'];v=c.find('s:v',N);f=c.find('s:f',N);typ=c.attrib.get('t')
    if typ=='inlineStr':value=''.join(c.find('s:is',N).itertext())
    elif typ=='s':value=ss[int(v.text)] if v is not None else ''
    elif v is not None and v.text is not None:
     if typ in ['str','e']:value=v.text
     else:
      value=float(v.text)
      if value.is_integer():value=int(value)
    else:value=''
    if value!='':cells[addr]=value
    if f is not None:formulas[addr]=f.text or ''
   out[sh.attrib['name']]={'cells':cells,'formulas':formulas}
 return out

def records(name):
 with (ROOT/'01_data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

class ReleaseTests(unittest.TestCase):
 def test_sheet_names(self):
  sheets=xlsx_cells(ROOT/'01_data/Healthcare_Chatbots_Evidence.xlsx')
  self.assertEqual(len(sheets),15)
  self.assertNotIn('Revision response',sheets);self.assertNotIn('Appraisal archive labels',sheets)
 def test_s03_randomization_consistent(self):
  r=next(r for r in records('extraction_revised24.csv') if r['Study ID']=='S03')
  self.assertIn('27',r['Randomized N']);self.assertIn('random assignment',r['Randomized N'].lower())
  self.assertNotIn('unclear allocation procedures',' '.join(r.values()).lower())
  self.assertIn('concealment',r['Key limitations'])
 def test_s09_recruitment_not_completers(self):
  r=next(r for r in records('extraction_revised24.csv') if r['Study ID']=='S09')
  self.assertIn('Not reported',r['Recruited N']);self.assertNotIn('3,629',r['Recruited N'])
  self.assertIn('3,629',r['Completed/endpoint N']);self.assertIn('3,629',r['Analyzed N'])
 def test_s09_program_sum(self):self.assertEqual(1648+1243+738,3629)
 def test_s09_roster(self):
  r=next(r for r in records('full_study_roster26.csv') if r['Study ID']=='S09')
  self.assertIn('not reported',r['Sample summary'].lower());self.assertNotIn('Recruited: 3,629',r['Sample summary'])
 def test_public_code_no_private_dependency(self):
  import ast
  for p in (ROOT/'03_code').glob('*.py'):
   for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
    if isinstance(node,ast.Import):mods=[a.name.split('.')[0] for a in node.names]
    elif isinstance(node,ast.ImportFrom):mods=[(node.module or '').split('.')[0]]
    else:continue
    self.assertNotIn('artifact_tool',mods)
 def test_important_spacing(self):
  bad=['Sections6.2','manual48s','digital8s','illustrated by9cases','and18analyst','23October2026','Methods2.1']
  for p in (ROOT/'01_data').glob('*.csv'):
   t=p.read_text(encoding='utf-8-sig')
   for token in bad:self.assertNotIn(token,t,p.name)
 def test_thousands_separator_spacing(self):
  for p in (ROOT/'01_data').glob('*.csv'):
   self.assertIsNone(re.search(r'(?<=\d),[ \t]+(?=\d{3}(?!\d))',p.read_text(encoding='utf-8-sig')),p.name)
 def test_workbook_against_csv_model(self):
  actual=xlsx_cells(ROOT/'01_data/Healthcare_Chatbots_Evidence.xlsx')
  for m in build_model():
   sheet=actual[m['name']]
   for a,v in m['cells'].items():
    if v in ('',None):continue
    got=sheet['cells'].get(a)
    if isinstance(v,(int,float)):self.assertAlmostEqual(got,v,places=10,msg=m['name']+'!'+a)
    else:self.assertEqual(got,v,m['name']+'!'+a)
   for a,f in m['formulas'].items():self.assertEqual(sheet['formulas'].get(a),f,m['name']+'!'+a)
 def test_public_archive_no_editorial_files(self):
  files=[str(p.relative_to(ROOT)).lower() for p in ROOT.rglob('*') if p.is_file()]
  self.assertFalse(any('reviewer_response' in p or 'latest_response_matrix' in p or '/previous_revision/' in p for p in files))
 def test_rebuild_from_public_code(self):
  import tempfile
  from build_workbook import build
  with tempfile.TemporaryDirectory() as d:
   new=build(Path(d)/'reproduced.xlsx');actual=xlsx_cells(new)
   for m in build_model():
    for a,v in m['cells'].items():
     if v in ('',None):continue
     self.assertEqual(actual[m['name']]['cells'].get(a),v,m['name']+'!'+a)
 def test_title_unchanged(self):
  self.assertEqual((ROOT/'02_methods/TITLE.txt').read_text(encoding='utf-8').strip(),'From User Experience to Organizational Value: A Critical Integrative Review of Intelligent Chatbots in Healthcare Services')
 def test_numerical_counts_unchanged(self):
  r=json.loads((ROOT/'04_outputs/results.json').read_text(encoding='utf-8'))
  self.assertEqual((r['core']['n'],r['core']['user_outcome'],r['core']['clinical_outcome'],r['worked_cases'],r['claim_assessments']),(22,22,11,9,18))
if __name__=='__main__':unittest.main()
