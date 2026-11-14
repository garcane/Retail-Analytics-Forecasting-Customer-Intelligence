let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="FLAG_SHARE", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	// Write-back appends one block of rows per run_id (ML.* tables keep earlier runs): keep only the latest run.
	// run_id is UTC timestamp + uuid, so the text maximum is the most recent run.
	Latest = Table.SelectRows(Lowered, let r = List.Max(Lowered[run_id]) in each [run_id] = r),
	NoRun = Table.RemoveColumns(Latest, {"run_id"}),
	Typed = Table.TransformColumnTypes(NoRun, {{"flag_pct", Int64.Type}}, "en-US")
in
	Typed
