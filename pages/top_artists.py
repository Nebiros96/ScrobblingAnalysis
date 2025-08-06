import streamlit as st
from core.data_loader import load_data
import plotly.express as px

def show():
    st.title("Top 10 Artistas")

    df = load_data("top_artists")
    fig = px.bar(df, x="artist_name", y="plays", title="Artistas más reproducidos")
    st.plotly_chart(fig)
