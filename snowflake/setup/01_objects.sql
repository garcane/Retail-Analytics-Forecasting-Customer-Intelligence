-- 01_objects.sql  --  create the project objects (idempotent: CREATE ... IF NOT EXISTS only).
--
-- Creates: database RETAIL_OLIST, schemas RAW / STAGING / INTERMEDIATE / MARTS / PBI / ML,
--          warehouse RETAIL_WH (XSMALL, auto-suspend 60 s, starts suspended),
--          roles RETAIL_LOADER / RETAIL_TRANSFORMER / RETAIL_REPORTER.
-- Does NOT: replace or remove anything, create a resource monitor, or touch account-level settings.
-- Re-running is safe: existing objects are left exactly as they are (IF NOT EXISTS does not
-- alter an existing object, so a pre-existing RETAIL_WH with other settings stays unchanged;
-- the preflight output tells you whether that applies).
--
-- STATUS: written offline; NOT RUN against any Snowflake account (UNVERIFIED).
-- Prerequisite: 00_preflight.sql was run, reviewed and approved.
--
-- Roles needed (standard Snowflake system roles):
--   * SECURITYADMIN (or any role with CREATE ROLE) for the three CREATE ROLE statements.
--   * SYSADMIN (or any role with CREATE DATABASE / CREATE WAREHOUSE) for everything else.
--
-- SINGLE-ROLE FALLBACK: if you cannot use SECURITYADMIN (no CREATE ROLE privilege), skip STEP 1
-- and 02_grants.sql entirely. Run STEP 2 with the one role you do have (replace the USE ROLE line),
-- then set RETAIL_SF_ROLE to that role for the loader, dbt, Python and Power BI. Least-privilege
-- separation between loader / transformer / reporter is then NOT in force (documented trade-off).

-- ---------------------------------------------------------------------------------------------
-- STEP 1: roles
-- ---------------------------------------------------------------------------------------------
USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS RETAIL_LOADER      COMMENT = 'Retail Olist: loads CSV files into RETAIL_OLIST.RAW';
CREATE ROLE IF NOT EXISTS RETAIL_TRANSFORMER COMMENT = 'Retail Olist: dbt + Python; reads RAW, builds STAGING..PBI, writes ML';
CREATE ROLE IF NOT EXISTS RETAIL_REPORTER    COMMENT = 'Retail Olist: read-only for Power BI (PBI views, ML tables)';

-- ---------------------------------------------------------------------------------------------
-- STEP 2: database, schemas, warehouse
-- ---------------------------------------------------------------------------------------------
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS RETAIL_OLIST COMMENT = 'Olist e-commerce analytics (Snowflake + dbt implementation)';

CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.RAW          COMMENT = 'Verbatim CSV loads, all VARCHAR, plus load metadata';
CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.STAGING      COMMENT = 'dbt staging views (typed, renamed)';
CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.INTERMEDIATE COMMENT = 'dbt intermediate views';
CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.MARTS        COMMENT = 'dbt star schema + analytics marts';
CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.PBI          COMMENT = 'Power BI-facing views';
CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.ML           COMMENT = 'Python-written model outputs (scores, backtest, flag share)';

CREATE WAREHOUSE IF NOT EXISTS RETAIL_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
         AUTO_SUSPEND = 60
         AUTO_RESUME = TRUE
         INITIALLY_SUSPENDED = TRUE
         COMMENT = 'Retail Olist: single XSMALL warehouse, suspends after 60 s idle';
