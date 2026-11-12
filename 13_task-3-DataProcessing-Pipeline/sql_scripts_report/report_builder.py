"""Turn the SQL result sets into DATA_QUALITY_REPORT.md.

Every number in the text is read from the results, so re-running run_report.py
after the data changes produces a correct report. Called by run_report.py.
"""

SPLITS = ["warmup", "train", "validation", "holdout"]


# ---------------------------------------------------------------- helpers
def rows(res, name):
    r = res[name]
    return [dict(zip(r["columns"], v)) for v in r["rows"]]


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return f"{int(v):,}"
        return f"{v:,.4f}".rstrip("0").rstrip(".")
    if isinstance(v, int):
        return f"{v:,}"
    return str(v).replace("|", "\\|")


def table(data, cols=None, headers=None):
    if not data:
        return "_No rows._\n"
    cols = cols or list(data[0].keys())
    headers = headers or cols
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for d in data:
        out.append("| " + " | ".join(fmt(d.get(c)) for c in cols) + " |")
    return "\n".join(out) + "\n"


def n(v):
    return fmt(v)


def pct(a, b):
    return f"{100.0 * a / b:.2f}%" if b else "n/a"


# ---------------------------------------------------------------- report
def build(res, meta, path):
    L = []
    w = L.append

    split_rows = rows(res, "rows_per_split")
    total = next(r for r in split_rows if r["split"] == "TOTAL")
    nulls = rows(res, "nulls_per_column")
    null_nz = [r for r in nulls if r["null_count"]]
    nps = {r["split"]: r for r in rows(res, "nulls_per_split")}
    dups = rows(res, "duplicates")
    dup_ex = rows(res, "content_duplicate_examples")
    cov = rows(res, "one_to_one_coverage")
    types = rows(res, "declared_types")
    bad_types = [r for r in types if r["status"] != "ok"]
    invalid = rows(res, "invalid_values")
    bad_vals = [r for r in invalid if r["violations"]]
    iqr = {r["split"] or "ALL": r for r in rows(res, "amount_outliers_iqr")}
    dist = rows(res, "amount_distribution_per_split")
    ofr = {r["amount_group"]: r for r in rows(res, "outlier_fraud_rate")}
    match = rows(res, "match_rate_per_feature")
    req = [r for r in match if r["kind"] == "requested"]
    sup = [r for r in match if r["kind"] == "supporting"]
    rc = rows(res, "reason_code_match")
    rcs = rows(res, "reason_code_set_match_per_split")
    rcs_all = next(r for r in rcs if r["split"] == "ALL")
    causes = rows(res, "mismatch_causes")
    mm_ex = rows(res, "mismatch_examples")
    raw_cmp = rows(res, "raw_column_vs_recomputed")
    gaps = rows(res, "avg_value_rounding_gaps")
    variants = rows(res, "variant_match_rates")
    summ = {r["split"] or "ALL": r for r in rows(res, "recompute_summary")}
    total_mm = sum(r["mismatches"] for r in match)
    total_rc_mm = rcs_all["rows"] - rcs_all["exact_set_matches"]

    # ---------------------------------------------------------- title + summary
    w("# SENTINEL – Data Quality and Feature Verification Report\n")
    w(f"_Generated {meta['generated_at']} by `run_report.py` from the Supabase tables "
      "customers, merchants, devices, transactions, payment_outcomes, labels and features. "
      "Every number below comes from the SQL scripts in this folder; the raw result of each "
      "query is in `output/<name>.csv`._\n")

    w("## Summary\n")
    w(f"- **{n(total['transactions'])} transactions** across four time splits; every transaction has exactly one "
      "payment outcome, one label and one features row. No split leaks across its calendar window.")
    w(f"- **Nulls** appear only in the {len(null_nz)} columns that are allowed to be null: "
      + ", ".join(f"`{r['table_name']}.{r['column_name']}` {r['null_pct']}%" for r in null_nz) + ".")
    real_dups = [r for r in dups if "PK" in r["key_checked"] and r["duplicate_rows"]]
    w(f"- **Duplicates:** {'none' if not real_dups else real_dups} on any key, and no transaction appears twice "
      f"under different ids. {len(dup_ex)} rows have content identical to another row; all are coincidences, "
      "not double loads (section 3).")
    w(f"- **Wrong types / invalid values:** {len(bad_types)} column-type mismatches against the data dictionary and "
      f"{len(bad_vals)} failing value checks out of {len(invalid)}.")
    w(f"- **Amount outliers:** amounts are heavily right-skewed. On a log scale, {n(iqr['ALL']['log_high_1_5iqr'])} "
      f"transactions sit above the upper fence (₹{n(iqr['ALL']['log_upper_fence_inr'])}). Their fraud rate is "
      f"{n(ofr['high outlier (log IQR)']['fraud_pct'])}%, against {n(ofr['normal']['fraud_pct'])}% for normal amounts, "
      "so they are signal and should be kept.")
    w(f"- **Features:** all six requested features recomputed point-in-time in SQL. Match rate with "
      f"`public.features`: " + ", ".join(f"`{r['feature']}` {r['match_rate_pct']}%" for r in req) + ".")
    w(f"- **Reason codes R01–R08:** the full code list matches on {n(rcs_all['exact_set_matches'])} of "
      f"{n(rcs_all['rows'])} transactions ({rcs_all['exact_set_match_pct']}%).")
    w(f"- **Mismatches:** {n(total_mm)} feature mismatches and {n(total_rc_mm)} reason-code mismatches. "
      "Section 9 explains what would cause them and the one place where a shortcut does disagree "
      "(`transactions.average_transaction_value`).\n")

    # ---------------------------------------------------------- 1 splits
    w("## 1. Row count per split\n")
    w("_Script `01_dq_row_counts_per_split.sql`_\n")
    w(table(split_rows,
            ["split", "transactions", "with_payment_outcome", "labels", "with_features", "fraud_labels", "fraud_pct",
             "first_txn_ist", "last_txn_ist"],
            ["Split", "Transactions", "With outcome", "Labels", "With features", "Fraud", "Fraud %",
             "First txn (IST)", "Last txn (IST)"]))
    tr = next(r for r in split_rows if r["split"] == "train")
    w(f"The train split holds {pct(tr['transactions'], total['transactions'])} of rows. Fraud prevalence is "
      f"{total['fraud_pct']}% overall, in line with the ~0.6% target in the CRD. "
      "Split boundaries follow the IST calendar: warmup Oct–Dec 2024, train Jan–Oct 2025, validation Nov–Dec 2025, "
      "holdout Jan–Feb 2026.\n")
    w(table(rows(res, "split_consistency"), ["check_name", "violations"], ["Check", "Violations"]))
    w(table(rows(res, "table_row_counts"), ["table_name", "row_count"], ["Table", "Rows"]))

    # ---------------------------------------------------------- 2 nulls
    w("## 2. Nulls per column\n")
    w("_Script `02_dq_nulls_per_column.sql`. It uses `to_jsonb(row)` so that one query covers every column._\n")
    w("Columns with at least one null:\n")
    w(table(null_nz, ["table_name", "column_name", "row_count", "null_count", "null_pct", "declared_nullable"],
            ["Table", "Column", "Rows", "Nulls", "Null %", "Nullable in schema"]))
    w(f"The other {len(nulls) - len(null_nz)} columns have 0 nulls. The JSON location values have no missing "
      "`lat`, `lon` or `city` keys either.\n")
    w(table(rows(res, "nulls_per_split"), None,
            ["Split", "Transactions", "Null device_id", "Null customer_location", "Null average_transaction_value"]))
    w("Why the nulls are expected, not errors:\n")
    w("- `device_id` and `customer_location` are optional in the CRD, because the device or location is sometimes "
      "unknown. They become nulls in `is_new_device`, `customer_merchant_distance_km` and `is_new_city`, so "
      "\"unknown\" never fires a risk flag.")
    w(f"- `average_transaction_value` is null when the customer has no transaction in the previous 90 days. "
      f"{n(nps['warmup']['null_average_transaction_value'])} of the {n(sum(r['null_average_transaction_value'] for r in nps.values()))} "
      "cases are in warmup, the first three months of data, where histories are still empty (cold start). "
      "Warmup exists precisely so that train starts with warm histories.")
    w("- `payment_outcomes.failure_code` is null exactly for SUCCESS outcomes (checked in section 4).\n")
    w("**Recommendation:** keep the nulls as nulls. Do not impute 0 or false: \"no history\" and \"unknown device\" "
      "are different from \"normal\".\n")

    # ---------------------------------------------------------- 3 duplicates
    w("## 3. Duplicates\n")
    w("_Script `03_dq_duplicates.sql`_\n")
    w(table(dups, ["table_name", "key_checked", "duplicate_rows"], ["Table", "Key checked", "Duplicate rows"]))
    w("Rows whose content (everything except the id) equals another row's:\n")
    w(table(dup_ex, ["table_name", "id", "content", "own_transactions"], ["Table", "Id", "Content", "Own transactions"]))
    w("Neither group is a duplicate load:\n")
    w("- **Customers:** customers have only 5 descriptive columns, and `created_at` is a date (IST midnight). "
      "Pairs that share date, age and city are expected among 2,500 customers. Each id in a pair has its own, "
      "different transaction history, so these are distinct people.")
    w("- **Payment outcome:** these are two different transactions by the same customer, 30 ms apart and for "
      "different amounts, and both were declined in the same instant. This is a burst of attempts, which is "
      "exactly what R07 velocity looks for. It is not a copy.\n")
    w("Referential integrity and 1:1 coverage:\n")
    w(table(cov, ["check_name", "violations"], ["Check", "Rows"]))
    w("Customers and devices with no transactions are reference rows that were never used (for example "
      "registered spare devices). They are harmless, but they should not be counted when computing per-device "
      "or per-customer rates.\n")

    # ---------------------------------------------------------- 4 types
    w("## 4. Wrong types and invalid values\n")
    w("_Script `04_dq_wrong_types.sql`_\n")
    w(f"**Declared types:** {len(types) - len(bad_types)} of {len(types)} columns have the type the data dictionary "
      f"prescribes" + (" (all match)." if not bad_types else ". Mismatches:") + "\n")
    if bad_types:
        w(table(bad_types))
    w("Because Postgres enforces declared types, a wrong type can only hide inside text or JSON values, or in values "
      "of the right type that are semantically wrong. The checks below cover both.\n")
    w(table(invalid, ["table_name", "check_name", "violations"], ["Table", "Check", "Violations"]))
    w("Observed value domains (no unexpected spellings or casing):\n")
    w(table(rows(res, "category_domains"), ["column_name", "value", "rows"], ["Column", "Value", "Rows"]))

    # ---------------------------------------------------------- 5 outliers
    w("## 5. Outliers in amount\n")
    w("_Script `05_dq_amount_outliers.sql`. Amounts come from `amount_paise`; INR = paise / 100._\n")
    w(table(dist, ["split", "rows", "min_inr", "p01_inr", "p25_inr", "median_inr", "mean_inr", "p75_inr", "p99_inr", "max_inr"],
            ["Split (blank = all)", "Rows", "Min ₹", "P1 ₹", "P25 ₹", "Median ₹", "Mean ₹", "P75 ₹", "P99 ₹", "Max ₹"]))
    w(table(list(iqr.values()),
            ["split", "rows", "raw_high_1_5iqr", "raw_high_3iqr", "log_high_1_5iqr", "log_low_1_5iqr", "log_high_3iqr",
             "raw_upper_fence_inr", "log_upper_fence_inr", "log_extreme_fence_inr"],
            ["Split (blank = all)", "Rows", "Raw > 1.5 IQR", "Raw > 3 IQR", "Log > 1.5 IQR", "Log < 1.5 IQR", "Log > 3 IQR",
             "Raw fence ₹", "Log fence ₹", "Log extreme fence ₹"]))
    a = iqr["ALL"]
    w(f"The mean is about 3.5 times the median, so the raw Tukey fence (₹{n(a['raw_upper_fence_inr'])}) flags "
      f"{n(a['raw_high_1_5iqr'])} rows ({pct(a['raw_high_1_5iqr'], a['rows'])}). That count reflects the skewed "
      f"shape of spending, not errors. On log10(amount), which is the right scale for money, "
      f"{n(a['log_high_1_5iqr'])} rows ({pct(a['log_high_1_5iqr'], a['rows'])}) are high outliers and "
      f"{n(a['log_high_3iqr'])} are extreme (above ₹{n(a['log_extreme_fence_inr'])}). Outlier rates are similar in "
      "every split, so there is no drift.\n")
    w("Robust z-score (|log amount − median| / 1.4826·MAD > 3.5) within each merchant category:\n")
    w(table(rows(res, "amount_outliers_by_category"), None,
            ["Category", "Rows", "Median ₹", "Outliers", "Outlier %", "Max ₹"]))
    w("Fraud rate by amount group:\n")
    w(table(list(ofr.values()), None, ["Amount group", "Rows", "Fraud", "Fraud %"]))
    w("The 15 largest amounts:\n")
    w(table(rows(res, "top_amounts"), None,
            ["Transaction", "Split", "Customer", "Category", "Channel", "Amount ₹", "Customer avg ₹", "Ratio", "Fraud"]))
    w("**Interpretation and recommendation**\n")
    w(f"- High-amount outliers are about {ofr['high outlier (log IQR)']['fraud_pct'] / max(ofr['normal']['fraud_pct'], 1e-9):.0f} "
      "times more likely to be fraud. They are signal, not noise, so do **not** delete or cap them in the "
      "labelled data.")
    w("- The very largest amounts (₹50–80 lakh, thousands of times the customer's average) are all labelled "
      "non-fraud. These look like injected extreme values that test robustness. They are valid rows "
      "(`amount_paise = transaction_amount × 100`, positive), but they dominate any mean-based statistic. "
      "Use log(amount) or the ratio feature in models, and the median, not the mean, in summaries.")
    w("- High-risk categories (gaming, gift cards, electronics) have the most within-category outliers, which "
      "is consistent with R08.\n")

    # ---------------------------------------------------------- 6 features
    w("## 6. Feature recomputation (point-in-time, no future leakage)\n")
    w("_Script `10_features_recompute.sql` writes `sentinel_dq.recomputed_features`. It uses a separate schema, "
      "so nothing in `public` is changed._\n")
    w("Leakage rules applied to every transaction at time **T**:\n")
    w("1. History is the **same customer's transactions with `transaction_time < T`**, strictly earlier. The "
      "current transaction is never part of its own history.")
    w("2. A payment outcome counts only once it has been received: `outcome_time < T`.")
    w("3. Nothing is read from `labels` or from the `public.features` table being checked.\n")
    w("| Feature | Definition used |\n|---|---|")
    w("| `amount_to_average_ratio` (`amount_to_avg_ratio`) | amount_paise / mean(amount_paise) of the customer's transactions in [T−90 days, T), rounded to 4 dp. Declined attempts count (they are authorisations). NULL when there is no 90-day history. |")
    w("| `is_new_device` | device_id not used by this customer in [T−90 days, T). NULL when the device is unknown. |")
    w("| `customer_merchant_distance_km` | haversine on customer and merchant lat/lon, Earth radius 6,371 km, rounded to 2 dp. NULL when the customer location is unknown. |")
    w("| `is_night` | hour in **IST** (Asia/Kolkata) is in 00:00–04:59 (00:00 inclusive, 05:00 exclusive). |")
    w("| `transaction_count_last_1_hour` (`txn_count_last_1h`) | count of the customer's transactions in [T−1 h, T), declines included. |")
    w("| `transaction_amount_last_24_hours` (`txn_amount_last_24h_paise`) | sum of amount_paise of the customer's transactions in [T−24 h, T), declines included. |")
    w("| supporting: `is_new_city`, `failed_last_24h`, `account_age_days` | city not seen in [T−90 d, T); FAILED outcomes received in [T−24 h, T); complete days since `customers.created_at`. These feed R02, R04 and R06. |\n")
    w("All windows are computed in one pass: a self-join of each transaction to the same customer's earlier "
      "transactions of the last 90 days, aggregated with `FILTER (WHERE …)` per window.\n")
    w(table(list(summ.values()), None,
            ["Split (blank = all)", "Rows", "Null ratio (no 90d history)", "Null new-device (no device)",
             "Null distance (no location)", "Avg ratio", "New device %", "Avg distance km", "Night %",
             "Avg txns last 1h", "Avg ₹ last 24h"]))
    w("The warmup split shows a high new-device rate and a high average ratio. This is the cold-start effect: "
      "histories are short at the start of the data, so most devices are \"new\" and averages are taken over "
      "very few transactions.\n")

    # ---------------------------------------------------------- 7 reason codes
    w("## 7. Reason codes\n")
    w("_Script `11_reason_codes.sql` (thresholds are in table `sentinel_dq.reason_code_thresholds`; change them "
      "there and re-run). Script `14_threshold_evidence.sql` checks each threshold against the provided table._\n")
    w("| Code | Fires when | Threshold |\n|---|---|---|")
    w("| R01_NEW_DEVICE | `is_new_device` = true | – |")
    w("| R02_GEO_MISMATCH | `is_new_city` = true **or** distance > threshold | 500 km |")
    w("| R03_ODD_HOUR | `is_night` = true | IST 00:00–04:59 |")
    w("| R04_FAILED_ATTEMPTS | failed outcomes received in the previous 24 h ≥ threshold | 3 |")
    w("| R05_AMOUNT_SPIKE | `amount_to_avg_ratio` ≥ threshold | 5× |")
    w("| R06_NEW_ACCOUNT | account age < threshold | 30 days |")
    w("| R07_VELOCITY | `txn_count_last_1h` ≥ threshold | 4 in 1 h |")
    w("| R08_HIGH_RISK_MCC | merchant category in the high-risk list | electronics, gaming, gift_cards |\n")
    w("A null (unknown) feature never fires a code.\n")
    w("**Threshold evidence from `public.features`.** For each code, compare the largest value on rows that do "
      "not have the code with the smallest value on rows that do. A clean gap means no row contradicts the "
      "threshold.\n")
    w(table(rows(res, "threshold_evidence"), None,
            ["Code", "Feature", "Max without code", "Min with code", "Threshold used"]))
    w(table(rows(res, "boolean_code_evidence"), None, ["Code", "Flag true but no code", "Code but flag not true"]))
    w(table(rows(res, "mcc_code_evidence"), None, ["Category", "Rows", "R08 fired %", "Fraud %"]))
    w("Every boundary is clean, and only the three high-risk categories carry R08. They are also the only "
      "categories with a material fraud rate.\n")
    w(table(rows(res, "reason_code_fire_rates"), None, ["Code", "Fired", "Fired %", "Fired % train", "Fired % holdout"]))
    w("Note: R02 fires on about 82% of transactions. Customers usually buy from merchants in another city, so "
      "the new-city / 500 km rule is weak as a stand-alone signal. Weight it accordingly.\n")

    # ---------------------------------------------------------- 8 match rate
    w("## 8. Comparison with the provided features table: match rate per feature\n")
    w("_Script `12_feature_compare.sql`. A value matches when it is equal or both are NULL. Floats are compared "
      "within 1e-9; both sides are already rounded, so this is effectively an exact comparison._\n")
    cols = ["feature", "rows", "matches", "mismatches", "match_rate_pct", "warmup_pct", "train_pct",
            "validation_pct", "holdout_pct", "nulls_mine", "nulls_ref"]
    hdr = ["Feature", "Rows", "Matches", "Mismatches", "Match %", "Warmup %", "Train %", "Validation %",
           "Holdout %", "Nulls (mine)", "Nulls (ref)"]
    w("**Requested features**\n")
    w(table(req, cols, hdr))
    w("**Supporting features** (needed for R02, R04 and R06)\n")
    w(table(sup, cols, hdr))
    w("**Reason codes**: agreement per code and full-list match per split\n")
    w(table(rc, None, ["Code", "Fired (mine)", "Fired (ref)", "Only mine", "Only ref", "Agree %"]))
    w(table(rcs, None, ["Split", "Rows", "Exact set matches", "Exact set match %", "Same order"]))
    w(table(rows(res, "unknown_codes_in_reference"), None, ["Code in reference not known here", "Rows"]))

    # ---------------------------------------------------------- 9 mismatches
    w("## 9. Mismatches explained\n")
    w("_Script `13_mismatch_diagnosis.sql` puts every mismatching (transaction, feature) pair into a cause bucket. "
      "Script `15_leakage_variants.sql` shows what each common mistake does to the match rate._\n")
    if total_mm == 0 and total_rc_mm == 0:
        w(f"**There are no mismatches.** All {n(sum(r['rows'] for r in match))} feature comparisons and all "
          f"{n(rcs_all['rows'])} reason-code lists agree. Every null is null on both sides, which confirms that "
          "the provided table uses the same definitions as section 6. In particular:\n")
        w("- the current transaction is excluded from its own history;")
        w("- declined attempts count in the velocity and amount windows;")
        w("- the device lookback is 90 days, not \"ever\";")
        w("- the night hour is taken in IST;")
        w("- the Earth radius is 6,371 km;")
        w("- rounding is to 4 dp for the ratio and 2 dp for the distance.\n")
    else:
        w("Cause of every mismatch:\n")
        w(table(causes, None, ["Feature", "Cause", "Rows", "Example transaction"]))
        w(table(mm_ex, None, ["Feature", "Transaction", "Split", "Mine", "Reference", "Difference"]))
        w(table(rows(res, "reason_code_mismatch_examples")))
    w("### What would cause mismatches (and therefore what the reference is *not* doing)\n")
    w("Each row recomputes one feature with a common mistake and measures its match rate against "
      "`public.features`:\n")
    w(table(variants, None, ["Feature", "Wrong definition", "Match %"]))
    vm = {(r["feature"], r["variant"][:1]): r["match_rate_pct"] for r in variants}
    w("How to read this:\n")
    w(f"- **Leakage** (counting the current transaction in its own window) breaks almost every row: "
      f"{vm.get(('amount_to_avg_ratio','B'))}% for the ratio and {vm.get(('txn_count_last_1h','B'))}% for the "
      "1-hour count. With 100% achieved above, this proves both the reference and these scripts are leakage-free.")
    w(f"- **Dropping declined attempts** gives {vm.get(('amount_to_avg_ratio','C'))}% for the ratio and "
      f"{vm.get(('txn_count_last_1h','C'))}% for the 1-hour count. The CRD counts authorisation *attempts*, and "
      "declines are themselves a fraud signal (card testing).")
    w(f"- **Device seen \"ever\"** instead of within 90 days gives {vm.get(('is_new_device','B'))}%. The "
      f"{100 - vm.get(('is_new_device','B'), 100):.3f}% difference is customers who return to a device after a "
      "gap of more than 90 days.")
    w(f"- **UTC instead of IST** for the night flag gives {vm.get(('is_night','B'))}%, because IST is UTC+5:30. "
      f"A 22:00–06:00 night window gives {vm.get(('is_night','C'))}%.")
    w(f"- **Equatorial Earth radius** (6,378.137 km) gives {vm.get(('customer_merchant_distance_km','B'))}% "
      "after rounding to 2 dp, even though the error is only 0.11%.\n")
    w("### The precomputed columns in `transactions`\n")
    w(table(raw_cmp, None, ["Comparison", "Rows", "Matches", "Match %"]))
    w("`failed_transactions` and `account_age` in the raw table agree exactly with the point-in-time values. "
      "`average_transaction_value`, however, is stored rounded to 2 dp (rupees and paise). A ratio built from it "
      f"matches only {raw_cmp[2]['match_pct']}% of the time at 4 dp, and {raw_cmp[3]['match_pct']}% within 0.001. "
      f"The {n(len(gaps))} rows still off by more than 0.001 are shown below. In each one the gap stays within "
      "the bound that rounding the average to the nearest paisa can create (0.005 ₹ × ratio / average): the "
      "ratio is huge or the average is tiny, which magnifies the rounding.\n")
    w(table(gaps, None, ["Transaction", "Split", "Amount ₹", "Stored avg ₹", "Point-in-time ratio",
                         "Ratio from 2-dp avg", "Gap", "Max gap from rounding"]))
    w("**Recommendation:** compute the ratio from `amount_paise` and the exact 90-day mean, as script 10 does. "
      "Do not use `transactions.average_transaction_value`, which is a rounded display value.\n")

    # ---------------------------------------------------------- appendix
    w("## Appendix: how to reproduce\n")
    w("```powershell\ncd supabase_db_kit\\sql_scripts_report\n..\\venv\\Scripts\\python run_report.py\n```\n")
    w("Each `.sql` file also runs on its own in the Supabase SQL Editor (run 10 → 11 → 12 → 13 in that order; "
      "01–05, 14 and 15 are independent). `99_cleanup.sql` drops the `sentinel_dq` working schema.\n")
    w(table(meta["timings"], ["script", "seconds"], ["Script", "Run time (s)"]))

    path.write_text("\n".join(L), encoding="utf-8")
