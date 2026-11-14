-- 04_service_user.sql  --  key-pair service user for the local pipeline (load_raw.py, dbt, Python).
--
-- Creates RETAIL_SVC (TYPE = SERVICE: no password, no MFA prompt, key-pair only) and grants it the
-- loader and transformer roles. It is separate from any other project's service user, so revoking or
-- rotating it touches nothing else.
--
-- Before running, replace <RSA_PUBLIC_KEY> with the public key body (the base64 between the
-- BEGIN/END PUBLIC KEY lines, no line breaks). Generate the pair on the machine that runs the pipeline,
-- and keep the private key OUTSIDE the repository, for example:
--     python snowflake/setup/generate_key_pair.py      (writes ~/.snowflake/keys/retail_svc_rsa_key.p8)
-- A public key is not a secret, but this committed file keeps the placeholder so each environment uses its own key.
--
-- Needs SECURITYADMIN (CREATE USER, GRANT ROLE). Run after 01_objects.sql and 02_grants.sql.
-- Re-running is safe: IF NOT EXISTS leaves an existing user unchanged. To rotate the key:
--     ALTER USER RETAIL_SVC SET RSA_PUBLIC_KEY_2 = '<new key>';  then switch the client, then UNSET RSA_PUBLIC_KEY.

USE ROLE SECURITYADMIN;

CREATE USER IF NOT EXISTS RETAIL_SVC
    TYPE = SERVICE
    DEFAULT_ROLE = RETAIL_LOADER
    DEFAULT_WAREHOUSE = RETAIL_WH
    DEFAULT_NAMESPACE = RETAIL_OLIST.RAW
    RSA_PUBLIC_KEY = '<RSA_PUBLIC_KEY>'
    COMMENT = 'Retail Olist: local pipeline (RAW load, dbt, Python). Key-pair only.';

GRANT ROLE RETAIL_LOADER      TO USER RETAIL_SVC;
GRANT ROLE RETAIL_TRANSFORMER TO USER RETAIL_SVC;

DESC USER RETAIL_SVC;
