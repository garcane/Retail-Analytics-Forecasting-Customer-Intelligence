"""The single source of truth for the Power BI work: tables, relationships, measures, checks and pages.

Everything the three deliverables show is defined here, so they cannot drift apart:
  build_spec_html.py   -> docs/powerbi/DAX_SPECIFICATION.html
  build_mockup_html.py -> docs/powerbi/DASHBOARD_MOCKUP.html
  build_pbip.py        -> powerbi/RetailAnalytics.pbip (+ .Report, .SemanticModel)

Column names and types are read from the warehouse and the export queries (see `load_schema`), not typed by hand.
Each measure's DAX has a matching check: a SQL query over the warehouse and the exported files whose result is the value
the measure should return in the stated filter context. The checks are run by `compute_checks` and printed in the
specification as the first-open validation checklist.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
NAMESPACE = uuid.UUID("6f1c0c0e-3b0a-4f0e-9a43-1d7d7a5a9e11")  # fixed, so generated GUIDs are deterministic


def guid(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


# ------------------------------------------------------------------------------------------------ tables
@dataclass
class Table:
    name: str
    kind: str                 # "fact", "dimension" or "other"
    fmt: str                  # "parquet" or "csv"
    description: str
    date_table: bool = False
    sort_by: dict[str, str] = field(default_factory=dict)   # column -> column it sorts by
    hidden_suffixes: tuple[str, ...] = ("_key",)             # foreign/surrogate keys are hidden in the field list
    visible: tuple[str, ...] = ()                            # columns kept visible even if they match a hidden suffix
    formats: dict[str, str] = field(default_factory=dict)    # column -> format string

    @property
    def file(self) -> str:
        return f"{self.name}.{self.fmt}"


TABLES: list[Table] = [
    Table("dim_date", "dimension", "csv", "One row per calendar day, 2016 to 2020 (gap-free), plus a -1 'not applicable' member. Marked as the date table.",
          date_table=True, sort_by={"month_name": "month", "day_name": "day_of_week"}, visible=("date_key",),
          formats={"full_date": "dd mmm yyyy"}),
    Table("dim_customer", "dimension", "csv", "One row per real customer (customer_unique_id), plus an unknown member."),
    Table("dim_product", "dimension", "csv", "One row per product; English category with fallbacks."),
    Table("dim_seller", "dimension", "csv", "One row per seller."),
    Table("dim_geography", "dimension", "csv", "One row per zip-code prefix (median coordinates, most frequent city and state)."),
    Table("fact_orders", "fact", "parquet",
          "One row per order, including orders with no items. Items and payments are pre-aggregated to this grain. Derived flags: is_net_order, "
          "is_labelled_delivery; derived columns: promised_days, delay_bucket.",
          sort_by={"delay_bucket": "delay_bucket_order"}, formats={"items_price": "#,0.00", "items_freight": "#,0.00", "payment_total": "#,0.00",
                                                                     "delivery_days": "0.0", "delivery_delay_days": "0.0", "promised_days": "0.0"}),
    Table("fact_order_items", "fact", "parquet", "One row per order item. The core sales fact; flag is_net_order marks items of orders that were not canceled or unavailable.",
          formats={"price": "#,0.00", "freight_value": "#,0.00", "item_total_value": "#,0.00"}),
    Table("fact_payments", "fact", "parquet", "One row per payment. Analysed on its own; its total need not equal item revenue.",
          formats={"payment_value": "#,0.00"}),
    Table("fact_reviews", "fact", "parquet", "One row per (review_id, order_id). Free-text comments are not exported. Use is_latest_review_for_order for one review per order."),
    Table("late_delivery_scores", "other", "parquet",
          "Out-of-time risk score for every order in the six test months (2018-03 to 2018-08), from the v1 logistic regression trained only on orders "
          "resolved before each month. risk_percentile is within the month: 1.0 is the riskiest order of that month.",
          hidden_suffixes=("_key",), formats={"risk_score": "0.000", "risk_percentile": "0.000", "promised_days": "0.0"}),
    Table("forecast_backtest", "other", "csv",
          "Rolling-origin weekly forecasts: one row per target (orders or revenue), horizon (1 or 4 weeks), method and target week. "
          "The method 'actual' repeats the actual value so it can be drawn as a line.", formats={"forecast": "#,0", "actual": "#,0", "abs_error": "#,0"}),
    Table("flag_share", "other", "csv", "Disconnected helper table behind the 'flag the riskiest X%' slicer on the risk page (5 to 30)."),
]
TABLE_BY_NAME = {t.name: t for t in TABLES}

# Fixed schemas for the tables that are not read from the warehouse.
FIXED_SCHEMAS = {
    "late_delivery_scores": [
        ("order_id", "VARCHAR"), ("month", "VARCHAR"), ("purchase_date_key", "BIGINT"), ("risk_score", "DOUBLE"),
        ("risk_percentile", "DOUBLE"), ("flagged_top10", "BOOLEAN"), ("is_late", "BIGINT"), ("customer_state", "VARCHAR"),
        ("seller_state", "VARCHAR"), ("category", "VARCHAR"), ("promised_days", "DOUBLE"),
    ],
    "forecast_backtest": [
        ("target", "VARCHAR"), ("horizon", "BIGINT"), ("method", "VARCHAR"), ("target_week", "DATE"),
        ("forecast", "DOUBLE"), ("actual", "DOUBLE"), ("abs_error", "DOUBLE"),
    ],
    "flag_share": [("flag_pct", "BIGINT")],
}


def tmdl_type(duck: str) -> str:
    d = duck.upper()
    if d.startswith("DECIMAL"):
        return "decimal"
    return {"VARCHAR": "string", "BIGINT": "int64", "INTEGER": "int64", "SMALLINT": "int64", "TINYINT": "int64", "HUGEINT": "int64",
            "DOUBLE": "double", "FLOAT": "double", "BOOLEAN": "boolean", "TIMESTAMP": "dateTime", "DATE": "dateTime"}[d]


def m_type(duck: str) -> str:
    """Power Query type for CSV columns (Parquet keeps its own types)."""
    d = duck.upper()
    if d.startswith("DECIMAL"):
        return "Currency.Type"
    return {"VARCHAR": "type text", "BIGINT": "Int64.Type", "INTEGER": "Int64.Type", "SMALLINT": "Int64.Type", "TINYINT": "Int64.Type",
            "HUGEINT": "Int64.Type", "DOUBLE": "type number", "FLOAT": "type number", "BOOLEAN": "type logical",
            "TIMESTAMP": "type datetime", "DATE": "type date"}[d]


def load_schema(db: Path | None = None) -> dict[str, list[tuple[str, str]]]:
    """Column names and DuckDB types for every table, taken from the warehouse and the export queries."""
    import export_data  # local import: needs src/powerbi on the path

    con = duckdb.connect(str(db or ROOT / "warehouse.duckdb"), read_only=True)
    schema: dict[str, list[tuple[str, str]]] = {}
    for t in TABLES:
        if t.name in FIXED_SCHEMAS:
            schema[t.name] = FIXED_SCHEMAS[t.name]
        elif t.name in export_data.FACT_SQL:
            rows = con.execute(f"describe {export_data.FACT_SQL[t.name]}").fetchall()
            schema[t.name] = [(r[0], r[1]) for r in rows]
        else:
            rows = con.execute(f"describe select * from {t.name}").fetchall()
            schema[t.name] = [(r[0], r[1]) for r in rows]
    con.close()
    return schema


def column_hidden(table: Table, column: str) -> bool:
    return column not in table.visible and column.endswith(table.hidden_suffixes)


# ------------------------------------------------------------------------------------------------ relationships
@dataclass
class Relationship:
    many_table: str
    many_col: str
    one_table: str
    one_col: str
    active: bool = True
    note: str = ""

    @property
    def name(self) -> str:
        return guid("rel", self.many_table, self.many_col, self.one_table, self.one_col)


RELATIONSHIPS: list[Relationship] = [
    Relationship("fact_orders", "customer_key", "dim_customer", "customer_key", note="who ordered"),
    Relationship("fact_orders", "customer_geography_key", "dim_geography", "geography_key", note="customer state and city at the time of the order"),
    Relationship("fact_orders", "purchase_date_key", "dim_date", "date_key", note="the active date: orders are reported by purchase date"),
    Relationship("fact_orders", "approved_date_key", "dim_date", "date_key", False, "role-playing date; use USERELATIONSHIP"),
    Relationship("fact_orders", "carrier_date_key", "dim_date", "date_key", False, "role-playing date; use USERELATIONSHIP"),
    Relationship("fact_orders", "delivered_customer_date_key", "dim_date", "date_key", False, "role-playing date; use USERELATIONSHIP (see 'Orders by Delivery Date')"),
    Relationship("fact_orders", "estimated_delivery_date_key", "dim_date", "date_key", False, "role-playing date; use USERELATIONSHIP"),
    Relationship("fact_order_items", "order_id", "fact_orders", "order_id", note="items inherit date, customer and customer state from their order (one path, so no ambiguity)"),
    Relationship("fact_order_items", "product_key", "dim_product", "product_key"),
    Relationship("fact_order_items", "seller_key", "dim_seller", "seller_key"),
    Relationship("fact_payments", "order_id", "fact_orders", "order_id"),
    Relationship("fact_reviews", "order_id", "fact_orders", "order_id"),
    Relationship("late_delivery_scores", "purchase_date_key", "dim_date", "date_key", note="lets the month slicer filter the scores"),
]


# ------------------------------------------------------------------------------------------------ measures
@dataclass
class Measure:
    name: str
    table: str          # the table the measure lives in (also its home in the field list)
    dax: str
    fmt: str
    folder: str
    description: str


NET = "fact_order_items[is_net_order] = TRUE()"
LAB = "fact_orders[is_labelled_delivery] = TRUE()"
LATEST = "fact_reviews[is_latest_review_for_order] = TRUE()"
BUCKETED = "fact_orders[delay_bucket_order] >= 1"

MEASURES: list[Measure] = [
    # -- Sales overview
    Measure("Net Revenue", "fact_order_items", f"CALCULATE(SUM(fact_order_items[price]), {NET})", "#,0.00", "Sales",
            "Item price of orders that were not canceled or unavailable. Freight is separate."),
    Measure("Net Orders", "fact_order_items", f"CALCULATE(DISTINCTCOUNT(fact_order_items[order_id]), {NET})", "#,0", "Sales",
            "Distinct orders that have net items."),
    Measure("Average Order Value", "fact_order_items", "DIVIDE([Net Revenue], [Net Orders])", "#,0.00", "Sales", "Net revenue per net order."),
    Measure("Net Freight", "fact_order_items", f"CALCULATE(SUM(fact_order_items[freight_value]), {NET})", "#,0.00", "Sales", "Freight charged on net items."),
    Measure("Freight % of Revenue", "fact_order_items", "DIVIDE([Net Freight], [Net Revenue])", "0.0%", "Sales", "Freight as a share of net item revenue."),
    Measure("Items Sold", "fact_order_items", f"CALCULATE(COUNTROWS(fact_order_items), {NET})", "#,0", "Sales", "Number of net items."),
    Measure("Buying Customers", "fact_order_items", f"CALCULATE(DISTINCTCOUNT(fact_order_items[customer_key]), {NET})", "#,0", "Sales", "Distinct customers with a net item."),
    Measure("Net Revenue Prior Month", "fact_order_items", "CALCULATE([Net Revenue], DATEADD(dim_date[full_date], -1, MONTH))", "#,0.00", "Sales",
            "Net revenue one month earlier (needs the gap-free date table)."),
    Measure("Revenue MoM %", "fact_order_items", "DIVIDE([Net Revenue] - [Net Revenue Prior Month], [Net Revenue Prior Month])", "0.0%", "Sales",
            "Month-over-month growth. Meaningful only between months with real volume (2017-01 to 2018-08)."),
    Measure("Late Items %", "fact_order_items",
            f"VAR _late = CALCULATE(COUNTROWS(fact_order_items), {NET}, fact_orders[is_late] = TRUE()) "
            f"VAR _known = CALCULATE(COUNTROWS(fact_order_items), {NET}, fact_orders[is_late] IN {{TRUE(), FALSE()}}) RETURN DIVIDE(_late, _known)",
            "0.0%", "Sales", "Item-weighted late rate: each item carries its order's lateness (used for categories)."),
    Measure("Top 10 Sellers Revenue Share", "fact_order_items",
            "DIVIDE(SUMX(TOPN(10, ALLSELECTED(dim_seller[seller_key]), [Net Revenue]), [Net Revenue]), CALCULATE([Net Revenue], ALLSELECTED(dim_seller)))",
            "0.0%", "Sales", "Share of net revenue earned by the ten largest sellers in the current selection."),
    # -- Delivery and reviews
    Measure("Delivered Orders", "fact_orders", f"CALCULATE(COUNTROWS(fact_orders), {LAB})", "#,0", "Delivery",
            "Delivered orders with a late/on-time label and no timestamp anomaly (the population used for the model)."),
    Measure("Late Orders", "fact_orders", f"CALCULATE(COUNTROWS(fact_orders), {LAB}, fact_orders[is_late] = TRUE())", "#,0", "Delivery",
            "Delivered after the estimated date."),
    Measure("Late Rate %", "fact_orders", "DIVIDE([Late Orders], [Delivered Orders])", "0.0%", "Delivery", "Share of delivered orders that arrived late."),
    Measure("Median Delivery Days", "fact_orders", f"CALCULATE(MEDIAN(fact_orders[delivery_days]), {LAB})", "0.0", "Delivery", "Median days from purchase to delivery."),
    Measure("Average Promised Days", "fact_orders", f"CALCULATE(AVERAGE(fact_orders[promised_days]), {LAB})", "0.0", "Delivery", "Average delivery window promised at checkout."),
    Measure("Share Promised Under 20 Days", "fact_orders",
            f"DIVIDE(CALCULATE(COUNTROWS(fact_orders), {LAB}, fact_orders[promised_days] < 20), [Delivered Orders])", "0.0%", "Delivery",
            "Share of delivered orders promised in under 20 days (it jumped in 2018)."),
    Measure("Orders by Delivery Date", "fact_orders",
            "CALCULATE(COUNTROWS(fact_orders), USERELATIONSHIP(fact_orders[delivered_customer_date_key], dim_date[date_key]))", "#,0", "Delivery",
            "Example of the inactive relationship: orders counted by the day they were delivered, not purchased."),
    Measure("Net Orders (orders table)", "fact_orders", "CALCULATE(COUNTROWS(fact_orders), fact_orders[is_net_order] = TRUE())", "#,0", "Customers",
            "Net orders counted on the order grain (used for repeat-customer measures)."),
    Measure("Customers Ordering", "fact_orders", "COUNTROWS(FILTER(VALUES(dim_customer[customer_key]), [Net Orders (orders table)] >= 1))", "#,0", "Customers",
            "Real customers with at least one net order."),
    Measure("One-Time Customer Share", "fact_orders",
            "DIVIDE(COUNTROWS(FILTER(VALUES(dim_customer[customer_key]), [Net Orders (orders table)] = 1)), [Customers Ordering])", "0.0%", "Customers",
            "Share of customers who ordered exactly once (about 97%)."),
    Measure("Average Review Score", "fact_reviews", f"CALCULATE(AVERAGE(fact_reviews[review_score]), {LATEST}, {BUCKETED})", "0.00", "Reviews",
            "Average of the latest review per delivered order. Use with fact_orders[delay_bucket]."),
    Measure("Reviewed Orders", "fact_reviews", f"CALCULATE(COUNTROWS(fact_reviews), {LATEST}, {BUCKETED})", "#,0", "Reviews", "Delivered orders with a latest review."),
    Measure("Low Score %", "fact_reviews",
            f"DIVIDE(CALCULATE(COUNTROWS(fact_reviews), {LATEST}, {BUCKETED}, fact_reviews[review_score] <= 2), [Reviewed Orders])", "0.0%", "Reviews",
            "Share of reviews with 1 or 2 stars."),
    Measure("Payment Value", "fact_payments", "SUM(fact_payments[payment_value])", "#,0.00", "Payments", "Total paid (analysed on its own; does not exactly tie to item revenue)."),
    Measure("Payment Value Share %", "fact_payments", "DIVIDE([Payment Value], CALCULATE([Payment Value], ALL(fact_payments[payment_type])))", "0.0%", "Payments",
            "Share of payment value by payment type."),
    Measure("Average Installments", "fact_payments", "AVERAGE(fact_payments[payment_installments])", "0.00", "Payments", "Average number of instalments."),
    # -- Late-delivery risk
    Measure("Flag Share", "late_delivery_scores", "SELECTEDVALUE(flag_share[flag_pct], 10) / 100", "0%", "Risk", "The 'flag the riskiest X%' control (default 10%)."),
    Measure("Scored Orders", "late_delivery_scores", "COUNTROWS(late_delivery_scores)", "#,0", "Risk", "Orders scored out of time (the six test months)."),
    Measure("Late Rate (scored)", "late_delivery_scores", "AVERAGE(late_delivery_scores[is_late])", "0.0%", "Risk", "Actual late rate of the scored orders (the chance level)."),
    Measure("Flagged Orders", "late_delivery_scores",
            "VAR _cut = 1 - [Flag Share] RETURN CALCULATE(COUNTROWS(late_delivery_scores), late_delivery_scores[risk_percentile] > _cut)", "#,0", "Risk",
            "Orders in the riskiest X% of their month."),
    Measure("Late Rate Among Flagged", "late_delivery_scores",
            "VAR _cut = 1 - [Flag Share] RETURN CALCULATE(AVERAGE(late_delivery_scores[is_late]), late_delivery_scores[risk_percentile] > _cut)", "0.0%", "Risk",
            "Actual late rate among the flagged orders."),
    Measure("Lift", "late_delivery_scores", "DIVIDE([Late Rate Among Flagged], [Late Rate (scored)])", "0.0\"x\"", "Risk",
            "How many times better than chance the flagging is. Pooled over the selection, so it differs from the average of the monthly lifts (2.8x)."),
    Measure("Recall", "late_delivery_scores",
            "VAR _cut = 1 - [Flag Share] RETURN DIVIDE(CALCULATE(SUM(late_delivery_scores[is_late]), late_delivery_scores[risk_percentile] > _cut), SUM(late_delivery_scores[is_late]))",
            "0.0%", "Risk", "Share of all late orders that the flagged orders catch."),
    # -- Forecast
    Measure("Forecast Value", "forecast_backtest", "AVERAGE(forecast_backtest[forecast])", "#,0", "Forecast", "Average forecast of the selected methods."),
    Measure("Actual Value", "forecast_backtest", "AVERAGE(forecast_backtest[actual])", "#,0", "Forecast", "Actual value for the target week."),
    Measure("MAE", "forecast_backtest", 'CALCULATE(AVERAGE(forecast_backtest[abs_error]), KEEPFILTERS(forecast_backtest[method] <> "actual"))', "#,0", "Forecast",
            "Mean absolute error of the selected methods (the 'actual' line is excluded)."),
    Measure("MAE vs Naive", "forecast_backtest", 'DIVIDE([MAE], CALCULATE([MAE], forecast_backtest[method] = "naive_last_week"))', "0.00\"x\"", "Forecast",
            "Error relative to repeating last week; below 1 beats naive."),
]
MEASURE_BY_NAME = {m.name: m for m in MEASURES}


# ------------------------------------------------------------------------------------------------ checks
@dataclass
class Check:
    measure: str
    context: str        # the filter context in which the measure should return the value
    sql: str            # {D} is replaced by the exported data folder
    fmt: str            # how to print the value
    page: str = ""


NET_I = "oi.order_status not in ('canceled', 'unavailable')"
POP = "o.order_status = 'delivered' and o.is_late is not null and not o.has_timestamp_anomaly"
REV_MONTH = lambda ym: (  # noqa: E731
    f"select sum(oi.price) from fact_order_items oi join dim_date d on d.date_key = oi.purchase_date_key where {NET_I} and d.year_month = '{ym}'")
SC = "read_parquet('{D}/late_delivery_scores.parquet')"
FB = "read_csv('{D}/forecast_backtest.csv', header=true)"

CHECKS: list[Check] = [
    Check("Net Revenue", "no filters", f"select sum(price) from fact_order_items oi where {NET_I}", "R$ {:,.2f}", "Sales overview"),
    Check("Net Orders", "no filters", f"select count(distinct order_id) from fact_order_items oi where {NET_I}", "{:,.0f}", "Sales overview"),
    Check("Average Order Value", "no filters", f"select sum(price) / count(distinct order_id) from fact_order_items oi where {NET_I}", "R$ {:,.2f}", "Sales overview"),
    Check("Freight % of Revenue", "no filters", f"select sum(freight_value) / sum(price) from fact_order_items oi where {NET_I}", "{:.1%}", "Sales overview"),
    Check("Items Sold", "no filters", f"select count(*) from fact_order_items oi where {NET_I}", "{:,.0f}", "Sales overview"),
    Check("Buying Customers", "no filters", f"select count(distinct customer_key) from fact_order_items oi where {NET_I}", "{:,.0f}", "Sales overview"),
    Check("Net Revenue", "dim_date[year_month] = 2017-11", REV_MONTH("2017-11"), "R$ {:,.2f}", "Sales overview"),
    Check("Revenue MoM %", "dim_date[year_month] = 2017-11", f"select (({REV_MONTH('2017-11')}) / ({REV_MONTH('2017-10')}) - 1)", "{:.1%}", "Sales overview"),
    Check("Net Revenue", "dim_geography[state] = SP",
          f"select sum(oi.price) from fact_order_items oi join fact_orders o using (order_id) join dim_geography g on g.geography_key = o.customer_geography_key "
          f"where {NET_I} and g.state = 'SP'", "R$ {:,.2f}", "Sales overview"),
    Check("Net Revenue", "dim_product[product_category_name_english] = health_beauty",
          f"select sum(oi.price) from fact_order_items oi join dim_product p using (product_key) where {NET_I} and p.product_category_name_english = 'health_beauty'",
          "R$ {:,.2f}", "Sales overview"),
    Check("Late Items %", "dim_product[product_category_name_english] = health_beauty",
          f"select avg(o.is_late::int) from fact_order_items oi join fact_orders o using (order_id) join dim_product p using (product_key) "
          f"where {NET_I} and p.product_category_name_english = 'health_beauty'", "{:.1%}", "Sales overview"),
    Check("Top 10 Sellers Revenue Share", "no filters",
          f"select sum(rev) filter (where rn <= 10) / sum(rev) from (select sum(price) rev, row_number() over (order by sum(price) desc, seller_key) rn "
          f"from fact_order_items oi where {NET_I} group by seller_key)", "{:.1%}", "Sales overview"),
    Check("Delivered Orders", "no filters", f"select count(*) from fact_orders o where {POP}", "{:,.0f}", "Delivery and reviews"),
    Check("Late Orders", "no filters", f"select count(*) from fact_orders o where {POP} and o.is_late", "{:,.0f}", "Delivery and reviews"),
    Check("Late Rate %", "no filters", f"select avg(o.is_late::int) from fact_orders o where {POP}", "{:.2%}", "Delivery and reviews"),
    Check("Late Rate %", "dim_geography[state] = RJ",
          f"select avg(o.is_late::int) from fact_orders o join dim_geography g on g.geography_key = o.customer_geography_key where {POP} and g.state = 'RJ'",
          "{:.1%}", "Delivery and reviews"),
    Check("Median Delivery Days", "no filters", f"select median(o.delivery_days) from fact_orders o where {POP}", "{:.1f}", "Delivery and reviews"),
    Check("Average Promised Days", "no filters",
          f"select avg(date_diff('second', o.purchase_ts, o.estimated_delivery_ts) / 86400.0) from fact_orders o where {POP}", "{:.1f}", "Delivery and reviews"),
    Check("Share Promised Under 20 Days", "dim_date[year_month] = 2018-08",
          f"select avg((date_diff('second', o.purchase_ts, o.estimated_delivery_ts) / 86400.0 < 20)::int) from fact_orders o "
          f"join dim_date d on d.date_key = o.purchase_date_key where {POP} and d.year_month = '2018-08'", "{:.1%}", "Delivery and reviews"),
    Check("Reviewed Orders", "no filters",
          "select count(*) from fact_orders o join fact_reviews r on r.order_id = o.order_id and r.is_latest_review_for_order "
          "where o.order_status = 'delivered' and o.delivery_delay_days is not null", "{:,.0f}", "Delivery and reviews"),
    Check("Average Review Score", "fact_orders[delay_bucket] = on time or early",
          "select avg(r.review_score) from fact_orders o join fact_reviews r on r.order_id = o.order_id and r.is_latest_review_for_order "
          "where o.order_status = 'delivered' and o.delivery_delay_days is not null and o.delivery_delay_days <= 0", "{:.2f}", "Delivery and reviews"),
    Check("Low Score %", "fact_orders[delay_bucket] = 8-14 days late",
          "select avg((r.review_score <= 2)::int) from fact_orders o join fact_reviews r on r.order_id = o.order_id and r.is_latest_review_for_order "
          "where o.order_status = 'delivered' and o.delivery_delay_days > 7 and o.delivery_delay_days <= 14", "{:.1%}", "Delivery and reviews"),
    Check("Payment Value", "no filters", "select sum(payment_value) from fact_payments", "R$ {:,.2f}", "Sales overview"),
    Check("Payment Value Share %", "fact_payments[payment_type] = credit_card",
          "select sum(payment_value) filter (where payment_type = 'credit_card') / sum(payment_value) from fact_payments", "{:.1%}", "Sales overview"),
    Check("Average Installments", "fact_payments[payment_type] = credit_card",
          "select avg(payment_installments) from fact_payments where payment_type = 'credit_card'", "{:.2f}", "Sales overview"),
    Check("Customers Ordering", "no filters",
          "select count(distinct customer_key) from fact_orders where order_status not in ('canceled', 'unavailable') and item_count > 0 and customer_key <> -1",
          "{:,.0f}", "Sales overview"),
    Check("One-Time Customer Share", "no filters",
          "select avg((n = 1)::int) from (select customer_key, count(*) n from fact_orders where order_status not in ('canceled', 'unavailable') "
          "and item_count > 0 and customer_key <> -1 group by customer_key)", "{:.2%}", "Sales overview"),
    Check("Scored Orders", "no filters", f"select count(*) from {SC}", "{:,.0f}", "Late-delivery risk"),
    Check("Late Rate (scored)", "no filters", f"select avg(is_late) from {SC}", "{:.2%}", "Late-delivery risk"),
    Check("Flagged Orders", "flag_share[flag_pct] = 10 (default)", f"select count(*) from {SC} where risk_percentile > 0.9", "{:,.0f}", "Late-delivery risk"),
    Check("Late Rate Among Flagged", "flag_share[flag_pct] = 10", f"select avg(is_late) from {SC} where risk_percentile > 0.9", "{:.1%}", "Late-delivery risk"),
    Check("Lift", "flag_share[flag_pct] = 10, all months pooled",
          f"select avg(is_late) filter (where risk_percentile > 0.9) / avg(is_late) from {SC}", "{:.2f}x", "Late-delivery risk"),
    Check("Lift", "flag_share[flag_pct] = 10, dim_date[year_month] = 2018-08",
          f"select avg(is_late) filter (where risk_percentile > 0.9) / avg(is_late) from {SC} where month = '2018-08'", "{:.2f}x", "Late-delivery risk"),
    Check("Recall", "flag_share[flag_pct] = 10",
          f"select sum(is_late) filter (where risk_percentile > 0.9) / sum(is_late) from {SC}", "{:.1%}", "Late-delivery risk"),
    Check("MAE", "forecast_backtest[target] = orders, [horizon] = 1, [method] = naive_last_week",
          f"select avg(abs_error) from {FB} where target = 'orders' and horizon = 1 and method = 'naive_last_week'", "{:,.1f}", "Weekly forecast"),
    Check("MAE", "[target] = orders, [horizon] = 1, [method] = combo_naive_ma8",
          f"select avg(abs_error) from {FB} where target = 'orders' and horizon = 1 and method = 'combo_naive_ma8'", "{:,.1f}", "Weekly forecast"),
    Check("MAE vs Naive", "[target] = orders, [horizon] = 1, [method] = combo_naive_ma8",
          f"select avg(abs_error) filter (where method = 'combo_naive_ma8') / avg(abs_error) filter (where method = 'naive_last_week') from {FB} "
          "where target = 'orders' and horizon = 1", "{:.2f}x", "Weekly forecast"),
    Check("MAE vs Naive", "[target] = orders, [horizon] = 4, [method] = moving_average_8",
          f"select avg(abs_error) filter (where method = 'moving_average_8') / avg(abs_error) filter (where method = 'naive_last_week') from {FB} "
          "where target = 'orders' and horizon = 4", "{:.2f}x", "Weekly forecast"),
]

HEADLINE_CHECKS = [0, 1, 6, 7, 12, 14, 15, 18, 20, 26, 29, 31, 36]  # the short first-open checklist (indices into CHECKS)


def compute_checks(db: Path | None = None, data_dir: Path | None = None) -> list[dict]:
    """Run every check against the warehouse and the exported files; returns the checks with their expected value."""
    data = (data_dir or ROOT / "powerbi" / "data").as_posix()
    con = duckdb.connect(str(db or ROOT / "warehouse.duckdb"), read_only=True)
    out = []
    for c in CHECKS:
        value = con.execute(c.sql.replace("{D}", data)).fetchone()[0]
        out.append({"measure": c.measure, "context": c.context, "page": c.page, "value": float(value), "text": c.fmt.format(float(value)), "sql": c.sql})
    con.close()
    return out


# ------------------------------------------------------------------------------------------------ pages and visuals
Field = tuple[str, str, str]   # ("column" | "measure", table, name)


def col(table: str, name: str) -> Field:
    return ("column", table, name)


def mea(name: str) -> Field:
    return ("measure", MEASURE_BY_NAME[name].table, name)


@dataclass
class Visual:
    id: str
    type: str                    # Power BI visualType
    title: str
    x: int
    y: int
    w: int
    h: int
    roles: dict[str, list[Field]]
    sort: tuple[Field, str] | None = None   # (field, "Ascending" | "Descending")
    note: str = ""


@dataclass
class Page:
    id: str
    title: str
    description: str
    visuals: list[Visual]


YM = col("dim_date", "year_month")
STATE = col("dim_geography", "state")
CAT = col("dim_product", "product_category_name_english")

PAGES: list[Page] = [
    Page("sales", "Sales overview", "Revenue, orders and basket size over time, what sells, and where. Slicers: month, category, state.", [
        Visual("s_month", "slicer", "Month", 20, 12, 300, 48, {"Values": [YM]}),
        Visual("s_cat", "slicer", "Category", 340, 12, 300, 48, {"Values": [CAT]}),
        Visual("s_state", "slicer", "Customer state", 660, 12, 300, 48, {"Values": [STATE]}),
        Visual("c_rev", "card", "Net revenue (R$)", 20, 72, 240, 90, {"Values": [mea("Net Revenue")]}),
        Visual("c_ord", "card", "Orders", 270, 72, 240, 90, {"Values": [mea("Net Orders")]}),
        Visual("c_aov", "card", "Average order value (R$)", 520, 72, 240, 90, {"Values": [mea("Average Order Value")]}),
        Visual("c_frt", "card", "Freight % of revenue", 770, 72, 240, 90, {"Values": [mea("Freight % of Revenue")]}),
        Visual("c_cus", "card", "Buying customers", 1020, 72, 240, 90, {"Values": [mea("Buying Customers")]}),
        Visual("v_rev_month", "clusteredColumnChart", "Net revenue by month", 20, 172, 620, 250, {"Category": [YM], "Y": [mea("Net Revenue")]}),
        Visual("v_aov_month", "lineChart", "Average order value by month", 650, 172, 610, 250, {"Category": [YM], "Y": [mea("Average Order Value")]}),
        Visual("v_rev_cat", "clusteredBarChart", "Net revenue by category (sorted; scroll for the long tail)", 20, 432, 620, 280,
               {"Category": [CAT], "Y": [mea("Net Revenue")]}, sort=(mea("Net Revenue"), "Descending")),
        Visual("v_rev_state", "clusteredBarChart", "Net revenue by customer state", 650, 432, 610, 280,
               {"Category": [STATE], "Y": [mea("Net Revenue")]}, sort=(mea("Net Revenue"), "Descending")),
    ]),
    Page("delivery", "Delivery and reviews", "How often orders arrive late, how long deliveries take, what the promise looked like, and what late delivery does to reviews.", [
        Visual("d_month", "slicer", "Month", 20, 12, 300, 48, {"Values": [YM]}),
        Visual("d_state", "slicer", "Customer state", 340, 12, 300, 48, {"Values": [STATE]}),
        Visual("d_c_late", "card", "Late rate", 20, 72, 300, 90, {"Values": [mea("Late Rate %")]}),
        Visual("d_c_med", "card", "Median delivery days", 330, 72, 300, 90, {"Values": [mea("Median Delivery Days")]}),
        Visual("d_c_rev", "card", "Average review score", 640, 72, 300, 90, {"Values": [mea("Average Review Score")]}),
        Visual("d_c_short", "card", "Promised in under 20 days", 950, 72, 310, 90, {"Values": [mea("Share Promised Under 20 Days")]}),
        Visual("d_late_month", "lineChart", "Late rate by purchase month", 20, 172, 620, 250, {"Category": [YM], "Y": [mea("Late Rate %")]}),
        Visual("d_short_month", "lineChart", "Share promised in under 20 days, by month", 650, 172, 610, 250, {"Category": [YM], "Y": [mea("Share Promised Under 20 Days")]}),
        Visual("d_review_bucket", "clusteredColumnChart", "Average review score by how late the order arrived", 20, 432, 620, 280,
               {"Category": [col("fact_orders", "delay_bucket")], "Y": [mea("Average Review Score")]}, sort=(col("fact_orders", "delay_bucket_order"), "Ascending")),
        Visual("d_state_table", "tableEx", "Delivery by customer state", 650, 432, 610, 280,
               {"Values": [STATE, mea("Delivered Orders"), mea("Late Rate %"), mea("Median Delivery Days")]}, sort=(mea("Delivered Orders"), "Descending")),
    ]),
    Page("risk", "Late-delivery risk (model)", "Out-of-time scores for the six test months. Choose how many of the riskiest orders to flag and see how many are really late.", [
        Visual("r_month", "slicer", "Month", 20, 12, 300, 48, {"Values": [YM]}),
        Visual("r_flag", "slicer", "Flag the riskiest X% of orders", 340, 12, 300, 48, {"Values": [col("flag_share", "flag_pct")]}),
        Visual("r_state", "slicer", "Customer state", 660, 12, 300, 48, {"Values": [col("late_delivery_scores", "customer_state")]}),
        Visual("r_c_n", "card", "Scored orders", 20, 72, 240, 90, {"Values": [mea("Scored Orders")]}),
        Visual("r_c_base", "card", "Late rate (chance)", 270, 72, 240, 90, {"Values": [mea("Late Rate (scored)")]}),
        Visual("r_c_flag", "card", "Late rate among flagged", 520, 72, 240, 90, {"Values": [mea("Late Rate Among Flagged")]}),
        Visual("r_c_lift", "card", "Lift over chance", 770, 72, 240, 90, {"Values": [mea("Lift")]}),
        Visual("r_c_rec", "card", "Late orders caught", 1020, 72, 240, 90, {"Values": [mea("Recall")]}),
        Visual("r_lift_month", "clusteredColumnChart", "Lift by month", 20, 172, 620, 250, {"Category": [YM], "Y": [mea("Lift")]}),
        Visual("r_state_bar", "clusteredBarChart", "Late rate: flagged orders against all orders, by state", 650, 172, 610, 250,
               {"Category": [col("late_delivery_scores", "customer_state")], "Y": [mea("Late Rate Among Flagged"), mea("Late Rate (scored)")]},
               sort=(mea("Late Rate Among Flagged"), "Descending")),
        Visual("r_table", "tableEx", "Riskiest orders (sorted by risk score)", 20, 432, 1240, 280,
               {"Values": [col("late_delivery_scores", "order_id"), col("late_delivery_scores", "month"), col("late_delivery_scores", "risk_score"),
                           col("late_delivery_scores", "customer_state"), col("late_delivery_scores", "category"), col("late_delivery_scores", "is_late")]},
               sort=(col("late_delivery_scores", "risk_score"), "Descending")),
    ]),
    Page("forecast", "Weekly forecast", "Forecasts of weekly orders and revenue against what happened, by method. Choose the target, the horizon and the methods.", [
        Visual("f_target", "slicer", "Target", 20, 12, 300, 48, {"Values": [col("forecast_backtest", "target")]}),
        Visual("f_horizon", "slicer", "Weeks ahead", 340, 12, 300, 48, {"Values": [col("forecast_backtest", "horizon")]}),
        Visual("f_method", "slicer", "Method (keep 'actual' selected to see it)", 660, 12, 400, 48, {"Values": [col("forecast_backtest", "method")]}),
        Visual("f_c_mae", "card", "Mean absolute error", 20, 72, 300, 90, {"Values": [mea("MAE")]}),
        Visual("f_c_rel", "card", "Error relative to naive", 330, 72, 300, 90, {"Values": [mea("MAE vs Naive")]}),
        Visual("f_line", "lineChart", "Forecast against actual", 20, 172, 1240, 300,
               {"Category": [col("forecast_backtest", "target_week")], "Y": [mea("Forecast Value")], "Series": [col("forecast_backtest", "method")]}),
        Visual("f_mae_bar", "clusteredBarChart", "Mean absolute error by method", 20, 482, 620, 230,
               {"Category": [col("forecast_backtest", "method")], "Y": [mea("MAE")]}, sort=(mea("MAE"), "Ascending")),
        Visual("f_table", "tableEx", "Method comparison", 650, 482, 610, 230,
               {"Values": [col("forecast_backtest", "method"), mea("MAE"), mea("MAE vs Naive")]}, sort=(mea("MAE"), "Ascending")),
    ]),
]

PALETTE = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "yellow": "#eda100", "magenta": "#e87ba4", "green": "#008300", "violet": "#6250d6", "red": "#e34948"}
PAGE_W, PAGE_H = 1280, 720
