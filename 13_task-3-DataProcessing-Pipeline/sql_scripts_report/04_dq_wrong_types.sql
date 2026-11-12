-- =============================================================================
-- 04  Wrong types and invalid values
--   a) declared column type in the database vs the data dictionary (CRD)
--   b) values stored in a valid type but semantically wrong: JSON lat/lon that are
--      not numbers or out of range, ids with the wrong pattern, unknown category
--      values, money that does not reconcile, copies that disagree with the master
--      table, timestamps in the wrong order.
-- =============================================================================

-- @result: declared_types
WITH expected(table_name, column_name, expected_type) AS (VALUES
  ('customers','customer_id','text'),('customers','created_at','timestamp with time zone'),
  ('customers','customer_age','integer'),('customers','home_city','text'),('customers','region','text'),
  ('customers','is_synthetic','boolean'),
  ('merchants','merchant_id','text'),('merchants','synthetic_name','text'),('merchants','merchant_category','text'),
  ('merchants','merchant_location','jsonb'),('merchants','is_synthetic','boolean'),
  ('devices','device_id','text'),('devices','device_kind','text'),('devices','is_synthetic','boolean'),
  ('transactions','transaction_id','text'),('transactions','customer_id','text'),('transactions','merchant_id','text'),
  ('transactions','device_id','text'),('transactions','amount_paise','bigint'),('transactions','transaction_amount','numeric'),
  ('transactions','payment_channel','text'),('transactions','merchant_category','text'),
  ('transactions','transaction_time','timestamp with time zone'),('transactions','customer_age','integer'),
  ('transactions','customer_location','jsonb'),('transactions','merchant_location','jsonb'),
  ('transactions','account_age','integer'),('transactions','previous_transactions','integer'),
  ('transactions','average_transaction_value','numeric'),('transactions','failed_transactions','integer'),
  ('transactions','split','text'),('transactions','is_synthetic','boolean'),
  ('payment_outcomes','transaction_id','text'),('payment_outcomes','outcome_time','timestamp with time zone'),
  ('payment_outcomes','status','text'),('payment_outcomes','failure_code','text'),('payment_outcomes','is_synthetic','boolean'),
  ('labels','transaction_id','text'),('labels','fraud_label','smallint'),('labels','label_source','text'),
  ('labels','label_available_at','timestamp with time zone'),('labels','split','text'),
  ('labels','eligible_at_next_split_start','boolean'),('labels','is_synthetic','boolean'))
SELECT e.table_name, e.column_name, e.expected_type, c.data_type AS actual_type,
       CASE WHEN c.data_type IS NULL THEN 'MISSING COLUMN'
            WHEN c.data_type = e.expected_type THEN 'ok' ELSE 'TYPE MISMATCH' END AS status
FROM expected e
LEFT JOIN information_schema.columns c
  ON c.table_schema = 'public' AND c.table_name = e.table_name AND c.column_name = e.column_name
ORDER BY (c.data_type IS DISTINCT FROM e.expected_type) DESC, e.table_name, e.column_name;

