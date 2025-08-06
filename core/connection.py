from sqlalchemy import create_engine
import urllib
import streamlit as st

def get_engine():
    params = urllib.parse.quote_plus(
        f"DRIVER={st.secrets['sqlserver']['driver']};"
        f"SERVER={st.secrets['sqlserver']['server']};"
        f"DATABASE={st.secrets['sqlserver']['database']};"
        f"UID={st.secrets['sqlserver']['username']};"
        f"PWD={st.secrets['sqlserver']['password']};"
        "TrustServerCertificate=yes;"
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
