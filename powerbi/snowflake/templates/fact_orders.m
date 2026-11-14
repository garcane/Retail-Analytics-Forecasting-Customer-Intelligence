let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="FACT_ORDERS", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"order_id", type text}, {"order_status", type text}, {"customer_key", Int64.Type}, {"customer_geography_key", Int64.Type}, {"purchase_date_key", Int64.Type}, {"approved_date_key", Int64.Type}, {"carrier_date_key", Int64.Type}, {"delivered_customer_date_key", Int64.Type}, {"estimated_delivery_date_key", Int64.Type}, {"purchase_ts", type datetime}, {"estimated_delivery_ts", type datetime}, {"item_count", Int64.Type}, {"items_price", Currency.Type}, {"items_freight", Currency.Type}, {"payment_count", Int64.Type}, {"payment_total", Currency.Type}, {"delivery_days", type number}, {"delivery_delay_days", type number}, {"is_late", type logical}, {"has_timestamp_anomaly", type logical}, {"promised_days", type number}, {"is_net_order", type logical}, {"is_labelled_delivery", type logical}, {"delay_bucket", type text}, {"delay_bucket_order", Int64.Type}})
in
	Typed
