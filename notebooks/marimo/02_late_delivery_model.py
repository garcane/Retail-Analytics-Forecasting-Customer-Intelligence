import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Late-delivery model")


@app.cell
def _():
    import json
    import sys
    from pathlib import Path

    import duckdb
    import marimo as mo
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from sklearn.metrics import average_precision_score, precision_recall_curve

    # The repository root is the folder that holds pyproject.toml, wherever this notebook is started from.
    ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists())
    sys.path.insert(0, str(ROOT / "src" / "ml"))
    import explain_late_delivery as eld
    import late_delivery_baseline as ldb

    return (
        Patch,
        ROOT,
        average_precision_score,
        duckdb,
        eld,
        json,
        ldb,
        mdates,
        mo,
        np,
        pd,
        plt,
        precision_recall_curve,
    )


@app.cell
def _(plt):
    # One restrained palette: blue is the model / normal case, orange is lateness / the thing to look at, grey is context.
    BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#b9b8b1"
    SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3de"
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
        "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "lines.linewidth": 2, "figure.dpi": 100,
    })
    return BLUE, GREY, GRID, INK, INK_2, ORANGE


@app.cell
def _(mo):
    mo.md("""
    # Late-delivery model (interactive)

    **Question.** When a customer places an order, can we tell which orders are most likely to arrive *after* the delivery date they were promised?

    This is the interactive version of [`02_late_delivery_model.ipynb`](../02_late_delivery_model.ipynb). The logic is the same tested code in `src/ml/`; here you can change the controls and watch the charts respond. The written summary is [docs/ml/MODEL_CARD.md](../../docs/ml/MODEL_CARD.md).

    **To run it:** build the warehouse first (`uv run python src/transformation/build_warehouse.py`), then `uv run marimo edit notebooks/marimo/02_late_delivery_model.py` (or `marimo run` for the app view).

    **What to expect.** A moderate ranker, not a crystal ball: flagging the riskiest 10% of orders catches late deliveries about 2.8 times better than chance on average.
    """)
    return


@app.cell
def _(ROOT, duckdb, ldb, mo):
    _warehouse = ROOT / "warehouse.duckdb"
    mo.stop(
        not _warehouse.exists(),
        mo.md("**warehouse.duckdb not found.** Run `uv run python src/transformation/build_warehouse.py` first."),
    )
    _con = duckdb.connect(str(_warehouse), read_only=True)
    df = ldb.load(_con)  # one row per delivered order: features known at purchase, plus the label
    _con.close()
    FEATURES = ldb.NUMERIC_V1 + ldb.CATEGORICAL
    mo.md(f"**{len(df):,}** delivered orders, **{df['is_late'].mean():.1%}** arrived late; "
          f"{len(ldb.NUMERIC_V1)} numeric + {len(ldb.CATEGORICAL)} categorical features.")
    return FEATURES, df


@app.cell
def _(mo):
    mo.md("""
    ## 1. The data

    The label is `is_late`: the order arrived after the estimated delivery date shown at checkout. About 8% of delivered orders are late, but that rate swings a lot from month to month, which is the main difficulty.
    """)
    return


@app.cell
def _(GRID, INK_2, ORANGE, df, pd, plt):
    _m = df.groupby("month")["is_late"].agg(orders="size", late="mean")
    _m = _m[_m["orders"] >= 500]
    _fig, _ax = plt.subplots(figsize=(9, 3.8))
    _ax.plot(_m.index.to_timestamp(), 100 * _m["late"], color=ORANGE, marker="o", markersize=4)
    _ax.axvspan(pd.Timestamp("2018-03-01"), pd.Timestamp("2018-09-01"), color=GRID, alpha=0.7, linewidth=0)
    _ax.set_ylim(0, 25)
    _ax.text(pd.Timestamp("2018-03-08"), 23.2, "months used for testing", color=INK_2, fontsize=9)
    _ax.set_title("Share of delivered orders that arrived late, by purchase month")
    _ax.set_ylabel("late orders (%)")
    _fig
    return


