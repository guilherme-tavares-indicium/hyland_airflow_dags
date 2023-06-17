from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup



def create_task_for_stream(stream_name, stream_no):
    task_id = f'run_meltano_extraction_{stream_no}'
    task_name = f'run-container-extraction-{stream_no}'

    task_args = {
        "task_id": task_id,
        "namespace": 'prod-airflow',
        "image": '196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
        "image_pull_policy": 'Always',
        "is_delete_operator_pod": True,
        "cmds": ['/bin/bash', '-c'],
        "arguments": ['echo ${STREAMNAME}'],
        "env_vars": {
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": stream_name
        },
        "do_xcom_push": False,
    }

    return KubernetesPodOperator(dag=dag, **task_args)


default_args = {
    "owner": "airflow",
    "trigger_rule": "all_done",
    "email_on_failure": False,
    "email_on_retry": False,
    "concurrency": 1,
    "retries": 0
}

with DAG(
    'Meltano_Tap-S3_github_new',
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
        arguments=['python get_streams.py tap-github_issues'],
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": "meltano_contributors"
        },
        do_xcom_push=True
    )


    downstream_tasks = []
    xcom_push_task = None

    # Create downstream tasks based on the xcom output of get_stream_list task
    for i, stream_name in enumerate(get_stream_list.output['return_value']):
        print(f'name is {stream_name}')
        task = create_task_for_stream(stream_name, i + 1)
        downstream_tasks.append(task)

        if xcom_push_task is None:
            # Create a task to push the downstream tasks to XCom
            xcom_push_task = DummyOperator(task_id='xcom_push_task', dag=dag)
            get_stream_list >> xcom_push_task

    # Set the downstream relationship between tasks
    start >> get_stream_list >> xcom_push_task >> downstream_tasks