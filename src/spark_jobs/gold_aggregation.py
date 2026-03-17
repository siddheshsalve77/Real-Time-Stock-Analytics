import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, count

# Configuration
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

def main():
    print("Initializing Spark Session for Gold Layer...")
    
    spark = SparkSession.builder \
        .appName("StockGoldAggregation") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET) \
        .config("spark.hadoop.fs.s3a.endpoint", f"s3.{AWS_REGION}.amazonaws.com") \
        .getOrCreate()

    print("Reading Silver data...")
    
    # 1. Read from Silver Layer (Parquet)
    df_silver = spark.read.parquet(f"s3a://{S3_BUCKET}/silver/")
    
    print(f"Silver Schema:")
    df_silver.printSchema()

    # 2. Aggregations (Gold Layer)
    # We calculate metrics: Average Close, Max High, Min Low, Total Volume count per Symbol
    df_gold = df_silver.groupBy("symbol").agg(
        avg("close").alias("avg_closing_price"),
        max("high").alias("max_high_price"),
        min("low").alias("min_low_price"),
        count("volume").alias("total_records")
    )

    print("Gold Aggregation Results:")
    df_gold.show()

    # 3. Write to Gold Layer (CSV for easy viewing, or Parquet)
    # We use 'overwrite' mode. Coalesce to 1 file to make it a single CSV output.
    print("Writing to Gold layer...")
    df_gold.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(f"s3a://{S3_BUCKET}/gold/summary_stats/")

    print("Gold Layer write complete!")

    spark.stop()

if __name__ == "__main__":
    main()