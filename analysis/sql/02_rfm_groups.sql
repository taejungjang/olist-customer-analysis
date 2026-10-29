-- 02. 고객을 RFM 기준으로 5개 그룹으로 나누기
--
--   R (Recency)   마지막 구매가 며칠 전인가   -> 최근 / 휴면
--   F (Frequency) 구매한 날이 며칠인가        -> 2번 이상이면 "재구매 고객"
--   M (Monetary)  총 얼마를 썼나              -> 우수 / 일반
--
-- 사용하는 뷰: v_orders (01_base_view.sql)
-- 한 줄 = 고객 1명 (customer_unique_id)
--
-- 순서
--   1) 기준일 정하기
--   2) 고객별로 R, F, M 값 계산
--   3) R, M 을 고객 전체 기준 5등분해서 1~5점 매기기 (5점이 가장 좋음)
--   4) 점수로 5개 그룹 정하기

WITH

-- 1) 기준일: 데이터의 마지막 주문일 + 1일. 이 날짜에서 마지막 구매일을 빼서 "며칠 전"을 구한다.
reference_day AS (
    SELECT DATE(MAX(purchase_ts), '+1 day') AS day
    FROM v_orders
),

-- 2) 고객별 R, F, M 값
customer_values AS (
    SELECT
        customer_unique_id,
        -- R: 기준일 - 마지막 구매 시각 (일 단위, 소수점 버림)
        CAST(julianday((SELECT day FROM reference_day)) - julianday(MAX(purchase_ts)) AS INT) AS recency,
        -- F: 구매한 서로 다른 날의 수 (같은 날 여러 주문은 1번으로 센다)
        COUNT(DISTINCT DATE(purchase_ts)) AS frequency,
        -- M: 주문 금액의 합 (소수 둘째 자리까지)
        ROUND(SUM(order_value), 2) AS monetary
    FROM v_orders
    GROUP BY customer_unique_id
),

-- 3) 점수 매기기
--    NTILE(5) = 줄 세운 순서대로 고객을 5개 칸으로 똑같이 나눠 1~5번을 붙인다.
--    recency 는 작을수록(최근일수록) 좋으므로 6에서 빼서 최근 고객이 5점이 되게 한다.
customer_scores AS (
    SELECT
        *,
        6 - NTILE(5) OVER (ORDER BY recency) AS r_score,
        NTILE(5) OVER (ORDER BY monetary)    AS m_score
    FROM customer_values
)

-- 4) 그룹 정하기: 위에서부터 차례로 검사해서 처음 맞는 그룹에 넣는다.
--    r_score >= 4 : 최근 쪽 상위 40% (마지막 구매 177일 이내)
--    m_score >= 4 : 구매금액 상위 40% (R$110 이상)
SELECT
    *,
    CASE
        WHEN frequency >= 2                 THEN 1   -- 재구매 고객
        WHEN r_score >= 4 AND m_score >= 4  THEN 2   -- 최근 우수
        WHEN r_score >= 4                   THEN 3   -- 최근 일반
        WHEN m_score >= 4                   THEN 4   -- 휴면 우수
        ELSE                                     5   -- 휴면 일반
    END AS grp
FROM customer_scores;
