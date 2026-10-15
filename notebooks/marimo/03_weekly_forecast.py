import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="Weekly forecast")


@app.cell
def _():
    import sys
    from pathlib import Path

    import duckdb
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from matplotlib.patches import Patch

    ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists())
    sys.path.insert(0, str(ROOT / "src" / "ml"))
    import forecast_baseline as fb
    import forecast_models as fm

    return ROOT, duckdb, fb, fm, mo, np, pd, plt


@app.cell
def _(plt):
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
    # one colour per method, fixed, so a method keeps its colour whatever is selected
    METHOD_NAMES = {
        "naive_last_week": "naive", "moving_average_8": "8-week average", "simple_exp_smoothing": "exp. smoothing",
        "damped_trend": "damped trend", "ar1_trend_26w": "AR(1) + trend", "combo_naive_ma8": "combination",
    }
    METHOD_COLOURS = {
        "naive_last_week": GREY, "moving_average_8": BLUE, "simple_exp_smoothing": "#6250d6",
        "damped_trend": "#1baf7a", "ar1_trend_26w": "#e87ba4", "combo_naive_ma8": ORANGE,
    }
    return BLUE, GRID, INK, METHOD_COLOURS, METHOD_NAMES, ORANGE


@app.cell
def _(mo):
    mo.md("""
    # Weekly order forecast (interactive)

    **Question.** How many orders will the marketplace receive next week, and which simple method forecasts it best?

    This is the interactive version of [`03_weekly_forecast.ipynb`](../03_weekly_forecast.ipynb). The methods are deliberately simple because there are only 85 clean weeks of data. The logic is the tested code in `src/ml/`; the written summary is [docs/ml/MODEL_CARD.md](../../docs/ml/MODEL_CARD.md).

    **To run it:** build the warehouse first, then `uv run marimo edit notebooks/marimo/03_weekly_forecast.py`.

    **What to expect.** No method clearly beats the simplest ones, and the charts show why the more complex methods cannot be trusted on this little history.
    """)
    return


@app.cell
def _(ROOT, duckdb, fb, mo):
    _warehouse = ROOT / "warehouse.duckdb"
    mo.stop(
        not _warehouse.exists(),
        mo.md("**warehouse.duckdb not found.** Run `uv run python src/transformation/build_warehouse.py` first."),
    )
    _con = duckdb.connect(str(_warehouse), read_only=True)
    weekly = fb.weekly_series(_con)  # orders and net item revenue per ISO week
    _con.close()
    main_series = weekly.loc[fb.FIRST_WEEK:fb.LAST_CLEAN_WEEK]
    mo.md(f"**{len(main_series)}** clean weeks ({fb.FIRST_WEEK.date()} to {fb.LAST_CLEAN_WEEK.date()}) out of "
          f"{len(weekly)} weeks in the data.")
    return main_series, weekly


@app.cell
def _(mo):
    mo.md("""
    ## 1. The series, and which weeks are used

    The first weeks (late 2016) are tiny and the last weeks are cut off because the extract ends mid-week. Only the weeks between the shaded regions are used.
    """)
    return


