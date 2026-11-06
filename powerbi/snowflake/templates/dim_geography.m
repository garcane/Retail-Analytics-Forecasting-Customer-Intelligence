let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="DIM_GEOGRAPHY", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"geography_key", Int64.Type}, {"zip_prefix", type text}, {"city", type text}, {"state", type text}, {"latitude", type number}, {"longitude", type number}, {"n_source_points", Int64.Type}}, "en-US")
in
	Typed