-- @result: invalid_values
SELECT * FROM (
  -- JSON values of the wrong type
  SELECT 'transactions' AS table_name, 'customer_location.lat/lon not a number' AS check_name, count(*) AS violations
    FROM public.transactions WHERE customer_location IS NOT NULL
     AND (jsonb_typeof(customer_location->'lat') IS DISTINCT FROM 'number' OR jsonb_typeof(customer_location->'lon') IS DISTINCT FROM 'number')
  UNION ALL SELECT 'transactions', 'customer_location.city not a string', count(*)
    FROM public.transactions WHERE customer_location IS NOT NULL AND jsonb_typeof(customer_location->'city') IS DISTINCT FROM 'string'
  UNION ALL SELECT 'transactions', 'customer_location is not a JSON object', count(*)
    FROM public.transactions WHERE customer_location IS NOT NULL AND jsonb_typeof(customer_location) <> 'object'
  UNION ALL SELECT 'transactions', 'merchant_location.lat/lon not a number', count(*)
    FROM public.transactions
   WHERE jsonb_typeof(merchant_location->'lat') IS DISTINCT FROM 'number' OR jsonb_typeof(merchant_location->'lon') IS DISTINCT FROM 'number'
  UNION ALL SELECT 'merchants', 'merchant_location.lat/lon not a number', count(*)
    FROM public.merchants
   WHERE jsonb_typeof(merchant_location->'lat') IS DISTINCT FROM 'number' OR jsonb_typeof(merchant_location->'lon') IS DISTINCT FROM 'number'
  -- coordinates out of range (India is roughly lat 6..37, lon 68..98)
  UNION ALL SELECT 'transactions', 'customer lat/lon outside India bounding box', count(*)
    FROM public.transactions WHERE jsonb_typeof(customer_location->'lat') = 'number'
     AND NOT ((customer_location->>'lat')::float8 BETWEEN 6 AND 37.5 AND (customer_location->>'lon')::float8 BETWEEN 68 AND 98)
  UNION ALL SELECT 'transactions', 'merchant lat/lon outside India bounding box', count(*)
    FROM public.transactions WHERE jsonb_typeof(merchant_location->'lat') = 'number'
     AND NOT ((merchant_location->>'lat')::float8 BETWEEN 6 AND 37.5 AND (merchant_location->>'lon')::float8 BETWEEN 68 AND 98)
  -- id patterns
  UNION ALL SELECT 'customers', 'customer_id not like C_<16 hex>', count(*) FROM public.customers WHERE customer_id !~ '^C_[0-9a-f]{16}$'
  UNION ALL SELECT 'merchants', 'merchant_id not like M_<16 hex>', count(*) FROM public.merchants WHERE merchant_id !~ '^M_[0-9a-f]{16}$'
  UNION ALL SELECT 'devices',   'device_id not like D_<16 hex>',   count(*) FROM public.devices   WHERE device_id   !~ '^D_[0-9a-f]{16}$'
  UNION ALL SELECT 'transactions', 'transaction_id pattern differs from the majority', count(*)
    FROM public.transactions
   WHERE regexp_replace(transaction_id, '[0-9a-f]', 'x', 'g') <>
         (SELECT regexp_replace(transaction_id, '[0-9a-f]', 'x', 'g') p FROM public.transactions GROUP BY 1 ORDER BY count(*) DESC LIMIT 1)
  -- money
  UNION ALL SELECT 'transactions', 'amount_paise <> transaction_amount * 100', count(*)
    FROM public.transactions WHERE amount_paise <> transaction_amount * 100
  UNION ALL SELECT 'transactions', 'amount_paise <= 0', count(*) FROM public.transactions WHERE amount_paise <= 0
  UNION ALL SELECT 'transactions', 'average_transaction_value <= 0', count(*) FROM public.transactions WHERE average_transaction_value <= 0
  -- domains
  UNION ALL SELECT 'transactions', 'payment_channel not in (UPI, card, wallet, net_banking)', count(*)
    FROM public.transactions WHERE payment_channel NOT IN ('UPI','card','wallet','net_banking')
  UNION ALL SELECT 'payment_outcomes', 'status not in (SUCCESS, FAILED)', count(*)
    FROM public.payment_outcomes WHERE status NOT IN ('SUCCESS','FAILED')
  UNION ALL SELECT 'payment_outcomes', 'failure_code present on SUCCESS or missing on FAILED', count(*)
    FROM public.payment_outcomes WHERE (status = 'SUCCESS') = (failure_code IS NOT NULL)
  UNION ALL SELECT 'labels', 'fraud_label not 0/1', count(*) FROM public.labels WHERE fraud_label NOT IN (0,1)
  UNION ALL SELECT 'customers', 'customer_age outside 18..120', count(*) FROM public.customers WHERE customer_age NOT BETWEEN 18 AND 120
  UNION ALL SELECT 'transactions', 'negative counters (account_age, previous_transactions, failed_transactions)', count(*)
    FROM public.transactions WHERE account_age < 0 OR previous_transactions < 0 OR failed_transactions < 0
  UNION ALL SELECT 'all', 'is_synthetic = false', (
      (SELECT count(*) FROM public.customers WHERE NOT is_synthetic) + (SELECT count(*) FROM public.merchants WHERE NOT is_synthetic)
    + (SELECT count(*) FROM public.devices WHERE NOT is_synthetic) + (SELECT count(*) FROM public.transactions WHERE NOT is_synthetic)
    + (SELECT count(*) FROM public.payment_outcomes WHERE NOT is_synthetic) + (SELECT count(*) FROM public.labels WHERE NOT is_synthetic))
  -- copies that must agree with their master table
  UNION ALL SELECT 'transactions', 'merchant_category differs from merchants table', count(*)
    FROM public.transactions t JOIN public.merchants m USING (merchant_id) WHERE t.merchant_category <> m.merchant_category
  UNION ALL SELECT 'transactions', 'merchant_location differs from merchants table', count(*)
    FROM public.transactions t JOIN public.merchants m USING (merchant_id) WHERE t.merchant_location <> m.merchant_location
  UNION ALL SELECT 'transactions', 'customer_age differs from customers table', count(*)
    FROM public.transactions t JOIN public.customers c USING (customer_id) WHERE t.customer_age <> c.customer_age
  UNION ALL SELECT 'transactions', 'account_age <> full days since customers.created_at', count(*)
    FROM public.transactions t JOIN public.customers c USING (customer_id)
   WHERE t.account_age <> floor(extract(epoch FROM t.transaction_time - c.created_at) / 86400)
  -- time order
  UNION ALL SELECT 'transactions', 'transaction before customer created_at', count(*)
    FROM public.transactions t JOIN public.customers c USING (customer_id) WHERE t.transaction_time < c.created_at
  UNION ALL SELECT 'payment_outcomes', 'outcome_time <= transaction_time', count(*)
    FROM public.payment_outcomes p JOIN public.transactions t USING (transaction_id) WHERE p.outcome_time <= t.transaction_time
  UNION ALL SELECT 'labels', 'label_available_at <> transaction_time + 60 days', count(*)
    FROM public.labels l JOIN public.transactions t USING (transaction_id) WHERE l.label_available_at <> t.transaction_time + interval '60 days'
  UNION ALL SELECT 'transactions', 'transaction_time after dataset snapshot (2026-05-01)', count(*)
    FROM public.transactions WHERE transaction_time >= '2026-05-01'
) x
ORDER BY violations DESC, table_name, check_name;

-- @result: category_domains
SELECT 'payment_channel' AS column_name, payment_channel AS value, count(*) AS rows FROM public.transactions GROUP BY 2
UNION ALL SELECT 'merchant_category', merchant_category, count(*) FROM public.transactions GROUP BY 2
UNION ALL SELECT 'payment_outcomes.status', status, count(*) FROM public.payment_outcomes GROUP BY 2
UNION ALL SELECT 'payment_outcomes.failure_code', coalesce(failure_code, '(null)'), count(*) FROM public.payment_outcomes GROUP BY 2
UNION ALL SELECT 'labels.label_source', label_source, count(*) FROM public.labels GROUP BY 2
UNION ALL SELECT 'devices.device_kind', device_kind, count(*) FROM public.devices GROUP BY 2
UNION ALL SELECT 'customers.region', region, count(*) FROM public.customers GROUP BY 2
ORDER BY 1, 3 DESC;
