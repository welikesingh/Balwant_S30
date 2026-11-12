-- =============================================================================
-- 14  Evidence for the reason-code thresholds
-- For each code, look at public.features alone: the largest feature value on rows
-- WITHOUT the code and the smallest value on rows WITH the code. A clean gap
-- between the two confirms the threshold used in 11_reason_codes.sql.
-- (R02 is checked only on rows with is_new_city = false, because a new city fires
--  R02 regardless of distance.)
-- =============================================================================

-- @result: threshold_evidence
SELECT 'R02_GEO_MISMATCH' AS code, 'customer_merchant_distance_km (is_new_city = false)' AS feature,
       max(f.customer_merchant_distance_km) FILTER (WHERE NOT f.reason_codes ? 'R02_GEO_MISMATCH')::numeric AS max_without_code,
       min(f.customer_merchant_distance_km) FILTER (WHERE f.reason_codes ? 'R02_GEO_MISMATCH')::numeric     AS min_with_code,
       '> 500' AS threshold_used
FROM public.features f WHERE f.is_new_city = false
UNION ALL
SELECT 'R04_FAILED_ATTEMPTS', 'failed outcomes in previous 24h (transactions.failed_transactions)',
       max(t.failed_transactions) FILTER (WHERE NOT f.reason_codes ? 'R04_FAILED_ATTEMPTS'),
       min(t.failed_transactions) FILTER (WHERE f.reason_codes ? 'R04_FAILED_ATTEMPTS'), '>= 3'
FROM public.features f JOIN public.transactions t USING (transaction_id)
UNION ALL
SELECT 'R05_AMOUNT_SPIKE', 'amount_to_avg_ratio',
       max(f.amount_to_avg_ratio) FILTER (WHERE NOT f.reason_codes ? 'R05_AMOUNT_SPIKE')::numeric,
       min(f.amount_to_avg_ratio) FILTER (WHERE f.reason_codes ? 'R05_AMOUNT_SPIKE')::numeric, '>= 5'
FROM public.features f
UNION ALL
SELECT 'R06_NEW_ACCOUNT', 'account_age (days) - note: reversed, code fires BELOW',
       max(t.account_age) FILTER (WHERE f.reason_codes ? 'R06_NEW_ACCOUNT'),
       min(t.account_age) FILTER (WHERE NOT f.reason_codes ? 'R06_NEW_ACCOUNT'), '< 30'
FROM public.features f JOIN public.transactions t USING (transaction_id)
UNION ALL
SELECT 'R07_VELOCITY', 'txn_count_last_1h',
       max(f.txn_count_last_1h) FILTER (WHERE NOT f.reason_codes ? 'R07_VELOCITY'),
       min(f.txn_count_last_1h) FILTER (WHERE f.reason_codes ? 'R07_VELOCITY'), '>= 4'
FROM public.features f;

-- @result: boolean_code_evidence
-- R01 and R03 are pure flag codes: the code must fire exactly when the flag is true.
SELECT 'R01_NEW_DEVICE' AS code,
       count(*) FILTER (WHERE f.is_new_device IS TRUE  AND NOT f.reason_codes ? 'R01_NEW_DEVICE') AS flag_true_no_code,
       count(*) FILTER (WHERE f.is_new_device IS NOT TRUE AND f.reason_codes ? 'R01_NEW_DEVICE')  AS code_without_flag
FROM public.features f
UNION ALL
SELECT 'R03_ODD_HOUR',
       count(*) FILTER (WHERE f.is_night AND NOT f.reason_codes ? 'R03_ODD_HOUR'),
       count(*) FILTER (WHERE NOT f.is_night AND f.reason_codes ? 'R03_ODD_HOUR')
FROM public.features f;

-- @result: mcc_code_evidence
-- R08: the share of rows with the code, per merchant category (should be 100% or 0%).
SELECT t.merchant_category,
       count(*) AS rows,
       round(100.0 * avg((f.reason_codes ? 'R08_HIGH_RISK_MCC')::int), 2) AS r08_fired_pct,
       round(100.0 * avg(l.fraud_label), 3)                               AS fraud_pct
FROM public.features f
JOIN public.transactions t USING (transaction_id)
JOIN public.labels l USING (transaction_id)
GROUP BY t.merchant_category
ORDER BY r08_fired_pct DESC, fraud_pct DESC;
