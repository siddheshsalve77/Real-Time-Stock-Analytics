import os
import json
import boto3
from kafka import KafkaConsumer
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
TOPIC = os.getenv('KAFKA_TOPIC')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')

def main():
    print(f"Connecting to Kafka at {KAFKA_SERVER}...")
    
    # Initialize Kafka Consumer
    # 'auto_offset_reset=earliest' means it will read all messages from the beginning
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='stock-s3-consumer-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    # Initialize S3 Client
    s3_client = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    print(f"Consumer started. Listening to topic: {TOPIC}")
    print(f"Writing data to S3 Bucket: {BUCKET_NAME} in folder: bronze/")
    
    try:
        for message in consumer:
            # 1. Get the stock data from Kafka message
            stock_data = message.value
            
            # 2. Create a unique filename
            # Format: bronze/AAPL/2024-03-17_10-30-00-123456.json
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
            symbol = stock_data.get('symbol', 'UNKNOWN')
            
            # This defines the "folder" structure in S3
            file_key = f"bronze/{symbol}/{timestamp}.json"
            
            # 3. Convert data to JSON string
            file_content = json.dumps(stock_data)
            
            # 4. Upload to S3
            try:
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=file_key,
                    Body=file_content
                )
                print(f"Uploaded to S3: {file_key}")
                
            except Exception as e:
                print(f"Error uploading to S3: {e}")
                
    except KeyboardInterrupt:
        print("Stopping consumer...")

if __name__ == "__main__":
    main()