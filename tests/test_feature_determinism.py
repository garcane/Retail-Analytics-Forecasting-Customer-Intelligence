"""The feature query must be deterministic: ties are broken by a fixed rule, never by DuckDB's thread scheduling.

Before the fix, `arg_max(category, price)` picked an arbitrary row when an order's most expensive items tied on price
in different categories (57 labelled orders in the real warehouse). The pick changed between multi-threaded runs, and
because the order feeds its category's running totals, category_prior_n / category_prior_late changed for thousands
of later orders. Ties now resolve to the alphabetically first category (and payment type), the same rule as the
Snowflake models, so DuckDB and Snowflake agree row for row.
"""

from datetime import datetime, timedelta

D = datetime(2018, 1, 1)


def day(n: float) -> datetime:
    return D + timedelta(days=n)


def _add_categories(mini) -> None:
    mini.con.execute("insert into dim_product values (2, 500, 1000, 2, 'watches_gifts'), (3, 500, 1000, 2, 'art')")


def _tied_order(mini, purchase, delivered) -> str:
    """An order with two items at the same price, in 'watches_gifts' and 'art', and two equal payments."""
    oid = mini.add_order(purchase, delivered, late=False)
    mini.con.execute("delete from fact_order_items where order_id = ?", [oid])
    mini.con.execute("insert into fact_order_items values (?, 1, 2, 50, 5, 2, 1), (?, 1, 3, 50, 5, 2, 1)", [oid, oid])
    mini.con.execute("delete from fact_payments where order_id = ?", [oid])
    mini.con.execute("insert into fact_payments values (?, 1, 'voucher', 55), (?, 1, 'boleto', 55)", [oid, oid])
    return oid


def _single_item_order(mini, purchase, delivered, product_key) -> str:
    oid = mini.add_order(purchase, delivered, late=False)
    mini.con.execute("update fact_order_items set product_key = ? where order_id = ?", [product_key, oid])
    return oid


def test_price_tie_resolves_to_the_alphabetically_first_category(mini):
    _add_categories(mini)
    _tied_order(mini, day(0), day(5))
    later_art = _single_item_order(mini, day(10), day(20), 3)
    later_watches = _single_item_order(mini, day(10), day(20), 2)
    f = mini.features()
    assert f.loc[later_art, "category_prior_n"] == 1        # the tied order was counted as 'art'
    assert f.loc[later_watches, "category_prior_n"] == 0    # ... and not as 'watches_gifts'


def test_payment_value_tie_resolves_to_the_alphabetically_first_type(mini):
    _add_categories(mini)
    tied = _tied_order(mini, day(0), day(5))
    assert mini.features().loc[tied, "main_payment_type"] == "boleto"


def test_repeated_multithreaded_runs_are_identical(mini):
    _add_categories(mini)
    for i in range(40):
        _tied_order(mini, day(i), day(i + 3))
        _single_item_order(mini, day(i + 0.5), day(i + 4), 2 + i % 2)
    mini.con.execute("set threads = 8")
    first = mini.features().sort_index()
    for _ in range(5):
        assert mini.features().sort_index().equals(first)
