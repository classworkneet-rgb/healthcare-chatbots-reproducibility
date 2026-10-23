#!/usr/bin/env python3
"""Rebuild the XLSX from CSVs using only Python's standard library.

OOXML cells include calculated caches for the supplied summary formulas. Opening
in Excel or compatible software recalculates the formulas. Numerical analysis
must be run first: python 03_code/reproduce.py. No online API is used.
"""
from __future__ import annotations
import argparse,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from workbook_model import ROOT,build_model,col
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
C='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('',S);ET.register_namespace('r',R)
def elt(tag,attrs=None,text=None):
 e=ET.Element(tag,attrs or {})
 if text is not None:e.text=str(text)
 return e
def xml(e):return ET.tostring(e,encoding='utf-8',xml_declaration=True)
def sub(p,tag,attrs=None,text=None):e=elt(tag,attrs,text);p.append(e);return e
def rownum(a):return int(''.join(c for c in a if c.isdigit()))
def colnum(a):
 n=0
 for c in a:
  if not c.isalpha():break
  n=n*26+ord(c)-64
 return n

def styles():
 x=elt(f'{{{S}}}styleSheet');fonts=sub(x,f'{{{S}}}fonts',{'count':'4'})
 for size,color,bold in [(10,'FF000000',False),(14,'FFFFFFFF',True),(10,'FFFFFFFF',True),(10,'FF5B6573',False)]:
  e=sub(fonts,f'{{{S}}}font');sub(e,f'{{{S}}}sz',{'val':str(size)});sub(e,f'{{{S}}}name',{'val':'Calibri'});sub(e,f'{{{S}}}color',{'rgb':color})
  if bold:sub(e,f'{{{S}}}b')
 fills=sub(x,f'{{{S}}}fills',{'count':'4'})
 for typ,color in [('none',None),('gray125',None),('solid','FF17365D'),('solid','FFFFF2CC')]:
  e=sub(fills,f'{{{S}}}fill');p=sub(e,f'{{{S}}}patternFill',{'patternType':typ})
  if color:sub(p,f'{{{S}}}fgColor',{'rgb':color});sub(p,f'{{{S}}}bgColor',{'indexed':'64'})
 borders=sub(x,f'{{{S}}}borders',{'count':'2'})
 for flag in [False,True]:
  b=sub(borders,f'{{{S}}}border')
  for side in ['left','right','top','bottom','diagonal']:
   q=sub(b,f'{{{S}}}{side}',{'style':'thin'} if flag and side!='diagonal' else {})
   if flag and side!='diagonal':sub(q,f'{{{S}}}color',{'rgb':'FFD9E2F3'})
 base=sub(x,f'{{{S}}}cellStyleXfs',{'count':'1'});sub(base,f'{{{S}}}xf',{'numFmtId':'0','fontId':'0','fillId':'0','borderId':'0'})
 fs=sub(x,f'{{{S}}}cellXfs',{'count':'8'})
 specs=[(0,0,0,0),(1,2,0,0),(3,0,0,0),(2,2,1,0),(0,0,1,0),(0,0,1,0),(0,0,1,10),(0,3,0,0)]
 for fi,fill,bi,nf in specs:
  q=sub(fs,f'{{{S}}}xf',{'numFmtId':str(nf),'fontId':str(fi),'fillId':str(fill),'borderId':str(bi),'xfId':'0','applyAlignment':'1','applyNumberFormat':'1'})
  sub(q,f'{{{S}}}alignment',{'vertical':'top','wrapText':'1'})
 ns=sub(x,f'{{{S}}}cellStyles',{'count':'1'});sub(ns,f'{{{S}}}cellStyle',{'name':'Normal','xfId':'0','builtinId':'0'})
 return xml(x)