@app.cell
def _(BLUE, GREY, ORANGE, df, mo, pd, plt):
    _d = df.copy()
    _d["promise"] = pd.cut(_d["promised_days"], [0, 20, 30, 1000], right=False,
                           labels=["promised under 20 days", "20 to 29 days", "30+ days"])
    _t = _d.groupby(["month", "promise"], observed=True)["is_late"].agg(["mean", "size"]).reset_index()
    _t = _t[_t["size"] >= 100]
    _pivot = 100 * _t.pivot(index="month", columns="promise", values="mean")
    _pivot = _pivot.loc[pd.Period("2017-06"):]
    _fig, _ax = plt.subplots(figsize=(9, 4))
    for _column, _colour in zip(_pivot.columns, [ORANGE, BLUE, GREY]):
        _ax.plot(_pivot.index.to_timestamp(), _pivot[_column], color=_colour, marker="o", markersize=4, label=_column)
    _ax.set_title("Late rate by promised delivery window")
    _ax.set_ylabel("late orders (%)")
    _ax.legend(frameon=False)
    mo.vstack([
        _fig,
        mo.md("The three groups mostly move together, driven by the month. **In August 2018 they split apart: orders "
              "promised in under 20 days are late about 14% of the time, while the 30+ day promises are almost never "
              "late.** Which promise length is \"risky\" is not constant over time; this is why the model struggles in "
              "the last test month."),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2. How the model is tested

    Orders are tested **in time order**, never shuffled: for each test month the model trains only on orders whose delivery was already known before that month began, then scores that month's orders. The blue bar is what the model could learn from; the orange bar is the month it is scored on.
    """)
    return


@app.cell
def _(BLUE, ORANGE, Patch, ldb, mdates, plt):
    _fig, _ax = plt.subplots(figsize=(9, 3.4))
    for _i, _month in enumerate(ldb.TEST_MONTHS):
        _start, _end = _month.start_time, _month.end_time
        _left = mdates.date2num(ldb.TRAIN_START)
        _ax.broken_barh([(_left, mdates.date2num(_start) - _left)], (_i - 0.34, 0.68), facecolors=BLUE)
        _ax.broken_barh([(mdates.date2num(_start), mdates.date2num(_end) - mdates.date2num(_start))],
                        (_i - 0.34, 0.68), facecolors=ORANGE)
    _ax.xaxis_date()
    _ax.set_yticks(range(len(ldb.TEST_MONTHS)))
    _ax.set_yticklabels([str(_m) for _m in ldb.TEST_MONTHS])
    _ax.invert_yaxis()
    _ax.grid(axis="y", visible=False)
    _ax.set_title("Rolling-origin test: each month is scored by a model trained on everything resolved before it")
    _ax.legend(handles=[Patch(color=BLUE, label="training data"), Patch(color=ORANGE, label="month being scored")],
               frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3. Training and scoring

    One **logistic regression** per test month, on 19 features known at purchase (the promised window, basket size and weight, customer and seller state, distance, weekday and hour, payment, and the seller's earlier late rate). Nothing known only after delivery is used ([LEAKAGE_ANALYSIS.md](../../docs/ml/LEAKAGE_ANALYSIS.md)). This cell takes about 15 seconds.
    """)
    return


@app.cell
def _(FEATURES, df, ldb, mo, pd):
    store = {}
    _rows = []
    for _month in ldb.TEST_MONTHS:
        _train = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < _month.start_time)]
        _test = df[df["month"] == _month]
        _model = ldb.make_models(ldb.NUMERIC_V1, "v1")["logistic_regression_v1"].fit(_train[FEATURES], _train["is_late"])
        _p = _model.predict_proba(_test[FEATURES])[:, 1]
        _y = _test["is_late"].to_numpy()
        store[str(_month)] = {"y": _y, "p": _p, "model": _model, "test": _test}
        _rows.append({"month": str(_month), "train_orders": len(_train), **ldb.evaluate(_y, _p)})
    summary = pd.DataFrame(_rows).set_index("month")
    mo.vstack([
        summary[["train_orders", "n", "base_rate", "pr_auc", "roc_auc", "brier", "precision_at_top", "recall_at_top"]].round(3),
        mo.md("`base_rate` is what random guessing achieves; `pr_auc` is how well the ranking concentrates late orders at "
              "the top; `precision_at_top` and `recall_at_top` describe the riskiest 10% of orders."),
    ])
    return (store,)


