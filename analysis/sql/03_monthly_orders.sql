-- 03. 월별 주문 수 (현황 파악용)
--
-- 사용하는 표: orders (v_orders 가 아니라 원본 주문 표. 아직 배송 전인 주문도 월별 흐름에는 포함)
-- 한 줄 = 한 달
-- 기간: 2017-01 ~ 2018-08 (이후 달은 데이터가 불완전해서 제외)

SELECT
    strftime('%Y-%m', order_purchase_timestamp) AS month,      -- 예: 2018-03
    COUNT(DISTINCT order_id)                    AS orders      -- 그 달 주문 수
FROM orders
WHERE order_status <> 'canceled'                               -- 취소된 주문 제외
  AND order_purchase_timestamp >= '2017-01-01'
  AND order_purchase_timestamp <  '2018-09-01'
GROUP BY month
ORDER BY month;
