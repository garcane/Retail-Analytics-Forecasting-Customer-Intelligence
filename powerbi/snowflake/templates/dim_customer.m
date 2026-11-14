let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="DIM_CUSTOMER", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"customer_key", Int64.Type}, {"customer_unique_id", type text}, {"customer_zip_code_prefix", type text}, {"customer_city", type text}, {"customer_state", type text}}, "en-US")
in
	Typed
