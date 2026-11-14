"""snowflake/ml/scoring_task.sql and the setup grants: non-destructive, and the model call matches the signature."""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = (ROOT / "snowflake" / "ml" / "scoring_task.sql").read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("register_model", ROOT / "snowflake" / "ml" / "register_model.py")
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)


def strip_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def test_predict_proba_arguments_match_the_shared_helper():
    task_args = re.search(r"PREDICT_PROBA\('\s*\|\|\s*(.*?)\|\|\s*'\):output_feature_1", TASK, re.S).group(1)
    task_args = "".join(re.findall(r"'([^']*)'", task_args)).strip().rstrip(",").strip()
    helper_args = re.search(r"PREDICT_PROBA\((.*)\):output_feature_1", rm.predict_proba_sql("V1_X")).group(1)
    assert [a.strip() for a in task_args.split(",")] == [a.strip() for a in helper_args.split(",")]


def test_task_is_idempotent_and_non_destructive():
    code = strip_comments(TASK)
    assert not re.search(r"\b(DROP|TRUNCATE|OR\s+REPLACE)\b", code, re.I)
    assert "CREATE TASK IF NOT EXISTS" in code and "RESUME" not in code.upper()
    assert code.count("CREATE TABLE IF NOT EXISTS") == 2
    assert "WHERE NOT EXISTS (SELECT 1 FROM RETAIL_OLIST.ML.SCORING_CONFIG)" in code
    # replaces only its own (model_version, scored_month) rows, inside one transaction
    assert re.search(r"BEGIN TRANSACTION;\s*DELETE FROM RETAIL_OLIST\.ML\.LATE_DELIVERY_SCORES_REGISTRY WHERE "
                     r"model_version = :v AND scored_month = :m;\s*EXECUTE IMMEDIATE :stmt;", code)
    assert "ROLLBACK" in code


def test_task_never_writes_the_backtest_scores_table():
    code = strip_comments(TASK)
    assert not re.search(r"(INSERT INTO|DELETE FROM)\s+RETAIL_OLIST\.ML\.LATE_DELIVERY_SCORES\b(?!_)", code)


def test_run_id_follows_the_project_format():
    assert "'YYYYMMDD\"T\"HH24MISS\"Z\"'" in TASK and "LEFT(MD5(UUID_STRING()), 8)" in TASK
    assert rm.version_name("abc1234", "20261113") == "V1_20261113_ABC1234"


def test_setup_files_are_additive_and_keep_placeholders():
    for name in ("07_git_workspace.sql", "08_scoring_task_grants.sql"):
        code = strip_comments((ROOT / "snowflake" / "setup" / name).read_text(encoding="utf-8"))
        assert not re.search(r"\b(DROP|TRUNCATE|OR\s+REPLACE)\b", code, re.I), name
    git = (ROOT / "snowflake" / "setup" / "07_git_workspace.sql").read_text(encoding="utf-8")
    assert "IF NOT EXISTS RETAIL_GIT_API" in git and "<https://github.com/ACCOUNT>" in git
