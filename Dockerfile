FROM apache/airflow:2.2.3

USER root

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        mongo-tools \
        build-essential \
        python3-dev \
        nano \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir 'apache-airflow[postgres, mongo]'
RUN pip install --no-cache-dir 'dbt==0.21.1'

COPY ./dags /opt/airflow/dags

USER airflow