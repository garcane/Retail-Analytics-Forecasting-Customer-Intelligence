let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="ML", Kind="Schema"]}[Data],
	Item = Schema{[Name="LATE_DELIVERY_SCORES", Kind="Table"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"order_id", type text}, {"month", type text}, {"purchase_date_key", Int64.Type}, {"risk_score", type number}, {"risk_percentile", type number}, {"flagged_top10", type logical}, {"is_late", Int64.Type}, {"customer_state", type text}, {"seller_state", type text}, {"category", type text}, {"promised_days", type number}})
in
	Typed
