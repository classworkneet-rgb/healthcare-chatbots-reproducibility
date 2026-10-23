#!/usr/bin/env python3
"""Maintain checksums after an explicitly reviewed change; not an integrity repair."""
from pathlib import Path
import argparse, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'SHA256SUMS.txt','MANIFEST.json'}
def included():
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(x in {'.git','__pycache__','build','.venv','venv'} for x in rel.parts): continue
        if str(rel) in EXCLUDED or p.suffix in {'.pyc','.pyo'}: continue
        yield p,rel.as_posix()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-reviewed-changes',action='store_true')
    args=parser.parse_args()
    if not args.confirm_reviewed_changes:
        parser.error('Review all changed inputs/outputs first, then use --confirm-reviewed-changes.')
    records=[{'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,rel in included()]
    (ROOT/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['path']+'\n' for r in records),encoding='utf-8')
    (ROOT/'MANIFEST.json').write_text(json.dumps({'version':'1.0.0','files':records},indent=2)+'\n',encoding='utf-8')
    print(f'Manifest regenerated after operator confirmation: {len(records)} files')
if __name__=='__main__':main()
