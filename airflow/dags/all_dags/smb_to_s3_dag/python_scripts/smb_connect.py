
def download_to_tmp(year, **kwargs):

    import logging
    import os
    from airflow.hooks.base_hook import BaseHook
    from smbclient import (
        listdir,
        register_session,
        delete_session,
        shutil,
    )
    logging.basicConfig(level=logging.INFO)

    conn_fileserver = BaseHook.get_connection('fileserver_semparar')
    fileserver_user = conn_fileserver.login
    fileserver_pass = conn_fileserver.password
    server = "vpn-forti.hutransportes.com.br"
    main_dir = r"\\" + f"{server}" + r"\SemParar"
    tmp_dir = "/opt/airflow/downloads"

    logging.info(fileserver_user)

    if os.path.isdir(tmp_dir):
        pass
    else:
        os.makedirs(tmp_dir)

    try:
        # Optional - register the server with explicit credentials
        logging.info("Registering session")
        register_session(
            server,
            username=fileserver_user,
            password=fileserver_pass
        )

        files = [file for file in listdir(main_dir) if file.endswith(f'{year}.xlsx')]
        logging.info(f"Copying {len(files)} files from remote server")

        for filename in files:
            logging.info(f"Saving '{filename}' in '{tmp_dir}' folder")
            shutil.copy(f"{main_dir}/{filename}", tmp_dir)
        logging.info("All done.")

    finally:
        logging.info("Closing connection.")
        delete_session(server)
