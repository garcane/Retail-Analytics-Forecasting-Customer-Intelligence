"""Shared fixtures: a tiny hand-built warehouse for the feature SQL, and the real one when it has been built."""

from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
FEATURES_SQL = ROOT / "sql" / "ml" / "late_delivery_features.sql"
WAREHOUSE = ROOT / "warehouse.duckdb"


class MiniWarehouse:
    """Just the tables and columns the feature SQL reads, filled from a few lines of Python.

    Every order has one item from seller 1 (state SP) of product 1 (category 'toys'), shipped to a customer in RJ.
    """

    def __init__(self) -> None:
        self.con = duckdb.connect(":memory:")
        self.con.execute(
            """
            create table fact_orders (order_id varchar, customer_key bigint, customer_geography_key bigint,
                purchase_ts timestamp, estimated_delivery_ts timestamp, delivered_customer_ts timestamp,
                is_late boolean, item_count integer, items_price decimal(12,2), items_freight decimal(12,2),
                payment_count integer, order_status varchar, has_timestamp_anomaly boolean);
            create table fact_order_items (order_id varchar, seller_key bigint, product_key bigint,
                price decimal(12,2), freight_value decimal(12,2), seller_geography_key bigint,
                customer_geography_key bigint);
            create table fact_payments (order_id varchar, payment_installments integer, payment_type varchar,
                payment_value decimal(12,2));
            create table dim_product (product_key bigint, product_weight_g double, product_volume_cm3 double,
                product_photos_qty integer, product_category_name_english varchar);
            create table dim_seller (seller_key bigint, seller_state varchar);
            create table dim_geography (geography_key bigint, state varchar, latitude double, longitude double);
            insert into dim_product values (1, 500, 1000, 2, 'toys');
            insert into dim_seller values (1, 'SP');
            insert into dim_geography values (1, 'RJ', -22.9, -43.2), (2, 'SP', -23.5, -46.6);
            """
        )
        self.n = 0

    def add_order(self, purchase: datetime, delivered: datetime | None, *, late: bool | None = None,
                  status: str = "delivered", anomaly: bool = False, seller: int = 1) -> str:
        self.n += 1
        oid = f"o{self.n}"
        est = purchase + timedelta(days=15)
        if late is None and delivered is not None:
            late = delivered > est
        self.con.execute(
            "insert into fact_orders values (?, 1, 1, ?, ?, ?, ?, 1, 100, 10, 1, ?, ?)",
            [oid, purchase, est, delivered, late, status, anomaly],
        )
        self.con.execute("insert into fact_order_items values (?, ?, 1, 100, 10, 2, 1)", [oid, seller])
        self.con.execute("insert into fact_payments values (?, 1, 'credit_card', 110)", [oid])
        return oid

    def features(self):
        return self.con.execute(FEATURES_SQL.read_text(encoding="utf-8")).df().set_index("order_id")


@pytest.fixture
def mini() -> MiniWarehouse:
    return MiniWarehouse()


@pytest.fixture(scope="session")
def warehouse():
    if not WAREHOUSE.exists():
        pytest.skip("warehouse.duckdb not built; run src/transformation/build_warehouse.py")
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    yield con
    con.close()
