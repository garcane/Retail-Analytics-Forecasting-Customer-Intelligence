let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="FORECAST_BACKTEST", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	// Write-back appends one block of rows per run_id (ML.* tables keep earlier runs): keep only the latest run.
	// run_id is UTC timestamp + uuid, so the text maximum is the most recent run.
	Latest = Table.SelectRows(Lowered, let r = List.Max(Lowered[run_id]) in each [run_id] = r),
	NoRun = Table.RemoveColumns(Latest, {"run_id"}),
	Typed = Table.TransformColumnTypes(NoRun, {{"target", type text}, {"horizon", Int64.Type}, {"method", type text}, {"target_week", type date}, {"forecast", type number}, {"actual", type number}, {"abs_error", type number}}, "en-US")
in
	Typed
