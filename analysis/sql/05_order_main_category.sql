-- 05. 주문별 "대표 상품군" 정하기
--
-- 한 주문에 상품이 여러 개 담길 수 있어서, 주문의 상품군을 하나로 정해야 한다.
-- 규칙: 그 주문에서 가장 비싼 상품의 상품군을 주문의 상품군으로 본다.
--
-- 사용하는 표: order_items(주문 상품), products(상품), category_translation(상품군 영어 이름)
-- 한 줄 = 주문 1건 (상품군을 알 수 없는 주문은 빠진다)

SELECT
    order_id,
    category
FROM (
    SELECT
        i.order_id,
        t.product_category_name_english AS category,
        -- 같은 주문 안에서 가격이 높은 순서대로 1, 2, 3 ... 번호 붙이기
        ROW_NUMBER() OVER (PARTITION BY i.order_id ORDER BY i.price DESC) AS price_rank
    FROM order_items AS i
    JOIN products AS p
      ON p.product_id = i.product_id
    JOIN category_translation AS t
      ON t.product_category_name = p.product_category_name
)
WHERE price_rank = 1;                                   -- 가장 비싼 상품 1개만 남긴다
