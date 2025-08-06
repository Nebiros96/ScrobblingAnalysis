import streamlit as st
from core.data_loader import load_data
import altair as alt

def show():
    st.title("Visión general del uso de Last.fm")

    df = load_data("monthly_trends")
    st.subheader("Scrobblings mensuales")

    chart = alt.Chart(df).mark_line(point=True).encode(
        x="month:T",
        y="plays:Q"
    ).properties(width=700)

    st.altair_chart(chart)
