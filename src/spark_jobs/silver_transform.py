# src/spark_jobs/silver_transform.py
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

# Configuration from Environment Variables
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

def main():
    print("Initializing Spark Session...")
    
    # 1. Initialize Spark with S3 Config
    # We use the 'hadoop-aws' package which is included in the Docker image to talk to S3
    spark = SparkSession.builder \
        .appName("StockSilverETL") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET) \
        .config("spark.hadoop.fs.s3a.endpoint", f"s3.{AWS_REGION}.amazonaws.com") \
        .getOrCreate()

    print("Reading Bronze data from S3...")
    
    # 2. Read JSON files from the Bronze folder
    # 's3a://' is the protocol Spark uses for S3
    df = spark.read.json(f"s3a://{S3_BUCKET}/bronze/*/*.json")
    
    print(f"Read {df.count()} records.")

    # 3. Transformations (Cleaning & Enrichment)
    # - Remove duplicates (just in case)
    # - Ensure correct data types (Timestamps often come in as strings, we convert to proper timestamp)
    df_clean = df \
        .dropDuplicates() \
        .withColumn("event_timestamp", to_timestamp(col("timestamp"))) \
        .drop("timestamp")

    print("Schema after cleaning:")
    df_clean.printSchema()

    # 4. Write to Silver Layer in Parquet format
    # Partitioning by 'symbol' makes queries faster (e.g. querying only AAPL data)
    print("Writing to Silver layer...")
    df_clean.write \
        .mode("overwrite") \
        .partitionBy("symbol") \
        .parquet(f"s3a://{S3_BUCKET}/silver/")

    print("Silver Layer write complete!")

    spark.stop()

if __name__ == "__main__":
    main()