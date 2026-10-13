"""
Paso 3: genera el dashboard interactivo (docs/index.html).

Ejecuta las consultas SQL de la carpeta sql/, arma un JSON con los resultados
y lo inserta en la plantilla dashboard/plantilla.html. El resultado es una
sola página HTML que se abre con doble clic o se publica en GitHub Pages.
"""
import json
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "olist.db"
PLANTILLA = ROOT / "dashboard" / "plantilla.html"
SALIDA = ROOT / "docs" / "index.html"

# Nombres de categorías en español, para una audiencia no técnica
CATEGORIAS_ES = {
    "health_beauty": "Salud y belleza", "watches_gifts": "Relojes y regalos",
    "bed_bath_table": "Cama, baño y mesa", "sports_leisure": "Deportes y ocio",
    "computers_accessories": "Accesorios de computación", "furniture_decor": "Muebles y decoración",
    "housewares": "Artículos para el hogar", "cool_stuff": "Novedades", "auto": "Automotor",
    "toys": "Juguetes", "garden_tools": "Jardinería", "baby": "Bebés", "perfumery": "Perfumería",
    "telephony": "Telefonía", "office_furniture": "Muebles de oficina", "stationery": "Librería",
    "computers": "Computadoras", "pet_shop": "Mascotas", "musical_instruments": "Instrumentos musicales",
    "small_appliances": "Pequeños electrodomésticos", "unknown": "Sin categoría",
    "electronics": "Electrónica", "fashion_bags_accessories": "Bolsos y accesorios",
    "consoles_games": "Consolas y videojuegos", "construction_tools_construction": "Herramientas de construcción",
    "luggage_accessories": "Valijas y viaje", "home_appliances_2": "Electrodomésticos II",
    "home_construction": "Construcción del hogar", "home_appliances": "Electrodomésticos",
    "agro_industry_and_commerce": "Agro, industria y comercio", "furniture_living_room": "Muebles de living",
    "home_confort": "Confort del hogar", "fixed_telephony": "Telefonía fija",
    "air_conditioning": "Aire acondicionado", "audio": "Audio",
    "small_appliances_home_oven_and_coffee": "Hornos y cafeteras",
    "kitchen_dining_laundry_garden_furniture": "Muebles de cocina y jardín",
    "books_general_interest": "Libros de interés general", "construction_tools_lights": "Iluminación",
    "construction_tools_safety": "Seguridad para obra", "industry_commerce_and_business": "Industria y negocios",
    "food": "Alimentos", "market_place": "Marketplace", "costruction_tools_garden": "Herramientas de jardín",
    "art": "Arte", "fashion_shoes": "Calzado", "drinks": "Bebidas",
    "signaling_and_security": "Señalización y seguridad", "furniture_bedroom": "Muebles de dormitorio",
    "books_technical": "Libros técnicos", "costruction_tools_tools": "Herramientas",
    "food_drink": "Comidas y bebidas", "fashion_male_clothing": "Ropa de hombre",
    "fashion_underwear_beach": "Ropa interior y playa", "christmas_supplies": "Navidad",
    "tablets_printing_image": "Tablets e impresión", "cine_photo": "Cine y foto", "music": "Música",
    "dvds_blu_ray": "DVD y Blu-ray", "party_supplies": "Cotillón", "books_imported": "Libros importados",
    "furniture_mattress_and_upholstery": "Colchones y tapizados",
    "portable_kitchen_food_preparers": "Procesadoras de cocina", "fashio_female_clothing": "Ropa de mujer",
    "fashion_sport": "Ropa deportiva", "la_cuisine": "Cocina gourmet",
    "arts_and_craftmanship": "Artesanías", "diapers_and_hygiene": "Pañales e higiene",
    "pc_gamer": "PC gamer", "flowers": "Flores", "home_comfort_2": "Confort del hogar II",
    "cds_dvds_musicals": "CDs y musicales", "fashion_childrens_clothes": "Ropa infantil",
    "security_and_services": "Seguridad y servicios",
}


def consultas(con: sqlite3.Connection, archivo: str) -> dict[str, pd.DataFrame]:
    texto = (ROOT / "sql" / archivo).read_text(encoding="utf-8")
    bloques = re.split(r"^-- name:\s*(\w+)\s*$", texto, flags=re.M)
    return {n: pd.read_sql_query(s, con) for n, s in zip(bloques[1::2], bloques[2::2])}


def filas(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", force_ascii=False))


def main() -> None:
    con = sqlite3.connect(DB)
    q = {}
    for archivo in [
        "01_mejores_clientes.sql", "02_productos.sql", "03_estacionalidad.sql",
        "04_clientes_inactivos.sql", "05_dashboard.sql",
    ]:
        q.update(consultas(con, archivo))

    cats = q["todas_categorias"].copy()
    cats["nombre"] = cats["categoria"].map(CATEGORIAS_ES).fillna(cats["categoria"].str.replace("_", " "))

    lista = q["lista_recontactar"].head(500).copy()
    lista["id"] = lista["customer_unique_id"].str[:8]

    datos = {
        "kpis": filas(q["kpis"])[0],
        "deciles": filas(q["concentracion_por_decil"]),
        "recurrencia": filas(q["recurrencia"]),
        "top_clientes": filas(q["top_clientes"].head(10).assign(id=lambda d: d.customer_unique_id.str[:8])),
        "estados": filas(q["estados"]),
        "categorias": filas(cats[["nombre", "unidades", "ingresos"]]),
        "rotacion": filas(q["productos_baja_rotacion"]),
        "mensual": filas(q["ventas_mensuales"]),
        "dia_semana": filas(q["dia_semana"]),
        "heatmap": filas(q["heatmap_dia_hora"]),
        "mejores_dias": filas(q["mejores_dias"].head(5)),
        "segmentos": filas(q["segmentos_actividad"]),
        "recontactar": filas(q["ticket_recontactar"])[0],
        "lista": filas(lista[["id", "estado", "ultima_compra", "dias_sin_comprar", "pedidos", "gasto"]]),
    }

    html = PLANTILLA.read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(datos, ensure_ascii=False)
    )
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Dashboard generado en {SALIDA} ({SALIDA.stat().st_size / 1024:.0f} KB)")
    print("Abrilo con doble clic o publicalo con GitHub Pages (carpeta /docs).")


if __name__ == "__main__":
    main()
