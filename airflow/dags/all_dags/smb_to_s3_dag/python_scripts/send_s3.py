
def send_to_s3(table, sheet, year, **kwargs):

    from asyncio.log import logger
    import os
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    def excel_to_json(filepath, sheet, output_file_name):
        """
        Convert an Excel file to a JSON file.
        """
        import pandas as pd
        import gzip

        df = pd.read_excel(filepath, sheet_name=sheet, engine='openpyxl')
        df.columns = df.columns.str.lower()
        json_data = df.to_json(orient='records', lines=True, force_ascii=False)
        encoded = json_data.encode('utf-8')
        # Compress
        with gzip.open(f'{output_file_name}', 'w') as json_file:
            json_file.write(encoded)

    EXEC_DATE = kwargs['ds']
    print(EXEC_DATE)
    tmp_dir = "/opt/airflow/downloads"
    source_s3 = S3Hook("airflow_aws_conn")
    destination_bucket = "data-s3"
    s3_prefix = "data/raw/something"
    files = [file for file in os.listdir(tmp_dir) if file.endswith(f'{year}.xlsx')]

    logger.info(tmp_dir)

    for filename in files:
        logger.info(filename)
        filepath_input = f"{tmp_dir}/{filename}"
        output_filename = filename.replace(".xlsx", ".json.gz")
        output_filename = f"{sheet}_{output_filename}"
        filepath_output = f"{tmp_dir}/{output_filename}"

        excel_to_json(filepath=filepath_input, sheet=sheet, output_file_name=filepath_output)

        key_full_path = f"{s3_prefix}/{table}/{EXEC_DATE}/{year}/{output_filename}"

        source_s3.load_file(replace=True, bucket_name=destination_bucket, filename=filepath_output, key=key_full_path)
