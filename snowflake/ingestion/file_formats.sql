-- file_formats.sql  --  CSV file format + internal named stage for the Olist files.
-- Idempotent: CREATE ... IF NOT EXISTS, then ALTER FILE FORMAT ... SET so the format always matches
-- this file (IF NOT EXISTS alone never updates an existing format).
--
-- Why each option (all nine Olist CSVs are UTF-8, comma-separated, with a header row; line endings are CRLF in seven files, LF-only in olist_geolocation_dataset.csv, and the category translation file has a BOM and no trailing newline):
--   FIELD_OPTIONALLY_ENCLOSED_BY = '"'   fields may be quoted; a doubled quote ("") inside a quoted
--                                        field is read as one literal quote.
--   RECORD_DELIMITER (left at default)   seven files use CRLF line endings (geolocation is LF-only). Snowflake documents the
--                                        default newline delimiter as logical, i.e. it should also accept
--                                        \r\n without leaving a trailing CR on the last field. UNVERIFIED:
--                                        the runbook has a live check for a trailing CR (CHR(13)).
--   (embedded newlines)                order_reviews review_comment_message has line breaks INSIDE
--                                        quoted fields: 99,224 records but ~104.7k physical lines.
--                                        Quoted newlines stay inside the field (default behaviour).
--   SKIP_HEADER = 1                      drop the header row.
--   SKIP_BYTE_ORDER_MARK = TRUE          product_category_name_translation.csv starts with a UTF-8 BOM.
--   ESCAPE_UNENCLOSED_FIELD = NONE       Snowflake's default is backslash, which would silently eat
--                                        literal backslashes. The real data has them in UNQUOTED
--                                        fields (sellers: 'rio de janeiro \rio de janeiro';
--                                        reviews: 'Informacao\preocupada', 'm\nual').
--   ESCAPE = NONE                        no escape character inside quoted fields either.
--   EMPTY_FIELD_AS_NULL, NULL_IF = ('')  empty fields become NULL; the text 'NULL' is NOT treated
--                                        as null (it is not in NULL_IF).
--   ERROR_ON_COLUMN_COUNT_MISMATCH       fail on a short/long record instead of silently padding.
--   SKIP_BLANK_LINES = FALSE             a blank line is an error, not silently dropped.
--   TRIM_SPACE = FALSE                   values are loaded verbatim.
--
-- Run as RETAIL_LOADER after ddl_raw.sql.
-- STATUS: written offline; NOT RUN against any Snowflake account (UNVERIFIED). The behaviour of each
-- option on the real files is exactly what the first live load + row-count check will confirm.

USE ROLE RETAIL_LOADER;
USE WAREHOUSE RETAIL_WH;
USE SCHEMA RETAIL_OLIST.RAW;

CREATE FILE FORMAT IF NOT EXISTS RAW.OLIST_CSV
    TYPE = CSV
    COMMENT = 'Olist CSV: quoted fields, embedded newlines, UTF-8, header row, no backslash escaping';

ALTER FILE FORMAT RAW.OLIST_CSV SET
    FIELD_DELIMITER = ','
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    ENCODING = 'UTF8'
    SKIP_BYTE_ORDER_MARK = TRUE
    ESCAPE = NONE
    ESCAPE_UNENCLOSED_FIELD = NONE
    EMPTY_FIELD_AS_NULL = TRUE
    NULL_IF = ('')
    ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE
    SKIP_BLANK_LINES = FALSE
    TRIM_SPACE = FALSE
    COMPRESSION = AUTO;

CREATE STAGE IF NOT EXISTS RAW.OLIST_STAGE
    FILE_FORMAT = RAW.OLIST_CSV
    COMMENT = 'Internal stage for Olist CSV uploads (PUT by ingestion/load_raw.py)';
