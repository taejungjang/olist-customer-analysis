-- 01. 분석 대상 주문만 모아 둔 "뷰(v_orders)" 만들기
--
-- 뷰 = 이름을 붙여 저장해 둔 조회문. 이후 SQL에서는 orders 표 대신 v_orders 를 쓰면
-- 항상 "배송이 끝난 주문"만 보게 된다.
--
-- 사용하는 표: orders(주문), customers(고객), order_items(주문 상품)
-- 한 줄 = 배송이 끝난 주문 1건

DROP VIEW IF EXISTS v_orders;

CREATE VIEW v_orders AS
SELECT
    o.order_id,
    c.customer_unique_id,                              -- 같은 사람이면 같은 번호 (주문마다 바뀌는 customer_id 와 다름)
    c.customer_state,
    o.order_purchase_timestamp       AS purchase_ts,   -- 주문한 시각
    o.order_delivered_carrier_date   AS carrier_ts,    -- 배송사에 넘긴 시각
    o.order_delivered_customer_date  AS delivered_ts,  -- 고객이 받은 시각
    o.order_estimated_delivery_date  AS estimated_ts,  -- 예상 도착일

    -- 주문 금액 = 그 주문에 담긴 상품 가격의 합 (배송비 제외)
    (SELECT SUM(price)
       FROM order_items AS i
      WHERE i.order_id = o.order_id)  AS order_value,

    -- 배송비 합계
    (SELECT SUM(freight_value)
       FROM order_items AS i
      WHERE i.order_id = o.order_id)  AS freight
FROM orders AS o
JOIN customers AS c
  ON c.customer_id = o.customer_id                     -- 주문 -> 고객 연결
WHERE o.order_status = 'delivered'                     -- 배송 완료된 주문만
  AND o.order_delivered_customer_date IS NOT NULL;     -- 받은 시각이 기록된 주문만
