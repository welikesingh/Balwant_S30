-- =============================================================================
-- 01  Row count per split (warmup, train, validation, holdout)
-- Read-only. Run in the Supabase SQL editor or via run_report.py.
-- Each "-- @result:" marker names one result set for run_report.py.
-- =============================================================================

-- @result: rows_per_split
-- Rows per split in every split-bearing table, plus how many transactions of each
-- split have their outcome / label / features row (completeness of the load).
WITH s(split, ord) AS (VALUES ('warmup',1),('train',2),('validation',3),('holdout',4))
SELECT s.split,
       (SELECT count(*) FROM public.transactions t WHERE t.split = s.split)                        AS transactions,
       (SELECT count(*) FROM public.transactions t JOIN public.payment_outcomes p USING (transaction_id)
         WHERE t.split = s.split)                                                                  AS with_payment_outcome,
       (SELECT count(*) FROM public.labels l WHERE l.split = s.split)                              AS labels,
       (SELECT count(*) FROM public.transactions t JOIN public.features f USING (transaction_id)
         WHERE t.split = s.split)                                                                  AS with_features,
       (SELECT sum(l.fraud_label) FROM public.labels l WHERE l.split = s.split)                    AS fraud_labels,
       (SELECT round(100.0 * avg(l.fraud_label), 3) FROM public.labels l WHERE l.split = s.split)  AS fraud_pct,
       (SELECT min(t.transaction_time) AT TIME ZONE 'Asia/Kolkata' FROM public.transactions t WHERE t.split = s.split) AS first_txn_ist,
       (SELECT max(t.transaction_time) AT TIME ZONE 'Asia/Kolkata' FROM public.transactions t WHERE t.split = s.split) AS last_txn_ist
FROM s
UNION ALL
SELECT 'TOTAL',
       (SELECT count(*) FROM public.transactions),
       (SELECT count(*) FROM public.payment_outcomes),
       (SELECT count(*) FROM public.labels),
       (SELECT count(*) FROM public.features),
       (SELECT sum(fraud_label) FROM public.labels),
       (SELECT round(100.0 * avg(fraud_label), 3) FROM public.labels),
       (SELECT min(transaction_time) AT TIME ZONE 'Asia/Kolkata' FROM public.transactions),
       (SELECT max(transaction_time) AT TIME ZONE 'Asia/Kolkata' FROM public.transactions);

-- @result: table_row_counts
SELECT 'customers' AS table_name, count(*) AS row_count FROM public.customers
UNION ALL SELECT 'merchants',        count(*) FROM public.merchants
UNION ALL SELECT 'devices',          count(*) FROM public.devices
UNION ALL SELECT 'transactions',     count(*) FROM public.transactions
UNION ALL SELECT 'payment_outcomes', count(*) FROM public.payment_outcomes
UNION ALL SELECT 'labels',           count(*) FROM public.labels
UNION ALL SELECT 'features',         count(*) FROM public.features;

-- @result: split_consistency
-- The split stored on labels must equal the split of the transaction, and splits
-- must follow the calendar (IST): warmup < 2025-01, train 2025-01..10,
-- validation 2025-11..12, holdout 2026-01..02.
SELECT 'labels.split <> transactions.split' AS check_name, count(*) AS violations
  FROM public.labels l JOIN public.transactions t USING (transaction_id) WHERE l.split <> t.split
UNION ALL
SELECT 'transaction outside its split calendar window', count(*)
  FROM public.transactions t
 WHERE NOT CASE t.split
     WHEN 'warmup'     THEN (t.transaction_time AT TIME ZONE 'Asia/Kolkata') <  '2025-01-01'
     WHEN 'train'      THEN (t.transaction_time AT TIME ZONE 'Asia/Kolkata') >= '2025-01-01' AND (t.transaction_time AT TIME ZONE 'Asia/Kolkata') < '2025-11-01'
     WHEN 'validation' THEN (t.transaction_time AT TIME ZONE 'Asia/Kolkata') >= '2025-11-01' AND (t.transaction_time AT TIME ZONE 'Asia/Kolkata') < '2026-01-01'
     WHEN 'holdout'    THEN (t.transaction_time AT TIME ZONE 'Asia/Kolkata') >= '2026-01-01' AND (t.transaction_time AT TIME ZONE 'Asia/Kolkata') < '2026-03-01'
     ELSE false END
UNION ALL
SELECT 'split value not in (warmup,train,validation,holdout)', count(*)
  FROM (SELECT split FROM public.transactions UNION ALL SELECT split FROM public.labels) x
 WHERE split NOT IN ('warmup','train','validation','holdout');
