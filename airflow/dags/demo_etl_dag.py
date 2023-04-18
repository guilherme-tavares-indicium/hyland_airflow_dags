from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import Variable
import boto3
import subprocess
import base64
import os
import json


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 17),
    'retries': 0,
}

def pull_ecr_image():

    
    # Create a boto3 client for ECR
    print(accessKeyId)
    print(secretAccessKey)
    ecr = boto3.client('ecr',
                       region_name='us-east-1',
                       aws_access_key_id=accessKeyId,
                       aws_secret_access_key=secretAccessKey
                       )

    # Retrieve an ECR login command
    login_response = ecr.get_authorization_token()

    # Extract the username and password from the login command
    username, password = base64.b64decode(login_response['authorizationData'][0]['authorizationToken']).decode().split(':')

    # Log in to the ECR registry using the extracted username and password
    subprocess.run(['docker', 'login', '-u', username, '--password', password, login_response['authorizationData'][0]['proxyEndpoint']])

    # Pull the latest version of the image from the ECR repository
    subprocess.run(['docker', 'pull', '196029031078.dkr.ecr.us-east-1.amazonaws.com/hyland-poc-ecr:latest'])


with DAG('pull_and_run_dag', default_args=default_args, schedule_interval=None) as dag:

    accessKeyId_str = Variable.get("AWS_ACCESS_KEY_ID")
    accessKeyId = json.loads(accessKeyId_str)['AWS_ACCESS_KEY_ID']

    secretAccessKey_str = Variable.get("AWS_SECRET_ACCESS_KEY")
    secretAccessKey = json.loads(secretAccessKey_str)['AWS_SECRET_ACCESS_KEY']
    
    pull_image = PythonOperator(
        task_id='pull_ecr_image_task',
        python_callable=pull_ecr_image
    )
    
    run_etl_container = KubernetesPodOperator(
        task_id='run_container_task_etl',
        name='run-container-etl',
        namespace='prod-airflow',
        # image='196029031078.dkr.ecr.us-east-1.amazonaws.com/hyland-poc-ecr:latest',
        image='hello-world',
        image_pull_policy='Always',
        is_delete_operator_pod=True,
        dag=dag,
        env_vars={
            'AWS_ACCESS_KEY_ID': accessKeyId,
            'AWS_SECRET_ACCESS_KEY': secretAccessKey,
        }
    )

    pull_image >> run_etl_container
