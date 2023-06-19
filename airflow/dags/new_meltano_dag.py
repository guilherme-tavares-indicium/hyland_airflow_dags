from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

with open("/airflow/dags/utils/get_streams.sh", 'r') as file:
    script_content = file.read()

def _process_obtained_data(ti):
    xcom_output = ti.xcom_pull(task_ids='get_stream_list')
    streams = xcom_output.get('return_value')
    Variable.set(key='list_of_streams',
                 value=xcom_output.get('return_value'), serialize_json=True)

def _print_greeting(stream_name, greeting):
    print(f'{greeting} from {stream_name}')

default_args = {
    "owner": "airflow",
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

    start = DummyOperator(task_id='start')

    get_stream_list = KubernetesPodOperator(
        task_id='get_stream_list',
        name='get-stream-list',
        namespace='prod-airflow',
        image='196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
        cmds=['/bin/bash', '-c'],
        arguments=[script_content],
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": "meltano_contributors"
        },
        do_xcom_push=True
    )

    preparation_task = PythonOperator(
        task_id='preparation_task',
        python_callable=_process_obtained_data)

    iterable_list = Variable.get('list_of_streams',
                                 default_var=[''],
                                 deserialize_json=True)

    end = DummyOperator(
        task_id='end',
        trigger_rule='none_failed')
    
    with TaskGroup('dynamic_tasks_group',
                   prefix_group_id=False,
                   ) as dynamic_tasks_group:
        if iterable_list:
            for index, stream in enumerate(iterable_list):
                task_args = {
                    "task_id": f'run_stream_{stream}',
                    "namespace": 'prod-airflow',
                    "image": '196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
                    "image_pull_policy": 'Always',
                    "is_delete_operator_pod": True,
                    "cmds": ['/bin/bash', '-c'],
                    "arguments": [f'meltano select tap-github_issues {stream} && meltano run tap-github_issues target-s3'],
                    "env_vars": {
                        "AWS_ID": Variable.get("AWS_ID"),
                        "AWS_PSW": Variable.get("AWS_PSW"),
                        "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN")
                    },
                    "do_xcom_push": False,
                }

                stream_task =  KubernetesPodOperator(dag=dag, **task_args)
                stream_task

    start >> get_stream_list >> preparation_task >> dynamic_tasks_group >> end