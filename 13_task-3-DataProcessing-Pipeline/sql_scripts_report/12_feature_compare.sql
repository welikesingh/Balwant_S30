-- =============================================================================
-- 12  Compare recomputed values with the provided public.features table
-- Match rule: equal, or both NULL. Floats: |mine - ref| <= 1e-9 (both are rounded,
-- 4 dp for the ratio, 2 dp for the distance, so this is effectively exact).
-- Needs 10_features_recompute.sql and 11_reason_codes.sql to have run.
-- =============================================================================

DROP TABLE IF EXISTS sentinel_dq.feature_compare;
CREATE TABLE sentinel_dq.feature_compare AS
SELECT m.transaction_id, m.split, v.feature, v.requested, v.mine, v.ref,
       CASE WHEN v.mine IS NULL AND v.ref IS NULL THEN true
            WHEN v.mine IS NULL OR  v.ref IS NULL THEN false
            WHEN v.is_float THEN abs(v.mine::float8 - v.ref::float8) <= 1e-9
            ELSE v.mine = v.ref END AS is_match
FROM sentinel_dq.recomputed_features m
JOIN public.features f USING (transaction_id)
CROSS JOIN LATERAL (VALUES
  -- requested features
  ('amount_to_avg_ratio',           true,  m.amount_to_avg_ratio::text,           f.amount_to_avg_ratio::text,           true),
  ('is_new_device',                 true,  m.is_new_device::text,                 f.is_new_device::text,                 false),
  ('customer_merchant_distance_km', true,  m.customer_merchant_distance_km::text, f.customer_merchant_distance_km::text, true),
  ('is_night',                      true,  m.is_night::text,                      f.is_night::text,                      false),
  ('txn_count_last_1h',             true,  m.txn_count_last_1h::text,             f.txn_count_last_1h::text,             false),
  ('txn_amount_last_24h_paise',     true,  m.txn_amount_last_24h_paise::text,     f.txn_amount_last_24h_paise::text,     false),
  -- supporting features the reason codes depend on
  ('is_new_city',                   false, m.is_new_city::text,                   f.is_new_city::text,                   false),
  ('hour_of_day',                   false, m.hour_of_day::text,                   f.hour_of_day::text,                   false),
  ('has_recent_failures',           false, m.has_recent_failures::text,           f.has_recent_failures::text,           false),
  ('is_new_account',                false, m.is_new_account::text,                f.is_new_account::text,                false)
) AS v(feature, requested, mine, ref, is_float);

CREATE INDEX ON sentinel_dq.feature_compare (feature, split);

-- @result: match_rate_per_feature
SELECT feature,
       CASE WHEN requested THEN 'requested' ELSE 'supporting' END            AS kind,
       count(*)                                                             AS rows,
       count(*) FILTER (WHERE is_match)                                     AS matches,
       count(*) FILTER (WHERE NOT is_match)                                 AS mismatches,
       round(100.0 * avg(is_match::int), 4)                                 AS match_rate_pct,
       round(100.0 * avg(is_match::int) FILTER (WHERE split = 'warmup'), 4)     AS warmup_pct,
       round(100.0 * avg(is_match::int) FILTER (WHERE split = 'train'), 4)      AS train_pct,
       round(100.0 * avg(is_match::int) FILTER (WHERE split = 'validation'), 4) AS validation_pct,
       round(100.0 * avg(is_match::int) FILTER (WHERE split = 'holdout'), 4)    AS holdout_pct,
       count(*) FILTER (WHERE mine IS NULL)                                 AS nulls_mine,
       count(*) FILTER (WHERE ref  IS NULL)                                 AS nulls_ref
FROM sentinel_dq.feature_compare
GROUP BY feature, requested
ORDER BY requested DESC, feature;

-- @result: reason_code_match
-- Per code: how often my code and the provided code agree.
WITH codes(code) AS (SELECT code FROM sentinel_dq.reason_code_thresholds)
SELECT c.code,
       count(*) FILTER (WHERE r.reason_codes ? c.code)                              AS fired_mine,
       count(*) FILTER (WHERE f.reason_codes ? c.code)                              AS fired_ref,
       count(*) FILTER (WHERE (r.reason_codes ? c.code) AND NOT (f.reason_codes ? c.code)) AS only_mine,
       count(*) FILTER (WHERE (f.reason_codes ? c.code) AND NOT (r.reason_codes ? c.code)) AS only_ref,
       round(100.0 * avg(((r.reason_codes ? c.code) = (f.reason_codes ? c.code))::int), 4) AS agree_pct
FROM sentinel_dq.recomputed_reason_codes r
JOIN public.features f USING (transaction_id)
CROSS JOIN codes c
GROUP BY c.code ORDER BY c.code;

-- @result: reason_code_set_match_per_split
-- Whole code list equal (order-insensitive: jsonb @> both ways).
SELECT coalesce(r.split, 'ALL') AS split,
       count(*) AS rows,
       count(*) FILTER (WHERE r.reason_codes @> f.reason_codes AND f.reason_codes @> r.reason_codes) AS exact_set_matches,
       round(100.0 * avg((r.reason_codes @> f.reason_codes AND f.reason_codes @> r.reason_codes)::int), 4) AS exact_set_match_pct,
       count(*) FILTER (WHERE r.reason_codes = f.reason_codes) AS same_order_matches
FROM sentinel_dq.recomputed_reason_codes r
JOIN public.features f USING (transaction_id)
GROUP BY ROLLUP (r.split)
ORDER BY CASE coalesce(r.split, 'ALL') WHEN 'warmup' THEN 1 WHEN 'train' THEN 2 WHEN 'validation' THEN 3 WHEN 'holdout' THEN 4 ELSE 5 END;

-- @result: unknown_codes_in_reference
-- Any code in public.features that this script does not know about.
SELECT code, count(*) AS rows
FROM public.features f, jsonb_array_elements_text(f.reason_codes) code
WHERE code NOT IN (SELECT code FROM sentinel_dq.reason_code_thresholds)
GROUP BY code;

-- @result: coverage
SELECT 'transactions without a row in public.features' AS check_name,
       count(*) AS rows FROM sentinel_dq.recomputed_features m
 WHERE NOT EXISTS (SELECT 1 FROM public.features f WHERE f.transaction_id = m.transaction_id)
UNION ALL
SELECT 'public.features rows without a transaction', count(*) FROM public.features f
 WHERE NOT EXISTS (SELECT 1 FROM sentinel_dq.recomputed_features m WHERE m.transaction_id = f.transaction_id);
