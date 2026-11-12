-- =============================================================================
-- 05  Outliers in amount (amount_paise; 100 paise = 1 INR)
-- Three lenses:
--   * Tukey fences on the raw amount (Q1 - 1.5 IQR, Q3 + 1.5 IQR) and extreme (3 IQR)
--   * Tukey fences on log10(amount): amounts are right-skewed, so this is the fairer test
--   * Robust z-score per merchant_category: |log amount - median| / (1.4826 * MAD) > 3.5
-- =============================================================================

-- @result: amount_distribution_per_split
SELECT split, count(*) AS rows,
       min(amount_paise) / 100.0                                                  AS min_inr,
       percentile_cont(0.01) WITHIN GROUP (ORDER BY amount_paise) / 100.0         AS p01_inr,
       percentile_cont(0.25) WITHIN GROUP (ORDER BY amount_paise) / 100.0         AS p25_inr,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY amount_paise) / 100.0         AS median_inr,
       round(avg(amount_paise) / 100.0, 2)                                        AS mean_inr,
       percentile_cont(0.75) WITHIN GROUP (ORDER BY amount_paise) / 100.0         AS p75_inr,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY amount_paise) / 100.0         AS p99_inr,
       max(amount_paise) / 100.0                                                  AS max_inr
FROM public.transactions
GROUP BY ROLLUP (split)
ORDER BY min(transaction_time) NULLS LAST;

-- @result: amount_outliers_iqr
WITH q AS (
  SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY amount_paise)              AS q1,
         percentile_cont(0.75) WITHIN GROUP (ORDER BY amount_paise)              AS q3,
         percentile_cont(0.25) WITHIN GROUP (ORDER BY log(amount_paise::numeric)) AS lq1,
         percentile_cont(0.75) WITHIN GROUP (ORDER BY log(amount_paise::numeric)) AS lq3
  FROM public.transactions)
SELECT t.split,
       count(*) AS rows,
       count(*) FILTER (WHERE t.amount_paise > q.q3 + 1.5 * (q.q3 - q.q1))                     AS raw_high_1_5iqr,
       count(*) FILTER (WHERE t.amount_paise > q.q3 + 3.0 * (q.q3 - q.q1))                     AS raw_high_3iqr,
       count(*) FILTER (WHERE log(t.amount_paise::numeric) > q.lq3 + 1.5 * (q.lq3 - q.lq1))    AS log_high_1_5iqr,
       count(*) FILTER (WHERE log(t.amount_paise::numeric) < q.lq1 - 1.5 * (q.lq3 - q.lq1))    AS log_low_1_5iqr,
       count(*) FILTER (WHERE log(t.amount_paise::numeric) > q.lq3 + 3.0 * (q.lq3 - q.lq1))    AS log_high_3iqr,
       round(((q.q3 + 1.5 * (q.q3 - q.q1)) / 100.0)::numeric, 2)                  AS raw_upper_fence_inr,
       round((power(10, q.lq3 + 1.5 * (q.lq3 - q.lq1)) / 100.0)::numeric, 2) AS log_upper_fence_inr,
       round((power(10, q.lq3 + 3.0 * (q.lq3 - q.lq1)) / 100.0)::numeric, 2) AS log_extreme_fence_inr
FROM public.transactions t CROSS JOIN q
GROUP BY ROLLUP (t.split), q.q1, q.q3, q.lq1, q.lq3
ORDER BY min(t.transaction_time) NULLS LAST;

-- @result: amount_outliers_by_category
-- Robust z on log10(amount) within each merchant category.
WITH l AS (SELECT merchant_category, log(amount_paise::numeric)::float8 AS la FROM public.transactions),
     med AS (SELECT merchant_category, percentile_cont(0.5) WITHIN GROUP (ORDER BY la) AS m FROM l GROUP BY 1),
     mad AS (SELECT l.merchant_category, percentile_cont(0.5) WITHIN GROUP (ORDER BY abs(l.la - med.m)) AS mad
               FROM l JOIN med USING (merchant_category) GROUP BY 1)
SELECT l.merchant_category,
       count(*)                                                                      AS rows,
       round((power(10, med.m) / 100)::numeric, 2)                                   AS median_inr,
       count(*) FILTER (WHERE abs(l.la - med.m) / nullif(1.4826 * mad.mad, 0) > 3.5) AS robust_z_outliers,
       round(100.0 * count(*) FILTER (WHERE abs(l.la - med.m) / nullif(1.4826 * mad.mad, 0) > 3.5) / count(*), 3) AS outlier_pct,
       round((power(10, max(l.la)) / 100)::numeric, 2)                               AS max_inr
FROM l JOIN med USING (merchant_category) JOIN mad USING (merchant_category)
GROUP BY l.merchant_category, med.m, mad.mad
ORDER BY outlier_pct DESC;

-- @result: top_amounts
-- The 15 largest amounts with context: are they fraud? how far above the customer's normal?
SELECT t.transaction_id, t.split, t.customer_id, t.merchant_category, t.payment_channel,
       t.amount_paise / 100.0                 AS amount_inr,
       t.average_transaction_value            AS customer_avg_inr,
       f.amount_to_avg_ratio,
       l.fraud_label
FROM public.transactions t
LEFT JOIN public.features f USING (transaction_id)
LEFT JOIN public.labels   l USING (transaction_id)
ORDER BY t.amount_paise DESC
LIMIT 15;

-- @result: outlier_fraud_rate
-- Are log-scale amount outliers more likely to be fraud? (tells you whether to keep them)
WITH q AS (SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY log(amount_paise::numeric)) lq1,
                  percentile_cont(0.75) WITHIN GROUP (ORDER BY log(amount_paise::numeric)) lq3 FROM public.transactions)
SELECT CASE WHEN log(t.amount_paise::numeric) > q.lq3 + 1.5 * (q.lq3 - q.lq1) THEN 'high outlier (log IQR)'
            WHEN log(t.amount_paise::numeric) < q.lq1 - 1.5 * (q.lq3 - q.lq1) THEN 'low outlier (log IQR)'
            ELSE 'normal' END                AS amount_group,
       count(*)                              AS rows,
       sum(l.fraud_label)                    AS fraud,
       round(100.0 * avg(l.fraud_label), 3)  AS fraud_pct
FROM public.transactions t JOIN public.labels l USING (transaction_id) CROSS JOIN q
GROUP BY 1 ORDER BY 1;