@app.cell
def _(mo, store):
    month_picker = mo.ui.dropdown(options=list(store), value="2018-08", label="Test month")
    flag_share = mo.ui.slider(start=5, stop=30, step=5, value=10, label="Flag the riskiest X% of orders", show_value=True)
    mo.hstack([month_picker, flag_share], justify="start", gap=2)
    return flag_share, month_picker


@app.cell
def _(
    BLUE,
    GREY,
    average_precision_score,
    month_picker,
    plt,
    precision_recall_curve,
    store,
):
    _s = store[month_picker.value]
    _precision, _recall, _ = precision_recall_curve(_s["y"], _s["p"])
    _fig, _ax = plt.subplots(figsize=(7, 4.2))
    _ax.plot(_recall, _precision, color=BLUE, label="model")
    _ax.axhline(_s["y"].mean(), color=GREY, linestyle="--", linewidth=1.2, label="chance (the base late rate)")
    _ax.set_xlabel("recall (share of late orders found)")
    _ax.set_ylabel("precision")
    _ax.set_title(f"{month_picker.value}: PR-AUC {average_precision_score(_s['y'], _s['p']):.2f} "
                  f"vs chance {_s['y'].mean():.2f}")
    _ax.legend(frameon=False)
    _fig
    return


@app.cell
def _(BLUE, GREY, flag_share, ldb, mo, np, plt, store):
    _share = flag_share.value / 100
    _rows = []
    for _m, _s in store.items():
        _r = ldb.top_share_metrics(_s["y"], _s["p"], _share)
        _rows.append((_m, _s["y"].mean(), _r["precision_at_top"], _r["recall_at_top"]))
    _x = np.arange(len(_rows))
    _w = 0.38
    _fig, _ax = plt.subplots(figsize=(9, 4.2))
    _ax.bar(_x - _w / 2, [100 * r[1] for r in _rows], _w, color=GREY, label="late rate across all orders")
    _ax.bar(_x + _w / 2, [100 * r[2] for r in _rows], _w, color=BLUE,
            label=f"late rate among the riskiest {flag_share.value}% flagged")
    for _i, _r in enumerate(_rows):
        _ax.text(_i + _w / 2, 100 * _r[2] + 0.8, f"{_r[2] / _r[1]:.1f}x", ha="center", fontsize=9)
    _ax.set_xticks(_x)
    _ax.set_xticklabels([r[0] for r in _rows])
    _ax.set_ylabel("late orders (%)")
    _ax.grid(axis="x", visible=False)
    _ax.set_title("What flagging buys (labels: how many times better than chance)")
    _ax.legend(frameon=False, loc="upper right")
    _lift = np.mean([r[2] / r[1] for r in _rows])
    _recall = np.mean([r[3] for r in _rows])
    mo.vstack([
        _fig,
        mo.md(f"Flagging the riskiest **{flag_share.value}%** finds late deliveries **{_lift:.1f}x** more often than chance "
              f"on average, and catches **{_recall:.0%}** of all late orders. Slide the control: flagging more orders catches "
              "more of the late ones but dilutes the precision. At 10% the lift is 2.4 to 3.9 times in five months and "
              "only 1.2 times in August 2018."),
    ])
    return


