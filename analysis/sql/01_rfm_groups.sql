-- RFM 고객 그룹: 최근성(R), 구매 횟수(F), 구매 금액(M)
-- R, M은 고객 전체를 5등분한 점수(5점이 가장 좋음). F는 서로 다른 날 2번 이상 구매하면 재구매 고객.
WITH snap AS (
  SELECT DATE(MAX(purchase_ts), '+1 day') AS d FROM v_orders
),
base AS (
  SELECT customer_unique_id,
         CAST(julianday((SELECT d FROM snap)) - julianday(MAX(purchase_ts)) AS INT) AS recency,
         COUNT(DISTINCT DATE(purchase_ts)) AS frequency,  -- 같은 날 추가 주문은 한 번으로 셈
         ROUND(SUM(order_value),2) AS monetary
  FROM v_orders
  GROUP BY customer_unique_id
),
scored AS (
  SELECT *,
         6 - NTILE(5) OVER (ORDER BY recency) AS r_score,
         NTILE(5) OVER (ORDER BY monetary)    AS m_score
  FROM base
)
SELECT *,
  CASE
    WHEN frequency >= 2                  THEN 1   -- 재구매 고객
    WHEN r_score >= 4 AND m_score >= 4   THEN 2   -- 최근 고액
    WHEN r_score >= 4                    THEN 3   -- 최근 소액
    WHEN m_score >= 4                    THEN 4   -- 이탈 고액
    ELSE 5                                        -- 이탈 소액
  END AS grp
FROM scored;