@app.cell
def _(BLUE, GRID, fb, pd, plt, weekly):
    _w = weekly.loc["2016-12-19":]
    _fig, (_a, _b) = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True)
    for _ax, _column, _title in [(_a, "orders", "Orders per week"), (_b, "revenue", "Net item revenue per week (R$)")]:
        _ax.plot(_w.index, _w[_column], color=BLUE)
        _ax.axvspan(_w.index[0], fb.FIRST_WEEK, color=GRID, alpha=0.8, linewidth=0)
        _ax.axvspan(fb.LAST_CLEAN_WEEK + pd.Timedelta(days=7), _w.index[-1] + pd.Timedelta(days=7), color=GRID, alpha=0.8, linewidth=0)
        _ax.set_title(_title)
    _bf = fb.BLACK_FRIDAY_WEEKS[0]
    _a.annotate("Black Friday week\n(the only one in the data)", (_bf, _w.loc[_bf, "orders"]), xytext=(-140, -4),
                textcoords="offset points", fontsize=9, arrowprops={"arrowstyle": "-", "color": "#52514e"})
    _a.text(_w.index[1], _a.get_ylim()[1] * 0.85, "too few orders", fontsize=8.5, color="#52514e")
    _a.text(fb.LAST_CLEAN_WEEK + pd.Timedelta(days=9), _a.get_ylim()[1] * 0.85, "extract\ncut off", fontsize=8.5, color="#52514e")
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    Orders grew roughly tenfold through 2017 and then flattened around 6,000 to 7,000 a month in 2018. There is **one** Black Friday in the data (week of 2017-11-20), so whether it is a repeating seasonal peak cannot be tested.

    ## 2. How forecasts are tested

    For every week from the 27th onward, each method is shown only the weeks *up to that point* and asked for the next week (or the week four ahead). Then the origin moves forward one week. That gives 59 one-week and 56 four-week forecasts per method; no method ever sees a week it is forecasting.

    | method | idea |
    |---|---|
    | naive | repeat last week |
    | 8-week average | the average of the last eight weeks |
    | exp. smoothing | a weighted average favouring recent weeks, weight fitted to the history |
    | damped trend | a level plus a trend that fades out |
    | AR(1) + trend | a small regression on last week and a time trend |
    | combination | the average of the naive and 8-week-average forecasts |
    """)
    return


@app.cell
def _(fb, fm, main_series, mo):
    backtests = {(t, h): fb.backtest(main_series[t], h, fm.MODELS) for t in ("orders", "revenue") for h in fb.HORIZONS}
    scores = {key: fb.score(bt) for key, bt in backtests.items()}
    mo.md(f"Backtests done: {len(backtests[('orders', 1)])} one-week and {len(backtests[('orders', 4)])} four-week "
          "forecasts per method and target.")
    return backtests, scores


@app.cell
def _(METHOD_NAMES, mo):
    target_picker = mo.ui.radio(options={"orders": "orders", "revenue (R$)": "revenue"}, value="orders", label="Forecast target")
    horizon_picker = mo.ui.radio(options={"1 week ahead": 1, "4 weeks ahead": 4}, value="1 week ahead", label="Horizon")
    method_picker = mo.ui.multiselect(
        options={v: k for k, v in METHOD_NAMES.items()}, value=["naive", "combination"], label="Methods to draw")
    mo.hstack([target_picker, horizon_picker, method_picker], justify="start", gap=2)
    return horizon_picker, method_picker, target_picker


@app.cell
def _(
    INK,
    METHOD_COLOURS,
    METHOD_NAMES,
    backtests,
    fb,
    horizon_picker,
    method_picker,
    mo,
    plt,
    target_picker,
):
    mo.stop(not method_picker.value, mo.md("_Choose at least one method._"))
    _bt = backtests[(target_picker.value, horizon_picker.value)]
    _fig, _ax = plt.subplots(figsize=(9.5, 4.4))
    _ax.plot(_bt.index, _bt["actual"], color=INK, linewidth=2.6, label=f"actual {target_picker.value}")
    for _m in method_picker.value:
        _ax.plot(_bt.index, _bt[_m], color=METHOD_COLOURS[_m], linewidth=1.6, label=METHOD_NAMES[_m])
    _bf = fb.BLACK_FRIDAY_WEEKS[0]
    if _bf in _bt.index:
        _ax.annotate("Black Friday", (_bf, _bt.loc[_bf, "actual"]), xytext=(-90, -6), textcoords="offset points", fontsize=9,
                     arrowprops={"arrowstyle": "-", "color": "#52514e"})
    _ax.set_title(f"Forecast {horizon_picker.value} week{'s' if horizon_picker.value > 1 else ''} ahead, {target_picker.value} per week")
    _ax.set_ylabel(target_picker.value)
    _ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=len(method_picker.value) + 1)
    _fig
    return


@app.cell
def _(
    METHOD_COLOURS,
    METHOD_NAMES,
    horizon_picker,
    plt,
    scores,
    target_picker,
):
    _s = scores[(target_picker.value, horizon_picker.value)]
    _order = list(METHOD_NAMES)
    _mae = [_s[m]["mae"] for m in _order]
    _fig, _ax = plt.subplots(figsize=(9, 4.2))
    _ax.bar([METHOD_NAMES[m] for m in _order], _mae, color=[METHOD_COLOURS[m] for m in _order], width=0.62)
    _ax.axhline(_mae[0], color="#52514e", linestyle="--", linewidth=1)
    for _i, (_v, _m) in enumerate(zip(_mae, _order)):
        # labels sit above both the bar and the dashed naive line, so the line never runs through the text
        _ax.text(_i, max(_v, _mae[0]) * 1.02, f"{_v:,.0f}\n({_s[_m]['mae_vs_naive']:.2f}x naive)", ha="center", fontsize=8.5)
    _ax.set_ylim(0, max(_mae) * 1.22)
    _ax.set_ylabel(f"mean absolute error ({target_picker.value})")
    _ax.set_title(f"Forecast error by method, {horizon_picker.value} week{'s' if horizon_picker.value > 1 else ''} ahead (dashed line: naive)")
    _ax.grid(axis="x", visible=False)
    plt.setp(_ax.get_xticklabels(), rotation=20, ha="right", fontsize=9)
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    For **orders**: one week ahead, the combination has the smallest error (about 183 orders, 10% below naive), while smoothing and the regressions are no better than repeating last week. Four weeks ahead, the 8-week average is best (about 272, 23% below naive), and the damped trend and the regression are *worse* than naive. Switch the target to **revenue** and see how the ranking changes.

    ## 3. When do the errors happen?
    """)
    return


