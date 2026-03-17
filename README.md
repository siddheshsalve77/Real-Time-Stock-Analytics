# Real-Time Stock Analytics Pipeline

A production-ready **Apache Airflow + Apache Spark + Kafka** data pipeline for real-time stock data processing using the **Medallion Architecture** (Bronze → Silver → Gold layers).

## 🎯 Project Overview

This project demonstrates a modern data engineering architecture that:
- **Fetches** real-time stock data from Yahoo Finance (yfinance)
- **Streams** data through Kafka topics
- **Processes** data using Apache Spark with S3 integration
- **Orchestrates** workflows with Apache Airflow on Docker
- **Stores** raw, cleaned, and aggregated data in AWS S3

Perfect for learning **data pipelines**, **distributed processing**, and **cloud data engineering**.

---

## 🏗️ Architecture

### Medallion Architecture (Three Layers)

```
Bronze Layer (Raw)
    ↓
    ├─ Receives stock data from Kafka
    └─ Stores JSON files in S3: s3://bucket/bronze/SYMBOL/
    
Silver Layer (Cleaned)
    ↓
    ├─ Removes duplicates
    ├─ Converts timestamps
    └─ Stores Parquet files in S3: s3://bucket/silver/symbol=SYMBOL/
    
Gold Layer (Analytics)
    ↓
    ├─ Aggregates data (daily summaries, moving averages)
    └─ Optimized for analytics: s3://bucket/gold/
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Apache Airflow 2.8.0 | Workflow scheduling & monitoring |
| **Streaming** | Apache Kafka 7.5.0 | Real-time data ingestion |
| **Processing** | Apache Spark 3.5.0 | Distributed data transformation |
| **Storage** | AWS S3 | Data lake storage |
| **Containerization** | Docker & Docker Compose | Local development environment |
| **Database** | SQLite (Airflow metadata) | Task tracking & DAG state |

---

## 📋 Prerequisites

### System Requirements
- **Docker** & **Docker Compose** (latest)
- **Python 3.9+** (for local development)
- **Git**
- **AWS Account** with S3 bucket and credentials

### AWS Setup
1. Create an S3 bucket (e.g., `stock-pipeline-yourname`)
2. Get your **AWS Access Key ID** and **Secret Access Key**
3. Note your bucket's **AWS Region** (e.g., `ap-south-1`)

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/siddheshsalve77/Real-Time-Stock-Analytics.git
cd Real-Time-Stock-Analytics
```

### 2. Configure Environment Variables
Create or update `.env` file in the project root:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-bucket-name

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9093
KAFKA_TOPIC=stock_ticks
```

**⚠️ Important:** Never commit `.env` to git! Add it to `.gitignore`.

### 3. Start Services with Docker Compose
```bash
docker-compose -f docker-compose.kafka.yml up -d
```

This starts:
- ✅ Zookeeper (Kafka dependency)
- ✅ Kafka broker
- ✅ Airflow Webserver (UI on http://localhost:8080)
- ✅ Airflow Scheduler
- ✅ Airflow Initializer

### 4. Access Airflow UI
Open your browser: **http://localhost:8080**

**Login Credentials:**
- Username: `admin`
- Password: `password`

### 5. Verify Services
```bash
docker ps
```

You should see 6 containers running:
- `stock-zookeeper`
- `stock-kafka`
- `stock-airflow-init`
- `stock-airflow-webserver`
- `stock-airflow-scheduler`

---

## 📊 Running the Pipeline

### Step 1: Populate Bronze Layer
Run the Kafka producer to fetch and send stock data:

```bash
python src/producers/producer.py
```

This will:
- Fetch stock data for AAPL, GOOGL, MSFT, AMZN
- Send data to Kafka topic `stock_ticks` every 5 seconds
- Output: `Sent: SYMBOL @ price`

### Step 2: Trigger the Airflow DAG
1. Go to http://localhost:8080/dags
2. Find `stock_medallion_pipeline`
3. Click the **Play** button (top right)
4. Select **Trigger DAG**

### Step 3: Monitor Execution
The DAG will execute 4 tasks in order:

```
start 
  ↓
