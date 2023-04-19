from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def log_hello():
    print("hello from the dag, Zach")

dag = DAG(
    'simple_dag_zach',
    description='A simple DAG that logs "hello from the dag"',
    schedule_interval='@once',
    start_date=datetime(2023, 4, 19),
    catchup=False
)

log_task = PythonOperator(
    task_id='log_hello_zach',
    python_callable=log_hello,
    dag=dag
)

log_task