from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
from docker.types import Mount
import os

# Default arguments
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'stock_medallion_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    start = EmptyOperator(task_id='start')

    # Task 1: Silver Layer (Spark)
    silver_job = DockerOperator(
        task_id='run_silver_transformation',
        image='apache/spark:3.5.0',
        command='/opt/spark/bin/spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /app/src/spark_jobs/silver_transform.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='host',
        auto_remove=True,
        # FIX 1: Don't try to mount Airflow's tmp folder
        mount_tmp_dir=False, 
        # FIX 2: Run as root to allow Spark to write to its cache
        user='root',
        # Mount local folder so Spark container can see your code
        mounts=[Mount(source=r'C:\AWS-PROJECTS\Stock-Pipeline', target='/app', type='bind')],
        environment={
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_REGION': os.getenv('AWS_REGION'),
            'S3_BUCKET_NAME': os.getenv('S3_BUCKET_NAME')
        }
    )

    # Task 2: Gold Layer (Spark)
    gold_job = DockerOperator(
        task_id='run_gold_aggregation',
        image='apache/spark:3.5.0',
        command='/opt/spark/bin/spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /app/src/spark_jobs/gold_aggregation.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='host',
        auto_remove=True,
        mount_tmp_dir=False,
        user='root',
        mounts=[Mount(source=r'C:\AWS-PROJECTS\Stock-Pipeline', target='/app', type='bind')],
        environment={
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_REGION': os.getenv('AWS_REGION'),
            'S3_BUCKET_NAME': os.getenv('S3_BUCKET_NAME')
        }
    )

    end = EmptyOperator(task_id='end')

    # Pipeline Order: Start -> Silver -> Gold -> End
    start >> silver_job >> gold_job >> end