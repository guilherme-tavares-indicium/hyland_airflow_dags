drop table if exists {{ params.schema }}.{{ params.table_name }}_temp_{{ds}};

create table {{ params.schema }}.{{ params.table_name }}_temp_{{ds}} (like {{ params.schema }}.{{ params.table_name }});

COPY {{ params.schema }}.{{ params.table_name }}_temp_{{ds}}
FROM 's3://{{ var.value.TARGET_BUCKET }}{{ params.s3_bucket_key }}/{{ds}}'
with credentials
'aws_access_key_id={{ conn.airflow_aws_conn.login }};aws_secret_access_key={{conn.airflow_aws_conn.password}}'
{{ params.copy_options }};

update {{ params.schema }}.{{ params.table_name }}_temp_{{ds}} set airflow_execution_date = {{ ds }};

truncate table {{ params.schema }}.{{ params.table_name }};

insert into {{ params.schema }}.{{ params.table_name }} select * from {{ params.schema }}.{{ params.table_name }}_temp_{{ds}};

drop table {{ params.schema }}.{{ params.table_name }}_temp_{{ds}};
