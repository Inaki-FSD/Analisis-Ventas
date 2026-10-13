-- P2: ¿Qué productos generan más ingresos y cuáles venden poco?

-- name: top_categorias
WITH cat AS (
    SELECT categoria,
           COUNT(*)             AS unidades,
           ROUND(SUM(ingreso),2) AS ingresos
    FROM ventas
    GROUP BY categoria
)
SELECT
    categoria,
    unidades,
    ingresos,
    ROUND(100.0 * ingresos / (SELECT SUM(ingresos) FROM cat), 2)            AS pct_ingresos,
    ROUND(100.0 * SUM(ingresos) OVER (ORDER BY ingresos DESC)
          / (SELECT SUM(ingresos) FROM cat), 2)                              AS pct_acumulado
FROM cat
ORDER BY ingresos DESC
LIMIT 15;

-- name: categorias_bajas
-- Las 10 categorías que menos venden (en ingresos).
SELECT categoria,
       COUNT(*)              AS unidades,
       ROUND(SUM(ingreso),2) AS ingresos
FROM ventas
GROUP BY categoria
ORDER BY ingresos ASC
LIMIT 10;

-- name: top_productos
SELECT product_id,
       categoria,
       COUNT(*)              AS unidades,
       ROUND(SUM(ingreso),2) AS ingresos
FROM ventas
GROUP BY product_id, categoria
ORDER BY ingresos DESC
LIMIT 15;

-- name: productos_baja_rotacion
-- Cuántos productos vendieron una sola unidad en todo el período.
WITH prod AS (
    SELECT product_id, COUNT(*) AS unidades
    FROM ventas
    GROUP BY product_id
)
SELECT
    CASE WHEN unidades = 1 THEN '1 unidad'
         WHEN unidades BETWEEN 2 AND 5 THEN '2-5 unidades'
         WHEN unidades BETWEEN 6 AND 20 THEN '6-20 unidades'
         ELSE 'más de 20' END AS rango_ventas,
    COUNT(*) AS productos,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM prod), 2) AS pct_productos,
    ROUND(SUM(unidades), 0) AS unidades_totales
FROM prod
GROUP BY rango_ventas
ORDER BY MIN(unidades);
