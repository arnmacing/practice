import os
from datetime import datetime, timedelta

import pandas as pd
from bson import json_util
from airflow.decorators import dag, task
from airflow.providers.mongo.hooks.mongo import MongoHook

CSV_FILE_PATH = '/opt/airflow/dbt/sample/last_upload.csv'

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 5),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


@dag(
    dag_id='mongo_dag',
    default_args=default_args,
    description='A simple DAG to interact with MongoDB',
    schedule_interval='@hourly',
    catchup=False,
    max_active_runs=1,
    tags=['mongodb', 'elt', 'service'],
)
def mongo_example_dag():
    @task
    def mongo_query():
        hook = MongoHook(conn_id='mongo_default')
        client = hook.get_conn()
        database_name = 'service'
        collection_name = 'service_data'
        collection = client[database_name][collection_name]
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        query = {
            'timestamp': {
                '$gte': start_time,
                '$lt': end_time,
            },
        }
        documents = collection.find(query)

        serializable_docs = [json_util.loads(json_util.dumps(doc)) for doc in documents]
        return serializable_docs

    @task
    def save_to_csv(documents):
        os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)

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

        df.to_csv(CSV_FILE_PATH, index=False)
        print(f"CSV file saved to {CSV_FILE_PATH}")

    documents = mongo_query()
    save_to_csv(documents)


dag_instance = mongo_example_dag()
