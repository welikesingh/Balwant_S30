-- =============================================================================
-- 15  What common mistakes would do to the match rate
-- Each variant recomputes one feature the WRONG way and measures its match rate
-- against public.features. This explains the mismatches you would see with a
-- careless implementation (and proves the provided table follows the strict
-- no-leakage definition). Read-only.
-- =============================================================================

-- @result: variant_match_rates
WITH tx AS (
  SELECT t.transaction_id, t.customer_id, t.transaction_time, t.amount_paise, t.device_id, p.status, p.outcome_time
  FROM public.transactions t LEFT JOIN public.payment_outcomes p USING (transaction_id)
),
w AS (  -- windows that INCLUDE the current transaction (prv.time <= cur.time)
  SELECT cur.transaction_id,
         round(cur.amount_paise / avg(prv.amount_paise), 4)::float8                                   AS ratio_incl_current,
         round(cur.amount_paise / avg(prv.amount_paise) FILTER (WHERE prv.transaction_time < cur.transaction_time
                                     AND prv.status = 'SUCCESS' AND prv.outcome_time < cur.transaction_time), 4)::float8 AS ratio_success_only,
         count(*) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '1 hour')    AS cnt1h_incl_current,
         count(*) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '1 hour'
                            AND prv.transaction_time < cur.transaction_time
                            AND prv.status = 'SUCCESS' AND prv.outcome_time < cur.transaction_time)   AS cnt1h_success_only,
         sum(prv.amount_paise) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '24 hours') AS amt24_incl_current,
         coalesce(sum(prv.amount_paise) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '24 hours'
                            AND prv.transaction_time < cur.transaction_time
                            AND prv.status = 'SUCCESS' AND prv.outcome_time < cur.transaction_time), 0) AS amt24_success_only
  FROM tx cur JOIN tx prv
    ON prv.customer_id = cur.customer_id
   AND prv.transaction_time <= cur.transaction_time
   AND prv.transaction_time >= cur.transaction_time - interval '90 days'
  GROUP BY cur.transaction_id, cur.amount_paise
),
first_use AS (  -- first time each customer used each device
  SELECT customer_id, device_id, min(transaction_time) AS first_time
  FROM tx WHERE device_id IS NOT NULL GROUP BY 1, 2
),
dev_ever AS (   -- device "seen at any time before" instead of within 90 days
  SELECT cur.transaction_id,
         CASE WHEN cur.device_id IS NOT NULL THEN cur.transaction_time = fu.first_time END AS new_device_ever
  FROM tx cur
  LEFT JOIN first_use fu ON fu.customer_id = cur.customer_id AND fu.device_id = cur.device_id
),
v AS (
  SELECT f.*, w.ratio_incl_current, w.ratio_success_only, w.cnt1h_incl_current, w.cnt1h_success_only,
         w.amt24_incl_current, w.amt24_success_only, d.new_device_ever,
         t.transaction_time AS tt, t.customer_location, t.merchant_location
  FROM public.features f
  JOIN w USING (transaction_id) JOIN dev_ever d USING (transaction_id)
  JOIN public.transactions t USING (transaction_id)
)
SELECT feature, variant, round(100.0 * avg(ok::int), 3) AS match_rate_pct
FROM v CROSS JOIN LATERAL (VALUES
  ('amount_to_avg_ratio', 'B. current transaction included in its own 90d average (LEAKAGE)',
      v.ratio_incl_current IS NOT DISTINCT FROM v.amount_to_avg_ratio),
  ('amount_to_avg_ratio', 'C. declined attempts dropped from history',
      v.ratio_success_only IS NOT DISTINCT FROM v.amount_to_avg_ratio),
  ('is_new_device',       'B. device seen at ANY time before (no 90-day window)',
      v.new_device_ever IS NOT DISTINCT FROM v.is_new_device),
  ('customer_merchant_distance_km', 'B. Earth radius 6378.137 km (equatorial) instead of 6371',
      (v.customer_location IS NULL AND v.customer_merchant_distance_km IS NULL) OR
      round((2 * 6378.137 * asin(sqrt(
          power(sin((radians((v.merchant_location->>'lat')::float8) - radians((v.customer_location->>'lat')::float8)) / 2), 2)
        + cos(radians((v.customer_location->>'lat')::float8)) * cos(radians((v.merchant_location->>'lat')::float8))
        * power(sin(radians((v.merchant_location->>'lon')::float8 - (v.customer_location->>'lon')::float8) / 2), 2))))::numeric, 2)::float8
        = v.customer_merchant_distance_km),
  ('is_night',            'B. hour taken in UTC instead of IST',
      (extract(hour FROM v.tt AT TIME ZONE 'UTC') < 5) = v.is_night),
  ('is_night',            'C. night = 22:00-06:00 IST',
      (extract(hour FROM v.tt AT TIME ZONE 'Asia/Kolkata') >= 22 OR extract(hour FROM v.tt AT TIME ZONE 'Asia/Kolkata') < 6) = v.is_night),
  ('txn_count_last_1h',   'B. current transaction counted (LEAKAGE)',  v.cnt1h_incl_current = v.txn_count_last_1h),
  ('txn_count_last_1h',   'C. declined attempts not counted',          v.cnt1h_success_only = v.txn_count_last_1h),
  ('txn_amount_last_24h_paise', 'B. current amount added (LEAKAGE)',   v.amt24_incl_current = v.txn_amount_last_24h_paise),
  ('txn_amount_last_24h_paise', 'C. declined attempts not summed',     v.amt24_success_only = v.txn_amount_last_24h_paise)
) AS x(feature, variant, ok)
WHERE ok IS NOT NULL
GROUP BY feature, variant
ORDER BY feature, variant;
