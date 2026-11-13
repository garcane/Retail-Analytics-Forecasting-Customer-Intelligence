-- 06_model_registry_grants.sql  --  let RETAIL_TRANSFORMER register models in RETAIL_OLIST.ML
-- (snowflake/ml/register_model.py, Snowflake Model Registry).
--
-- CREATE MODEL   creates the MODEL object and its versions (Registry.log_model).
-- CREATE STAGE   only for snowflake-ml-python's fallback upload path, which puts the model files on a
--                SCOPED TEMPORARY stage in the same schema (dropped automatically at the end of the session).
-- Both are limited to the ML schema. Nothing account-wide, nothing on other schemas or other projects.
-- RETAIL_REPORTER is not given the models: Power BI reads scores from ML tables, not the model.
--
-- Needs the schema owner (SYSADMIN) or SECURITYADMIN. Run after 01_objects.sql and 02_grants.sql.
-- Re-running is safe (granting a privilege a role already holds is a no-op). To undo:
--     REVOKE CREATE MODEL, CREATE STAGE ON SCHEMA RETAIL_OLIST.ML FROM ROLE RETAIL_TRANSFORMER;

USE ROLE SYSADMIN;

GRANT CREATE MODEL ON SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_TRANSFORMER;
GRANT CREATE STAGE ON SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_TRANSFORMER;

SHOW GRANTS ON SCHEMA RETAIL_OLIST.ML;
