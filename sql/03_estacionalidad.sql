-- P3: ¿En qué períodos se concentran las ventas?
-- Nota: el dataset tiene datos muy escasos en 2016 y desde sep-2018;
-- el análisis mensual usa solo meses completos (2017-01 a 2018-08).

-- name: ventas_mensuales
SELECT mes,
       COUNT(DISTINCT order_id) AS pedidos,
       ROUND(SUM(ingreso), 2)   AS ingresos
FROM ventas
WHERE mes BETWEEN '2017-01' AND '2018-08'
GROUP BY mes
ORDER BY mes;

-- name: dia_semana
-- 0 = domingo ... 6 = sábado (convención de SQLite)
SELECT CAST(STRFTIME('%w', fecha_compra) AS INTEGER) AS dia_semana,
       COUNT(DISTINCT order_id)                       AS pedidos,
       ROUND(SUM(ingreso), 2)                         AS ingresos
FROM ventas
GROUP BY dia_semana
ORDER BY dia_semana;

-- name: heatmap_dia_hora
SELECT CAST(STRFTIME('%w', fecha_compra) AS INTEGER) AS dia_semana,
       CAST(STRFTIME('%H', fecha_compra) AS INTEGER) AS hora,
       COUNT(DISTINCT order_id)                       AS pedidos
FROM ventas
GROUP BY dia_semana, hora;

-- name: mejores_dias
SELECT dia,
       COUNT(DISTINCT order_id) AS pedidos,
       ROUND(SUM(ingreso), 2)   AS ingresos
FROM ventas
GROUP BY dia
ORDER BY ingresos DESC
LIMIT 10;
