import oracledb
import os
from app.config import DB_USER, DB_PASS, DB_DSN

def get_connection():
    oracledb.init_oracle_client(
        lib_dir=r"C:\Users\TI\Documents\Projetos\instantclient-basic-windows.x64-19.29.0.0.0dbru\instantclient_19_29"
    )

    return oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=DB_DSN
    )