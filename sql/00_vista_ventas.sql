-- Vista base del análisis: una fila por ítem vendido.
-- Criterio: solo pedidos ENTREGADOS (se excluyen cancelados, no disponibles, etc.).
-- Ingreso = precio del producto (price), sin flete.
DROP VIEW IF EXISTS ventas;
CREATE VIEW ventas AS
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state                         AS estado,
    o.order_purchase_timestamp               AS fecha_compra,
    DATE(o.order_purchase_timestamp)         AS dia,
    STRFTIME('%Y-%m', o.order_purchase_timestamp) AS mes,
    i.product_id,
    COALESCE(p.category, 'unknown')          AS categoria,
    i.price                                  AS ingreso,
    i.freight_value                          AS flete
FROM orders o
JOIN customers   c ON c.customer_id = o.customer_id
JOIN order_items i ON i.order_id    = o.order_id
LEFT JOIN products p ON p.product_id = i.product_id
WHERE o.order_status = 'delivered';
