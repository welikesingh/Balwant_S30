-- =============================================================================
-- 10  Recompute features point-in-time (no future leakage)
--
-- Writes ONE table: sentinel_dq.recomputed_features (separate schema; nothing in
-- public.* is changed). Re-running replaces it. 99_cleanup.sql drops the schema.
--
-- Leakage rules applied to every row "cur" at time T = cur.transaction_time:
--   * history = the same customer's transactions with transaction_time < T
--     (strictly earlier; the current transaction is never part of its own history)
--   * a payment outcome is known only once outcome_time < T
--   * nothing from labels or from public.features is read here
--
-- Definitions (CRD feature catalogue, data/feature_catalogue.json):
--   amount_to_avg_ratio           amount_paise / mean(amount_paise of history in [T-90d, T)),
--                                 rounded to 4 dp; NULL when that 90-day history is empty.
--                                 Declined attempts count (they are authorisations).
--   is_new_device                 device_id not used by this customer in [T-90d, T);
--                                 NULL when device_id is NULL.
--   customer_merchant_distance_km haversine(customer lat/lon, merchant lat/lon), R = 6371 km,
--                                 rounded to 2 dp; NULL when customer location unknown.
--   is_new_city                   customer city not seen in [T-90d, T); NULL if unknown.
--   hour_of_day / is_night        hour in IST (Asia/Kolkata); night = 00:00 <= h < 05:00.
--   txn_count_last_1h             count of history in [T-1h, T)   (declines included)
--   txn_amount_last_24h_paise     sum of amount_paise of history in [T-24h, T)
--   failed_last_24h               history rows with status FAILED and outcome_time in [T-24h, T)
--   has_recent_failures           failed_last_24h >= 3
--   account_age_days              complete days since customers.created_at
--   is_new_account                account_age_days < 30
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS sentinel_dq;
DROP TABLE IF EXISTS sentinel_dq.recomputed_features;

CREATE TABLE sentinel_dq.recomputed_features AS
WITH tx AS (
  SELECT t.transaction_id, t.customer_id, t.split, t.transaction_time, t.amount_paise,
         t.device_id, t.merchant_category,
         t.customer_location->>'city'            AS city,
         (t.customer_location->>'lat')::float8   AS c_lat,
         (t.customer_location->>'lon')::float8   AS c_lon,
         (t.merchant_location->>'lat')::float8   AS m_lat,
         (t.merchant_location->>'lon')::float8   AS m_lon,
         c.created_at,
         p.status, p.outcome_time
  FROM public.transactions t
  JOIN public.customers c USING (customer_id)
  LEFT JOIN public.payment_outcomes p USING (transaction_id)
),
hist AS (
  -- one pass: pair every transaction with its own customer's EARLIER transactions
  -- of the last 90 days, then aggregate each window with FILTER.
  SELECT cur.transaction_id,
         avg(prv.amount_paise)                                                       AS avg_amount_90d,
         count(*)                                                                    AS n_90d,
         bool_or(prv.device_id = cur.device_id)                                      AS device_seen_90d,
         bool_or(prv.city = cur.city)                                                AS city_seen_90d,
         count(*) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '1 hour')  AS cnt_1h,
         sum(prv.amount_paise) FILTER (WHERE prv.transaction_time >= cur.transaction_time - interval '24 hours') AS amt_24h,
         count(*) FILTER (WHERE prv.status = 'FAILED'
                            AND prv.outcome_time <  cur.transaction_time            -- outcome already received
                            AND prv.outcome_time >= cur.transaction_time - interval '24 hours') AS failed_24h
  FROM tx cur
  JOIN tx prv
    ON prv.customer_id = cur.customer_id
   AND prv.transaction_time <  cur.transaction_time                                  -- strictly before: no leakage
   AND prv.transaction_time >= cur.transaction_time - interval '90 days'
  GROUP BY cur.transaction_id
)
SELECT tx.transaction_id,
       tx.split,
       tx.customer_id,
       tx.transaction_time,
       tx.merchant_category,
       CASE WHEN h.n_90d > 0
            THEN round(tx.amount_paise / h.avg_amount_90d, 4)::float8 END             AS amount_to_avg_ratio,
       CASE WHEN tx.device_id IS NOT NULL
            THEN NOT coalesce(h.device_seen_90d, false) END                           AS is_new_device,
       CASE WHEN tx.c_lat IS NOT NULL AND tx.c_lon IS NOT NULL
            THEN round((2 * 6371.0 * asin(sqrt(
                    power(sin((radians(tx.m_lat) - radians(tx.c_lat)) / 2), 2)
                  + cos(radians(tx.c_lat)) * cos(radians(tx.m_lat))
                  * power(sin(radians(tx.m_lon - tx.c_lon) / 2), 2))))::numeric, 2)::float8
       END                                                                            AS customer_merchant_distance_km,
       CASE WHEN tx.city IS NOT NULL
            THEN NOT coalesce(h.city_seen_90d, false) END                             AS is_new_city,
       extract(hour FROM tx.transaction_time AT TIME ZONE 'Asia/Kolkata')::int        AS hour_of_day,
       extract(hour FROM tx.transaction_time AT TIME ZONE 'Asia/Kolkata') < 5         AS is_night,
       coalesce(h.cnt_1h, 0)::int                                                     AS txn_count_last_1h,
       coalesce(h.amt_24h, 0)::bigint                                                 AS txn_amount_last_24h_paise,
       coalesce(h.failed_24h, 0)::int                                                 AS failed_last_24h,
       coalesce(h.failed_24h, 0) >= 3                                                 AS has_recent_failures,
       floor(extract(epoch FROM tx.transaction_time - tx.created_at) / 86400)::int    AS account_age_days,
       floor(extract(epoch FROM tx.transaction_time - tx.created_at) / 86400) < 30    AS is_new_account
FROM tx
LEFT JOIN hist h USING (transaction_id);

ALTER TABLE sentinel_dq.recomputed_features ADD PRIMARY KEY (transaction_id);
ANALYZE sentinel_dq.recomputed_features;

-- @result: recompute_summary
SELECT split,
       count(*)                                           AS rows,
       count(*) FILTER (WHERE amount_to_avg_ratio IS NULL)           AS null_ratio_no_90d_history,
       count(*) FILTER (WHERE is_new_device IS NULL)                 AS null_new_device_no_device,
       count(*) FILTER (WHERE customer_merchant_distance_km IS NULL) AS null_distance_no_location,
       round(avg(amount_to_avg_ratio)::numeric, 3)                   AS avg_ratio,
       round(100.0 * avg(is_new_device::int), 2)                     AS new_device_pct,
       round(avg(customer_merchant_distance_km)::numeric, 1)         AS avg_distance_km,
       round(100.0 * avg(is_night::int), 2)                          AS night_pct,
       round(avg(txn_count_last_1h)::numeric, 3)                     AS avg_txn_count_1h,
       round(avg(txn_amount_last_24h_paise) / 100.0, 2)              AS avg_amount_24h_inr
FROM sentinel_dq.recomputed_features
GROUP BY ROLLUP (split)
ORDER BY min(transaction_time) NULLS LAST;
