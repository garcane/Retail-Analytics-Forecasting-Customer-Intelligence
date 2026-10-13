"""The marimo notebooks are plain Python files; check they are valid marimo apps and stay in step with the project."""

import ast
import subprocess
import sys

import pytest

from conftest import ROOT

NOTEBOOKS = sorted((ROOT / "notebooks" / "marimo").glob("*.py"))
SRC_ML = {p.stem for p in (ROOT / "src" / "ml").glob("*.py")}


def test_both_marimo_notebooks_exist_alongside_the_jupyter_ones():
    assert [p.name for p in NOTEBOOKS] == ["02_late_delivery_model.py", "03_weekly_forecast.py"]
    for name in ("02_late_delivery_model.ipynb", "03_weekly_forecast.ipynb"):
        assert (ROOT / "notebooks" / name).exists()


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_marimo_check_passes(path):
    """marimo's own checker flags a variable defined in two cells, cycles, and malformed cells."""
    result = subprocess.run([sys.executable, "-m", "marimo", "check", str(path)], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_file_is_a_marimo_app_that_only_uses_existing_project_modules(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert any(isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "app" for n in tree.body)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        else:
            continue
        for name in names:
            if name in {"late_delivery_baseline", "explain_late_delivery", "forecast_baseline", "forecast_models"}:
                assert name in SRC_ML


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_no_machine_specific_paths(path):
    source = path.read_text(encoding="utf-8")
    assert "C:\\Users" not in source and "C:/Users" not in source


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_interactive_controls_are_present(path):
    """The point of the marimo versions is interactivity; guard against converting them back to static charts."""
    assert "mo.ui." in path.read_text(encoding="utf-8")
