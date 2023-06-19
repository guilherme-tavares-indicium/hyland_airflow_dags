from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup


def _process_obtained_data(ti):
    xcom_output = ti.xcom_pull(task_ids='get_stream_list')
    streams = xcom_output.get('return_value')
    Variable.set(key='list_of_streams',
                 value=xcom_output.get('return_value'), serialize_json=True)

def _print_greeting(stream_name, greeting):
    print(f'{greeting} from {stream_name}')

# def create_task_for_stream(stream_name, stream_no):
#     task_id = f'run_meltano_extraction_{stream_no}'
#     task_name = f'run-container-extraction-{stream_no}'

#     task_args = {
#         "task_id": task_id,
#         "namespace": 'prod-airflow',
#         "image": '196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
#         "image_pull_policy": 'Always',
#         "is_delete_operator_pod": True,
#         "cmds": ['/bin/bash', '-c'],
#         "arguments": ['echo ${STREAMNAME}'],
#         "env_vars": {
#             "AWS_ID": Variable.get("AWS_ID"),
#             "AWS_PSW": Variable.get("AWS_PSW"),
#             "GITHUB_TOKEN": Variable.get("GITHUB_TOKEN"),
#             "STREAMNAME": stream_name
#         },
#         "do_xcom_push": False,
#     }

#     return KubernetesPodOperator(dag=dag, **task_args)


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

    start = DummyOperator(task_id='run_this_first')

    get_stream_list = KubernetesPodOperator(
        task_id='get_stream_list',
        name='get-stream-list',
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
                say_hello = PythonOperator(
                    task_id=f'say_hello_from_{stream}',
                    python_callable=_print_greeting,
                    op_kwargs={'stream_name': stream, 'greeting': 'Hello'}
                )
                # TaskGroup level dependencies
                say_hello

    # Set the downstream relationship between tasks
    start >> get_stream_list >> dynamic_tasks_group >> end