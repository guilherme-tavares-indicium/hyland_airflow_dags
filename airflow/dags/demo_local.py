from datetime import datetime, timedelta
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
# from kubernetes.client import models as k8s


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 25),
    'retries': 0,
}

with DAG('pull_and_run_local', default_args=default_args, schedule_interval=None) as dag:

   
    run_etl_container = KubernetesPodOperator(
        task_id='run_container_task_etl',
        name='run-container-etl',
        namespace='prod-airflow',
        image='046390580407.dkr.ecr.us-east-1.amazonaws.com/hylandcdtemplate_ecr',
        # image_pull_secrets=[k8s.V1LocalObjectReference('aws-registry')],
        # image='hello-world',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
    )