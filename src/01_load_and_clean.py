"""
Paso 1: limpieza con pandas y carga a una base SQLite.

Lee los CSV de Olist desde data/raw/, los limpia y los guarda como tablas
en data/olist.db, que luego se consulta con SQL (carpeta sql/).
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "olist.db"


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(RAW / nombre)


def main() -> None:
    customers = leer("olist_customers_dataset.csv")
    orders = leer("olist_orders_dataset.csv")
    items = leer("olist_order_items_dataset.csv")
    payments = leer("olist_order_payments_dataset.csv")
    products = leer("olist_products_dataset.csv")
    trans = leer("product_category_name_translation.csv")

    # --- Pedidos: fechas como datetime y duplicados fuera
    cols_fecha = [c for c in orders.columns if c.endswith(("_at", "_date", "_timestamp"))]
    for c in cols_fecha:
        orders[c] = pd.to_datetime(orders[c])
    antes = len(orders)
    orders = orders.drop_duplicates("order_id")
    print(f"Pedidos: {antes} -> {len(orders)} (duplicados eliminados: {antes - len(orders)})")

    # --- Productos: categoria en ingles; faltantes -> 'unknown'
    # (se agregan al diccionario dos categorias que no estan en el CSV de traduccion)
    extra = pd.DataFrame(
        {
            "product_category_name": ["pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"],
            "product_category_name_english": ["pc_gamer", "portable_kitchen_food_preparers"],
        }
    )
    trans = pd.concat([trans, extra], ignore_index=True)
    products = products.merge(trans, on="product_category_name", how="left")
    products["category"] = products["product_category_name_english"].fillna("unknown")
    products = products[["product_id", "category"]]

    # --- Items: tipos numericos y sin valores negativos
    items["price"] = items["price"].astype(float)
    items["freight_value"] = items["freight_value"].astype(float)
    items = items[(items["price"] > 0) & (items["freight_value"] >= 0)]

    # --- Clientes: customer_id cambia por pedido; customer_unique_id identifica a la persona
    customers = customers.drop_duplicates("customer_id")

    # --- Carga a SQLite
    if DB.exists():
        DB.unlink()
    with sqlite3.connect(DB) as con:
        customers.to_sql("customers", con, index=False)
        orders.to_sql("orders", con, index=False)
        items.to_sql("order_items", con, index=False)
        payments.to_sql("order_payments", con, index=False)
        products.to_sql("products", con, index=False)
        con.execute("CREATE INDEX idx_orders_cust ON orders(customer_id)")
        con.execute("CREATE INDEX idx_items_order ON order_items(order_id)")
        con.execute("CREATE INDEX idx_items_prod ON order_items(product_id)")
        # Vista base: una fila por item vendido, solo pedidos entregados
        con.executescript((ROOT / "sql" / "00_vista_ventas.sql").read_text(encoding="utf-8"))
        n = con.execute("SELECT COUNT(*), ROUND(SUM(ingreso),2) FROM ventas").fetchone()
        print(f"Vista 'ventas': {n[0]} items, ingresos totales R$ {n[1]:,.2f}")
    print(f"Base creada en {DB}")


if __name__ == "__main__":
    main()
