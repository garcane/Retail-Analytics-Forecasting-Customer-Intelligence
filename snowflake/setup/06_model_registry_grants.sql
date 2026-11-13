-- 06_model_registry_grants.sql  --  let RETAIL_TRANSFORMER register models in RETAIL_OLIST.ML
-- (snowflake/ml/register_model.py, Snowflake Model Registry).
--
-- CREATE MODEL   creates the MODEL object and its versions (Registry.log_model).
-- CREATE STAGE   needed on every in-warehouse scoring call from Python: ModelVersion.run with a pandas frame
--                (register_model.py --verify, and the check after --register) uploads the input through
--                write_pandas, which puts it on a TEMPORARY stage and a temporary table in ML (the table uses
--                the CREATE TABLE on ML from 02_grants.sql). snowflake-ml-python's fallback model upload also
--                uses a SCOPED TEMPORARY stage here. All are dropped at the end of the session.
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
