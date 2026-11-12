# SENTINEL – Data Quality and Feature Verification Report

_Generated 2026-11-11T18:39:54-06:00 by `run_report.py` from the Supabase tables customers, merchants, devices, transactions, payment_outcomes, labels and features. Every number below comes from the SQL scripts in this folder; the raw result of each query is in `output/<name>.csv`._

## Summary

- **110,000 transactions** across four time splits; every transaction has exactly one payment outcome, one label and one features row. No split leaks across its calendar window.
- **Nulls** appear only in the 4 columns that are allowed to be null: `transactions.device_id` 1.035%, `transactions.customer_location` 2.961%, `transactions.average_transaction_value` 2.572%, `payment_outcomes.failure_code` 89.077%.
- **Duplicates:** none on any key, and no transaction appears twice under different ids. 8 rows have content identical to another row; all are coincidences, not double loads (section 3).
- **Wrong types / invalid values:** 0 column-type mismatches against the data dictionary and 0 failing value checks out of 29.
- **Amount outliers:** amounts are heavily right-skewed. On a log scale, 985 transactions sit above the upper fence (₹27,381.55). Their fraud rate is 16.142%, against 0.461% for normal amounts, so they are signal and should be kept.
- **Features:** all six requested features recomputed point-in-time in SQL. Match rate with `public.features`: `amount_to_avg_ratio` 100.0%, `customer_merchant_distance_km` 100.0%, `is_new_device` 100.0%, `is_night` 100.0%, `txn_amount_last_24h_paise` 100.0%, `txn_count_last_1h` 100.0%.
- **Reason codes R01–R08:** the full code list matches on 110,000 of 110,000 transactions (100.0%).
- **Mismatches:** 0 feature mismatches and 0 reason-code mismatches. Section 9 explains what would cause them and the one place where a shortcut does disagree (`transactions.average_transaction_value`).

## 1. Row count per split

_Script `01_dq_row_counts_per_split.sql`_

| Split | Transactions | With outcome | Labels | With features | Fraud | Fraud % | First txn (IST) | Last txn (IST) |
|---|---|---|---|---|---|---|---|---|
| warmup | 10,000 | 10,000 | 10,000 | 10,000 | 60 | 0.6 | 2024-10-01T00:05:15.602000 | 2024-12-31T23:39:03.133000 |
| train | 72,050 | 72,050 | 72,050 | 72,050 | 438 | 0.608 | 2025-01-01T00:37:56.971000 | 2025-10-31T23:46:30.969000 |
| validation | 14,061 | 14,061 | 14,061 | 14,061 | 89 | 0.633 | 2025-11-01T00:14:47.012000 | 2025-12-31T23:34:31.050000 |
| holdout | 13,889 | 13,889 | 13,889 | 13,889 | 73 | 0.526 | 2026-01-01T01:06:56.017000 | 2026-02-28T23:37:27.471000 |
| TOTAL | 110,000 | 110,000 | 110,000 | 110,000 | 660 | 0.6 | 2024-10-01T00:05:15.602000 | 2026-02-28T23:37:27.471000 |

The train split holds 65.50% of rows. Fraud prevalence is 0.6% overall, in line with the ~0.6% target in the CRD. Split boundaries follow the IST calendar: warmup Oct–Dec 2024, train Jan–Oct 2025, validation Nov–Dec 2025, holdout Jan–Feb 2026.

| Check | Violations |
|---|---|
| labels.split <> transactions.split | 0 |
| transaction outside its split calendar window | 0 |
| split value not in (warmup,train,validation,holdout) | 0 |

| Table | Rows |
|---|---|
| customers | 2,500 |
| merchants | 200 |
| devices | 10,120 |
| transactions | 110,000 |
| payment_outcomes | 110,000 |
| labels | 110,000 |
| features | 110,000 |

## 2. Nulls per column

_Script `02_dq_nulls_per_column.sql`. It uses `to_jsonb(row)` so that one query covers every column._

Columns with at least one null:

| Table | Column | Rows | Nulls | Null % | Nullable in schema |
|---|---|---|---|---|---|
| transactions | device_id | 110,000 | 1,138 | 1.035 | YES |
| transactions | customer_location | 110,000 | 3,257 | 2.961 | YES |
| transactions | average_transaction_value | 110,000 | 2,829 | 2.572 | YES |
| payment_outcomes | failure_code | 110,000 | 97,985 | 89.077 | YES |

The other 40 columns have 0 nulls. The JSON location values have no missing `lat`, `lon` or `city` keys either.

| Split | Transactions | Null device_id | Null customer_location | Null average_transaction_value |
|---|---|---|---|---|
| warmup | 10,000 | 185 | 273 | 2,001 |
| train | 72,050 | 858 | 2,153 | 624 |
| validation | 14,061 | 46 | 421 | 105 |
| holdout | 13,889 | 49 | 410 | 99 |

