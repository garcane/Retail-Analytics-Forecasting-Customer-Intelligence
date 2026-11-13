"""The Snowflake notebooks (notebooks/snowflake/): generated, in sync, parseable, and free of local-only access."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "snowflake"
NOTEBOOKS = sorted(OUT.glob("*.ipynb"))


def code_cells(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            for c in nb["cells"] if c["cell_type"] == "code"]


def test_the_three_notebooks_exist_and_are_up_to_date():
    assert [p.name for p in NOTEBOOKS] == ["02_late_delivery_model_sf.ipynb", "03_weekly_forecast_sf.ipynb",
                                           "04_train_register_sf.ipynb"]
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_snowflake_notebooks.py"), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_cells_parse_and_use_the_notebook_session(path):
    cells = code_cells(path)
    for src in cells:
        python = "\n".join(line for line in src.splitlines() if not line.lstrip().startswith(("%", "!")))
        ast.parse(python)
    joined = "\n".join(cells)
    assert "from_active_session()" in joined
    assert "duckdb.connect" not in joined and "warehouse.duckdb" not in joined.replace('"warehouse.duckdb"', "")
    for forbidden in ("C:\\Users", "C:/Users", "SNOWFLAKE_PRIVATE_KEY", "os.environ", ".env"):
        assert forbidden not in joined, forbidden


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebooks_store_no_outputs(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    assert all(not c.get("outputs") for c in nb["cells"] if c["cell_type"] == "code")


def test_ported_notebooks_keep_every_original_analysis_cell():
    for original, ported in (("02_late_delivery_model.ipynb", "02_late_delivery_model_sf.ipynb"),
                             ("03_weekly_forecast.ipynb", "03_weekly_forecast_sf.ipynb")):
        orig = code_cells(ROOT / "notebooks" / original)
        port = code_cells(OUT / ported)
        # install cell + setup cell + every original cell after setup + a final check cell
        assert len(port) == len(orig) + 2
        assert "checks passed" in port[-1]


def test_requirements_pin_the_versions_the_results_depend_on():
    reqs = (OUT / "requirements.txt").read_text(encoding="utf-8").split()
    assert "scikit-learn==1.9.1" in reqs and "snowflake-ml-python==2.8.0" in reqs and "duckdb" in reqs


def test_train_register_notebook_never_sets_the_default_version():
    joined = "\n".join(code_cells(OUT / "04_train_register_sf.ipynb"))
    assert ".default" not in joined and "V1WS_" in joined and "rm.log_kwargs(" in joined
