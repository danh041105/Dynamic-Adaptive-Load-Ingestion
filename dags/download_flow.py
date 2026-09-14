from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from airflow.exceptions import AirflowSkipException
from src import generate_file_enm, generate_file_megaplexer

def check_can_generate():
    """
    Kiểm tra xem có thể generate dữ liệu hay không.
    """
    enabled = Variable.get("enable_generate_data", default_var="true")
    if enabled == "true":
        return "start_generate_data"
    return "skip_generate_data"

def update_generate_count(max_count=10):
    """
        Tăng số lần generate sau mỗi lần generate thành công. Tối đa là 30 lần. Nếu đủ 30 lần, khóa generate và 
        chuyển sang trigger delete_flow.
    """
    count = int(Variable.get("generate_count", default_var="0"))
    count += 1
    Variable.set("generate_count", str(count))

    if count >= max_count:
        Variable.set("enable_generate_data", "false")
        return "trigger_delete_flow"
    return "end_generate_data"


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
    start_date = datetime(2026, 9, 1), # Ngày bắt đầu chạy DAG
    schedule = "*/1 * * * *",  # Chạy mỗi phút  
    catchup = False,
    max_active_runs = 1,   # Giới hạn số lượng DAG chạy đồng thời trong 1 thời điểm
    max_active_tasks = 2,  # Giới hạn số lượng task chạy đồng thời trong DAG
    tags = ["generate", "data", "nifi", "ingestion", "file"],
    dagrun_timeout = timedelta(hours=2),  # Thời gian tối đa cho phép chạy DAG là 2 giờ

) as dag:

    start_download = EmptyOperator(task_id="start_generate_data")
    
    enm_generate_task = PythonOperator(
        task_id="generate_enm_data",
        python_callable=generate_file_enm.generate_enm_data,
    )
    # megaplexer_generate_task = PythonOperator(
    #     task_id="generate_megaplexer_data",
    #     python_callable=generate_file_megaplexer.generate_megaplexer_data,
    # )

    check_generate = BranchPythonOperator(
        task_id="check_generate_state",
        python_callable=check_can_generate,
    )

    skip_generate = EmptyOperator(task_id="skip_generate_data")

    check_count = BranchPythonOperator(
        task_id="check_generate_count",
        python_callable=update_generate_count,
    )

    delete_dag = TriggerDagRunOperator(
        task_id="trigger_delete_flow",
        trigger_dag_id="delete_flow",
        wait_for_completion=True,
        deferrable=True,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    end_generate_task = EmptyOperator(task_id="end_generate_data")

    check_generate >> [start_download, skip_generate]
    start_download >> [enm_generate_task] >> check_count
    check_count >> [end_generate_task, delete_dag]