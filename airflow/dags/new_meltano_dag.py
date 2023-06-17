from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator

def create_task_for_stream(dag, stream_name, stream_no):
    task = KubernetesPodOperator(
        # ... task definition remains the same
    )
    return task

def create_downstream_tasks(ti):
    xcom_output = ti.xcom_pull(task_ids='get_stream_list')
    streams = xcom_output.get('return_value')
    
    downstream_tasks = []
    for i, stream_name in enumerate(streams):
        task_id = f'run_meltano_extraction_{i + 1}'
        subtask = create_task_for_stream(dag, stream_name, i + 1)
        downstream_tasks.append(subtask)
        
    ti.xcom_push(key='downstream_tasks', value=downstream_tasks)

def set_downstream_tasks(ti):
    downstream_tasks = ti.xcom_pull(key='downstream_tasks', task_ids='create_tasks2')
    
    for task in downstream_tasks:
        task.set_downstream(ti.task)

default_args = {
    "owner": "airflow",
    "trigger_rule": "all_done",
    "email_on_failure": False,
    "email_on_retry": False,
    "concurrency": 1,
    "retries": 0
}

with DAG(
    'Meltano_Tap-S3_github_NEW',
    default_args=default_args,
    description='Dag to run meltano using docker',
    schedule_interval='@once',
    start_date=datetime(year=2023, month=6, day=16),
    tags=["from: API", "to: S3", "tool: Meltano"],
    catchup=False
) as dag:

    start = DummyOperator(task_id='run_this_first')

    get_stream_list = KubernetesPodOperator(
        # ... KubernetesPodOperator definition remains the same
    )

    create_tasks = PythonOperator(
        task_id='create_tasks2',
        python_callable=create_downstream_tasks,
        provide_context=True,
        dag=dag,
    )

    set_downstream = PythonOperator(
        task_id='set_downstream_tasks2',
        python_callable=set_downstream_tasks,
        provide_context=True,
        dag=dag,
    )

    start >> get_stream_list >> create_tasks >> set_downstream

