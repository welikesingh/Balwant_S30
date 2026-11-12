-- =============================================================================
-- 03  Duplicates
--   a) primary-key duplicates (should be impossible: PKs are enforced)
--   b) full-row duplicates ignoring the id (same content loaded twice under new ids)
--   c) business-key duplicates (same customer, merchant, amount, time)
--   d) orphan / missing 1:1 rows between transactions and payment_outcomes/labels/features
-- =============================================================================

-- @result: duplicates
SELECT 'customers'        AS table_name, 'customer_id (PK)'    AS key_checked, count(*) - count(DISTINCT customer_id)    AS duplicate_rows FROM public.customers
UNION ALL SELECT 'merchants',        'merchant_id (PK)',     count(*) - count(DISTINCT merchant_id)    FROM public.merchants
UNION ALL SELECT 'devices',          'device_id (PK)',       count(*) - count(DISTINCT device_id)      FROM public.devices
UNION ALL SELECT 'transactions',     'transaction_id (PK)',  count(*) - count(DISTINCT transaction_id) FROM public.transactions
UNION ALL SELECT 'payment_outcomes', 'transaction_id (PK)',  count(*) - count(DISTINCT transaction_id) FROM public.payment_outcomes
UNION ALL SELECT 'labels',           'transaction_id (PK)',  count(*) - count(DISTINCT transaction_id) FROM public.labels
-- full-row duplicates excluding the id column
UNION ALL SELECT 'customers', 'all columns except customer_id', count(*) - count(DISTINCT (to_jsonb(c) - 'customer_id')) FROM public.customers c
UNION ALL SELECT 'merchants', 'all columns except merchant_id', count(*) - count(DISTINCT (to_jsonb(m) - 'merchant_id')) FROM public.merchants m
UNION ALL SELECT 'merchants', 'synthetic_name',                 count(*) - count(DISTINCT synthetic_name)                 FROM public.merchants
UNION ALL SELECT 'transactions', 'all columns except transaction_id', count(*) - count(DISTINCT (to_jsonb(t) - 'transaction_id')) FROM public.transactions t
UNION ALL SELECT 'transactions', 'customer_id + merchant_id + amount_paise + transaction_time',
         count(*) - count(DISTINCT (customer_id, merchant_id, amount_paise, transaction_time)) FROM public.transactions
UNION ALL SELECT 'transactions', 'customer_id + transaction_time',
         count(*) - count(DISTINCT (customer_id, transaction_time)) FROM public.transactions
UNION ALL SELECT 'payment_outcomes', 'all columns except transaction_id', count(*) - count(DISTINCT (to_jsonb(p) - 'transaction_id')) FROM public.payment_outcomes p
-- devices: same kind is expected, so only id-level duplicates matter (checked above)
;

-- @result: business_key_duplicate_examples
SELECT customer_id, merchant_id, amount_paise, transaction_time, count(*) AS copies,
       string_agg(transaction_id, ', ' ORDER BY transaction_id) AS transaction_ids
FROM public.transactions
GROUP BY customer_id, merchant_id, amount_paise, transaction_time
HAVING count(*) > 1
ORDER BY copies DESC, transaction_time
LIMIT 20;

-- @result: content_duplicate_examples
-- Rows whose content (everything except the id) equals another row's. For each one,
-- the transaction count shows whether it is a double load (copies share one history,
-- or one copy is empty) or a coincidence of low-cardinality columns.
SELECT 'customers' AS table_name, c.customer_id AS id,
       format('created %s, age %s, %s / %s', c.created_at::date, c.customer_age, c.home_city, c.region) AS content,
       (SELECT count(*) FROM public.transactions t WHERE t.customer_id = c.customer_id) AS own_transactions
FROM public.customers c
WHERE (to_jsonb(c) - 'customer_id') IN (SELECT to_jsonb(x) - 'customer_id' FROM public.customers x GROUP BY 1 HAVING count(*) > 1)
UNION ALL
SELECT 'payment_outcomes', p.transaction_id,
       format('%s %s at %s; txn by %s at %s, %s paise', p.status, p.failure_code, p.outcome_time,
              t.customer_id, t.transaction_time, t.amount_paise),
       NULL
FROM public.payment_outcomes p JOIN public.transactions t USING (transaction_id)
WHERE (to_jsonb(p) - 'transaction_id') IN (SELECT to_jsonb(x) - 'transaction_id' FROM public.payment_outcomes x GROUP BY 1 HAVING count(*) > 1)
ORDER BY 1, 3, 2;

-- @result: one_to_one_coverage
SELECT 'transactions without payment_outcome' AS check_name, count(*) AS violations
  FROM public.transactions t WHERE NOT EXISTS (SELECT 1 FROM public.payment_outcomes p WHERE p.transaction_id = t.transaction_id)
UNION ALL SELECT 'transactions without label', count(*)
  FROM public.transactions t WHERE NOT EXISTS (SELECT 1 FROM public.labels l WHERE l.transaction_id = t.transaction_id)
UNION ALL SELECT 'transactions without features row', count(*)
  FROM public.transactions t WHERE NOT EXISTS (SELECT 1 FROM public.features f WHERE f.transaction_id = t.transaction_id)
UNION ALL SELECT 'transactions with unknown customer', count(*)
  FROM public.transactions t WHERE NOT EXISTS (SELECT 1 FROM public.customers c WHERE c.customer_id = t.customer_id)
UNION ALL SELECT 'transactions with unknown merchant', count(*)
  FROM public.transactions t WHERE NOT EXISTS (SELECT 1 FROM public.merchants m WHERE m.merchant_id = t.merchant_id)
UNION ALL SELECT 'transactions with unknown device', count(*)
  FROM public.transactions t WHERE t.device_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM public.devices d WHERE d.device_id = t.device_id)
UNION ALL SELECT 'customers with no transactions', count(*)
  FROM public.customers c WHERE NOT EXISTS (SELECT 1 FROM public.transactions t WHERE t.customer_id = c.customer_id)
UNION ALL SELECT 'merchants with no transactions', count(*)
  FROM public.merchants m WHERE NOT EXISTS (SELECT 1 FROM public.transactions t WHERE t.merchant_id = m.merchant_id)
UNION ALL SELECT 'devices with no transactions', count(*)
  FROM public.devices d WHERE NOT EXISTS (SELECT 1 FROM public.transactions t WHERE t.device_id = d.device_id);