@app.cell
def _(BLUE, GREY, INK, ORANGE, month_picker, pd, plt, store):
    _fig, (_a, _b) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    _parts = []
    for _month, _s in store.items():
        _bucket = pd.qcut(pd.Series(_s["p"]).rank(method="first"), 5, labels=False)
        _parts.append(pd.DataFrame({"b": _bucket, "pred": _s["p"], "actual": _s["y"]}).groupby("b").mean())
    _cal = pd.concat(_parts).groupby(level=0).mean()
    _a.plot([0, 0.3], [0, 0.3], color=GREY, linestyle="--", linewidth=1.2)
    _a.plot(_cal["pred"], _cal["actual"], color=BLUE, marker="o")
    _a.set_xlabel("predicted late rate")
    _a.set_ylabel("actual late rate")
    _a.set_title("By risk group (average of the six months)")
    _levels = pd.DataFrame({m: {"pred": s["p"].mean(), "actual": s["y"].mean()} for m, s in store.items()}).T
    _b.plot([0, 0.25], [0, 0.25], color=GREY, linestyle="--", linewidth=1.2)
    for _month, _r in _levels.iterrows():
        _picked = _month == month_picker.value
        _b.scatter(_r["pred"], _r["actual"], color=ORANGE if _picked else GREY, s=70 if _picked else 40, zorder=3)
        _b.annotate(_month[2:], (_r["pred"], _r["actual"]), xytext=(5, 4), textcoords="offset points", fontsize=8.5, color=INK)
    _b.set_xlabel("average predicted late rate")
    _b.set_ylabel("actual late rate")
    _b.set_title("By month: the overall level is off (selected month in orange)")
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    **Left:** inside a month the ranking is sensible (higher predicted risk, higher actual rate), though the riskiest group is over-predicted. **Right:** the *level* is wrong by month; the model predicted about 7% in March 2018 when the real rate was 21%. The late rate swings in a way the past does not predict (recalibrating on recent data made things worse, see [RECALIBRATION_AND_WINDOW.md](../../docs/ml/RECALIBRATION_AND_WINDOW.md)).

    **So: use the model by rank, flagging a share of orders, not by quoting probabilities.**

    ## 4. What does the model rely on?

    Permutation importance: shuffle one group of related columns in a test month and see how much ranking quality (PR-AUC) drops. This takes about a minute, so it runs only when you press the button.
    """)
    return


@app.cell
def _(mo):
    run_importance = mo.ui.run_button(label="Compute permutation importance")
    run_importance
    return (run_importance,)


@app.cell
def _(
    BLUE,
    FEATURES,
    INK_2,
    average_precision_score,
    eld,
    mo,
    np,
    pd,
    plt,
    run_importance,
    store,
):
    mo.stop(not run_importance.value, mo.md("_Press the button above to compute._"))
    _rng = np.random.default_rng(0)
    _drops = {g: [] for g in eld.GROUPS}
    for _month, _s in store.items():
        _test, _model = _s["test"], _s["model"]
        _base = average_precision_score(_test["is_late"], _model.predict_proba(_test[FEATURES])[:, 1])
        for _group, _columns in eld.GROUPS.items():
            _drops[_group].append(eld.permutation_drop(_model, _test, _columns, _base, _rng))
    _imp = pd.DataFrame(_drops, index=list(store)).T
    _imp["mean"] = _imp.mean(axis=1)
    _imp = _imp.sort_values("mean")
    _fig, _ax = plt.subplots(figsize=(9, 3.9))
    _ax.barh(_imp.index, _imp["mean"], color=BLUE, height=0.55)
    for _y, (_, _row) in enumerate(_imp.iterrows()):
        _ax.scatter(_row.drop("mean"), [_y] * (len(_row) - 1), color=INK_2, s=14, zorder=3)
    _ax.axvline(0, color="#e4e3de")
    _ax.set_xlabel("ranking quality lost when shuffled (PR-AUC); dots are single months")
    _ax.set_title("What the model relies on: where parcels go, and how long they were promised")
    _ax.grid(axis="y", visible=False)
    mo.vstack([
        _fig,
        mo.md("Two groups do almost all the work: **the route** (states, same-state flag, distance) and **the promise** "
              "(`promised_days`). Basket size, seller history, payment and time of day add almost nothing. One dot for the "
              "route group is *negative* (August): shuffling it improved that month's ranking, a sign the geographic "
              "pattern learned earlier did not hold."),
    ])
    return


@app.cell
def _(BLUE, FEATURES, ORANGE, Patch, df, ldb, pd, plt):
    _train = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < ldb.TEST_MONTHS[-1].start_time)]
    _final = ldb.make_models(ldb.NUMERIC_V1, "v1")["logistic_regression_v1"].fit(_train[FEATURES], _train["is_late"])
    _names = [n.split("__", 1)[1] for n in _final[:-1].get_feature_names_out()]
    _coef = pd.Series(_final[-1].coef_[0], index=_names)
    _top = _coef.reindex(_coef.abs().sort_values(ascending=False).index).head(14).sort_values()
    _fig, _ax = plt.subplots(figsize=(9, 4.8))
    _ax.barh(_top.index, _top.values, color=[ORANGE if v > 0 else BLUE for v in _top.values], height=0.6)
    _ax.axvline(0, color="#52514e", linewidth=0.8)
    _ax.set_xlabel("logistic regression coefficient (numeric features are standardised)")
    _ax.set_title("The 14 strongest effects in the final model")
    _ax.legend(handles=[Patch(color=ORANGE, label="raises the risk of a late delivery"), Patch(color=BLUE, label="lowers it")],
               frameon=False, loc="lower right")
    _ax.grid(axis="y", visible=False)
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    A longer promise (`promised_days`) is the strongest numeric effect and lowers the risk. Some destination states carry a high risk (Alagoas, Rio de Janeiro) and others a low one (Paraná, Minas Gerais, São Paulo). State and payment-type columns are one-hot with no reference category, so compare states with states, not with payment types.

    ## 5. What I tried that did not help

    The plain model ("v1") was never beaten. Pick the measure to compare:

    | set | adds |
    |---|---|
    | **v1** | the features above (the reference) |
    | v2 | late-rate history for the route and the product category |
    | v3 | v2 plus the system-wide late rate over the previous 28 days |
    | v5 | v1 plus delivery-time *slack* (promised days minus how long deliveries on the route have been taking) |
    """)
    return


