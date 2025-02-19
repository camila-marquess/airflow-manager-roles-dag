from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def say_hello():
    print("Hello, World!")


with DAG(
    dag_id="hello_world_dag",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args={"owner": "team-hello-world"},
) as dag:
    hello_task = PythonOperator(task_id="say_hello_task", python_callable=say_hello)

hello_task
