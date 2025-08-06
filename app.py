import streamlit as st
from pages import overview, top_artists

st.set_page_config(page_title="Scrobblings Dashboard", layout="wide")

st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a:", ["Visión general", "Top Artistas"])

if page == "Visión general":
    overview.show()
elif page == "Top Artistas":
    top_artists.show()
