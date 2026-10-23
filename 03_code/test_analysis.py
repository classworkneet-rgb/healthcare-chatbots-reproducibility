import unittest
import reproduce as r
class AnalysisTests(unittest.TestCase):
 def setUp(self):self.rows=r.read('coding_revised_all24.csv')
 def test_core_membership(self):
  r.validate(self.rows);self.assertEqual({x['study_id'] for x in self.rows if x['core_flag']=='0'},{'S06','S07'})
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):r.validate(self.rows+[self.rows[0]])
 def test_unknown_not_zero(self):
  bad=[dict(x) for x in self.rows];bad[0]['clinical_outcome']=''
  with self.assertRaises(ValueError):r.validate(bad)
 def test_empty_denominator_rejected(self):
  with self.assertRaises(ValueError):r.tally([])
 def test_productivity_not_operations(self):
  x=next(x for x in self.rows if x['study_id']=='S24');self.assertEqual(x['patient_productivity'],'1');self.assertEqual(x['health_system_operations'],'0')
 def test_satisfaction_not_safety(self):
  self.assertEqual(next(x for x in self.rows if x['study_id']=='S05')['safety_focused_investigation'],'0')
 def test_wellbeing_not_operations(self):
  self.assertEqual(next(x for x in self.rows if x['study_id']=='S21')['health_system_operations'],'0')
 def test_case_identity(self):
  cases=r.read('claim_evidence_ledger9.csv');self.assertEqual(len({x['case_id'] for x in cases}),9)
 def test_current_reports_outside_core(self):
  self.assertTrue({x['record_id'] for x in r.read('currency_evidence.csv')}.isdisjoint({x['study_id'] for x in self.rows}))
 def test_primary_result(self):
  t=r.tally([x for x in self.rows if x['core_flag']=='1']);self.assertEqual((t['n'],t['clinical_outcome'],t['health_system_operations']),(22,11,1))
 def test_judson_observed_timing(self):
  e=r.read('verified_endpoints.csv')
  times={x['group']:float(x['value']) for x in e if x['record_id']=='S11' and x['endpoint']=='entrance_clearance'}
  self.assertEqual(times,{'manual':48.0,'digital':8.0})
 def test_judson_queue(self):
  e=r.read('verified_endpoints.csv')
  times={x['group']:float(x['value']) for x in e if x['record_id']=='S11' and x['endpoint']=='peak_shift_queue'}
  self.assertEqual(times,{'before':500.0,'after':100.0})
 def test_xiaoe_distinct_populations(self):
  e=r.read('verified_endpoints.csv')
  sums={t:sum(int(x['n']) for x in e if x['record_id']=='S18' and x['timepoint']==t) for t in ['randomized','day7_observed','day30_observed']}
  self.assertEqual(sums,{'randomized':148,'day7_observed':125,'day30_observed':106})
 def test_balanced_dispositions(self):
  a=r.read('claim_dispositions18.csv')
  self.assertEqual(len(a),18)
  self.assertEqual({x['disposition'] for x in a},{'Supported within tested conditions','Supported with qualifications','Not established','Not assessed'})
 def test_two_claims_per_case(self):
  from collections import Counter
  counts=Counter(x['case_id'] for x in r.read('claim_dispositions18.csv'))
  self.assertEqual(set(counts.values()),{2});self.assertEqual(len(counts),9)
 def test_framework_comparators_present(self):
  self.assertEqual({x['key'] for x in r.read('framework_comparison.csv')},{'proctor','nasss','nice','present'})
 def test_no_unfinished_stage_instruction(self):
  text=(r.ROOT/'01_data/extraction_revised24.csv').read_text()
  self.assertNotIn('verify per time point in Stage 4',text)
 def test_targeted_core_coverage(self):
  core={x['study_id'] for x in self.rows if x['core_flag']=='1'}
  self.assertTrue(core.issubset({x['record_id'] for x in r.read('source_verification_v2.csv')}))
 def test_primary_abstract_limit_preserved(self):
  row=next(x for x in r.read('claim_evidence_ledger9.csv') if x['case_id']=='CE08')
  self.assertIn('abstract',row['verification_level'].lower())
 def test_judson_not_blanket_no_evidence(self):
  row=next(x for x in r.read('claim_evidence_ledger9.csv') if x['case_id']=='CE04')
  self.assertEqual(row['primary_disposition'],'Supported with qualifications')
  self.assertIn('48',row['observed_endpoint'])
if __name__=='__main__':unittest.main()
