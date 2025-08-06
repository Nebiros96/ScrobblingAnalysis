import pandas as pd
from core.connection import get_engine
from core.queries import QUERIES

def load_data(query_name):
    engine = get_engine()
    query = QUERIES[query_name]
    return pd.read_sql(query, engine)
