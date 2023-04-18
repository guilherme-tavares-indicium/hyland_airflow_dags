FROM techindicium/indicium_airflow_custom:latest
COPY requirements.txt /opt/airflow/

RUN pip install -r /opt/airflow/requirements.txt