let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="FORECAST_BACKTEST", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"target", type text}, {"horizon", Int64.Type}, {"method", type text}, {"target_week", type date}, {"forecast", type number}, {"actual", type number}, {"abs_error", type number}}, "en-US")
in
	Typed