Why the nulls are expected, not errors:

- `device_id` and `customer_location` are optional in the CRD, because the device or location is sometimes unknown. They become nulls in `is_new_device`, `customer_merchant_distance_km` and `is_new_city`, so "unknown" never fires a risk flag.
- `average_transaction_value` is null when the customer has no transaction in the previous 90 days. 2,001 of the 2,829 cases are in warmup, the first three months of data, where histories are still empty (cold start). Warmup exists precisely so that train starts with warm histories.
- `payment_outcomes.failure_code` is null exactly for SUCCESS outcomes (checked in section 4).

**Recommendation:** keep the nulls as nulls. Do not impute 0 or false: "no history" and "unknown device" are different from "normal".

## 3. Duplicates

_Script `03_dq_duplicates.sql`_

| Table | Key checked | Duplicate rows |
|---|---|---|
| customers | customer_id (PK) | 0 |
| merchants | merchant_id (PK) | 0 |
| devices | device_id (PK) | 0 |
| transactions | transaction_id (PK) | 0 |
| payment_outcomes | transaction_id (PK) | 0 |
| labels | transaction_id (PK) | 0 |
| customers | all columns except customer_id | 3 |
| merchants | all columns except merchant_id | 0 |
| merchants | synthetic_name | 0 |
| transactions | all columns except transaction_id | 0 |
| transactions | customer_id + merchant_id + amount_paise + transaction_time | 0 |
| transactions | customer_id + transaction_time | 0 |
| payment_outcomes | all columns except transaction_id | 1 |

Rows whose content (everything except the id) equals another row's:

| Table | Id | Content | Own transactions |
|---|---|---|---|
| customers | C_6addba27873b634f | created 2022-07-31, age 49, Kochi / south | 67 |
| customers | C_96d400a9352c2b0f | created 2022-07-31, age 49, Kochi / south | 66 |
| customers | C_455ee5bf4a70cda1 | created 2023-06-25, age 25, Jamshedpur / east | 46 |
| customers | C_fbc7d8229cf6e5dc | created 2023-06-25, age 25, Jamshedpur / east | 40 |
| customers | C_7f6b1b9b71567004 | created 2023-06-29, age 53, Delhi / north | 82 |
| customers | C_c25537057bf5eab7 | created 2023-06-29, age 53, Delhi / north | 84 |
| payment_outcomes | TX_0000001635 | FAILED SIMULATED_AUTH_FAILURE at 2024-10-15 20:35:37.132+00; txn by C_31ba4431ee1ada4e at 2024-10-15 20:35:35.741+00, 89679 paise |  |
| payment_outcomes | TX_0000001636 | FAILED SIMULATED_AUTH_FAILURE at 2024-10-15 20:35:37.132+00; txn by C_31ba4431ee1ada4e at 2024-10-15 20:35:35.771+00, 51071 paise |  |

Neither group is a duplicate load:

- **Customers:** customers have only 5 descriptive columns, and `created_at` is a date (IST midnight). Pairs that share date, age and city are expected among 2,500 customers. Each id in a pair has its own, different transaction history, so these are distinct people.
- **Payment outcome:** these are two different transactions by the same customer, 30 ms apart and for different amounts, and both were declined in the same instant. This is a burst of attempts, which is exactly what R07 velocity looks for. It is not a copy.

Referential integrity and 1:1 coverage:

| Check | Rows |
|---|---|
| transactions without payment_outcome | 0 |
| transactions without label | 0 |
| transactions without features row | 0 |
| transactions with unknown customer | 0 |
| transactions with unknown merchant | 0 |
| transactions with unknown device | 0 |
| customers with no transactions | 20 |
| merchants with no transactions | 0 |
| devices with no transactions | 4,715 |

Customers and devices with no transactions are reference rows that were never used (for example registered spare devices). They are harmless, but they should not be counted when computing per-device or per-customer rates.

## 4. Wrong types and invalid values

_Script `04_dq_wrong_types.sql`_

**Declared types:** 44 of 44 columns have the type the data dictionary prescribes (all match).

Because Postgres enforces declared types, a wrong type can only hide inside text or JSON values, or in values of the right type that are semantically wrong. The checks below cover both.

