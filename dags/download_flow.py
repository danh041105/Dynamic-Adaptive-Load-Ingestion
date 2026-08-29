from pathlib import Path
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.time_delta import TimeDeltaSensorAsync

from src import generate_file_enm, generate_file_megaplexer, delete_file

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "max_retry_delay": timedelta(minutes=30),   # Tối đa chờ 30 phút giữa các lần retry
    "execution_timeout": timedelta(hours=2),     # Mỗi task tối đa chạy 2 tiếng
    "depends_on_past": False,                    # Không phụ thuộc vào lần chạy trước
}

with DAG(
    dag_id = "download_flow",
    default_args = default_args,
    description = "DAG for generating data",
    schedule_interval = timedelta(minutes=1),
    start_date = datetime.now(),
    catchup = False,
    max_active_runs = 1,
    tags = ["generate", "data", "nifi", "ingestion", "file"],
    dagrun_timeout = timedelta(hours=2),  # Thời gian tối đa cho phép chạy DAG là 2 giờ

) as dag:

    start_download = EmptyOperator(task_id="start_generate_data")

    enm_generate_task = PythonOperator(
        task_id="generate_enm_data",
        python_callable=generate_file_enm.generate_enm_data,
    )

    megaplexer_generate_task = PythonOperator(
        task_id="generate_megaplexer_data",
        python_callable=generate_file_megaplexer.generate_megaplexer_data,
    )

    end_generate_task = EmptyOperator(task_id="end_generate_data")

    wait_before_delete_task = TimeDeltaSensorAsync(
        task_id="wait_30_minutes_before_delete",
        delta=timedelta(minutes=30),
    )

    delete_files_task = PythonOperator(
        task_id="delete_files",
        python_callable=delete_file.delete_files,
    )

# Định nghĩa luồng chạy của DAG
    start_download >> [enm_generate_task, megaplexer_generate_task] >> end_generate_task
    end_generate_task >> wait_before_delete_task >> delete_files_task
