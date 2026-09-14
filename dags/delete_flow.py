from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from src import delete_file


def enable_generate_after_delete():
    """
    Chỉ được gọi sau khi delete_files chạy thành công.
    Reset bộ đếm và cho phép download_flow generate trở lại.
    """
    Variable.set("generate_count", "0")
    Variable.set("enable_generate_data", "true")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "max_retry_delay": timedelta(minutes=30),   # Tối đa chờ 30 phút giữa các lần retry
    "execution_timeout": timedelta(hours=2),     # Mỗi task tối đa chạy 2 tiếng
    "depends_on_past": False,    
}

with DAG(
    dag_id = "delete_flow",
    default_args = default_args,
    description = "DAG for deleting data",
    start_date = datetime(2026, 9, 1), # Ngày bắt đầu chạy DAG
    schedule_interval = None,  # Không có lịch trình định kỳ, chỉ chạy khi được trigger
    catchup = False,
    max_active_runs = 1,
    tags = ["delete", "data", "nifi", "ingestion", "file"],
    dagrun_timeout = timedelta(hours=2),  # Thời gian tối đa cho phép chạy DAG là 2 giờ
) as dag:
    
    start_delete = EmptyOperator(task_id="start_delete_data")

    delete_files_task = PythonOperator(
        task_id="delete_files",
        python_callable=delete_file.delete_files,
    )

    enable_generate_task = PythonOperator(
        task_id="enable_generate_after_delete",
        python_callable=enable_generate_after_delete,
    )

    end_delete_task = EmptyOperator(task_id="end_delete_data")

    start_delete >> delete_files_task >> enable_generate_task >> end_delete_task
