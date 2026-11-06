let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="DIM_PRODUCT", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"product_key", Int64.Type}, {"product_id", type text}, {"product_category_name", type text}, {"product_category_name_english", type text}, {"product_name_length", Int64.Type}, {"product_description_length", Int64.Type}, {"product_photos_qty", Int64.Type}, {"product_weight_g", Int64.Type}, {"product_length_cm", Int64.Type}, {"product_height_cm", Int64.Type}, {"product_width_cm", Int64.Type}, {"product_volume_cm3", Int64.Type}}, "en-US")
in
	Typed
