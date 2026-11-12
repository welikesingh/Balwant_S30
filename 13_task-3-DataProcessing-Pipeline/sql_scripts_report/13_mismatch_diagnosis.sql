-- =============================================================================
-- 13  Explain every mismatch
-- Each mismatching (transaction, feature) pair is put into a cause bucket by
-- testing the usual suspects against the raw data. A bucket "unexplained" would
-- mean a real disagreement in definition that needs a human look.
-- Needs 12_feature_compare.sql.
-- =============================================================================

-- @result: mismatch_causes
WITH mm AS (
  SELECT c.*, t.customer_location, t.device_id, t.transaction_time
  FROM sentinel_dq.feature_compare c
  JOIN public.transactions t USING (transaction_id)
  WHERE NOT c.is_match
)
SELECT feature,
       CASE
         WHEN mine IS NULL AND ref IS NOT NULL THEN 'null only in mine (e.g. missing location/device or no 90d history)'
         WHEN ref IS NULL AND mine IS NOT NULL THEN 'null only in reference'
         WHEN feature IN ('amount_to_avg_ratio') AND abs(mine::float8 - ref::float8) <= 0.00011
              THEN 'last-digit rounding (4 dp half-up vs float half-even)'
         WHEN feature IN ('customer_merchant_distance_km') AND abs(mine::float8 - ref::float8) <= 0.011
              THEN 'last-digit rounding (2 dp) / float precision'
         WHEN feature IN ('hour_of_day','is_night') THEN 'time zone / night window'
         ELSE 'unexplained - definition differs'
       END AS cause,
       count(*) AS rows,
       min(transaction_id) AS example_transaction_id
FROM mm
GROUP BY 1, 2
ORDER BY 1, 3 DESC;

-- @result: mismatch_examples
-- Up to 10 examples per feature, with both values side by side.
SELECT feature, transaction_id, split, mine, ref,
       CASE WHEN feature IN ('amount_to_avg_ratio','customer_merchant_distance_km')
                 AND mine IS NOT NULL AND ref IS NOT NULL
            THEN round((mine::float8 - ref::float8)::numeric, 6) END AS difference
FROM (SELECT c.*, row_number() OVER (PARTITION BY feature ORDER BY transaction_id) rn
        FROM sentinel_dq.feature_compare c WHERE NOT is_match) x
WHERE rn <= 10
ORDER BY feature, transaction_id;

-- @result: reason_code_mismatch_examples
SELECT r.transaction_id, r.split, r.reason_codes AS mine, f.reason_codes AS ref
FROM sentinel_dq.recomputed_reason_codes r
JOIN public.features f USING (transaction_id)
WHERE NOT (r.reason_codes @> f.reason_codes AND f.reason_codes @> r.reason_codes)
ORDER BY r.transaction_id
LIMIT 20;

-- @result: raw_column_vs_recomputed
-- The transactions table also carries pre-computed columns. Comparing them with the
-- point-in-time values shows which of them are safe to use as features.
SELECT 'transactions.failed_transactions = failed outcomes in previous 24h' AS comparison,
       count(*) AS rows,
       count(*) FILTER (WHERE t.failed_transactions = m.failed_last_24h) AS matches,
       round(100.0 * avg((t.failed_transactions = m.failed_last_24h)::int), 4) AS match_pct
FROM public.transactions t JOIN sentinel_dq.recomputed_features m USING (transaction_id)
UNION ALL
SELECT 'transactions.account_age = complete days since created_at', count(*),
       count(*) FILTER (WHERE t.account_age = m.account_age_days),
       round(100.0 * avg((t.account_age = m.account_age_days)::int), 4)
FROM public.transactions t JOIN sentinel_dq.recomputed_features m USING (transaction_id)
UNION ALL
SELECT 'round(amount / average_transaction_value, 4) = amount_to_avg_ratio', count(*),
       count(*) FILTER (WHERE round(t.transaction_amount / t.average_transaction_value, 4)::float8 IS NOT DISTINCT FROM m.amount_to_avg_ratio),
       round(100.0 * avg((round(t.transaction_amount / t.average_transaction_value, 4)::float8 IS NOT DISTINCT FROM m.amount_to_avg_ratio)::int), 4)
FROM public.transactions t JOIN sentinel_dq.recomputed_features m USING (transaction_id)
UNION ALL
SELECT 'same, within 0.001 (shows the gap is rounding of the 2-dp average)', count(*),
       count(*) FILTER (WHERE (t.average_transaction_value IS NULL AND m.amount_to_avg_ratio IS NULL)
                           OR abs(t.transaction_amount / t.average_transaction_value - m.amount_to_avg_ratio::numeric) <= 0.0011),
       round(100.0 * avg(((t.average_transaction_value IS NULL AND m.amount_to_avg_ratio IS NULL)
                           OR coalesce(abs(t.transaction_amount / t.average_transaction_value - m.amount_to_avg_ratio::numeric) <= 0.0011, false))::int), 4)
FROM public.transactions t JOIN sentinel_dq.recomputed_features m USING (transaction_id);

-- @result: avg_value_rounding_gaps
-- Rows where the ratio built from transactions.average_transaction_value (a 2-dp
-- rounded mean) is off by more than 0.001. The rounding error of the average
-- (at most 0.005 INR) is multiplied by the ratio, so big gaps appear only where the
-- ratio is huge or the customer's average is tiny.
SELECT t.transaction_id, t.split, t.transaction_amount, t.average_transaction_value,
       m.amount_to_avg_ratio                                           AS point_in_time_ratio,
       round(t.transaction_amount / t.average_transaction_value, 4)     AS ratio_from_2dp_average,
       round(abs(t.transaction_amount / t.average_transaction_value - m.amount_to_avg_ratio::numeric), 4) AS gap,
       round(0.005 * m.amount_to_avg_ratio::numeric / t.average_transaction_value, 4) AS max_gap_from_rounding
FROM public.transactions t JOIN sentinel_dq.recomputed_features m USING (transaction_id)
WHERE abs(t.transaction_amount / t.average_transaction_value - m.amount_to_avg_ratio::numeric) > 0.0011
ORDER BY gap DESC;
