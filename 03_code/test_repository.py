"""Repository-level guardrails; not an independent validation of scientific evidence."""
import unittest, ast, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RepositoryTests(unittest.TestCase):
    def test_one_command_runner(self):
        self.assertTrue((ROOT/'check_reproduction.py').is_file())
    def test_source_limits_documented(self):
        t=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertIn('non-systematic',t.lower())
        self.assertIn('paired screening',t)
    def test_no_manuscript_or_author_only_files(self):
        for p in ROOT.rglob('*'):
            if not p.is_file() or 'build' in p.parts: continue
            self.assertNotIn(p.suffix.lower(),{'.docx','.pdf'})
            self.assertNotIn('reviewer_response',p.name.lower())
            self.assertNotIn('title_page',p.name.lower())
    def test_dictionary_available(self):
        self.assertTrue((ROOT/'docs/data_dictionary.csv').is_file())
    def test_workflow_is_pinned(self):
        t=(ROOT/'.github/workflows/reproducibility.yml').read_text(encoding='utf-8')
        refs=re.findall(r'uses:\s*[^@\s]+@([^\s]+)',t)
        self.assertEqual(len(refs),2)
        self.assertTrue(all(re.fullmatch(r'[a-f0-9]{40}',x) for x in refs))
    def test_no_publication_or_doi_invention(self):
        self.assertFalse((ROOT/'CITATION.cff').exists())
        self.assertIn('not supplied',(ROOT/'CITATION.md').read_text(encoding='utf-8'))
    def test_claim_totals(self):
        r=json.loads((ROOT/'04_outputs/results.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(r['claim_dispositions'].values()),18)
    def test_results_json_uses_canonical_lf(self):
        data=(ROOT/'04_outputs/results.json').read_bytes()
        self.assertNotIn(b'\r',data)
        self.assertIsInstance(json.loads(data.decode('utf-8')),dict)
    def test_validation_report_uses_canonical_lf(self):
        data=(ROOT/'04_outputs/validation_report.txt').read_bytes()
        self.assertNotIn(b'\r',data)
        self.assertIn('ANALYTICAL REPRODUCTION: PASS',data.decode('utf-8'))
    def test_manifest_paths_safe(self):
        for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
            digest,rel=line.split('  ',1)
            self.assertRegex(digest,r'^[a-f0-9]{64}$')
            self.assertFalse(Path(rel).is_absolute())
            self.assertNotIn('..',Path(rel).parts)
if __name__=='__main__':unittest.main()
