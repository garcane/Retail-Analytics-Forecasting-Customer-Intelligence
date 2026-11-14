let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="LATE_DELIVERY_SCORES", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	// Write-back appends one block of rows per run_id (ML.* tables keep earlier runs): keep only the latest run.
	// run_id is UTC timestamp + uuid, so the text maximum is the most recent run.
	Latest = Table.SelectRows(Lowered, let r = List.Max(Lowered[run_id]) in each [run_id] = r),
	NoRun = Table.RemoveColumns(Latest, {"run_id"}),
	Typed = Table.TransformColumnTypes(NoRun, {{"order_id", type text}, {"month", type text}, {"purchase_date_key", Int64.Type}, {"risk_score", type number}, {"risk_percentile", type number}, {"flagged_top10", type logical}, {"is_late", Int64.Type}, {"customer_state", type text}, {"seller_state", type text}, {"category", type text}, {"promised_days", type number}})
in
	Typed
