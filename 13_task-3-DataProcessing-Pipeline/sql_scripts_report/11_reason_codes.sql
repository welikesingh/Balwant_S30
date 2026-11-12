-- =============================================================================
-- 11  Reason codes R01-R08 from the recomputed features
--
-- Thresholds live in ONE table (sentinel_dq.reason_code_thresholds) so they can be
-- changed in a single place and re-run. Values below are the class thresholds as
-- they appear in the provided features table (script 14 shows the evidence: every
-- boundary is clean, i.e. no row of public.features contradicts them).
--
--   R01_NEW_DEVICE      is_new_device = true
--   R02_GEO_MISMATCH    is_new_city = true  OR  distance_km >  500
--   R03_ODD_HOUR        is_night = true (IST 00:00-04:59)
--   R04_FAILED_ATTEMPTS failed outcomes in previous 24h >= 3
--   R05_AMOUNT_SPIKE    amount_to_avg_ratio >= 5
--   R06_NEW_ACCOUNT     account age < 30 days
--   R07_VELOCITY        txn_count_last_1h >= 4
--   R08_HIGH_RISK_MCC   merchant_category IN (electronics, gaming, gift_cards)
-- A NULL feature (unknown) never fires a code.
-- =============================================================================

DROP TABLE IF EXISTS sentinel_dq.reason_code_thresholds;
CREATE TABLE sentinel_dq.reason_code_thresholds (
  code        text PRIMARY KEY,
  description text NOT NULL,
  num_value   numeric,
  list_value  text[]
);
INSERT INTO sentinel_dq.reason_code_thresholds VALUES
  ('R01_NEW_DEVICE',      'is_new_device = true',                         NULL, NULL),
  ('R02_GEO_MISMATCH',    'is_new_city = true OR distance_km > value',    500,  NULL),
  ('R03_ODD_HOUR',        'is_night = true (IST hour < 5)',               NULL, NULL),
  ('R04_FAILED_ATTEMPTS', 'failed outcomes in previous 24h >= value',     3,    NULL),
  ('R05_AMOUNT_SPIKE',    'amount_to_avg_ratio >= value',                 5,    NULL),
  ('R06_NEW_ACCOUNT',     'account age in days < value',                  30,   NULL),
  ('R07_VELOCITY',        'txn_count_last_1h >= value',                   4,    NULL),
  ('R08_HIGH_RISK_MCC',   'merchant_category in list',                    NULL, ARRAY['electronics','gaming','gift_cards']);

DROP TABLE IF EXISTS sentinel_dq.recomputed_reason_codes;
CREATE TABLE sentinel_dq.recomputed_reason_codes AS
WITH p AS (
  SELECT max(num_value)  FILTER (WHERE code = 'R02_GEO_MISMATCH')    AS r02_km,
         max(num_value)  FILTER (WHERE code = 'R04_FAILED_ATTEMPTS') AS r04_fail,
         max(num_value)  FILTER (WHERE code = 'R05_AMOUNT_SPIKE')    AS r05_ratio,
         max(num_value)  FILTER (WHERE code = 'R06_NEW_ACCOUNT')     AS r06_days,
         max(num_value)  FILTER (WHERE code = 'R07_VELOCITY')        AS r07_cnt,
         (SELECT list_value FROM sentinel_dq.reason_code_thresholds WHERE code = 'R08_HIGH_RISK_MCC') AS r08_mcc
  FROM sentinel_dq.reason_code_thresholds
)
SELECT f.transaction_id, f.split,
       to_jsonb(array_remove(ARRAY[
         CASE WHEN f.is_new_device THEN 'R01_NEW_DEVICE' END,
         CASE WHEN f.is_new_city OR f.customer_merchant_distance_km > p.r02_km THEN 'R02_GEO_MISMATCH' END,
         CASE WHEN f.is_night THEN 'R03_ODD_HOUR' END,
         CASE WHEN f.failed_last_24h >= p.r04_fail THEN 'R04_FAILED_ATTEMPTS' END,
         CASE WHEN f.amount_to_avg_ratio >= p.r05_ratio THEN 'R05_AMOUNT_SPIKE' END,
         CASE WHEN f.account_age_days < p.r06_days THEN 'R06_NEW_ACCOUNT' END,
         CASE WHEN f.txn_count_last_1h >= p.r07_cnt THEN 'R07_VELOCITY' END,
         CASE WHEN f.merchant_category = ANY (p.r08_mcc) THEN 'R08_HIGH_RISK_MCC' END
       ], NULL)) AS reason_codes
FROM sentinel_dq.recomputed_features f CROSS JOIN p;

ALTER TABLE sentinel_dq.recomputed_reason_codes ADD PRIMARY KEY (transaction_id);

-- @result: reason_code_thresholds
SELECT code, description, num_value, array_to_string(list_value, ', ') AS list_value
FROM sentinel_dq.reason_code_thresholds ORDER BY code;

-- @result: reason_code_fire_rates
SELECT c.code,
       count(*) FILTER (WHERE r.reason_codes ? c.code)                                   AS fired,
       round(100.0 * count(*) FILTER (WHERE r.reason_codes ? c.code) / count(*), 2)       AS fired_pct,
       round(100.0 * count(*) FILTER (WHERE r.reason_codes ? c.code AND r.split = 'train')
             / nullif(count(*) FILTER (WHERE r.split = 'train'), 0), 2)                   AS fired_pct_train,
       round(100.0 * count(*) FILTER (WHERE r.reason_codes ? c.code AND r.split = 'holdout')
             / nullif(count(*) FILTER (WHERE r.split = 'holdout'), 0), 2)                 AS fired_pct_holdout
FROM sentinel_dq.recomputed_reason_codes r
CROSS JOIN sentinel_dq.reason_code_thresholds c
GROUP BY c.code ORDER BY c.code;
