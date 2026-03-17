from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'stock_pipeline_dag',
    default_args=default_args,
    schedule_interval='@daily', # Run once a day
    catchup=False
)

# 1. Spark Submit Task for Silver Layer
# We use BashOperator to run the spark-submit command inside the container
# Note: In a real production setup, we would use a dedicated Spark Operator
run_silver_job = BashOperator(
    task_id='run_silver_transformation',
    bash_command='spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /opt/airflow/src/spark_jobs/silver_transform.py',
    dag=dag,
)

# 2. Spark Submit Task for Gold Layer
run_gold_job = BashOperator(
    task_id='run_gold_aggregation',
    bash_command='spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /opt/airflow/src/spark_jobs/gold_aggregation.py',
    dag=dag,
)

# Set Dependency: Silver must finish before Gold
run_silver_job >> run_gold_job