{#-
  Schema routing.

  prod target : the custom schema name, upper-cased, with no prefix (RAW/STAGING/INTERMEDIATE/MARTS/PBI/ML).
  any other   : <DBT_DEV_SUFFIX>_<CUSTOM_SCHEMA> (dev and ci), e.g. DBT_DEV_MARTS, so a developer or a CI
                run never writes into the production schemas.
  no custom schema configured : the target's own schema.

  The suffix is read with env_var() so no value is committed; the defaults (DBT_DEV for dev, DBT_CI for ci)
  keep `dbt parse --target ci` working with an empty environment.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema | trim }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim | upper }}
    {%- else -%}
        {{ env_var('DBT_DEV_SUFFIX', 'DBT_CI' if target.name == 'ci' else 'DBT_DEV') | trim | upper }}_{{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