@app.cell
def _(
    METHOD_COLOURS,
    METHOD_NAMES,
    backtests,
    horizon_picker,
    method_picker,
    mo,
    plt,
    target_picker,
):
    mo.stop(not method_picker.value, mo.md("_Choose at least one method above._"))
    _bt = backtests[(target_picker.value, horizon_picker.value)]
    _fig, _ax = plt.subplots(figsize=(9.5, 3.8))
    for _m in dict.fromkeys(["naive_last_week", *method_picker.value]):
        _ax.plot(_bt.index, (_bt["actual"] - _bt[_m]).abs(), color=METHOD_COLOURS[_m], label=METHOD_NAMES[_m])
    _ax.set_title("Absolute error each week")
    _ax.set_ylabel(target_picker.value)
    _ax.legend(frameon=False)
    _share = {METHOD_NAMES[_m]: ((_bt["actual"] - _bt[_m]).abs() < (_bt["actual"] - _bt["naive_last_week"]).abs()).mean()
              for _m in method_picker.value if _m != "naive_last_week"}
    mo.vstack([
        _fig,
        mo.md("Share of weeks where each selected method beats naive: " + (", ".join(f"**{k}** {v:.0%}" for k, v in _share.items()) or "n/a")
              + ". The biggest errors cluster around Black Friday and the weeks after, when the series jumps and then falls back."),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 4. Can this backtest rank the methods? Not reliably.

    The same methods run on **revenue**, which moves with orders. If the backtest could really tell good methods from bad, the ranking should be similar. Each dot is a method's error divided by the naive error (below 1 beats naive):
    """)
    return


@app.cell
def _(BLUE, METHOD_NAMES, ORANGE, fb, np, plt, scores):
    _order = list(METHOD_NAMES)
    _fig, _axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for _ax, _h in zip(_axes, fb.HORIZONS):
        _y = np.arange(len(_order))[::-1]
        _o = [scores[("orders", _h)][m]["mae_vs_naive"] for m in _order]
        _r = [scores[("revenue", _h)][m]["mae_vs_naive"] for m in _order]
        for _yi, _a, _b in zip(_y, _o, _r):
            _ax.plot([_a, _b], [_yi, _yi], color="#e4e3de", linewidth=2, zorder=1)
        _ax.scatter(_o, _y, color=BLUE, s=55, zorder=3, label="orders")
        _ax.scatter(_r, _y, color=ORANGE, s=55, zorder=3, label="revenue")
        _ax.axvline(1.0, color="#52514e", linestyle="--", linewidth=1)
        _ax.set_yticks(_y)
        _ax.set_yticklabels([METHOD_NAMES[m] for m in _order])
        _ax.set_title(f"{_h} week{'s' if _h > 1 else ''} ahead")
        _ax.set_xlabel("error relative to naive (below 1 beats naive)")
        _ax.grid(axis="y", visible=False)
    _axes[0].legend(frameon=False, loc="lower right")
    plt.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md("""
    Look at the AR(1) + trend row: for orders it is among the worst methods (about 1.1 times the naive error one week ahead, 1.5 times four weeks ahead); for revenue it is among the best (about 0.87 and 0.76). Two series that rise and fall together should not rank a method so differently, so **85 weeks are too few to tell these methods apart**.

    ## Takeaways

    - **One week ahead:** the average of the naive forecast and the 8-week average. **Four weeks ahead:** the 8-week average.
    - **Do not trust the fancier methods on this little history.** Their rankings flip between orders and revenue.
    - **The combination was assembled after seeing that its two parts were the baseline winners**, so its advantage is optimistic; it beats naive in only half the weeks.
    - **Every method under-forecasts on average** (orders grew through 2017) and **none anticipates Black Friday**; with one occurrence, seasonality cannot be learned.
    - **More data would help more than a cleverer method**, in particular a second year.

    **Limits.** 85 weeks, one marketplace, data ending in 2018, no tuning. Full tables are in [reports/forecast_models_metrics.json](../../reports/forecast_models_metrics.json).
    """)
    return


if __name__ == "__main__":
    app.run()
