let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="FACT_REVIEWS", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"review_id", type text}, {"order_id", type text}, {"customer_key", Int64.Type}, {"review_creation_date_key", Int64.Type}, {"review_answer_date_key", Int64.Type}, {"review_creation_ts", type datetime}, {"review_answer_ts", type datetime}, {"review_score", Int64.Type}, {"has_comment", type logical}, {"is_latest_review_for_order", type logical}})
in
	Typed
