#!/usr/bin/env python3
"""Offline reproducibility for the fixed illustrative corpus, not a search/selection replay."""
from __future__ import annotations
import csv,json,itertools
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04_outputs'
BINARY=['core_flag','comparative','user_outcome','clinical_outcome','safety_focused_investigation','response_accuracy_benchmark','referral_intention_proxy','health_system_operations','patient_productivity']

def read(name:str)->list[dict[str,str]]:
    with (ROOT/'01_data'/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def write(name:str,rows:list[dict])->None:
    if not rows:raise ValueError(f'No output rows for {name}')
    OUT.mkdir(exist_ok=True)
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def validate(rows:list[dict])->None:
    ids=[r['study_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate report IDs')
    for r in rows:
        for key in BINARY:
            if str(r[key]) not in {'0','1'}:
                raise ValueError(f"{r['study_id']}:{key} must be 0 or 1; unknowns cannot become zero")

def tally(rows:list[dict])->dict:
    n=len(rows)
    if not n:raise ValueError('An empty denominator has no percentage')
    d={'n':n,'mental':sum(r['domain']=='Mental health and well-being' for r in rows)}
    for k in ['comparative','user_outcome','clinical_outcome','safety_focused_investigation','health_system_operations','patient_productivity']:
        d[k]=sum(int(r[k]) for r in rows)
    for k,v in list(d.items()):
        if k!='n':d[k+'_pct']=round(100*v/n,1)
    return d

def main()->None:
    OUT.mkdir(exist_ok=True)
    allrows=read('coding_revised_all24.csv');validate(allrows)
    core=[r for r in allrows if int(r['core_flag'])]
    standalone=read('coding_revised_core22.csv')
    assert core==standalone,'Standalone core file differs from filtered master'
    assert len(allrows)==24 and len(core)==22
    assert {r['study_id'] for r in allrows if not int(r['core_flag'])}=={'S06','S07'}
    roster=read('full_study_roster26.csv')
    assert len(roster)==26 and len({r['Study ID'] for r in roster})==26
    assert {r['study_id'] for r in core}<={r['Study ID'] for r in roster}
    expected={'n':22,'mental':13,'comparative':7,'user_outcome':22,'clinical_outcome':11,'safety_focused_investigation':1,'health_system_operations':1,'patient_productivity':1}
    res=tally(core);assert all(res[k]==v for k,v in expected.items())
    summary=[]
    for dim in ['domain','design_family','geographic_context','legacy_confidence']:
        cnt=Counter(r[dim] for r in core);assert sum(cnt.values())==22
        for label,n in sorted(cnt.items()):
            summary.append({'dimension':dim,'category':label,'n':n,'denominator':22,'percent':round(100*n/22,1),'report_ids':'; '.join(r['study_id'] for r in core if r[dim]==label)})
    write('descriptive_counts.csv',summary)
    legacy=read('sensitivity_baseline24.csv')
    scenarios=[{'scenario':'Legacy24 (superseded; not a final result)','n':24,'user_n':22,'clinical_n':11,'safety_related_n':sum(int(r['Direct safety/accuracy evaluation']) for r in legacy),'operations_n':sum(int(r['Direct organizational/workflow outcome']) for r in legacy),'interpretation':'Old misclassification retained for traceability only'}]
    for label,rr in [('Corrected24 including generic benchmarks',allrows),('Healthcare-specific22',core),('Core excluding inherited Lower labels',[r for r in core if r['legacy_confidence']!='Lower']),('Core excluding referral-intention proxy',[r for r in core if r['study_id']!='S04'])]:
        t=tally(rr);scenarios.append({'scenario':label,'n':t['n'],'user_n':t['user_outcome'],'clinical_n':t['clinical_outcome'],'safety_related_n':t['safety_focused_investigation'],'operations_n':t['health_system_operations'],'interpretation':'Report counts only; not pooled effects or safety certification'})
    t=tally(allrows);scenarios.append({'scenario':'Expanded26 including consumer context','n':26,'user_n':t['user_outcome']+2,'clinical_n':t['clinical_outcome'],'safety_related_n':t['safety_focused_investigation'],'operations_n':t['health_system_operations'],'interpretation':'Consumer perceived benefit is not coded as clinical efficacy'})
    for r in scenarios:
        for k in ['user','clinical','safety_related','operations']:r[k+'_pct']=round(100*r[k+'_n']/r['n'],1)
    write('sensitivity_results.csv',scenarios)
    loo=[{'removed_id':r['study_id'],**tally([x for x in core if x['study_id']!=r['study_id']])} for r in core];write('leave_one_out.csv',loo)
    cols=['user_outcome','clinical_outcome','safety_focused_investigation','health_system_operations','patient_productivity']
    pairs=[]
    for a,b in itertools.combinations(cols,2):
        ids=[r['study_id'] for r in core if int(r[a]) and int(r[b])]
        pairs.append({'outcome_a':a,'outcome_b':b,'co_measured_n':len(ids),'denominator':22,'percent':round(100*len(ids)/22,1),'report_ids':'; '.join(ids),'interpretation':'Co-measurement only; no tested mediation or causal linkage inferred'})
    write('outcome_cooccurrence.csv',pairs)
    assert next(x['co_measured_n'] for x in pairs if x['outcome_a']=='clinical_outcome' and x['outcome_b']=='health_system_operations')==0
    theory=read('theory_examples.csv');assert len(theory)==3
    cases=read('claim_evidence_ledger9.csv');assert len(cases)==9 and len({r['case_id'] for r in cases})==9
    assert all(r['source_url'] and r['doi'] and r['additional_evidence_required'] for r in cases)
    claims=read('claim_dispositions18.csv')
    allowed={'Supported within tested conditions','Supported with qualifications','Not established','Not assessed'}
    assert len(claims)==18 and len({x['assessment_id'] for x in claims})==18
    assert {x['disposition'] for x in claims}==allowed
    for case in cases:
        assert len([x for x in claims if x['case_id']==case['case_id']])==2
    statuses=Counter(x['disposition'] for x in claims)
    write('claim_disposition_counts.csv',[{'disposition':k,'analyst_specified_claims':v,'interpretation':'Illustrative classifications, not study-quality grades or external validation'} for k,v in sorted(statuses.items())])
    endpoints=read('verified_endpoints.csv')
    n7=sum(int(x['n']) for x in endpoints if x['record_id']=='S18' and x['timepoint']=='day7_observed')
    n30=sum(int(x['n']) for x in endpoints if x['record_id']=='S18' and x['timepoint']=='day30_observed')
    nrandom=sum(int(x['n']) for x in endpoints if x['record_id']=='S18' and x['timepoint']=='randomized')
    assert (nrandom,n7,n30)==(148,125,106)
    audit=read('source_verification_v2.csv')
    assert {x['study_id'] for x in core}<={x['record_id'] for x in audit}
    write('verification_coverage.csv',[{'scope':'Historical core reports with a current targeted source check','n':22,'boundary':'Access and fields vary; not complete independent re-extraction'},
      {'scope':'Contemporary illustrative reports','n':4,'boundary':'U03 limited to primary-author-hosted abstract'},
      {'scope':'Established-framework comparison sources','n':3,'boundary':'Conceptual crosswalk, not comparative validation'}])
    results={'design':'Non-systematic critical integrative review','title':(ROOT/'02_methods/TITLE.txt').read_text().strip(),'core':res,'theory_examples':{'selected_examples':3,'prevalence_claimed':False},'sensitivity_scenarios':len(scenarios),'leave_one_out_runs':len(loo),'cooccurrence_pairs':len(pairs),'worked_cases':len(cases),'claim_assessments':len(claims),'claim_dispositions':dict(statuses),'current_targeted_source_records':len(audit),'leave_one_out_ranges':{k:[min(r[k] for r in loo),max(r[k] for r in loo)] for k in ['mental_pct','user_outcome_pct','clinical_outcome_pct','safety_focused_investigation_pct','health_system_operations_pct']},'systematic_search_claimed':False,'independent_human_review_documented':False,'external_framework_validation':False,'author_source_approval_required':True}
    (OUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    (OUT/'validation_report.txt').write_text('ANALYTICAL REPRODUCTION: PASS\n22 historical analytical reports; 4 contextual reports; 4 contemporary illustrations outside the denominator.\nSix deterministic scenarios; 22 leave-one-out runs; 10 outcome co-occurrence pairs; 9 source-linked cases; 18 claim dispositions. Current source checks record 29 sources at different access levels.\nThis validates arithmetic, identity/linkage constraints and internal consistency—not every inherited source interpretation, complete literature selection, independent review or framework efficacy.\n',encoding='utf-8')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
