-- 02_grants.sql  --  least-privilege grants for the three project roles (additive GRANTs only).
--
-- Prerequisite: 01_objects.sql has been run (STEP 1 and STEP 2).
-- Run as SECURITYADMIN (or any role holding MANAGE GRANTS). Not needed in the single-role fallback.
--
-- Privilege model:
--   RETAIL_LOADER       owns what it creates in RAW (tables, stage, file format). Writes RAW only.
--   RETAIL_TRANSFORMER  reads RAW; creates tables/views in STAGING, INTERMEDIATE, MARTS, PBI, ML.
--                       CREATE SCHEMA on the database is needed ONLY for the dbt dev target, which
--                       creates <DBT_DEV_SUFFIX>_STAGING etc. Revoke it if you only use the prod target.
--   RETAIL_REPORTER     read-only: PBI views and ML tables (Power BI). Nothing else.
--
-- Future grants cover objects created later (dbt rebuilds, new ML tables). They apply to objects
-- created by ANY role in the schema, so they do not depend on who runs the DDL.
--
-- STATUS: written offline; NOT RUN against any Snowflake account (UNVERIFIED).

USE ROLE SECURITYADMIN;

-- ---------------------------------------------------------------------------------------------
-- Role hierarchy and membership
-- ---------------------------------------------------------------------------------------------
GRANT ROLE RETAIL_LOADER      TO ROLE SYSADMIN;
GRANT ROLE RETAIL_TRANSFORMER TO ROLE SYSADMIN;
GRANT ROLE RETAIL_REPORTER    TO ROLE SYSADMIN;

-- Grant the roles to the user running this script (default: yourself). To grant to a different
-- user, change the next line to e.g.  SET RETAIL_GRANTEE_USER = 'SOME_USER';
SET RETAIL_GRANTEE_USER = CURRENT_USER();
GRANT ROLE RETAIL_LOADER      TO USER IDENTIFIER($RETAIL_GRANTEE_USER);
GRANT ROLE RETAIL_TRANSFORMER TO USER IDENTIFIER($RETAIL_GRANTEE_USER);
GRANT ROLE RETAIL_REPORTER    TO USER IDENTIFIER($RETAIL_GRANTEE_USER);

-- ---------------------------------------------------------------------------------------------
-- Warehouse and database
-- ---------------------------------------------------------------------------------------------
GRANT USAGE ON WAREHOUSE RETAIL_WH TO ROLE RETAIL_LOADER;
GRANT USAGE ON WAREHOUSE RETAIL_WH TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE ON WAREHOUSE RETAIL_WH TO ROLE RETAIL_REPORTER;

GRANT USAGE ON DATABASE RETAIL_OLIST TO ROLE RETAIL_LOADER;
GRANT USAGE ON DATABASE RETAIL_OLIST TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE ON DATABASE RETAIL_OLIST TO ROLE RETAIL_REPORTER;

GRANT CREATE SCHEMA ON DATABASE RETAIL_OLIST TO ROLE RETAIL_TRANSFORMER;  -- dbt dev target only

-- ---------------------------------------------------------------------------------------------
-- RAW: loader writes, transformer reads
-- ---------------------------------------------------------------------------------------------
GRANT USAGE, CREATE TABLE, CREATE STAGE, CREATE FILE FORMAT ON SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT SELECT, INSERT, TRUNCATE ON ALL TABLES    IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT SELECT, INSERT, TRUNCATE ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT USAGE ON ALL FILE FORMATS    IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT USAGE ON FUTURE FILE FORMATS IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT READ, WRITE ON ALL STAGES    IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;
GRANT READ, WRITE ON FUTURE STAGES IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_LOADER;

GRANT USAGE ON SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_TRANSFORMER;
GRANT SELECT ON ALL TABLES    IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_TRANSFORMER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_TRANSFORMER;

-- ---------------------------------------------------------------------------------------------
-- Build schemas: transformer creates and owns the objects
-- ---------------------------------------------------------------------------------------------
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA RETAIL_OLIST.STAGING      TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA RETAIL_OLIST.INTERMEDIATE TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA RETAIL_OLIST.MARTS        TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE, CREATE TABLE, CREATE VIEW ON SCHEMA RETAIL_OLIST.PBI          TO ROLE RETAIL_TRANSFORMER;
GRANT USAGE, CREATE TABLE ON SCHEMA RETAIL_OLIST.ML                        TO ROLE RETAIL_TRANSFORMER;

-- ML tables are written by the Python write-back as RETAIL_TRANSFORMER (create-if-not-exists,
-- delete-by-run_id + insert). If another role created a table first, these cover it.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_TRANSFORMER;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_TRANSFORMER;

-- ---------------------------------------------------------------------------------------------
-- Reporter: Power BI reads PBI views and ML tables only
-- (PBI views read MARTS through the owner's rights, so no MARTS grant is needed for the reporter)
-- ---------------------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER;
GRANT SELECT ON ALL VIEWS     IN SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER;
GRANT SELECT ON ALL TABLES    IN SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER;

GRANT USAGE ON SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_REPORTER;
GRANT SELECT ON ALL TABLES    IN SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_REPORTER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_REPORTER;
