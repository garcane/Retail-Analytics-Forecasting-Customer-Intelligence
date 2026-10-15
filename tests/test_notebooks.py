"""The ML notebooks are committed with their outputs; make sure they were run cleanly and still match the code."""

import ast

import nbformat
import pytest

from conftest import ROOT

NOTEBOOKS = ["02_late_delivery_model.ipynb", "03_weekly_forecast.ipynb"]
MODULES = {p.stem for p in (ROOT / "src" / "ml").glob("*.py")}


@pytest.fixture(scope="module", params=NOTEBOOKS)
def notebook(request):
    return nbformat.read(ROOT / "notebooks" / request.param, as_version=4)


def code_cells(nb):
    return [c for c in nb.cells if c.cell_type == "code"]


def test_every_code_cell_was_executed_without_error(notebook):
    for i, cell in enumerate(code_cells(notebook)):
        assert cell.execution_count is not None, f"code cell {i} was never run"
        assert not [o for o in cell.outputs if o.output_type == "error"], f"code cell {i} stored an error"


def test_the_charts_are_stored_in_the_notebook(notebook):
    figures = sum(1 for c in code_cells(notebook) for o in c.outputs if "image/png" in o.get("data", {}))
    assert figures >= 5


def test_notebook_code_parses_and_only_imports_modules_that_exist(notebook):
    for cell in code_cells(notebook):
        tree = ast.parse(cell.source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            for name in names:
                # project modules must exist under src/ml; everything else is a normal package
                if name in {"late_delivery_baseline", "explain_late_delivery", "forecast_baseline", "forecast_models"}:
                    assert name in MODULES


def test_the_notebooks_do_not_hard_code_machine_specific_paths(notebook):
    for cell in notebook.cells:
        assert "C:\\Users" not in cell.source and "C:/Users" not in cell.source