| Table | Check | Violations |
|---|---|---|
| all | is_synthetic = false | 0 |
| customers | customer_age outside 18..120 | 0 |
| customers | customer_id not like C_<16 hex> | 0 |
| devices | device_id not like D_<16 hex> | 0 |
| labels | fraud_label not 0/1 | 0 |
| labels | label_available_at <> transaction_time + 60 days | 0 |
| merchants | merchant_id not like M_<16 hex> | 0 |
| merchants | merchant_location.lat/lon not a number | 0 |
| payment_outcomes | failure_code present on SUCCESS or missing on FAILED | 0 |
| payment_outcomes | outcome_time <= transaction_time | 0 |
| payment_outcomes | status not in (SUCCESS, FAILED) | 0 |
| transactions | account_age <> full days since customers.created_at | 0 |
| transactions | amount_paise <= 0 | 0 |
| transactions | amount_paise <> transaction_amount * 100 | 0 |
| transactions | average_transaction_value <= 0 | 0 |
| transactions | customer lat/lon outside India bounding box | 0 |
| transactions | customer_age differs from customers table | 0 |
| transactions | customer_location is not a JSON object | 0 |
| transactions | customer_location.city not a string | 0 |
| transactions | customer_location.lat/lon not a number | 0 |
| transactions | merchant lat/lon outside India bounding box | 0 |
| transactions | merchant_category differs from merchants table | 0 |
| transactions | merchant_location differs from merchants table | 0 |
| transactions | merchant_location.lat/lon not a number | 0 |
| transactions | negative counters (account_age, previous_transactions, failed_transactions) | 0 |
| transactions | payment_channel not in (UPI, card, wallet, net_banking) | 0 |
| transactions | transaction before customer created_at | 0 |
| transactions | transaction_id pattern differs from the majority | 0 |
| transactions | transaction_time after dataset snapshot (2026-05-01) | 0 |

Observed value domains (no unexpected spellings or casing):

| Column | Value | Rows |
|---|---|---|
| customers.region | south | 650 |
| customers.region | east | 596 |
| customers.region | north | 493 |
| customers.region | west | 461 |
| customers.region | northeast | 160 |
| customers.region | central | 140 |
| devices.device_kind | mobile | 7,590 |
| devices.device_kind | browser | 2,530 |
| labels.label_source | mature_no_fraud | 109,340 |
| labels.label_source | investigator_verdict | 330 |
| labels.label_source | confirmed_chargeback | 330 |
| merchant_category | grocery | 20,358 |
| merchant_category | quick_commerce | 16,606 |
| merchant_category | food | 14,902 |
| merchant_category | electronics | 14,206 |
| merchant_category | gaming | 10,692 |
| merchant_category | gift_cards | 7,704 |
| merchant_category | healthcare | 7,219 |
| merchant_category | travel | 6,398 |
| merchant_category | education | 6,288 |
| merchant_category | other | 5,627 |
| payment_channel | UPI | 63,927 |
| payment_channel | card | 34,041 |
| payment_channel | wallet | 7,418 |
| payment_channel | net_banking | 4,614 |
| payment_outcomes.failure_code | (null) | 97,985 |
| payment_outcomes.failure_code | SIMULATED_AUTH_FAILURE | 12,015 |
| payment_outcomes.status | SUCCESS | 97,985 |
| payment_outcomes.status | FAILED | 12,015 |

## 5. Outliers in amount

_Script `05_dq_amount_outliers.sql`. Amounts come from `amount_paise`; INR = paise / 100._

| Split (blank = all) | Rows | Min ₹ | P1 ₹ | P25 ₹ | Median ₹ | Mean ₹ | P75 ₹ | P99 ₹ | Max ₹ |
|---|---|---|---|---|---|---|---|---|---|
| warmup | 10,000 | 15.94 | 92.5808 | 576.405 | 1,230.435 | 5,305.72 | 2,732.53 | 26,267.4767 | 7,995,933.05 |
|  | 110,000 | 8.2 | 89.0998 | 582.55 | 1,250.34 | 4,478.12 | 2,717.585 | 25,242.8972 | 7,995,933.05 |
| train | 72,050 | 8.2 | 90.2245 | 583.555 | 1,254.57 | 4,326.23 | 2,717.375 | 25,375.9976 | 7,694,232.83 |
| validation | 14,061 | 18.89 | 81.368 | 582.38 | 1,238.17 | 4,555.75 | 2,717.14 | 24,420.102 | 6,757,902.12 |
| holdout | 13,889 | 8.43 | 88.5456 | 580.32 | 1,250.56 | 4,591.58 | 2,708.07 | 24,450.6416 | 7,632,118.12 |

| Split (blank = all) | Rows | Raw > 1.5 IQR | Raw > 3 IQR | Log > 1.5 IQR | Log < 1.5 IQR | Log > 3 IQR | Raw fence ₹ | Log fence ₹ | Log extreme fence ₹ |
|---|---|---|---|---|---|---|---|---|---|
| warmup | 10,000 | 972 | 513 | 95 | 35 | 4 | 5,920.14 | 27,381.55 | 275,888.07 |
|  | 110,000 | 10,344 | 5,490 | 985 | 411 | 55 | 5,920.14 | 27,381.55 | 275,888.07 |
| train | 72,050 | 6,784 | 3,596 | 652 | 261 | 36 | 5,920.14 | 27,381.55 | 275,888.07 |
| validation | 14,061 | 1,340 | 703 | 117 | 61 | 9 | 5,920.14 | 27,381.55 | 275,888.07 |
| holdout | 13,889 | 1,248 | 678 | 121 | 54 | 6 | 5,920.14 | 27,381.55 | 275,888.07 |

