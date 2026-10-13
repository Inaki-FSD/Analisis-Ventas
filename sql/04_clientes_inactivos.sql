-- P4: ¿Qué clientes dejaron de comprar y conviene recontactar?
--
-- Criterios (ajustables):
--   * Fecha de referencia = última compra registrada en el dataset.
--   * Inactivo  = sin compras hace más de 180 días.
--   * Conviene recontactar = inactivo Y (compró 2+ veces  O  gastó >= R$ 300).
--     Es decir: clientes recurrentes o de alto valor que se enfriaron.

-- name: segmentos_actividad
WITH ref AS (SELECT MAX(dia) AS hoy FROM ventas),
cli AS (
    SELECT customer_unique_id,
           MAX(dia)                 AS ultima_compra,
           COUNT(DISTINCT order_id) AS pedidos,
           SUM(ingreso)             AS gasto
    FROM ventas
    GROUP BY customer_unique_id
),
est AS (
    SELECT cli.*,
           CAST(JULIANDAY(ref.hoy) - JULIANDAY(cli.ultima_compra) AS INTEGER) AS dias_sin_comprar
    FROM cli, ref
)
SELECT
    CASE
        WHEN dias_sin_comprar <= 90  THEN '1. Activo (0-90 días)'
        WHEN dias_sin_comprar <= 180 THEN '2. En riesgo (91-180 días)'
        ELSE                              '3. Inactivo (+180 días)'
    END                              AS estado_cliente,
    COUNT(*)                         AS clientes,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM est), 2) AS pct_clientes,
    ROUND(SUM(gasto), 2)             AS gasto_historico
FROM est
GROUP BY estado_cliente
ORDER BY estado_cliente;

-- name: lista_recontactar
WITH ref AS (SELECT MAX(dia) AS hoy FROM ventas),
cli AS (
    SELECT customer_unique_id,
           MAX(estado)              AS estado,
           MAX(dia)                 AS ultima_compra,
           COUNT(DISTINCT order_id) AS pedidos,
           ROUND(SUM(ingreso), 2)   AS gasto
    FROM ventas
    GROUP BY customer_unique_id
)
SELECT
    cli.customer_unique_id,
    cli.estado,
    cli.ultima_compra,
    CAST(JULIANDAY(ref.hoy) - JULIANDAY(cli.ultima_compra) AS INTEGER) AS dias_sin_comprar,
    cli.pedidos,
    cli.gasto
FROM cli, ref
WHERE JULIANDAY(ref.hoy) - JULIANDAY(cli.ultima_compra) > 180
  AND (cli.pedidos >= 2 OR cli.gasto >= 300)
ORDER BY cli.gasto DESC;