def worksheet(m):
 x=elt(f'{{{S}}}worksheet');views=sub(x,f'{{{S}}}sheetViews');view=sub(views,f'{{{S}}}sheetView',{'workbookViewId':'0'})
 fr,fc=m['freeze_rows'],m['freeze_columns']
 if fr or fc:sub(view,f'{{{S}}}pane',{'xSplit':str(fc),'ySplit':str(fr),'topLeftCell':f'{col(fc+1)}{fr+1}','activePane':'bottomRight' if fc else 'bottomLeft','state':'frozen'})
 sub(x,f'{{{S}}}sheetFormatPr',{'defaultRowHeight':'18'})
 cols=sub(x,f'{{{S}}}cols')
 for j,w in m['widths'].items():sub(cols,f'{{{S}}}col',{'min':str(j),'max':str(j),'width':str(w),'customWidth':'1'})
 sd=sub(x,f'{{{S}}}sheetData');rr={}
 for a in sorted(m['cells'],key=lambda a:(rownum(a),colnum(a))):
  i=rownum(a)
  if i not in rr:rr[i]=sub(sd,f'{{{S}}}row',{'r':str(i),'ht':str(m['heights'].get(i,30)),'customHeight':'1'})
  value=m['cells'][a];at={'r':a,'s':str(m['styles'].get(a,4))}
  if a in m['formulas']:
   c=sub(rr[i],f'{{{S}}}c',at);sub(c,f'{{{S}}}f',text=m['formulas'][a]);sub(c,f'{{{S}}}v',text=value)
  elif isinstance(value,(int,float)):
   c=sub(rr[i],f'{{{S}}}c',at);sub(c,f'{{{S}}}v',text=value)
  else:
   at['t']='inlineStr';c=sub(rr[i],f'{{{S}}}c',at);ss=sub(c,f'{{{S}}}is');sub(ss,f'{{{S}}}t',{'{http://www.w3.org/XML/1998/namespace}space':'preserve'},'' if value is None else value)
 if m['autofilter']:sub(x,f'{{{S}}}autoFilter',{'ref':m['autofilter']})
 if m['merges']:
  merges=sub(x,f'{{{S}}}mergeCells',{'count':str(len(m['merges']))})
  for r in m['merges']:sub(merges,f'{{{S}}}mergeCell',{'ref':r})
 sub(x,f'{{{S}}}pageMargins',{'left':'0.3','right':'0.3','top':'0.5','bottom':'0.5','header':'0.2','footer':'0.2'})
 return xml(x)

def build(path):
 models=build_model();path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 wb=elt(f'{{{S}}}workbook');ss=sub(wb,f'{{{S}}}sheets')
 rel=elt(f'{{{P}}}Relationships')
 for i,m in enumerate(models,1):
  sub(ss,f'{{{S}}}sheet',{'name':m['name'],'sheetId':str(i),f'{{{R}}}id':f'rId{i}'})
  sub(rel,f'{{{P}}}Relationship',{'Id':f'rId{i}','Type':R+'/worksheet','Target':f'worksheets/sheet{i}.xml'})
 sub(rel,f'{{{P}}}Relationship',{'Id':f'rId{len(models)+1}','Type':R+'/styles','Target':'styles.xml'})
 sub(wb,f'{{{S}}}calcPr',{'calcId':'191029','fullCalcOnLoad':'1','forceFullCalc':'1'})
 content=elt(f'{{{C}}}Types')
 for ext,typ in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml')]:sub(content,f'{{{C}}}Default',{'Extension':ext,'ContentType':typ})
 for part,typ in [('/xl/workbook.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),('/xl/styles.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'),('/docProps/core.xml','application/vnd.openxmlformats-package.core-properties+xml'),('/docProps/app.xml','application/vnd.openxmlformats-officedocument.extended-properties+xml')]+[(f'/xl/worksheets/sheet{i}.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml') for i in range(1,len(models)+1)]:sub(content,f'{{{C}}}Override',{'PartName':part,'ContentType':typ})
 rootrel=elt(f'{{{P}}}Relationships')
 for i,t,target in [(1,R+'/officeDocument','xl/workbook.xml'),(2,P+'/metadata/core-properties','docProps/core.xml'),(3,R+'/extended-properties','docProps/app.xml')]:sub(rootrel,f'{{{P}}}Relationship',{'Id':f'rId{i}','Type':t,'Target':target})
 from xml.sax.saxutils import escape
 title=escape((ROOT/'02_methods/TITLE.txt').read_text().strip())
 core=f'''<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{title}</dc:title><dc:subject>Study-level evidence and analytical calculations</dc:subject><dc:creator></dc:creator><cp:lastModifiedBy></cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">2026-10-23T00:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-10-23T00:00:00Z</dcterms:modified></cp:coreProperties>'''
 app='''<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Evidence workbook</Application></Properties>'''
 parts={'[Content_Types].xml':xml(content),'_rels/.rels':xml(rootrel),'xl/workbook.xml':xml(wb),'xl/_rels/workbook.xml.rels':xml(rel),'xl/styles.xml':styles(),'docProps/core.xml':core.encode(),'docProps/app.xml':app.encode()}
 for i,m in enumerate(models,1):parts[f'xl/worksheets/sheet{i}.xml']=worksheet(m)
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in parts.items():
   info=zipfile.ZipInfo(name,date_time=(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
 print(f'WORKBOOK REBUILD: PASS; {len(models)} sheets; {path}')
 return path
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'01_data/Healthcare_Chatbots_Evidence.xlsx');args=p.parse_args()
 build(args.output)