run_silver_transformation (Spark - Docker)
  ↓
run_gold_aggregation (Spark - Docker)
  ↓
end
```

**View logs:**
- Airflow UI: Click on each task → **Logs**
- Terminal: `docker logs stock-airflow-scheduler`

### Step 4: Check Results in S3

```bash
# List bronze layer (raw JSON)
aws s3 ls s3://your-bucket/bronze/AAPL/ --region ap-south-1

# List silver layer (cleaned Parquet)
aws s3 ls s3://your-bucket/silver/symbol=AAPL/ --region ap-south-1

# List gold layer (aggregated)
aws s3 ls s3://your-bucket/gold/ --region ap-south-1
```

---

## 📁 Project Structure

```
stock-pipeline/
├── .env                          # AWS credentials (DO NOT COMMIT)
├── .gitignore                    # Git ignore patterns
├── README.md                      # This file
├── docker-compose.kafka.yml       # Docker services definition
├── requirements.txt               # Python dependencies
│
├── dags/                          # Airflow DAGs
│   └── stock_pipeline_dag.py      # Main orchestration DAG
│
├── src/                           
│   ├── producers/                # Data ingestion
│   │   └── producer.py           # Kafka producer (fetches stock data)
│   │
│   ├── consumers/                # Data consumption
│   │   └── spark_consumer.py     # Kafka consumer (PySpark)
│   │
│   ├── spark_jobs/               # Spark ETL jobs
│   │   ├── silver_transform.py   # Bronze → Silver transformation
│   │   └── gold_aggregation.py   # Silver → Gold aggregation
│   │
│   └── utils/                    # Helper functions
│       └── helpers.py            # Utilities for logging, config
│
├── config/                        # Configuration files
│   └── aws_config.py             # AWS service configuration
│
└── tests/                         # Unit tests (future)
```

---

## 🔧 Configuration Guide

### Modify Stock Symbols
Edit [dags/stock_pipeline_dag.py](dags/stock_pipeline_dag.py) or [src/producers/producer.py](src/producers/producer.py):

```python
SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']  # Add more symbols
```

### Change Data Fetch Interval
In [src/producers/producer.py](src/producers/producer.py):

```python
time.sleep(5)  # Change to 10, 30, etc. (seconds)
```

### Adjust Spark Configuration
In [dags/stock_pipeline_dag.py](dags/stock_pipeline_dag.py), update DockerOperator resource limits:

```python
silver_job = DockerOperator(
    # ... existing config ...
    resources={'memory': '2g', 'cpus': 2},  # Add resource limits
)
```

### Enable Airflow Logging
In `docker-compose.kafka.yml`:

```yaml
environment:
  - AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
```

---

## 🐛 Troubleshooting

### Issue: Airflow UI shows "Empty Response"
**Solution:** Wait 30 seconds for services to initialize, then refresh the page.

### Issue: Docker containers fail with "Database not initialized"
**Solution:** 
```bash
docker-compose -f docker-compose.kafka.yml down
docker volume rm stock-pipeline_airflow_home
docker-compose -f docker-compose.kafka.yml up -d
```

### Issue: Spark job fails with "S3 credentials not found"
**Solution:**
1. Verify `.env` file has correct credentials
2. Restart Airflow containers:
```bash
docker-compose -f docker-compose.kafka.yml restart stock-airflow-scheduler stock-airflow-webserver
```

### Issue: Kafka producer shows "Connection refused"
**Solution:** Ensure Kafka is running:
```bash
docker logs stock-kafka | grep "started"
```

### Issue: "Permission denied" when running Docker commands
**Solution:** Add your user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📊 Data Format Examples

### Bronze Layer (Raw JSON)
```json
{
  "symbol": "AAPL",
  "timestamp": "2026-03-17 10:30:00",
  "open": 195.42,
  "high": 196.50,
  "low": 195.20,
  "close": 196.05,
  "volume": 45000000
}
```

### Silver Layer (Cleaned Parquet)
Same structure with:
- Deduplicated records
- Timestamp converted to proper format
- Partitioned by `symbol` for faster queries

### Gold Layer (Aggregated)
```json
{
  "symbol": "AAPL",
  "date": "2026-03-17",
  "daily_close": 196.05,
  "daily_high": 196.50,
  "daily_low": 195.20,
  "avg_price_7day": 195.80,
  "volume": 45000000
}
```

---

## 🧪 Development & Testing

### Run Producer Locally
```bash
# Ensure Kafka is running, then:
python src/producers/producer.py
```

### Run Spark Job Locally (with Docker)
```bash
docker run --rm \
  -v ${PWD}:/app \
  --env-file .env \
  --network host \
  apache/spark:3.5.0 \
  /opt/spark/bin/spark-submit \
    --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
    /app/src/spark_jobs/silver_transform.py
