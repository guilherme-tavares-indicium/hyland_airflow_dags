from indicium_dag_factory.models.factory_manager import FactoryManager
from airflow import DAG  # noqa: F401
from os import environ


factory_manager = FactoryManager(environ.get("DAG_FACTORY_HOME"))
factory_manager.generate_dags(globals())
