from datetime import datetime
import yaml
from airflow import DAG
# from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator

# def create_new_kubernetes_operator_task(task_id, output, dag, task_no):
#     return KubernetesPodOperator(
#         task_id=task_id,
#         name=f'run-stream-{task_no}',
#         namespace='prod-airflow',
#         image='046390580407.dkr.ecr.us-east-1.amazonaws.com/hyland_aws_meltano_ecr',
#         image_pull_policy='Always',
#         is_delete_operator_pod=True,
#         dag=dag,
#         cmds=['/bin/bash', '-c'],
#         arguments=[f'meltano select tap-github_issues $STREAMNAME "*" && meltano run tap-github_issues target-s3'],
#         env_vars={
#             "AWS_ID": Variable.get("AWS_ID"),
#             "AWS_PSW": Variable.get("AWS_PSW"),
#             "GITHUB_TOKEN" : Variable.get("GITHUB_TOKEN"),
#             "STREAMNAME": output
#         },
#     )

# DAG
default_args = {
    'name': 'meltano_github_dag',
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
    start_date=datetime(2023, 6, 16),
    tags=["from: API", "to: S3", "tool: Meltano"],
    catchup=False
) as dag:
    
    start = DummyOperator(task_id='run_this_first', dag=dag)

    run_meltano_extract = KubernetesPodOperator(
        task_id='run_meltano_extraction',
        name='run-container-extraction',
        namespace='prod-airflow',
        image='196029031078.dkr.ecr.us-east-1.amazonaws.com/prod-meltano-hylandtraining:5ba8dc20a968fe5fd0512d43d41866f83779d917',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
        cmds=['/bin/bash', '-c'],
        # arguments=['meltano select tap-github_issues meltano_contributors "*" && meltano run tap-github_issues target-jsonl'],
        arguments=['echo "hello world"'],
        env_vars={
            "AWS_ID": Variable.get("AWS_ID"),
            "AWS_PSW": Variable.get("AWS_PSW"),
            "GITHUB_TOKEN" : Variable.get("GITHUB_TOKEN"),
            "STREAMNAME": "meltano_contributors"
        },
    )

start >> run_meltano_extract