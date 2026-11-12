-- =============================================================================
-- 02  Nulls per column for customers, merchants, devices, transactions,
--     payment_outcomes, labels.
-- Generic trick: to_jsonb(row) turns every column into a key, so one query covers
-- every column without listing them. A JSON null value = SQL NULL.
-- Also checks the keys inside the location JSON (lat, lon, city).
-- =============================================================================

-- @result: nulls_per_column
WITH cols AS (
  SELECT 'customers' AS table_name, e.key AS column_name, (e.value = 'null'::jsonb) AS is_null
    FROM public.customers r, jsonb_each(to_jsonb(r)) e
  UNION ALL SELECT 'merchants', e.key, e.value = 'null'::jsonb
    FROM public.merchants r, jsonb_each(to_jsonb(r)) e
  UNION ALL SELECT 'devices', e.key, e.value = 'null'::jsonb
    FROM public.devices r, jsonb_each(to_jsonb(r)) e
  UNION ALL SELECT 'transactions', e.key, e.value = 'null'::jsonb
    FROM public.transactions r, jsonb_each(to_jsonb(r)) e
  UNION ALL SELECT 'payment_outcomes', e.key, e.value = 'null'::jsonb
    FROM public.payment_outcomes r, jsonb_each(to_jsonb(r)) e
  UNION ALL SELECT 'labels', e.key, e.value = 'null'::jsonb
    FROM public.labels r, jsonb_each(to_jsonb(r)) e
)
SELECT c.table_name, c.column_name,
       count(*)                                   AS row_count,
       count(*) FILTER (WHERE c.is_null)          AS null_count,
       round(100.0 * count(*) FILTER (WHERE c.is_null) / count(*), 3) AS null_pct,
       ic.is_nullable                             AS declared_nullable
FROM cols c
JOIN information_schema.columns ic
  ON ic.table_schema = 'public' AND ic.table_name = c.table_name AND ic.column_name = c.column_name
GROUP BY c.table_name, c.column_name, ic.is_nullable, ic.ordinal_position
ORDER BY CASE c.table_name WHEN 'customers' THEN 1 WHEN 'merchants' THEN 2 WHEN 'devices' THEN 3
                           WHEN 'transactions' THEN 4 WHEN 'payment_outcomes' THEN 5 ELSE 6 END,
         ic.ordinal_position;

-- @result: nulls_per_split
-- The nullable transaction columns, broken down by split (are nulls concentrated somewhere?).
SELECT split,
       count(*)                                                  AS transactions,
       count(*) FILTER (WHERE device_id IS NULL)                 AS null_device_id,
       count(*) FILTER (WHERE customer_location IS NULL)         AS null_customer_location,
       count(*) FILTER (WHERE average_transaction_value IS NULL) AS null_average_transaction_value
FROM public.transactions
GROUP BY split
ORDER BY min(transaction_time);

-- @result: null_json_keys
-- Nulls hidden inside the JSON location columns.
SELECT 'transactions.customer_location' AS json_column,
       count(*) FILTER (WHERE customer_location IS NOT NULL)                                  AS non_null_rows,
       count(*) FILTER (WHERE customer_location IS NOT NULL AND (customer_location->'lat' IS NULL OR customer_location->'lat' = 'null')) AS missing_lat,
       count(*) FILTER (WHERE customer_location IS NOT NULL AND (customer_location->'lon' IS NULL OR customer_location->'lon' = 'null')) AS missing_lon,
       count(*) FILTER (WHERE customer_location IS NOT NULL AND (customer_location->'city' IS NULL OR customer_location->'city' = 'null')) AS missing_city
FROM public.transactions
UNION ALL
SELECT 'transactions.merchant_location', count(*),
       count(*) FILTER (WHERE merchant_location->'lat'  IS NULL OR merchant_location->'lat'  = 'null'),
       count(*) FILTER (WHERE merchant_location->'lon'  IS NULL OR merchant_location->'lon'  = 'null'),
       count(*) FILTER (WHERE merchant_location->'city' IS NULL OR merchant_location->'city' = 'null')
FROM public.transactions
UNION ALL
SELECT 'merchants.merchant_location', count(*),
       count(*) FILTER (WHERE merchant_location->'lat'  IS NULL OR merchant_location->'lat'  = 'null'),
       count(*) FILTER (WHERE merchant_location->'lon'  IS NULL OR merchant_location->'lon'  = 'null'),
       count(*) FILTER (WHERE merchant_location->'city' IS NULL OR merchant_location->'city' = 'null')
FROM public.merchants;