```

### Monitor Kafka Topic
```bash
docker exec stock-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --from-beginning
```

---

## 📈 Scaling & Performance

### For Production Environments:

1. **Replace SQLite with PostgreSQL:**
   - Update Airflow DB connection in `docker-compose.kafka.yml`
   - Use managed RDS for high availability

2. **Use Celery Executor:**
   - Change `SequentialExecutor` to `CeleryExecutor`
   - Add Redis for task queuing

3. **Increase Spark Resources:**
   - Allocate more memory/CPU in DockerOperator
   - Use standalone Spark cluster instead of Docker

4. **Kafk Optimization:**
   - Increase partitions for parallelism
   - Configure retention policies
   - Set up monitoring with Confluent Control Center

5. **S3 Optimization:**
   - Use S3 lifecycle policies for data archival
   - Enable versioning and encryption
   - Configure CloudFront for caching

---

## 🔐 Security Best Practices

⚠️ **IMPORTANT:**

1. **Never commit `.env` file** - Use `.env.example` instead:
   ```bash
   cp .env .env.example
   # Edit .env.example and remove sensitive values
   git add .env.example
   ```

2. **Use AWS IAM Roles** instead of hardcoded keys in production

3. **Enable S3 bucket encryption** (AES-256 or KMS)

4. **Rotate AWS credentials regularly**

5. **Use VPC endpoints** for private S3 access

---

## 📚 Learning Resources

- [Apache Airflow Documentation](https://airflow.apache.org/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [AWS S3 Developer Guide](https://docs.aws.amazon.com/s3/)
- [Medallion Architecture Blog](https://www.databricks.com/blog/2022/06/24/multi-hop-architecture-design-pattern-combining-dataflows-to-build-reliable-data-pipelines.html)

---

## 🤝 Contributing

Contributions are welcome! Follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the MIT License.

---

## 👨‍💻 Author

**Siddhesh Salve**  
GitHub: [@siddheshsalve77](https://github.com/siddheshsalve77)

---

## 🎓 What You'll Learn

By working with this project, you'll understand:

✅ **Apache Airflow** - DAG orchestration, task dependencies, monitoring  
✅ **Apache Kafka** - Event streaming, producers, consumers  
✅ **Apache Spark** - Distributed processing, SQL queries, DataFrame API  
✅ **AWS S3** - Object storage, IAM, data lakes  
✅ **Docker** - Containerization, compose, networking  
✅ **Data Engineering** - ETL/ELT patterns, medallion architecture  
✅ **Python** - Real-world data pipeline development  

---

## 📞 Support

For issues, questions, or suggestions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Open a GitHub Issue with detailed logs
3. Include Docker versions and `.env` (without credentials)

---

## 🚀 Next Steps

After mastering this project:
- Add more data sources (APIs, databases)
- Implement real-time ML model serving
- Set up monitoring with Prometheus + Grafana
- Migrate to Kubernetes for cloud scaling
- Add data quality checks with Great Expectations
- Set up CI/CD pipelines with GitHub Actions

---

**Happy Data Engineering! 🎉**
