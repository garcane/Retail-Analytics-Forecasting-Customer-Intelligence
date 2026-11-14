let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="DIM_SELLER", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"seller_key", Int64.Type}, {"seller_id", type text}, {"seller_zip_code_prefix", type text}, {"seller_city", type text}, {"seller_state", type text}}, "en-US")
in
	Typed
