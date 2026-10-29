-- 04. 재구매 고객은 첫 구매 후 며칠 만에 다시 샀나
--
-- 사용하는 뷰: v_orders (01_base_view.sql)
-- 한 줄 = 서로 다른 날 2번 이상 구매한 고객 1명
-- 같은 날 추가 주문은 "다시 산 것"으로 보지 않는다.
--
-- 순서
--   1) 고객별로 구매한 날짜만 뽑는다 (같은 날은 1번)
--   2) 날짜 순서대로 1번째, 2번째 ... 번호를 붙인다
--   3) 1번째 구매일과 2번째 구매일의 간격(일)을 구한다

WITH

-- 1) 고객별 구매한 날짜 (중복 제거)
purchase_days AS (
    SELECT DISTINCT
        customer_unique_id,
        DATE(purchase_ts) AS purchase_date
    FROM v_orders
),

-- 2) 고객 안에서 날짜가 빠른 순서로 번호 붙이기 (1 = 첫 구매일, 2 = 두 번째 구매일)
numbered_days AS (
    SELECT
        customer_unique_id,
        purchase_date,
        ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_date) AS day_number
    FROM purchase_days
)

-- 3) 같은 고객의 1번째 날짜와 2번째 날짜를 한 줄에 놓고 간격 계산
SELECT
    first_day.customer_unique_id,
    CAST(julianday(second_day.purchase_date) - julianday(first_day.purchase_date) AS INT) AS gap_days
FROM numbered_days AS first_day
JOIN numbered_days AS second_day
  ON  second_day.customer_unique_id = first_day.customer_unique_id
  AND first_day.day_number  = 1
  AND second_day.day_number = 2;
