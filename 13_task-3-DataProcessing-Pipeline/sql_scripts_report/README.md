# SENTINEL data-quality report (SQL)

All checks are plain PostgreSQL. Run them in the Supabase SQL Editor one by one, or run
everything and regenerate the report with:

```powershell
cd supabase_db_kit\sql_scripts_report
..\venv\Scripts\python run_report.py      # reads DATABASE_URL from ..\.env, ~2 minutes
```

| File | What it does |
|---|---|
| `01_dq_row_counts_per_split.sql` | Rows per split (warmup/train/validation/holdout) per table, fraud %, split-window checks |
| `02_dq_nulls_per_column.sql` | Nulls for every column of the 6 tables, per split, and inside location JSON |
| `03_dq_duplicates.sql` | Key, full-row and business-key duplicates; orphan / missing 1:1 rows |
| `04_dq_wrong_types.sql` | Declared types vs data dictionary; invalid values (JSON types, ranges, ids, domains, money, time order) |
| `05_dq_amount_outliers.sql` | Amount distribution, IQR fences (raw and log), robust z per category, fraud rate of outliers |
| `10_features_recompute.sql` | Point-in-time features → `sentinel_dq.recomputed_features` |
| `11_reason_codes.sql` | Thresholds table + reason codes R01–R08 → `sentinel_dq.recomputed_reason_codes` |
| `12_feature_compare.sql` | Match rate per feature and split vs `public.features`; reason-code agreement |
| `13_mismatch_diagnosis.sql` | Cause bucket and examples for every mismatch; raw-column comparisons |
| `14_threshold_evidence.sql` | Shows each reason-code threshold is consistent with `public.features` |
| `15_leakage_variants.sql` | Match rate of common wrong definitions (leakage, UTC, no declines, ...) |
| `99_cleanup.sql` | Drops the `sentinel_dq` working schema (public tables untouched) |
| `run_report.py`, `report_builder.py` | Runner and Markdown report generator |
| `DATA_QUALITY_REPORT.md` | The generated report |
| `output/*.csv`, `output/results.json` | Raw result of every query |

Scripts 10 → 11 → 12 → 13 depend on each other in that order; the others are independent.
Scripts 10–12 write only to schema `sentinel_dq`; nothing in `public` is modified.
Reason-code thresholds are edited in one place: the INSERT in `11_reason_codes.sql`.
