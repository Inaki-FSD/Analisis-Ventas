-- Consultas extra que alimentan el dashboard (docs/index.html).

-- name: kpis
SELECT
    ROUND(SUM(ingreso), 2)               AS ingresos,
    COUNT(DISTINCT order_id)             AS pedidos,
    COUNT(DISTINCT customer_unique_id)   AS clientes,
    COUNT(DISTINCT product_id)           AS productos,
    COUNT(DISTINCT categoria)            AS categorias,
    ROUND(SUM(ingreso) / COUNT(DISTINCT order_id), 2) AS ticket_promedio,
    MIN(dia)                             AS desde,
    MAX(dia)                             AS hasta
FROM ventas;

-- name: estados
SELECT estado,
       COUNT(DISTINCT customer_unique_id) AS clientes,
       ROUND(SUM(ingreso), 2)             AS ingresos,
       ROUND(100.0 * SUM(ingreso) / (SELECT SUM(ingreso) FROM ventas), 2) AS pct_ingresos
FROM ventas
GROUP BY estado
ORDER BY ingresos DESC;

-- name: todas_categorias
SELECT categoria,
       COUNT(*)              AS unidades,
       ROUND(SUM(ingreso),2) AS ingresos
FROM ventas
GROUP BY categoria
ORDER BY ingresos DESC;

-- name: ticket_recontactar
-- Ticket promedio por pedido de los clientes inactivos valiosos (base del simulador).
WITH ref AS (SELECT MAX(dia) AS hoy FROM ventas),
cli AS (
    SELECT customer_unique_id,
           MAX(dia)                 AS ultima_compra,
           COUNT(DISTINCT order_id) AS pedidos,
           SUM(ingreso)             AS gasto
    FROM ventas
    GROUP BY customer_unique_id
)
SELECT COUNT(*)                              AS clientes,
       ROUND(SUM(gasto), 2)                  AS gasto_historico,
       ROUND(SUM(gasto) / SUM(pedidos), 2)   AS ticket_promedio
FROM cli, ref
WHERE JULIANDAY(ref.hoy) - JULIANDAY(cli.ultima_compra) > 180
  AND (cli.pedidos >= 2 OR cli.gasto >= 300);