The mean is about 3.5 times the median, so the raw Tukey fence (₹5,920.14) flags 10,344 rows (9.40%). That count reflects the skewed shape of spending, not errors. On log10(amount), which is the right scale for money, 985 rows (0.90%) are high outliers and 55 are extreme (above ₹275,888.07). Outlier rates are similar in every split, so there is no drift.

Robust z-score (|log amount − median| / 1.4826·MAD > 3.5) within each merchant category:

| Category | Rows | Median ₹ | Outliers | Outlier % | Max ₹ |
|---|---|---|---|---|---|
| gaming | 10,692 | 1,374.47 | 40 | 0.374 | 3,490,740.82 |
| gift_cards | 7,704 | 1,368.19 | 28 | 0.363 | 3,066,750.84 |
| electronics | 14,206 | 1,295.16 | 48 | 0.338 | 7,694,232.83 |
| quick_commerce | 16,606 | 1,213.19 | 21 | 0.126 | 7,995,933.05 |
| other | 5,627 | 1,196 | 7 | 0.124 | 7,516,509.14 |
| grocery | 20,358 | 1,212.99 | 22 | 0.108 | 7,632,118.12 |
| healthcare | 7,219 | 1,248.78 | 6 | 0.083 | 1,991,633.28 |
| travel | 6,398 | 1,274.3 | 4 | 0.063 | 7,248,375.68 |
| food | 14,902 | 1,213.05 | 9 | 0.06 | 6,955,134.75 |
| education | 6,288 | 1,208.1 | 3 | 0.048 | 85,751.32 |

Fraud rate by amount group:

| Amount group | Rows | Fraud | Fraud % |
|---|---|---|---|
| high outlier (log IQR) | 985 | 159 | 16.142 |
| low outlier (log IQR) | 411 | 0 | 0 |
| normal | 108,604 | 501 | 0.461 |

The 15 largest amounts:

| Transaction | Split | Customer | Category | Channel | Amount ₹ | Customer avg ₹ | Ratio | Fraud |
|---|---|---|---|---|---|---|---|---|
| TX_0000002112 | warmup | C_9b3aee21759c3763 | quick_commerce | UPI | 7,995,933.05 | 1,471.32 | 5,434.5303 | 0 |
| TX_0000033861 | train | C_37048b52cb878832 | electronics | UPI | 7,694,232.83 | 2,420.43 | 3,178.8748 | 0 |
| TX_0000106202 | holdout | C_44aef9e23e0196b6 | grocery | net_banking | 7,632,118.12 | 3,931.65 | 1,941.1998 | 0 |
| TX_0000065887 | train | C_f681a029884b7fdb | grocery | UPI | 7,565,602.83 | 1,137.23 | 6,652.6845 | 0 |
| TX_0000100505 | holdout | C_2874214784bbe319 | other | UPI | 7,516,509.14 | 3,609.4 | 2,082.4828 | 0 |
| TX_0000059977 | train | C_2dad835a9d2976a1 | grocery | UPI | 7,358,224.2 | 1,901.58 | 3,869.538 | 0 |
| TX_0000006634 | warmup | C_ac991b41d253a515 | travel | UPI | 7,248,375.68 | 239.92 | 30,211.6359 | 0 |
| TX_0000013512 | train | C_ed14670b17bd7863 | food | card | 6,955,134.75 | 7,835.61 | 887.6316 | 0 |
| TX_0000084768 | validation | C_c520b909482fc445 | quick_commerce | UPI | 6,757,902.12 | 399.9 | 16,898.98 | 0 |
| TX_0000090926 | validation | C_a87fd72a2f42a59a | travel | card | 6,659,250.37 | 2,561.02 | 2,600.2344 | 0 |
| TX_0000041002 | train | C_ef9ffbb4eee94ac8 | quick_commerce | UPI | 6,119,968.31 | 1,882.05 | 3,251.7623 | 0 |
| TX_0000101653 | holdout | C_b484e7f4e0bdc6f0 | quick_commerce | card | 6,104,249.37 | 3,382.58 | 1,804.6145 | 0 |
| TX_0000003885 | warmup | C_ec0917ec69fef0e2 | electronics | card | 5,780,139.65 | 1,584.48 | 3,647.9726 | 0 |
| TX_0000053667 | train | C_486e0f014fc354f2 | grocery | UPI | 5,555,508.39 | 1,163.15 | 4,776.2431 | 0 |
| TX_0000076102 | train | C_f9298defacce338a | quick_commerce | UPI | 5,365,080.87 | 880 | 6,096.6915 | 0 |

