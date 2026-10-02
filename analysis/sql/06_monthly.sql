-- 월별 주문 수 (취소 제외)
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month,
       COUNT(DISTINCT o.order_id) AS orders
FROM orders o
WHERE o.order_status <> 'canceled'
  AND o.order_purchase_timestamp >= '2017-01-01' AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY month ORDER BY month;
