"""Report RETAIL_WH credit use from the RETAIL_MONITOR resource monitor (read-only).

    python snowflake/monitoring/credit_usage.py           # prints the target and stops
    python snowflake/monitoring/credit_usage.py --yes     # connects and reports

Uses the same environment variables and confirmation gate as src/data_access (see snowflake/README.md, section 2).
The role (RETAIL_SF_ROLE, default RETAIL_TRANSFORMER) needs MONITOR on the monitor: run
snowflake/setup/05_monitor_grant.sql once as ACCOUNTADMIN. Without it the monitor is invisible to the role and this
script says so instead of reporting zero. The figures are Snowflake's own metering for the current monthly cycle.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from data_access import connect
from data_access.backend import ConfirmationRequired, MissingConfigError

MONITOR = "RETAIL_MONITOR"
FIELDS = ("credit_quota", "used_credits", "remaining_credits", "frequency", "start_time", "end_time",
          "notify_at", "suspend_at", "suspend_immediately_at")


def read_monitor(raw) -> dict | None:
    """SHOW RESOURCE MONITORS lists only monitors the current role holds a privilege on."""
    cur = raw.cursor()
    try:
        cur.execute(f"SHOW RESOURCE MONITORS LIKE '{MONITOR}'")
        cols = [d[0].lower() for d in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()
    return dict(zip(cols, rows[0])) if rows else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--yes", action="store_true", help="confirm the printed Snowflake target")
    args = parser.parse_args()
    try:
        db = connect("snowflake", confirm=args.yes)
    except (ConfirmationRequired, MissingConfigError) as exc:
        print(exc, file=sys.stderr)
        return 1
    with db:
        mon = read_monitor(db.raw)
    if mon is None:
        print(f"{MONITOR} is not visible to this role. Run snowflake/setup/05_monitor_grant.sql as ACCOUNTADMIN, "
              f"or run SHOW RESOURCE MONITORS LIKE '{MONITOR}'; as ACCOUNTADMIN in Snowsight.", file=sys.stderr)
        return 2
    for key in FIELDS:
        if key in mon:
            print(f"{key:24s} {mon[key]}")
    try:
        used, quota = float(mon["used_credits"]), float(mon["credit_quota"])
        print(f"{'share of quota':24s} {used / quota:.1%}")
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
