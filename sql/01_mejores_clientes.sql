-- P1: ¿Quiénes son los mejores clientes y cuánto aportan al total?
-- Un cliente = customer_unique_id (customer_id cambia en cada pedido).

-- name: top_clientes
WITH por_cliente AS (
    SELECT
        customer_unique_id,
        estado,
        COUNT(DISTINCT order_id) AS pedidos,
        ROUND(SUM(ingreso), 2)   AS gasto_total
    FROM ventas
    GROUP BY customer_unique_id
),
total AS (SELECT SUM(gasto_total) AS t FROM por_cliente)
SELECT
    customer_unique_id,
    estado,
    pedidos,
    gasto_total,
    ROUND(100.0 * gasto_total / total.t, 3) AS pct_del_total
FROM por_cliente, total
ORDER BY gasto_total DESC
LIMIT 20;

-- name: concentracion_por_decil
-- ¿Qué parte de los ingresos aporta cada 10% de clientes (decil 1 = los mejores)?
WITH por_cliente AS (
    SELECT customer_unique_id, SUM(ingreso) AS gasto
    FROM ventas
    GROUP BY customer_unique_id
),
deciles AS (
    SELECT gasto, NTILE(10) OVER (ORDER BY gasto DESC) AS decil
    FROM por_cliente
)
SELECT
    decil,
    COUNT(*)                                              AS clientes,
    ROUND(SUM(gasto), 2)                                  AS ingresos,
    ROUND(100.0 * SUM(gasto) / (SELECT SUM(gasto) FROM por_cliente), 2) AS pct_ingresos
FROM deciles
GROUP BY decil
ORDER BY decil;

-- name: recurrencia
-- ¿Cuántos clientes compran una sola vez vs. repiten?
WITH por_cliente AS (
    SELECT customer_unique_id,
           COUNT(DISTINCT order_id) AS pedidos,
           SUM(ingreso)             AS gasto
    FROM ventas
    GROUP BY customer_unique_id
)
SELECT
    CASE WHEN pedidos = 1 THEN '1 pedido'
         WHEN pedidos = 2 THEN '2 pedidos'
         ELSE '3+ pedidos' END                 AS segmento,
    COUNT(*)                                   AS clientes,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM por_cliente), 2) AS pct_clientes,
    ROUND(SUM(gasto), 2)                       AS ingresos,
    ROUND(100.0 * SUM(gasto) / (SELECT SUM(gasto) FROM por_cliente), 2) AS pct_ingresos
FROM por_cliente
GROUP BY segmento
ORDER BY MIN(pedidos);
