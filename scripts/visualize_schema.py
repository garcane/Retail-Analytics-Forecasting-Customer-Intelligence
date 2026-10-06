"""Draw the star schema in warehouse.duckdb as a NetworkX graph (the "model view").

Nodes are the fact and dimension tables; each edge is a fact -> dimension relationship read from the
foreign keys in DuckDB's catalog, so the picture is generated from the real DDL and cannot drift from it.
An edge labelled xN means the fact references that dimension N times (role-playing, e.g. 5 date roles).

    uv run python src/transformation/build_warehouse.py     # build the warehouse first
    uv run python scripts/visualize_schema.py [--db warehouse.duckdb] [--out docs/data/star_schema.png]
"""

import argparse
import sys
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]

# Facts in a row in the middle, dimensions above and below. Tables not listed fall back to a spring layout.
POSITIONS = {
    "fact_payments": (-4.6, 0.0),
    "fact_orders": (-1.6, 0.0),
    "fact_order_items": (1.6, 0.0),
    "fact_reviews": (4.6, 0.0),
    "dim_date": (0.0, 3.3),
    "dim_geography": (-4.2, 2.6),
    "dim_product": (3.0, 2.6),
    "dim_seller": (6.2, 2.6),
    "dim_customer": (0.0, -3.3),
}

SURFACE, TEXT, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"
FACT_FILL, FACT_EDGE = "#d6e6fa", "#2a78d6"   # blue family: facts
DIM_FILL, DIM_EDGE = "#fde3d6", "#eb6834"     # orange family: dimensions


def load_graph(db: Path) -> nx.DiGraph:
    con = duckdb.connect(str(db), read_only=True)
    tables = [t for (t,) in con.execute("select table_name from duckdb_tables() order by 1").fetchall()
              if t.startswith(("dim_", "fact_"))]
    pks = dict(con.execute(
        "select table_name, constraint_column_names from duckdb_constraints() where constraint_type = 'PRIMARY KEY'"
    ).fetchall())

    g = nx.DiGraph()
    for t in tables:
        rows = con.execute(f"select count(*) from {t}").fetchone()[0]
        g.add_node(t, kind="fact" if t.startswith("fact_") else "dim", rows=rows, pk=pks.get(t, []))
    for table, cols, ref in con.execute(
        "select table_name, constraint_column_names, referenced_table "
        "from duckdb_constraints() where constraint_type = 'FOREIGN KEY'"
    ).fetchall():
        if g.has_edge(table, ref):
            g[table][ref]["columns"].extend(cols)
        else:
            g.add_edge(table, ref, columns=list(cols))
    con.close()
    return g


def node_label(g: nx.DiGraph, node: str) -> str:
    pk = ", ".join(g.nodes[node]["pk"])
    return f"{node}\nPK: {pk}\n{g.nodes[node]['rows']:,} rows"


def draw(g: nx.DiGraph, out: Path) -> None:
    missing = [n for n in g if n not in POSITIONS]
    pos = {n: POSITIONS[n] for n in g if n in POSITIONS}
    if missing:  # a new table was added to the warehouse but not to POSITIONS above
        pos.update(nx.spring_layout(g, seed=7))

    fig, ax = plt.subplots(figsize=(15, 8.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_axis_off()

    # Table boxes: networkx draws each node as a text label with a box around it.
    texts = {}
    for kind, fill, edge in (("fact", FACT_FILL, FACT_EDGE), ("dim", DIM_FILL, DIM_EDGE)):
        nodes = [n for n, d in g.nodes(data=True) if d["kind"] == kind]
        texts.update(nx.draw_networkx_labels(
            g, pos, labels={n: node_label(g, n) for n in nodes}, ax=ax, font_size=9, font_color=TEXT,
            bbox=dict(boxstyle="round,pad=0.55", fc=fill, ec=edge, lw=1.6),
        ))
    xs, ys = zip(*pos.values())
    ax.set_xlim(min(xs) - 2.3, max(xs) + 2.3)  # explicit limits: a tight crop mis-measures annotation arrows
    ax.set_ylim(min(ys) - 1.0, max(ys) + 1.0)
    fig.canvas.draw()  # lets matplotlib size each text box before arrows are clipped to it

    # Edges: arrows run between the points where the centre-to-centre line crosses each box border.
    def border_point(node: str, toward: tuple[float, float]) -> tuple[float, float]:
        box = texts[node].get_bbox_patch().get_window_extent()
        cx, cy = (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2
        dx, dy = toward[0] - cx, toward[1] - cy
        t = min((box.x1 - box.x0) / 2 / abs(dx) if dx else float("inf"),
                (box.y1 - box.y0) / 2 / abs(dy) if dy else float("inf"))
        return cx + dx * t, cy + dy * t

    to_display, to_data = ax.transData.transform, ax.transData.inverted().transform
    for u, v, data in g.edges(data=True):
        du, dv = to_display(pos[u]), to_display(pos[v])
        start, end = to_data(border_point(u, dv)), to_data(border_point(v, du))
        ax.annotate(
            "", xy=end, xytext=start, zorder=2.5,
            arrowprops=dict(arrowstyle="-|>", color=MUTED, alpha=0.7, lw=1.3, mutation_scale=15,
                            shrinkA=0, shrinkB=1),
        )
        if len(data["columns"]) > 1:  # role-playing: several foreign keys to the same dimension
            (x1, y1), (x2, y2) = pos[u], pos[v]
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"x{len(data['columns'])}", ha="center", va="center",
                    fontsize=9, color=MUTED, zorder=4, bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none"))

    handles = [
        plt.Line2D([], [], marker="s", ls="", ms=11, mfc=FACT_FILL, mec=FACT_EDGE, mew=1.6, label="fact table"),
        plt.Line2D([], [], marker="s", ls="", ms=11, mfc=DIM_FILL, mec=DIM_EDGE, mew=1.6, label="dimension table"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, labelcolor=TEXT)
    ax.set_title(
        "Olist star schema: facts reference dimensions, never each other  (xN = N foreign keys to the same dimension)",
        loc="left", fontsize=11, fontweight="bold", color=TEXT,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=125, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "data" / "star_schema.png")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"{args.db} not found - run src/transformation/build_warehouse.py first", file=sys.stderr)
        return 1
    g = load_graph(args.db)
    draw(g, args.out)
    print(f"{g.number_of_nodes()} tables, {g.number_of_edges()} fact->dimension relationships -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
