from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import json

def create_task_for_stream(dag, stream_name, stream_no):
    task = KubernetesPodOperator(
        task_id=f'run_meltano_extraction_{stream_no}',
        name=f'run-container-extraction-{stream_no}',
        namespace='prod-airflow',
        # ...
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": stream_name
        },
        do_xcom_push=False,
    )
    return task

def task_builder(ti):
    xcon_output = ti.xcom_pull(key='return_value', task_ids='run_meltano_extraction')
    streams = json.loads(xcon_output)

    last_task = start

    for i, stream_name in enumerate(streams):
        subtask = create_task_for_stream(dag, stream_name, i + 1)
        last_task >> subtask
        last_task = subtask

# DAG definition and tasks remain the same

with dag:
    start = DummyOperator(task_id='run_this_first')
    get_stream_list = KubernetesPodOperator(
        task_id='run_meltano_extraction',
        name='run-container-extraction',
        namespace='prod-airflow',
        # ...
        do_xcom_push=True
    )

    create_tasks = PythonOperator(
        task_id='create_tasks',
        python_callable=task_builder,
        provide_context=True,
        dag=dag,
    )

    start >> get_stream_list >> create_tasks




