from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
import json

def create_task_for_stream(dag, stream_name, stream_no):
    task = KubernetesPodOperator(
        task_id=f'run_meltano_extraction_{stream_no}',
        name=f'run-container-extraction-{stream_no}',
        namespace='prod-airflow',
        image='196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
        cmds=['/bin/bash', '-c'],
        arguments=['echo ${STREAMNAME}'],
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": stream_name
        },
        do_xcom_push=False,
    )
    return task


def create_downstream_tasks(ti):
    xcom_output = ti.xcom_pull(task_ids='run_meltano_extraction')
    streams = xcom_output.get('return_value')

    for i, stream_name in enumerate(streams):
        task_id = f'run_meltano_extraction_{i + 1}'
        subtask = create_task_for_stream(dag, stream_name, i + 1)
        ti.task.set_downstream(subtask)

default_args = {
    "owner": "airflow",
    "trigger_rule": "all_done",
    "email_on_failure": False,
    "email_on_retry": False,
    "concurrency": 1,
    "retries": 0
    }

with DAG(
    'Meltano_Tap-S3_github',
    default_args=default_args,
    description='Dag to run meltano using docker',
    schedule_interval='@once',
    start_date=datetime(year=2023, month=6, day=16),
    tags=["from: API", "to: S3", "tool: Meltano"],
    catchup=False
    ) as dag:

    start = DummyOperator(task_id='run_this_first')
    
    get_stream_list = KubernetesPodOperator(
        task_id='run_meltano_extraction',
        name='run-container-extraction',
        namespace='prod-airflow',
        image='196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
        cmds=['/bin/bash', '-c'],
        # arguments=['meltano select tap-github_issues meltano_contributors "*" && meltano run tap-github_issues target-jsonl'],
        arguments=['python get_streams.py tap-github_issues'],
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN" : Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": "meltano_contributors"
        },
        do_xcom_push=True
    )

    create_tasks = PythonOperator(
        task_id='create_tasks',
        python_callable=create_downstream_tasks,
        provide_context=True,
        dag=dag,
    )

    start >> get_stream_list >> create_tasks
