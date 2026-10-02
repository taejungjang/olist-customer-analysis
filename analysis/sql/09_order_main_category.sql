-- 주문별 대표 상품군 (주문에서 가장 비싼 상품의 상품군)
SELECT order_id, category
FROM (
  SELECT i.order_id, t.product_category_name_english AS category,
         ROW_NUMBER() OVER (PARTITION BY i.order_id ORDER BY i.price DESC) AS r
  FROM order_items i
  JOIN products p ON p.product_id = i.product_id
  JOIN category_translation t ON t.product_category_name = p.product_category_name
)
WHERE r = 1;
