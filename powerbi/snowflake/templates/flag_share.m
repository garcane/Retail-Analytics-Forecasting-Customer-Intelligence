let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="FLAG_SHARE", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"flag_pct", Int64.Type}}, "en-US")
in
	Typed
