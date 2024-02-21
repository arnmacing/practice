from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
import logging
import os
import pandas as pd
from bson import json_util

logger = logging.getLogger("airflow.task")

CSV_FILE_PATH = '/opt/airflow/dbt/dbt_practice/data/last_upload.csv'
DBT_PROJECT_PATH = '/opt/airflow/dbt/dbt_practice'

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 5, 0, 0, 0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email': ['arina.makunina@mail.ru'],
    'email_on_failure': True,
    'email_on_retry': True,
}


@dag(
    dag_id='mongo_dag',
    default_args=default_args,
    description='A simple DAG to interact with MongoDB',
    schedule_interval='@hourly',
    catchup=True,
    max_active_runs=1,
    tags=['mongodb', 'elt', 'service'],
)
def mongo_example_dag():
    @task
    def mongo_query(execution_date_str):
        hook = MongoHook(conn_id='mongo_default')
        client = hook.get_conn()
        database_name = 'service'
        collection_name = 'service_data'
        collection = client[database_name][collection_name]
        execution_date_str = execution_date_str[:-3] + execution_date_str[-2:]
        print(f"Время выполнения запроса: {execution_date_str}")
        execution_date = datetime.strptime(execution_date_str, '%Y-%m-%dT%H:%M:%S%z')
        print(execution_date)
        end_time = execution_date + timedelta(hours=1)
        start_time = execution_date
        query = {
            'timestamp': {
                '$gte': start_time,
                '$lt': end_time,
            },
        }
        documents = collection.find(query)

        serializable_docs = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            serializable_docs.append(doc)

        if not serializable_docs:
            logger.info("No records found in MongoDB. Skipping further processing.")
            raise AirflowSkipException()

        logger.info(f"Found {len(serializable_docs)} records in MongoDB.")
        logger.info(f"Columns: {list(serializable_docs[0].keys()) if serializable_docs else 'No records'}")

        return json_util.dumps(serializable_docs)

    @task
    def save_to_csv(documents):
        os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)

        documents = json_util.loads(documents)
        df = pd.DataFrame(documents)

        df['_id'] = df['_id'].apply(lambda x: x['$oid'] if '$oid' in x else str(x))
        df['timestamp'] = df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(x['$date'] / 1000) if '$date' in x else x
        )

        df['additional_info'] = df['additional_info'].apply(
            lambda x: json_util.dumps(x) if isinstance(x, dict) else x
        )
        df['origin'] = df['origin'].apply(
            lambda x: json_util.dumps(x) if isinstance(x, dict) else x
        )

        metadata = {
            'transaction_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'MongoDB',
        }

        for key, value in metadata.items():
            df[key] = value

        df.to_csv(CSV_FILE_PATH, index=False)
        logger.info(f"CSV file saved to {CSV_FILE_PATH} with metadata: {metadata}")

    seed_dbt = BashOperator(
        task_id='seed_dbt',
        bash_command=f"""
        dbt seed --profiles-dir {DBT_PROJECT_PATH} --project-dir {DBT_PROJECT_PATH} --full-refresh --select last_upload
        """
    )

    run_dbt_incremental_model = BashOperator(
        task_id='run_dbt_incremental_model',
        bash_command=f"dbt run --profiles-dir {DBT_PROJECT_PATH} --project-dir {DBT_PROJECT_PATH} --select tag:staging"
    )

    run_dbt_marts_model = BashOperator(
        task_id='run_dbt_marts_model',
        bash_command=f"dbt run --profiles-dir {DBT_PROJECT_PATH} --project-dir {DBT_PROJECT_PATH} --select tag:marts"
    )

    run_dbt_bi_model = BashOperator(
        task_id='run_dbt_bi_model',
        bash_command=f"dbt run --profiles-dir {DBT_PROJECT_PATH} --project-dir {DBT_PROJECT_PATH} --select tag:bi_views"
    )

    documents = mongo_query('{{ execution_date }}')
    csv = save_to_csv(documents)
    seed = seed_dbt
    run_incremental = run_dbt_incremental_model
    run_marts = run_dbt_marts_model
    run_bi = run_dbt_bi_model

    documents >> csv >> seed >> run_incremental >> run_marts >> run_bi


dag_instance = mongo_example_dag()
