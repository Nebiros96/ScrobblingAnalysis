import streamlit as st
from core.data_loader import load_data
import altair as alt

def show():
    st.title("Visión general del uso de Last.fm")

    df = load_data("last_10_scrobblings")
    st.subheader("Scrobblings mensuales")

    st.dataframe(df, use_container_width=True)