**Interpretation and recommendation**

- High-amount outliers are about 35 times more likely to be fraud. They are signal, not noise, so do **not** delete or cap them in the labelled data.
- The very largest amounts (₹50–80 lakh, thousands of times the customer's average) are all labelled non-fraud. These look like injected extreme values that test robustness. They are valid rows (`amount_paise = transaction_amount × 100`, positive), but they dominate any mean-based statistic. Use log(amount) or the ratio feature in models, and the median, not the mean, in summaries.
- High-risk categories (gaming, gift cards, electronics) have the most within-category outliers, which is consistent with R08.

## 6. Feature recomputation (point-in-time, no future leakage)

_Script `10_features_recompute.sql` writes `sentinel_dq.recomputed_features`. It uses a separate schema, so nothing in `public` is changed._

Leakage rules applied to every transaction at time **T**:

1. History is the **same customer's transactions with `transaction_time < T`**, strictly earlier. The current transaction is never part of its own history.
2. A payment outcome counts only once it has been received: `outcome_time < T`.
3. Nothing is read from `labels` or from the `public.features` table being checked.

| Feature | Definition used |
|---|---|
| `amount_to_average_ratio` (`amount_to_avg_ratio`) | amount_paise / mean(amount_paise) of the customer's transactions in [T−90 days, T), rounded to 4 dp. Declined attempts count (they are authorisations). NULL when there is no 90-day history. |
| `is_new_device` | device_id not used by this customer in [T−90 days, T). NULL when the device is unknown. |
| `customer_merchant_distance_km` | haversine on customer and merchant lat/lon, Earth radius 6,371 km, rounded to 2 dp. NULL when the customer location is unknown. |
| `is_night` | hour in **IST** (Asia/Kolkata) is in 00:00–04:59 (00:00 inclusive, 05:00 exclusive). |
| `transaction_count_last_1_hour` (`txn_count_last_1h`) | count of the customer's transactions in [T−1 h, T), declines included. |
| `transaction_amount_last_24_hours` (`txn_amount_last_24h_paise`) | sum of amount_paise of the customer's transactions in [T−24 h, T), declines included. |
| supporting: `is_new_city`, `failed_last_24h`, `account_age_days` | city not seen in [T−90 d, T); FAILED outcomes received in [T−24 h, T); complete days since `customers.created_at`. These feed R02, R04 and R06. |

All windows are computed in one pass: a self-join of each transaction to the same customer's earlier transactions of the last 90 days, aggregated with `FILTER (WHERE …)` per window.

| Split (blank = all) | Rows | Null ratio (no 90d history) | Null new-device (no device) | Null distance (no location) | Avg ratio | New device % | Avg distance km | Night % | Avg txns last 1h | Avg ₹ last 24h |
|---|---|---|---|---|---|---|---|---|---|---|
|  | 110,000 | 2,829 | 1,138 | 3,257 | 2.772 | 6.71 | 1,046.3 | 14.03 | 1.159 | 5,177.27 |
| warmup | 10,000 | 2,001 | 185 | 273 | 7.015 | 24.08 | 1,027 | 14.82 | 1.201 | 8,856.37 |
| train | 72,050 | 624 | 858 | 2,153 | 2.306 | 5.05 | 1,049.3 | 13.71 | 1.16 | 5,363.35 |
| validation | 14,061 | 105 | 46 | 421 | 3.707 | 4.93 | 1,034.4 | 14.77 | 1.126 | 3,058.48 |
| holdout | 13,889 | 99 | 49 | 410 | 1.776 | 4.76 | 1,056.4 | 14.43 | 1.156 | 3,708.04 |

The warmup split shows a high new-device rate and a high average ratio. This is the cold-start effect: histories are short at the start of the data, so most devices are "new" and averages are taken over very few transactions.

## 7. Reason codes

_Script `11_reason_codes.sql` (thresholds are in table `sentinel_dq.reason_code_thresholds`; change them there and re-run). Script `14_threshold_evidence.sql` checks each threshold against the provided table._

| Code | Fires when | Threshold |
|---|---|---|
| R01_NEW_DEVICE | `is_new_device` = true | – |
| R02_GEO_MISMATCH | `is_new_city` = true **or** distance > threshold | 500 km |
| R03_ODD_HOUR | `is_night` = true | IST 00:00–04:59 |
| R04_FAILED_ATTEMPTS | failed outcomes received in the previous 24 h ≥ threshold | 3 |
| R05_AMOUNT_SPIKE | `amount_to_avg_ratio` ≥ threshold | 5× |
| R06_NEW_ACCOUNT | account age < threshold | 30 days |
| R07_VELOCITY | `txn_count_last_1h` ≥ threshold | 4 in 1 h |
| R08_HIGH_RISK_MCC | merchant category in the high-risk list | electronics, gaming, gift_cards |

A null (unknown) feature never fires a code.

**Threshold evidence from `public.features`.** For each code, compare the largest value on rows that do not have the code with the smallest value on rows that do. A clean gap means no row contradicts the threshold.

| Code | Feature | Max without code | Min with code | Threshold used |
|---|---|---|---|---|
| R02_GEO_MISMATCH | customer_merchant_distance_km (is_new_city = false) | 470.17 | 500.88 | > 500 |
| R04_FAILED_ATTEMPTS | failed outcomes in previous 24h (transactions.failed_transactions) | 2 | 3 | >= 3 |
| R05_AMOUNT_SPIKE | amount_to_avg_ratio | 4.9982 | 5.0043 | >= 5 |
| R06_NEW_ACCOUNT | account_age (days) - note: reversed, code fires BELOW | 29 | 30 | < 30 |
| R07_VELOCITY | txn_count_last_1h | 3 | 4 | >= 4 |

| Code | Flag true but no code | Code but flag not true |
|---|---|---|
| R01_NEW_DEVICE | 0 | 0 |
| R03_ODD_HOUR | 0 | 0 |

| Category | Rows | R08 fired % | Fraud % |
|---|---|---|---|
| gift_cards | 7,704 | 100 | 2.648 |
| gaming | 10,692 | 100 | 2.319 |
| electronics | 14,206 | 100 | 1.457 |
| quick_commerce | 16,606 | 0 | 0.006 |
| other | 5,627 | 0 | 0 |
| education | 6,288 | 0 | 0 |
| travel | 6,398 | 0 | 0 |
| food | 14,902 | 0 | 0 |
| grocery | 20,358 | 0 | 0 |
| healthcare | 7,219 | 0 | 0 |

Every boundary is clean, and only the three high-risk categories carry R08. They are also the only categories with a material fraud rate.

| Code | Fired | Fired % | Fired % train | Fired % holdout |
|---|---|---|---|---|
| R01_NEW_DEVICE | 7,305 | 6.64 | 4.99 | 4.74 |
| R02_GEO_MISMATCH | 90,293 | 82.08 | 81.91 | 82.16 |
| R03_ODD_HOUR | 15,438 | 14.03 | 13.71 | 14.43 |
| R04_FAILED_ATTEMPTS | 9,877 | 8.98 | 8.87 | 9.01 |
| R05_AMOUNT_SPIKE | 3,068 | 2.79 | 2.7 | 2.78 |
| R06_NEW_ACCOUNT | 1,109 | 1.01 | 1.2 | 0.78 |
| R07_VELOCITY | 14,509 | 13.19 | 13.18 | 13.26 |
| R08_HIGH_RISK_MCC | 32,602 | 29.64 | 29.55 | 29.27 |

Note: R02 fires on about 82% of transactions. Customers usually buy from merchants in another city, so the new-city / 500 km rule is weak as a stand-alone signal. Weight it accordingly.

## 8. Comparison with the provided features table: match rate per feature

_Script `12_feature_compare.sql`. A value matches when it is equal or both are NULL. Floats are compared within 1e-9; both sides are already rounded, so this is effectively an exact comparison._

**Requested features**

| Feature | Rows | Matches | Mismatches | Match % | Warmup % | Train % | Validation % | Holdout % | Nulls (mine) | Nulls (ref) |
|---|---|---|---|---|---|---|---|---|---|---|
| amount_to_avg_ratio | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 2,829 | 2,829 |
| customer_merchant_distance_km | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 3,257 | 3,257 |
| is_new_device | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 1,138 | 1,138 |
| is_night | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| txn_amount_last_24h_paise | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| txn_count_last_1h | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |

**Supporting features** (needed for R02, R04 and R06)

| Feature | Rows | Matches | Mismatches | Match % | Warmup % | Train % | Validation % | Holdout % | Nulls (mine) | Nulls (ref) |
|---|---|---|---|---|---|---|---|---|---|---|
| has_recent_failures | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| hour_of_day | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| is_new_account | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 0 | 0 |
| is_new_city | 110,000 | 110,000 | 0 | 100 | 100 | 100 | 100 | 100 | 3,257 | 3,257 |

**Reason codes**: agreement per code and full-list match per split

| Code | Fired (mine) | Fired (ref) | Only mine | Only ref | Agree % |
|---|---|---|---|---|---|
| R01_NEW_DEVICE | 7,305 | 7,305 | 0 | 0 | 100 |
| R02_GEO_MISMATCH | 90,293 | 90,293 | 0 | 0 | 100 |
| R03_ODD_HOUR | 15,438 | 15,438 | 0 | 0 | 100 |
| R04_FAILED_ATTEMPTS | 9,877 | 9,877 | 0 | 0 | 100 |
| R05_AMOUNT_SPIKE | 3,068 | 3,068 | 0 | 0 | 100 |
| R06_NEW_ACCOUNT | 1,109 | 1,109 | 0 | 0 | 100 |
| R07_VELOCITY | 14,509 | 14,509 | 0 | 0 | 100 |
| R08_HIGH_RISK_MCC | 32,602 | 32,602 | 0 | 0 | 100 |

| Split | Rows | Exact set matches | Exact set match % | Same order |
|---|---|---|---|---|
| warmup | 10,000 | 10,000 | 100 | 10,000 |
| train | 72,050 | 72,050 | 100 | 72,050 |
| validation | 14,061 | 14,061 | 100 | 14,061 |
| holdout | 13,889 | 13,889 | 100 | 13,889 |
| ALL | 110,000 | 110,000 | 100 | 110,000 |

_No rows._

## 9. Mismatches explained

_Script `13_mismatch_diagnosis.sql` puts every mismatching (transaction, feature) pair into a cause bucket. Script `15_leakage_variants.sql` shows what each common mistake does to the match rate._

**There are no mismatches.** All 1,100,000 feature comparisons and all 110,000 reason-code lists agree. Every null is null on both sides, which confirms that the provided table uses the same definitions as section 6. In particular:

- the current transaction is excluded from its own history;
- declined attempts count in the velocity and amount windows;
- the device lookback is 90 days, not "ever";
- the night hour is taken in IST;
- the Earth radius is 6,371 km;
- rounding is to 4 dp for the ratio and 2 dp for the distance.

### What would cause mismatches (and therefore what the reference is *not* doing)

Each row recomputes one feature with a common mistake and measures its match rate against `public.features`:

| Feature | Wrong definition | Match % |
|---|---|---|
| amount_to_avg_ratio | B. current transaction included in its own 90d average (LEAKAGE) | 0.067 |
| amount_to_avg_ratio | C. declined attempts dropped from history | 63.065 |
| customer_merchant_distance_km | B. Earth radius 6378.137 km (equatorial) instead of 6371 | 8.905 |
| is_new_device | B. device seen at ANY time before (no 90-day window) | 99.123 |
| is_night | B. hour taken in UTC instead of IST | 63.442 |
| is_night | C. night = 22:00-06:00 IST | 90.305 |
| txn_amount_last_24h_paise | B. current amount added (LEAKAGE) | 0 |
| txn_amount_last_24h_paise | C. declined attempts not summed | 84.625 |
| txn_count_last_1h | B. current transaction counted (LEAKAGE) | 0 |
| txn_count_last_1h | C. declined attempts not counted | 84.897 |

How to read this:

- **Leakage** (counting the current transaction in its own window) breaks almost every row: 0.067% for the ratio and 0.0% for the 1-hour count. With 100% achieved above, this proves both the reference and these scripts are leakage-free.
- **Dropping declined attempts** gives 63.065% for the ratio and 84.897% for the 1-hour count. The CRD counts authorisation *attempts*, and declines are themselves a fraud signal (card testing).
- **Device seen "ever"** instead of within 90 days gives 99.123%. The 0.877% difference is customers who return to a device after a gap of more than 90 days.
- **UTC instead of IST** for the night flag gives 63.442%, because IST is UTC+5:30. A 22:00–06:00 night window gives 90.305%.
- **Equatorial Earth radius** (6,378.137 km) gives 8.905% after rounding to 2 dp, even though the error is only 0.11%.

### The precomputed columns in `transactions`

| Comparison | Rows | Matches | Match % |
|---|---|---|---|
| transactions.failed_transactions = failed outcomes in previous 24h | 110,000 | 110,000 | 100 |
| transactions.account_age = complete days since created_at | 110,000 | 110,000 | 100 |
| round(amount / average_transaction_value, 4) = amount_to_avg_ratio | 110,000 | 106,840 | 97.1273 |
| same, within 0.001 (shows the gap is rounding of the 2-dp average) | 110,000 | 109,977 | 99.9791 |

`failed_transactions` and `account_age` in the raw table agree exactly with the point-in-time values. `average_transaction_value`, however, is stored rounded to 2 dp (rupees and paise). A ratio built from it matches only 97.1273% of the time at 4 dp, and 99.9791% within 0.001. The 23 rows still off by more than 0.001 are shown below. In each one the gap stays within the bound that rounding the average to the nearest paisa can create (0.005 ₹ × ratio / average): the ratio is huge or the average is tiny, which magnifies the rounding.

| Transaction | Split | Amount ₹ | Stored avg ₹ | Point-in-time ratio | Ratio from 2-dp avg | Gap | Max gap from rounding |
|---|---|---|---|---|---|---|---|
| TX_0000065887 | train | 7,565,602.83 | 1,137.23 | 6,652.6845 | 6,652.6585 | 0.026 | 0.0292 |
| TX_0000037688 | train | 3,262,913.95 | 616.65 | 5,291.3358 | 5,291.3548 | 0.019 | 0.0429 |
| TX_0000089611 | validation | 2,893,830.99 | 714.93 | 4,047.6935 | 4,047.7123 | 0.0188 | 0.0283 |
| TX_0000053667 | train | 5,555,508.39 | 1,163.15 | 4,776.2431 | 4,776.2614 | 0.0183 | 0.0205 |
| TX_0000016148 | train | 1,991,633.28 | 542.94 | 3,668.2232 | 3,668.2383 | 0.0151 | 0.0338 |
| TX_0000076102 | train | 5,365,080.87 | 880 | 6,096.6915 | 6,096.6828 | 0.0087 | 0.0346 |
| TX_0000022864 | train | 1,918,627.28 | 707.19 | 2,713.0376 | 2,713.0294 | 0.0082 | 0.0192 |
| TX_0000020571 | train | 1,946,853.06 | 1,232.76 | 1,579.2701 | 1,579.2637 | 0.0064 | 0.0064 |
| TX_0000059977 | train | 7,358,224.2 | 1,901.58 | 3,869.538 | 3,869.5318 | 0.0062 | 0.0102 |
| TX_0000041002 | train | 6,119,968.31 | 1,882.05 | 3,251.7623 | 3,251.7565 | 0.0058 | 0.0086 |
| TX_0000033861 | train | 7,694,232.83 | 2,420.43 | 3,178.8748 | 3,178.8702 | 0.0046 | 0.0066 |
| TX_0000081104 | train | 4,603,232.5 | 1,983.57 | 2,320.685 | 2,320.6806 | 0.0044 | 0.0058 |
| TX_0000087228 | validation | 1,452,732.74 | 1,186.47 | 1,224.4116 | 1,224.4159 | 0.0043 | 0.0052 |
| TX_0000014782 | train | 4,205,767.17 | 1,868.29 | 2,251.1279 | 2,251.1319 | 0.004 | 0.006 |
| TX_0000050084 | train | 3,545,718.63 | 1,384.46 | 2,561.0873 | 2,561.0842 | 0.0031 | 0.0092 |
| TX_0000032420 | train | 14,511.06 | 154.79 | 93.7492 | 93.7468 | 0.0024 | 0.003 |
| TX_0000054574 | train | 3,766,367.6 | 2,555.07 | 1,474.0742 | 1,474.0761 | 0.0019 | 0.0029 |
| TX_0000063739 | train | 7,721.94 | 148.8 | 51.8932 | 51.8948 | 0.0016 | 0.0017 |
| TX_0000101111 | holdout | 4,320,966.04 | 3,590.66 | 1,203.3921 | 1,203.3905 | 0.0016 | 0.0017 |
| TX_0000069924 | train | 2,253,232.84 | 1,204.27 | 1,871.035 | 1,871.0363 | 0.0013 | 0.0078 |
| TX_0000000449 | warmup | 38,804.13 | 371.17 | 104.5466 | 104.5454 | 0.0012 | 0.0014 |
| TX_0000100505 | holdout | 7,516,509.14 | 3,609.4 | 2,082.4828 | 2,082.4816 | 0.0012 | 0.0029 |
| TX_0000076276 | train | 2,354,396.08 | 2,353.35 | 1,000.4434 | 1,000.4445 | 0.0011 | 0.0021 |

**Recommendation:** compute the ratio from `amount_paise` and the exact 90-day mean, as script 10 does. Do not use `transactions.average_transaction_value`, which is a rounded display value.

## Appendix: how to reproduce

```powershell
cd supabase_db_kit\sql_scripts_report
..\venv\Scripts\python run_report.py
```

Each `.sql` file also runs on its own in the Supabase SQL Editor (run 10 → 11 → 12 → 13 in that order; 01–05, 14 and 15 are independent). `99_cleanup.sql` drops the `sentinel_dq` working schema.

| Script | Run time (s) |
|---|---|
| 01_dq_row_counts_per_split.sql | 4.5 |
| 02_dq_nulls_per_column.sql | 15.6 |
| 03_dq_duplicates.sql | 9.3 |
| 04_dq_wrong_types.sql | 3 |
| 05_dq_amount_outliers.sql | 19.7 |
| 10_features_recompute.sql | 7 |
| 11_reason_codes.sql | 2.4 |
| 12_feature_compare.sql | 15.8 |
| 13_mismatch_diagnosis.sql | 8 |
| 14_threshold_evidence.sql | 1.1 |
| 15_leakage_variants.sql | 8.7 |
