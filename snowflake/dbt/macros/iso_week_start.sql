{#-
  Monday of the ISO week containing a date/timestamp expression, as DATE.

  Explicit arithmetic on dayofweekiso() (1 = Monday ... 7 = Sunday) so the result never depends on the
  WEEK_START / WEEK_OF_YEAR_POLICY session parameters. DuckDB equivalent: date_trunc('week', d)::date.
-#}
{% macro iso_week_start(date_expr) -%}
    dateadd(day, -(dayofweekiso({{ date_expr }}) - 1), ({{ date_expr }})::date)::date
{%- endmacro %}
