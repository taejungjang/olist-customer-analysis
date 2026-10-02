-- 재구매 고객이 첫 구매 후 며칠 만에 다시 샀는지 (같은 날 추가 주문은 제외)
WITH days AS (
  SELECT customer_unique_id, DATE(purchase_ts) AS d
  FROM v_orders GROUP BY customer_unique_id, DATE(purchase_ts)
),
ranked AS (
  SELECT customer_unique_id, d,
         ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY d) AS rn
  FROM days
)
SELECT a.customer_unique_id,
       CAST(julianday(b.d) - julianday(a.d) AS INT) AS gap_days
FROM ranked a
JOIN ranked b ON a.customer_unique_id = b.customer_unique_id AND a.rn = 1 AND b.rn = 2;
