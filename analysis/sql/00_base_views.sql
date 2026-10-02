-- 분석 기준 뷰: 배송 완료 주문 + 고객/배송 지표
DROP VIEW IF EXISTS v_orders;
CREATE VIEW v_orders AS
SELECT o.order_id,
       c.customer_unique_id,
       c.customer_state,
       o.order_purchase_timestamp                      AS purchase_ts,
       o.order_delivered_carrier_date                  AS carrier_ts,
       o.order_delivered_customer_date                 AS delivered_ts,
       o.order_estimated_delivery_date                 AS estimated_ts,
       (SELECT SUM(price) FROM order_items i WHERE i.order_id = o.order_id)         AS order_value,
       (SELECT SUM(freight_value) FROM order_items i WHERE i.order_id = o.order_id) AS freight
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;
