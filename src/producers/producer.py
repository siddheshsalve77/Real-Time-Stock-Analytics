import os
import json
import time
import yfinance as yf
from kafka import KafkaProducer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'stock_ticks')
SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']  # The stocks we want to track

def get_stock_data(symbol):
    """
    Fetches the latest stock data for a given symbol.
    """
    ticker = yf.Ticker(symbol)
    
    # We use .info to get current real-time data (simulated for this project)
    # In a real prod environment, you'd use a paid WebSocket API.
    try:
        data = ticker.history(period='1d')
        
        if not data.empty:
            # Construct a clean dictionary (JSON) for the message
            last_row = data.iloc[-1]
            message = {
                'symbol': symbol,
                'timestamp': str(last_row.name), # The index is the Datetime
                'open': last_row['Open'],
                'high': last_row['High'],
                'low': last_row['Low'],
                'close': last_row['Close'],
                'volume': int(last_row['Volume'])
            }
            return message
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
    return None

def send_to_kafka(producer, topic, data):
    """
    Sends data to Kafka topic.
    """
    try:
        # Send the dict directly - the serializer will handle JSON encoding
        producer.send(topic, value=data)
        producer.flush()
        print(f"Sent: {data['symbol']} @ {data['close']}")
    except Exception as e:
        print(f"Error sending to Kafka: {e}")

def main():
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
    
    # Initialize Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        # Serialize JSON to string (optional helper)
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print("Producer started. Sending stock data every 5 seconds...")
    
    try:
        while True:
            for symbol in SYMBOLS:
                stock_data = get_stock_data(symbol)
                
                if stock_data:
                    send_to_kafka(producer, TOPIC_NAME, stock_data)
            
            # Wait for 5 seconds before the next fetch
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("Stopping producer...")
        producer.close()

if __name__ == "__main__":
    main()