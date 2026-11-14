-- 00_preflight.sql  --  READ-ONLY.  Run this FIRST and review the output before anything else.
--
-- Purpose: show who/where you are and whether any RETAIL% database, warehouse or role already
-- exists in this Snowflake account (so 01_objects.sql cannot collide with another project's objects).
-- Every statement below is a SHOW or a plain SELECT. Nothing here creates, alters or removes anything.
--
-- STATUS: written offline; NOT RUN against any Snowflake account (UNVERIFIED).
-- Gate: do not run 01_objects.sql / 02_grants.sql until the output of this file has been reviewed
-- and approved by the account owner.

SHOW DATABASES LIKE 'RETAIL%';
SHOW WAREHOUSES LIKE 'RETAIL%';
SHOW ROLES LIKE 'RETAIL%';
SELECT CURRENT_ACCOUNT() AS account, CURRENT_ROLE() AS role, CURRENT_USER() AS user_name;
