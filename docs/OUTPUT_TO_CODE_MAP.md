# Output-to-input map

| Output | Inputs / operation |
|---|---|
| `results.json` | Master coding, core subset, roster, case/claim records, source checks |
| `descriptive_counts.csv` | Core domain/design/geography/historical label counts |
| `sensitivity_results.csv` | Six explicitly defined eligibility/coding alternatives |
| `leave_one_out.csv` | One deterministic removal of each of 22 core reports |
| `outcome_cooccurrence.csv` | Ten pairs of five overlapping outcome flags |
| `claim_disposition_counts.csv` | Eighteen specified claims, four disposition labels |
| `verification_coverage.csv` | Field-specific source-check records, not complete full-text coverage |
| `validation_report.txt` | Checks and limitations emitted by `03_code/reproduce.py` |
| Evidence workbook | CSVs and outputs listed in `03_code/workbook_model.py` |
| `manuscript_table_1.csv` to `manuscript_table_4.csv` | Supplied table-source content; not newly inferred by numerical code |
| `main_reference_crosswalk.csv` | Supplied citation mapping for the companion manuscript |

Workbook semantics are checked against the CSV-derived model. Narrative table text,
source judgments and bibliographic interpretations are not independently validated
by the arithmetic tests. The associated manuscript itself is intentionally not
published in this data/code folder.
