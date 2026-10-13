"""
Paso 2: ejecuta las consultas SQL (carpeta sql/), guarda las tablas en
outputs/tables/ y genera los gráficos en outputs/figures/.
"""
import re
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "olist.db"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

AZUL, NARANJA, GRIS, ROJO = "#2b6cb0", "#dd6b20", "#a0aec0", "#c53030"
plt.rcParams.update(
    {
        "figure.dpi": 130,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "font.size": 10,
    }
)


def ejecutar_sql(con: sqlite3.Connection, archivo: str) -> dict[str, pd.DataFrame]:
    """Ejecuta cada bloque '-- name: xxx' de un archivo .sql y devuelve DataFrames."""
    texto = (ROOT / "sql" / archivo).read_text(encoding="utf-8")
    bloques = re.split(r"^-- name:\s*(\w+)\s*$", texto, flags=re.M)
    out = {}
    for nombre, sql in zip(bloques[1::2], bloques[2::2]):
        df = pd.read_sql_query(sql, con)
        df.to_csv(TABLES / f"{nombre}.csv", index=False)
        out[nombre] = df
    return out


def r(x: float) -> str:
    return f"R$ {x:,.0f}"


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(FIGS / nombre, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    con = sqlite3.connect(DB)
    total = con.execute("SELECT SUM(ingreso) FROM ventas").fetchone()[0]
    n_cli = con.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM ventas").fetchone()[0]
    n_ped = con.execute("SELECT COUNT(DISTINCT order_id) FROM ventas").fetchone()[0]
    print(f"Ingresos totales: {r(total)} | clientes: {n_cli:,} | pedidos: {n_ped:,}")

    # ------------------------------------------------------------------ P1
    p1 = ejecutar_sql(con, "01_mejores_clientes.sql")
    top = p1["top_clientes"]
    dec = p1["concentracion_por_decil"]
    rec = p1["recurrencia"]
    print("\n[P1] Top 20 clientes aportan:", f"{top.pct_del_total.sum():.2f}% del total")
    print(dec.to_string(index=False))
    print(rec.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axes[0]
    ax.bar(dec["decil"].astype(str), dec["pct_ingresos"], color=[AZUL] + [GRIS] * 9)
    for x, v in zip(dec["decil"].astype(str), dec["pct_ingresos"]):
        ax.text(x, v + 0.3, f"{v:.0f}%", ha="center", fontsize=9)
    ax.set_title("Aporte a los ingresos por decil de clientes")
    ax.set_xlabel("Decil de clientes (1 = el 10% que más gasta)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax = axes[1]
    ax.barh(rec["segmento"][::-1], rec["pct_clientes"][::-1], color=GRIS, label="% de clientes")
    ax.barh(rec["segmento"][::-1], rec["pct_ingresos"][::-1], color=NARANJA, height=0.4, label="% de ingresos")
    ax.set_title("Clientes únicos vs. recurrentes")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(frameon=False)
    guardar(fig, "01_clientes_concentracion.png")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    t = top.head(10).iloc[::-1]
    etiquetas = [f"{c[:8]}… ({e})" for c, e in zip(t.customer_unique_id, t.estado)]
    ax.barh(etiquetas, t.gasto_total, color=AZUL)
    for y, (g, p) in enumerate(zip(t.gasto_total, t.pct_del_total)):
        ax.text(g, y, f"  {r(g)} ({p:.2f}%)", va="center", fontsize=9)
    ax.set_title("Top 10 clientes por gasto total")
    ax.set_xlim(0, t.gasto_total.max() * 1.3)
    guardar(fig, "02_top10_clientes.png")

    # ------------------------------------------------------------------ P2
    p2 = ejecutar_sql(con, "02_productos.sql")
    cat, bajas, rot = p2["top_categorias"], p2["categorias_bajas"], p2["productos_baja_rotacion"]
    print("\n[P2] Top categorías:\n", cat.head(8).to_string(index=False))
    print(bajas.to_string(index=False))
    print(rot.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    c10 = cat.head(10).iloc[::-1]
    axes[0].barh(c10.categoria, c10.ingresos / 1e3, color=AZUL)
    for y, (v, p) in enumerate(zip(c10.ingresos / 1e3, c10.pct_ingresos)):
        axes[0].text(v, y, f" {v:,.0f}k ({p:.1f}%)", va="center", fontsize=9)
    axes[0].set_title("Top 10 categorías por ingresos")
    axes[0].set_xlabel("Ingresos (miles de R$)")
    axes[0].set_xlim(0, (c10.ingresos / 1e3).max() * 1.3)
    b = bajas.iloc[::-1]
    axes[1].barh(b.categoria, b.ingresos, color=ROJO)
    for y, (v, u) in enumerate(zip(b.ingresos, b.unidades)):
        axes[1].text(v, y, f" {r(v)} ({u} u.)", va="center", fontsize=9)
    axes[1].set_title("10 categorías que menos venden")
    axes[1].set_xlabel("Ingresos (R$)")
    axes[1].set_xlim(0, b.ingresos.max() * 1.45)
    guardar(fig, "03_categorias.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(rot.rango_ventas, rot.pct_productos, color=[ROJO, NARANJA, GRIS, AZUL])
    for x, v, n in zip(rot.rango_ventas, rot.pct_productos, rot.productos):
        ax.text(x, v + 0.5, f"{v:.0f}%\n({n:,})", ha="center", fontsize=9)
    ax.set_title("Productos según unidades vendidas en todo el período")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, rot.pct_productos.max() * 1.2)
    guardar(fig, "04_baja_rotacion.png")

    # ------------------------------------------------------------------ P3
    p3 = ejecutar_sql(con, "03_estacionalidad.sql")
    mens, dsem, heat, dias = p3["ventas_mensuales"], p3["dia_semana"], p3["heatmap_dia_hora"], p3["mejores_dias"]
    print("\n[P3] Mejores días:\n", dias.head(5).to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(mens.mes, mens.ingresos / 1e3, marker="o", color=AZUL, lw=2)
    imax = mens.ingresos.idxmax()
    ax.annotate(
        f"Pico: {mens.mes[imax]}\n{r(mens.ingresos[imax])}\n(Black Friday)",
        (imax, mens.ingresos[imax] / 1e3),
        xytext=(imax - 6, mens.ingresos[imax] / 1e3 * 0.9),
        arrowprops=dict(arrowstyle="->", color=NARANJA),
        color=NARANJA,
        fontsize=9,
    )
    ax.set_title("Ingresos mensuales (pedidos entregados)")
    ax.set_ylabel("Miles de R$")
    ax.set_xticks(range(len(mens)))
    ax.set_xticklabels(mens.mes, rotation=60, ha="right")
    ax.set_ylim(0)
    guardar(fig, "05_ventas_mensuales.png")

    nombres = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1, 1.6]})
    pico = dsem.pedidos.idxmax()
    axes[0].bar(
        [nombres[d] for d in dsem.dia_semana],
        dsem.pedidos,
        color=[NARANJA if i == pico else GRIS for i in range(7)],
    )
    axes[0].set_title("Pedidos por día de la semana")
    mat = heat.pivot(index="dia_semana", columns="hora", values="pedidos").reindex(index=range(7), columns=range(24)).fillna(0)
    im = axes[1].imshow(mat.values, aspect="auto", cmap="Blues")
    axes[1].set_yticks(range(7))
    axes[1].set_yticklabels(nombres)
    axes[1].set_xticks(range(0, 24, 2))
    axes[1].set_xlabel("Hora del día")
    axes[1].set_title("Pedidos por día y hora")
    axes[1].spines[:].set_visible(False)
    fig.colorbar(im, ax=axes[1], label="Pedidos")
    guardar(fig, "06_dia_hora.png")

    # ------------------------------------------------------------------ P4
    p4 = ejecutar_sql(con, "04_clientes_inactivos.sql")
    seg, lista = p4["segmentos_actividad"], p4["lista_recontactar"]
    print("\n[P4]\n", seg.to_string(index=False))
    print(f"Clientes a recontactar: {len(lista):,} | gasto histórico {r(lista.gasto.sum())}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    cols = [AZUL, NARANJA, ROJO]
    axes[0].pie(
        seg.clientes,
        labels=[s.split(". ")[1] for s in seg.estado_cliente],
        autopct="%1.0f%%",
        colors=cols,
        startangle=90,
        wedgeprops=dict(width=0.45),
    )
    axes[0].set_title("Clientes según última compra")
    lr = lista.copy()
    lr["motivo"] = np.where(lr.pedidos >= 2, "Recurrente (2+ pedidos)", "Alto valor (≥ R$ 300)")
    cnt = lr.groupby("motivo").agg(clientes=("customer_unique_id", "count"), gasto=("gasto", "sum"))
    axes[1].bar(cnt.index, cnt.clientes, color=[NARANJA, AZUL])
    for x, (c, g) in zip(cnt.index, zip(cnt.clientes, cnt.gasto)):
        axes[1].text(x, c, f"{c:,}\n(gasto hist. {r(g)})", ha="center", va="bottom", fontsize=9)
    axes[1].set_ylim(0, cnt.clientes.max() * 1.25)
    axes[1].set_title(f"A recontactar: {len(lista):,} clientes inactivos valiosos")
    guardar(fig, "07_clientes_inactivos.png")

    # La lista completa es larga: se guardan los 500 clientes prioritarios
    lista.head(500).to_csv(TABLES / "lista_recontactar_top500.csv", index=False)
    (TABLES / "lista_recontactar.csv").unlink(missing_ok=True)
    print("\nListo. Gráficos en outputs/figures/, tablas en outputs/tables/")


if __name__ == "__main__":
    main()
