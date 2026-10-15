"""Run the analytics queries in sql/analytics/, save each result as CSV, and draw the figures used in the insights doc.

    uv run python src/analytics/run_analytics.py [--db warehouse.duckdb]

Tables go to reports/analytics/*.csv and figures to docs/analytics/figures/*.png. The database is opened read-only.
"""

import argparse
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "analytics"
TABLES = ROOT / "reports" / "analytics"
FIGURES = ROOT / "docs" / "analytics" / "figures"

# Reference palette (light surface). One accent per message; grey for context. Text uses ink, never a series colour.
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3de"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#b9b8b1"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "lines.linewidth": 2, "figure.dpi": 100,
})


def run_queries(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    TABLES.mkdir(parents=True, exist_ok=True)
    out = {}
    for path in sorted(SQL_DIR.glob("*.sql")):
        df = con.execute(path.read_text(encoding="utf-8")).df()
        df.to_csv(TABLES / f"{path.stem}.csv", index=False)
        out[path.stem] = df
    return out


def save(fig, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_monthly(df: pd.DataFrame) -> None:
    d = df[~df["thin_month"]].copy()
    d["month"] = pd.to_datetime(d["year_month"] + "-01")
    fig, (a, b) = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    a.bar(d["month"], d["net_revenue"] / 1e6, width=20, color=BLUE)
    a.set_title("Net revenue per month (R$ millions)")
    peak = d.loc[d["net_revenue"].idxmax()]
    a.set_ylim(0, d["net_revenue"].max() / 1e6 * 1.15)
    a.annotate(f"{peak['year_month']}: R$ {peak['net_revenue'] / 1e6:.2f}M", (peak["month"], peak["net_revenue"] / 1e6),
               xytext=(0, 5), textcoords="offset points", ha="center", color=INK, fontsize=9)
    a.set_ylabel("R$ millions")
    b.plot(d["month"], d["avg_order_value"], color=BLUE, marker="o", markersize=4)
    b.set_title("Average order value (R$)")
    b.set_ylim(0, d["avg_order_value"].max() * 1.25)
    b.set_ylabel("R$")
    fig.text(0.01, -0.01, "Months with fewer than 500 orders (2016 and 2018-09 onward) are left out. Net of canceled and unavailable orders.",
             fontsize=8, color=INK_2)
    fig.tight_layout()
    save(fig, "monthly_kpis")


def fig_categories(df: pd.DataFrame) -> None:
    d = df.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.barh(d["category"], d["net_revenue"] / 1e6, color=BLUE, height=0.62)
    for y, (rev, share) in enumerate(zip(d["net_revenue"] / 1e6, d["revenue_share_pct"])):
        ax.text(rev + 0.01, y, f"{rev:.2f}M  ({share:.1f}%)", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, d["net_revenue"].max() / 1e6 * 1.28)
    ax.set_title("Top 12 categories by net revenue (R$ millions, share of total)")
    ax.grid(axis="y", visible=False)
    top12 = df.head(12)["revenue_share_pct"].sum()
    fig.text(0.01, -0.01, f"These 12 categories are {top12:.0f}% of net revenue; {len(df)} categories in all.", fontsize=8, color=INK_2)
    fig.tight_layout()
    save(fig, "categories")


def fig_states(df: pd.DataFrame) -> None:
    d = df[df["delivered_orders"] >= 1000].sort_values("median_delivery_days").reset_index(drop=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 5.2), sharey=True)
    a.barh(d["customer_state"], d["median_delivery_days"], color=BLUE, height=0.62)
    a.set_title("Median days to deliver")
    for y, v in enumerate(d["median_delivery_days"]):
        a.text(v + 0.3, y, f"{v:.0f}", va="center", fontsize=8.5)
    b.barh(d["customer_state"], d["late_pct"], color=ORANGE, height=0.62)
    b.set_title("Orders delivered late (%)")
    for y, v in enumerate(d["late_pct"]):
        b.text(v + 0.2, y, f"{v:.1f}", va="center", fontsize=8.5)
    for ax in (a, b):
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, ax.get_xlim()[1] * 1.12)
    fig.text(0.01, -0.01, "Customer states with at least 1,000 delivered orders, ordered by median delivery time.", fontsize=8, color=INK_2)
    fig.tight_layout()
    save(fig, "states")


def fig_reviews(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [BLUE] + [ORANGE] * (len(df) - 1)
    ax.bar(df["delay_group"], df["avg_review_score"], color=colors, width=0.6)
    for x, (score, n) in enumerate(zip(df["avg_review_score"], df["orders"])):
        ax.text(x, score + 0.06, f"{score:.2f}", ha="center", fontsize=9)
        ax.text(x, 0.12, f"n = {n:,}", ha="center", fontsize=8, color=INK)
    ax.set_ylim(0, 5)
    ax.set_title("Average review score by how late the order arrived")
    ax.set_ylabel("Review score (1 to 5)")
    ax.grid(axis="x", visible=False)
    plt.setp(ax.get_xticklabels(), fontsize=8.5)
    fig.text(0.01, -0.02, "Delivered orders with a review. An association: late orders also differ in product, seller and region.", fontsize=8, color=INK_2)
    fig.tight_layout()
    save(fig, "reviews_vs_delay")


def fig_promise(df: pd.DataFrame) -> None:
    d = df[df["delivered_orders"] >= 500].copy()
    d["month"] = pd.to_datetime(d["purchase_month"] + "-01")
    fig, (a, b) = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True)
    a.plot(d["month"], d["late_pct"], color=ORANGE, marker="o", markersize=4)
    a.set_title("Orders delivered late (%)")
    a.set_ylim(0, d["late_pct"].max() * 1.2)
    b.plot(d["month"], d["promised_under_20d_pct"], color=BLUE, marker="o", markersize=4)
    b.set_title("Orders promised in under 20 days (%)")
    b.set_ylim(0, 100)
    last = d.iloc[-1]
    b.annotate(f"{last['purchase_month']}: {last['promised_under_20d_pct']:.0f}%", (last["month"], last["promised_under_20d_pct"]),
               xytext=(-8, 6), textcoords="offset points", ha="right", va="bottom", fontsize=9)
    fig.text(0.01, -0.01, "Delivered orders by purchase month, months with at least 500 orders.", fontsize=8, color=INK_2)
    fig.tight_layout()
    save(fig, "promise_and_lateness")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    tables = run_queries(con)
    con.close()

    pd.set_option("display.width", 200, "display.max_columns", 20)
    for name, df in tables.items():
        print(f"== {name}")
        print(df.head(15).to_string(index=False), "\n")

    fig_monthly(tables["01_monthly_kpis"])
    fig_categories(tables["02_category_performance"])
    fig_states(tables["03_state_performance"])
    fig_reviews(tables["05_delivery_vs_reviews"])
    fig_promise(tables["08_delivery_trend"])
    print(f"wrote {len(tables)} tables to {TABLES.relative_to(ROOT)} and 5 figures to {FIGURES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
