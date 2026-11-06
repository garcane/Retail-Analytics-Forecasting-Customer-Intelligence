let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="FACT_ORDER_ITEMS", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"order_id", type text}, {"order_item_id", Int64.Type}, {"order_status", type text}, {"customer_key", Int64.Type}, {"product_key", Int64.Type}, {"seller_key", Int64.Type}, {"customer_geography_key", Int64.Type}, {"seller_geography_key", Int64.Type}, {"purchase_date_key", Int64.Type}, {"shipping_limit_date_key", Int64.Type}, {"price", Currency.Type}, {"freight_value", Currency.Type}, {"item_total_value", Currency.Type}, {"is_net_order", type logical}})
in
	Typed
