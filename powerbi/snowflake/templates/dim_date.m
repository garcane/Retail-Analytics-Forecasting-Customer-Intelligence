let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="DIM_DATE", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"date_key", Int64.Type}, {"full_date", type date}, {"year", Int64.Type}, {"quarter", Int64.Type}, {"month", Int64.Type}, {"month_name", type text}, {"year_month", type text}, {"day_of_month", Int64.Type}, {"iso_week", Int64.Type}, {"day_of_week", Int64.Type}, {"day_name", type text}, {"is_weekend", type logical}}, "en-US")
in
	Typed
