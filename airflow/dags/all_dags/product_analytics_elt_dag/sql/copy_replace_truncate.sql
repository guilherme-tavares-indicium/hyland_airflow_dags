drop table if exists {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}};

create table {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}} (like {{ params.schema }}.{{ params.table_name }});

COPY {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}}
FROM 's3://{{ var.value.target_bucket }}/{{ var.value.target_bucket_prefix }}/{{ params.s3_bucket_key }}/{{ds_nodash}}/'
with credentials
'aws_access_key_id={{ conn.aws_default.login }};aws_secret_access_key={{conn.aws_default.password}}'
{{ params.copy_options }};

update {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}} set airflow_execution_date = '{{ds_nodash}}';

truncate table {{ params.schema }}.{{ params.table_name }};

insert into {{ params.schema }}.{{ params.table_name }} select * from {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}};

drop table {{ params.schema }}.{{ params.table_name }}_temp_{{ds_nodash}};