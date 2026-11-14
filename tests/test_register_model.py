"""snowflake/ml/register_model.py without Snowflake: gate, dry run, version naming, no replacement, pinned deps, verify."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("src", "src/ml"):
    sys.path.insert(0, str(ROOT / sub))
spec = importlib.util.spec_from_file_location("register_model", ROOT / "snowflake" / "ml" / "register_model.py")
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)

from data_access.backend import ConfirmationRequired  # noqa: E402


def feature_frame(n=400, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.normal(size=n) for c in rm.ldb.NUMERIC_V1})
    for c in rm.ldb.CATEGORICAL:
        df[c] = rng.choice(["SP", "RJ", "MG"], size=n)
    df["purchase_ts"] = pd.Timestamp("2017-06-01") + pd.to_timedelta(rng.integers(0, 400, n), unit="D")
    df["is_late"] = (rng.random(n) < 0.2).astype(int)
    return df


class FakeDB:
    raw = object()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeVersion:
    def __init__(self, model):
        self.model = model

    def run(self, X, function_name):
        assert function_name == "predict_proba"
        p = self.model.predict_proba(X)
        return X.assign(output_feature_0=p[:, 0], output_feature_1=p[:, 1])


class FakeModelRef:
    def __init__(self, reg):
        self.reg = reg
        self.default = None

    def versions(self):
        return [type("V", (), {"version_name": v})() for v in self.reg.logged]

    def version(self, name):
        return FakeVersion(self.reg.model)


class FakeRegistry:
    def __init__(self, existing=()):
        self.logged = list(existing)
        self.log_kwargs = None
        self.model = None
        self.ref = FakeModelRef(self)

    def models(self):
        return [type("M", (), {"name": rm.MODEL_NAME})()] if self.logged else []

    def get_model(self, name):
        return self.ref

    def log_model(self, model, **kw):
        self.log_kwargs = kw
        self.model = model
        self.logged.append(kw["version_name"])
        return FakeVersion(model)


@pytest.fixture
def env(monkeypatch, tmp_path):
    reg = FakeRegistry()
    monkeypatch.setattr(rm, "connect", lambda backend, confirm: FakeDB())
    monkeypatch.setattr(rm, "training_frame", lambda db: feature_frame())
    monkeypatch.setattr(rm, "registry_session", lambda db: (None, reg))
    monkeypatch.setattr(rm, "git_sha", lambda: "abc1234")
    monkeypatch.setattr(rm, "uncommitted_model_code", lambda: "")
    monkeypatch.setattr(rm, "EVIDENCE", tmp_path / "model_registry.json")
    monkeypatch.setattr(rm, "ROOT", tmp_path)
    return reg


def test_refuses_without_confirmation(monkeypatch, capsys):
    def connect(backend, confirm):
        raise ConfirmationRequired("refusing")

    monkeypatch.setattr(rm, "connect", connect)
    assert rm.main([]) == 1 and "refusing" in capsys.readouterr().err


def test_dry_run_is_the_default_and_registers_nothing(env, capsys):
    assert rm.main(["--yes"]) == 0
    assert env.log_kwargs is None and "dry run" in capsys.readouterr().out
    assert not rm.EVIDENCE.exists()


def test_register_logs_a_pinned_version_sets_default_and_checks_parity(env):
    assert rm.main(["--yes", "--register"]) == 0
    kw = env.log_kwargs
    assert kw["model_name"] == "LATE_DELIVERY_RISK" and kw["version_name"].startswith("V1_") and kw["version_name"].endswith("_ABC1234")
    assert kw["options"] == {"relax_version": False}
    assert kw["conda_dependencies"] == [f"scikit-learn=={__import__('sklearn').__version__}"]
    assert kw["target_platforms"] == ["WAREHOUSE"]
    assert kw["metrics"]["git_commit"] == "abc1234" and "backtest_roc_auc" in kw["metrics"]
    assert env.ref.default == kw["version_name"]
    evidence = json.loads(rm.EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["warehouse_parity"]["within_tolerance"] is True and evidence["warehouse_parity"]["max_abs_diff"] == 0


def test_an_existing_version_is_never_replaced(env, capsys):
    rm.main(["--yes", "--register"])
    first = env.log_kwargs
    env.log_kwargs = None
    assert rm.main(["--yes", "--register"]) == 2
    assert env.log_kwargs is None and "already exists" in capsys.readouterr().err
    assert env.logged == [first["version_name"]]


def test_verify_scores_an_existing_version_without_logging(env):
    rm.main(["--yes", "--register"])
    version = env.logged[0]
    env.log_kwargs = None
    assert rm.main(["--yes", "--verify", version.lower()]) == 0
    assert env.log_kwargs is None and env.logged == [version]


def test_verify_unknown_version_fails(env, capsys):
    assert rm.main(["--yes", "--verify", "V1_NOPE"]) == 2 and "no version" in capsys.readouterr().err


def test_failed_scoring_is_recorded_and_returns_nonzero(env, monkeypatch):
    def broken(mv, model, sample):
        raise RuntimeError("Anaconda terms not accepted")

    monkeypatch.setattr(rm, "warehouse_parity", broken)
    assert rm.main(["--yes", "--register"]) == 3
    assert "Anaconda" in json.loads(rm.EVIDENCE.read_text(encoding="utf-8"))["warehouse_parity"]["error"]


def test_backtest_metrics_come_from_the_snowflake_backtest_file():
    m = rm.backtest_metrics()
    real = json.loads((ROOT / "reports/snowflake/late_delivery_metrics.json").read_text())["macro_average"]["logistic_regression_v1"]
    assert m["roc_auc"] == pytest.approx(real["roc_auc"]) and m["pr_auc"] == pytest.approx(real["pr_auc"])


def test_version_name_is_an_identifier():
    assert rm.version_name("cc90dc8", "20261113") == "V1_20261113_CC90DC8"


def test_register_refuses_uncommitted_model_code_before_connecting(env, monkeypatch, capsys):
    monkeypatch.setattr(rm, "uncommitted_model_code", lambda: " M src/ml/late_delivery_baseline.py")
    monkeypatch.setattr(rm, "connect", lambda *a, **k: pytest.fail("connected despite uncommitted model code"))
    assert rm.main(["--yes", "--register"]) == 4
    assert env.log_kwargs is None and "uncommitted" in capsys.readouterr().err


def test_dry_run_and_verify_do_not_need_a_clean_tree(env, monkeypatch):
    monkeypatch.setattr(rm, "uncommitted_model_code", lambda: " M src/ml/late_delivery_baseline.py")
    assert rm.main(["--yes"]) == 0


def test_model_code_paths_exist():
    assert all((ROOT / p).is_dir() for p in rm.MODEL_CODE)
