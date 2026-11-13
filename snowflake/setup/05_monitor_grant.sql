-- 05_monitor_grant.sql  --  let the pipeline's own roles read RETAIL_MONITOR, so credit use can be measured
-- without an ACCOUNTADMIN session (snowflake/monitoring/credit_usage.py).
--
-- MONITOR on a resource monitor is read-only: it shows the quota, used and remaining credits and the
-- triggers in SHOW RESOURCE MONITORS. It cannot change the quota (that is MODIFY) and shows nothing about
-- other warehouses or other projects on the account. RETAIL_MONITOR is attached only to RETAIL_WH.
--
-- Needs ACCOUNTADMIN (only it can grant privileges on resource monitors). Run after 03_resource_monitor.sql.
-- Re-running is safe: granting a privilege a role already holds is a no-op. To undo:
--     REVOKE MONITOR ON RESOURCE MONITOR RETAIL_MONITOR FROM ROLE RETAIL_TRANSFORMER;
--
-- Not granted here, deliberately: the SNOWFLAKE.USAGE_VIEWER database role or MONITOR USAGE ON ACCOUNT.
-- Either would give per-hour metering (WAREHOUSE_METERING_HISTORY), but for every warehouse on the
-- account, including other projects'. Grant one only if that is acceptable.

USE ROLE ACCOUNTADMIN;

GRANT MONITOR ON RESOURCE MONITOR RETAIL_MONITOR TO ROLE RETAIL_TRANSFORMER;

SHOW RESOURCE MONITORS LIKE 'RETAIL_MONITOR';
