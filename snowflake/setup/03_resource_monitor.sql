-- 03_resource_monitor.sql  --  credit cap for the project warehouse (idempotent).
--
-- Creates resource monitor RETAIL_MONITOR: 5 credits per calendar month on RETAIL_WH.
--   75 %  -> email notification to account admins with verified emails
--   100 % -> SUSPEND (running queries finish, no new ones start)
--   110 % -> SUSPEND_IMMEDIATE (running queries are cancelled)
-- The quota resets monthly. An XSMALL warehouse uses 1 credit per running hour, so 5 credits is far
-- above a full load + dbt build (minutes of runtime) and only bites on runaway work.
--
-- Needs ACCOUNTADMIN (resource monitors are account-level objects). Run after 01_objects.sql.
-- Re-running is safe: IF NOT EXISTS leaves an existing monitor unchanged, and the ALTER only (re)attaches it.
-- To change the quota later:  ALTER RESOURCE MONITOR RETAIL_MONITOR SET CREDIT_QUOTA = <n>;

USE ROLE ACCOUNTADMIN;

CREATE RESOURCE MONITOR IF NOT EXISTS RETAIL_MONITOR
    WITH CREDIT_QUOTA = 5
         FREQUENCY = MONTHLY
         START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 75 PERCENT DO NOTIFY
             ON 100 PERCENT DO SUSPEND
             ON 110 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE RETAIL_WH SET RESOURCE_MONITOR = RETAIL_MONITOR;

SHOW RESOURCE MONITORS LIKE 'RETAIL_MONITOR';
