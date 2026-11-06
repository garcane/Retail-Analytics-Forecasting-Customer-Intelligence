let
	Source = Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse),
	Database = Source{[Name="RETAIL_OLIST", Kind="Database"]}[Data],
	Schema = Database{[Name="PBI", Kind="Schema"]}[Data],
	Item = Schema{[Name="FACT_PAYMENTS", Kind="View"]}[Data],
	Lowered = Table.TransformColumnNames(Item, Text.Lower),
	Typed = Table.TransformColumnTypes(Lowered, {{"order_id", type text}, {"payment_sequential", Int64.Type}, {"customer_key", Int64.Type}, {"purchase_date_key", Int64.Type}, {"payment_type", type text}, {"payment_installments", Int64.Type}, {"payment_value", Currency.Type}})
in
	Typed
