{#-
  yyyymmdd smart key for a date/timestamp expression; -1 when the expression is NULL (not applicable).
  DuckDB equivalent: coalesce(strftime(ts, '%Y%m%d')::integer, -1).
-#}
{% macro date_key(ts_expr) -%}
    coalesce(to_char({{ ts_expr }}, 'YYYYMMDD')::integer, -1)
{%- endmacro %}
