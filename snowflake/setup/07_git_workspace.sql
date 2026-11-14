-- 07_git_workspace.sql  --  let Snowflake Workspaces read this project's public GitHub repository, so the notebooks in
-- notebooks/snowflake/ run inside Snowflake on the committed code (Projects > Workspaces > From Git repository).
--
-- A public repository needs no secret. The integration only allows HTTPS reads under the prefix below; a workspace on a
-- public repository is read-only (edit locally, commit, push, then pull in the workspace).
-- Replace <https://github.com/ACCOUNT> with the repository owner's URL prefix in your worksheet copy; this committed
-- file keeps the placeholder. Never OR REPLACE: IF NOT EXISTS leaves an existing integration unchanged.
--
-- Needs ACCOUNTADMIN (CREATE API INTEGRATION is an account-level privilege). To undo:
--     DROP API INTEGRATION RETAIL_GIT_API;   (only after the workspaces using it are deleted)

USE ROLE ACCOUNTADMIN;

CREATE API INTEGRATION IF NOT EXISTS RETAIL_GIT_API
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('<https://github.com/ACCOUNT>')
    ENABLED = TRUE
    COMMENT = 'Retail Olist: read-only access to the public project repository for Snowflake Workspaces';

-- The notebooks run as RETAIL_TRANSFORMER (so it owns what they create); it must be able to use the integration.
GRANT USAGE ON INTEGRATION RETAIL_GIT_API TO ROLE RETAIL_TRANSFORMER;

SHOW INTEGRATIONS LIKE 'RETAIL_GIT_API';
