-- scoring_task.sql  --  score a month of orders inside Snowflake with the registered model, on a schedule.
--
-- Runs as RETAIL_TRANSFORMER on RETAIL_WH (no compute pool), after setup/08_scoring_task_grants.sql. Re-running this
-- file is safe: IF NOT EXISTS everywhere, the config row is only inserted when the table is empty, the task is created
-- SUSPENDED (Snowflake's default) and is only resumed by hand.
--
-- What it writes: ML.LATE_DELIVERY_SCORES_REGISTRY, one row per scored order with run_id, model version and month. It
-- deliberately does NOT write ML.LATE_DELIVERY_SCORES: the registered model was trained on every month, so its scores
-- for the 2018 test months are in-sample, while LATE_DELIVERY_SCORES holds the honest out-of-time backtest scores that
-- Power BI and the monitoring views read.
--
-- What it scores: ML.SCORING_CONFIG (one row) names the model version, pinned rather than "default", and the month
-- (NULL = the latest purchase month in the feature mart). The dataset is a static snapshot that ends in 2018, so on a
-- schedule this is a replay that re-scores the same month; with a live feed it would score each new month.
-- Each run replaces the rows for its (model_version, scored_month) in one transaction, with a new run_id in the
-- project's format (YYYYMMDDTHHMMSSZ-xxxxxxxx).
--
-- The PREDICT_PROBA arguments follow the model signature (SHOW FUNCTIONS IN MODEL ML.LATE_DELIVERY_RISK): the 16 v1
-- numeric features as FLOAT, then the three categoricals. tests/test_scoring_task_sql.py checks this list against
-- snowflake/ml/register_model.py predict_proba_sql.

USE ROLE RETAIL_TRANSFORMER;
USE WAREHOUSE RETAIL_WH;
USE SCHEMA RETAIL_OLIST.ML;

CREATE TABLE IF NOT EXISTS RETAIL_OLIST.ML.LATE_DELIVERY_SCORES_REGISTRY (
    run_id        VARCHAR       NOT NULL,
    model_version VARCHAR       NOT NULL,
    scored_month  VARCHAR       NOT NULL,
    order_id      VARCHAR       NOT NULL,
    risk_score    FLOAT,
    scored_at     TIMESTAMP_NTZ NOT NULL
) COMMENT = 'Scores from the registered LATE_DELIVERY_RISK model, written by task ML.SCORE_LATE_DELIVERY (in-sample for 2018).';

CREATE TABLE IF NOT EXISTS RETAIL_OLIST.ML.SCORING_CONFIG (
    model_version VARCHAR NOT NULL,
    scored_month  VARCHAR,
    updated_at    TIMESTAMP_NTZ
) COMMENT = 'One row: which registered model version task ML.SCORE_LATE_DELIVERY uses, and which month (NULL = latest).';

INSERT INTO RETAIL_OLIST.ML.SCORING_CONFIG (model_version, scored_month, updated_at)
    SELECT 'V1_20261113_CC90DC8', NULL, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
    WHERE NOT EXISTS (SELECT 1 FROM RETAIL_OLIST.ML.SCORING_CONFIG);

CREATE TASK IF NOT EXISTS RETAIL_OLIST.ML.SCORE_LATE_DELIVERY
    WAREHOUSE = RETAIL_WH
    SCHEDULE = 'USING CRON 0 6 * * 1 UTC'
    COMMENT = 'Retail Olist: score one month with the registered late-delivery model (see snowflake/ml/scoring_task.sql)'
AS
EXECUTE IMMEDIATE
$$
DECLARE
    v VARCHAR;
    m VARCHAR;
    rid VARCHAR;
    stmt VARCHAR;
    n INTEGER;
    bad_config EXCEPTION (-20001, 'ML.SCORING_CONFIG needs one row: model_version a version name, scored_month YYYY-MM or NULL');
BEGIN
    SELECT model_version, scored_month INTO :v, :m FROM RETAIL_OLIST.ML.SCORING_CONFIG LIMIT 1;
    IF (m IS NULL) THEN
        SELECT TO_CHAR(MAX(purchase_ts), 'YYYY-MM') INTO :m FROM RETAIL_OLIST.MARTS.MART_LATE_DELIVERY_FEATURES;
    END IF;
    IF (v IS NULL OR m IS NULL OR NOT REGEXP_LIKE(v, '[A-Za-z0-9_]+') OR NOT REGEXP_LIKE(m, '[0-9]{4}-[0-9]{2}')) THEN
        RAISE bad_config;
    END IF;
    rid := TO_CHAR(CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ, 'YYYYMMDD"T"HH24MISS"Z"')
           || '-' || LEFT(MD5(UUID_STRING()), 8);
    stmt := 'INSERT INTO RETAIL_OLIST.ML.LATE_DELIVERY_SCORES_REGISTRY '
         || '(run_id, model_version, scored_month, order_id, risk_score, scored_at) '
         || 'SELECT ''' || rid || ''', ''' || v || ''', ''' || m || ''', order_id, '
         || 'MODEL(RETAIL_OLIST.ML.LATE_DELIVERY_RISK, ' || v || ')!PREDICT_PROBA('
         || 'purchase_dow::float, purchase_hour::float, promised_days::float, item_count::float, items_price::float, '
         || 'items_freight::float, freight_ratio::float, n_sellers::float, total_weight_g::float, max_volume_cm3::float, '
         || 'max_item_freight::float, distance_km::float, same_state::float, max_installments::float, '
         || 'seller_prior_late_rate::float, seller_prior_n::float, customer_state, seller_state, main_payment_type'
         || '):output_feature_1::float, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ '
         || 'FROM RETAIL_OLIST.MARTS.MART_LATE_DELIVERY_FEATURES '
         || 'WHERE TO_CHAR(purchase_ts, ''YYYY-MM'') = ''' || m || '''';
    BEGIN TRANSACTION;
    DELETE FROM RETAIL_OLIST.ML.LATE_DELIVERY_SCORES_REGISTRY WHERE model_version = :v AND scored_month = :m;
    EXECUTE IMMEDIATE :stmt;
    n := SQLROWCOUNT;
    COMMIT;
    RETURN 'run ' || rid || ': scored ' || n || ' orders of ' || m || ' with ' || v;
EXCEPTION
    WHEN OTHER THEN
        ROLLBACK;
        RAISE;
END;
$$;

SHOW TASKS LIKE 'SCORE_LATE_DELIVERY' IN SCHEMA RETAIL_OLIST.ML;
