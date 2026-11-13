-- 08_scoring_task_grants.sql  --  let RETAIL_TRANSFORMER own and run the scheduled scoring task
-- (snowflake/ml/scoring_task.sql).
--
-- EXECUTE TASK   account-level: lets the role's tasks run (on schedule or with EXECUTE TASK). It does not let the
--                role create objects or read anything new; the task still runs with RETAIL_TRANSFORMER's own grants.
-- CREATE TASK    on RETAIL_OLIST.ML only.
-- The task uses RETAIL_WH, so its run time counts against RETAIL_MONITOR (5 credits a month).
--
-- Needs ACCOUNTADMIN (EXECUTE TASK) and the schema owner SYSADMIN (CREATE TASK). Re-running is safe. To undo:
--     REVOKE EXECUTE TASK ON ACCOUNT FROM ROLE RETAIL_TRANSFORMER;
--     REVOKE CREATE TASK ON SCHEMA RETAIL_OLIST.ML FROM ROLE RETAIL_TRANSFORMER;

USE ROLE ACCOUNTADMIN;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE RETAIL_TRANSFORMER;

USE ROLE SYSADMIN;
GRANT CREATE TASK ON SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_TRANSFORMER;

SHOW GRANTS TO ROLE RETAIL_TRANSFORMER;
