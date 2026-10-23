#!/usr/bin/env python3
"""Verify delivered file bytes against SHA256SUMS.txt; does not validate scientific claims."""
from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=ROOT/'SHA256SUMS.txt'
 if not manifest.exists():raise SystemExit('Missing SHA256SUMS.txt')
 good=0;bad=[]
 for line in manifest.read_text(encoding='utf-8').splitlines():
  expected,rel=line.split('  ',1);p=ROOT/rel
  if not p.is_file():bad.append(rel+': missing');continue
  actual=hashlib.sha256(p.read_bytes()).hexdigest()
  if actual!=expected:bad.append(rel+': checksum mismatch')
  else:good+=1
 print(f'INTEGRITY CHECK: {"FAIL" if bad else "PASS"}; {good} files verified')
 for x in bad:print(x)
 return int(bool(bad))
if __name__=='__main__':sys.exit(main())
