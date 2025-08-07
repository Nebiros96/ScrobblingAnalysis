# core/connection_notebook.py
from sqlalchemy import create_engine
import urllib

def get_engine_notebook():
    params = urllib.parse.quote_plus(
        "DRIVER=ODBC Driver 18 for SQL Server;"
        "SERVER=DESKTOP-0G59GSS;"
        "DATABASE=musica_julian;"
        "UID=sa;"
        "PWD=1088339312;"
        "TrustServerCertificate=yes;"
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