@app.cell
def _(mo):
    metric_picker = mo.ui.dropdown(
        options={"PR-AUC (higher is better)": "pr_auc", "ROC-AUC (higher is better)": "roc_auc",
                 "Brier score (lower is better)": "brier", "Recall at top 10% (higher is better)": "recall_at_top"},
        value="PR-AUC (higher is better)", label="Measure")
    metric_picker
    return (metric_picker,)


@app.cell
def _(BLUE, GREY, ORANGE, ROOT, json, metric_picker, mo, np, pd, plt):
    _macro = pd.DataFrame(json.loads((ROOT / "reports" / "late_delivery_metrics.json").read_text(encoding="utf-8"))["macro_average"]).T
    _sets = ["v1", "v2", "v3", "v5"]
    _key = metric_picker.value
    _logit = [_macro.loc[f"logistic_regression_{s}", _key] for s in _sets]
    _boost = [_macro.loc[f"gradient_boosting_{s}", _key] for s in _sets]
    _x = np.arange(len(_sets))
    _w = 0.38
    _fig, _ax = plt.subplots(figsize=(9, 4))
    _ax.bar(_x - _w / 2, _logit, _w, color=BLUE, label="logistic regression")
    _ax.bar(_x + _w / 2, _boost, _w, color=ORANGE, label="gradient boosting")
    if _key == "pr_auc":
        _ax.axhline(_macro.loc["constant_train_rate", "pr_auc"], color=GREY, linestyle="--", linewidth=1.2)
    for _xi, _v in zip(_x - _w / 2, _logit):
        _ax.text(_xi, _v * 1.01, f"{_v:.3f}", ha="center", fontsize=8.5)
    for _xi, _v in zip(_x + _w / 2, _boost):
        _ax.text(_xi, _v * 1.01, f"{_v:.3f}", ha="center", fontsize=8.5)
    _ax.set_xticks(_x)
    _ax.set_xticklabels(_sets)
    _ax.set_ylim(0, max(_logit + _boost) * 1.25)
    _ax.set_title("More features did not make the model better (mean of six months)")
    _ax.legend(frameon=False, loc="upper right", ncol=2)
    _ax.grid(axis="x", visible=False)
    mo.vstack([
        _fig,
        mo.md("Every added feature set leaves the logistic model no better and the boosted model worse "
              "([DRIFT_ANALYSIS.md](../../docs/ml/DRIFT_ANALYSIS.md) tests why): the trailing late rate and category history "
              "track the regime of the training period; route history repeats what state and distance already give; "
              "delivery slack added nothing."),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 6. Why August 2018 breaks the model

    For each month, how well does a single feature rank that month's orders on its own? An AUC of 0.5 means no skill; below 0.5 means the feature points the wrong way. Choose the features to compare:
    """)
    return


@app.cell
def _(mo):
    feature_picker = mo.ui.multiselect(
        options={"promised days": "promised_days", "distance": "distance_km", "route late-rate history": "route_rate",
                 "seller late-rate history": "seller_prior_late_rate", "trailing 28-day rate": "recent_rate_28d"},
        value=["promised days", "distance", "route late-rate history"], label="Features")
    feature_picker
    return (feature_picker,)


@app.cell
def _(BLUE, GREY, INK_2, ORANGE, ROOT, feature_picker, json, mo, pd, plt):
    _auc = pd.DataFrame(json.loads((ROOT / "reports" / "drift_metrics.json").read_text(encoding="utf-8"))["E1"]["by_month"]).set_index("month")
    _auc.index = pd.PeriodIndex(_auc.index, freq="M").to_timestamp()
    _names = {"promised_days": "promised days", "distance_km": "distance", "route_rate": "route late-rate history",
              "seller_prior_late_rate": "seller late-rate history", "recent_rate_28d": "trailing 28-day rate"}
    _colours = [ORANGE, BLUE, GREY, "#6250d6", "#1baf7a"]
    mo.stop(not feature_picker.value, mo.md("_Choose at least one feature._"))
    _fig, _ax = plt.subplots(figsize=(9, 4.2))
    for _col, _colour in zip(feature_picker.value, _colours):
        _ax.plot(_auc.index, _auc[_col], color=_colour, marker="o", markersize=4, label=_names[_col])
    _ax.axhline(0.5, color=INK_2, linewidth=0.8, linestyle="--")
    _ax.text(_auc.index[0], 0.51, "no skill", color=INK_2, fontsize=9)
    _ax.set_ylabel("ROC-AUC within the month")
    _ax.set_title("Single-feature skill by month")
    _ax.legend(frameon=False, loc="lower left")
    mo.vstack([
        _fig,
        mo.md("In August 2018 the promised window and the distance both fall well below 0.5: the promise had been shortened "
              "sharply (75% of that month's orders were promised in under 20 days), and short promises, not long routes, "
              "were the ones that came late. The model had learned that a long promise on a long route is safe; in August "
              "the rule no longer held."),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## Takeaways

    - **The model ranks orders moderately well.** Flagging the riskiest 10% finds late deliveries about 2.8 times better than chance on average (1.2 times in the worst month).
    - **Use it by rank, not by probability.** The monthly late rate cannot be predicted from the past, so the level of its probabilities is unreliable.
    - **It rests on the route and the promise.** Everything else adds little.
    - **It is fragile to policy change.** A sharp change in how delivery dates are promised breaks it; a monitor on the distribution of promised days is worth having.
    - **More features did not help**, and the notebook shows the evidence.

    **Limits.** Six test months, one market, data ending in 2018, no tuning. Details are in [MODEL_CARD.md](../../docs/ml/MODEL_CARD.md).
    """)
    return


if __name__ == "__main__":
    app.run()
