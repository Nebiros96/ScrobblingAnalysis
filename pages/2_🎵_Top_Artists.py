import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Top Artists - Last.fm Dashboard", layout="wide")

st.title("🎵 Top Artists")
st.subheader("Your most listened artists in your Last.fm history")

# --- Lógica de control de estado ---
# 1. Verificar si existe el usuario en la sesión
if "current_user" not in st.session_state:
    st.error("❌ No user has been selected. Return to the main page and enter one.")
    st.stop()

# 2. Verificar si la carga de datos fue exitosa
if "data_loaded_successfully" not in st.session_state or not st.session_state["data_loaded_successfully"]:
    st.warning("⚠️ Data has not been loaded or an error occurred. Please return to the main page and try again.")
    st.stop()

# Si todo está bien, cargar el DataFrame desde la sesión
user = st.session_state["current_user"]
df_user = st.session_state["df_user"]

# Mostrar información del usuario actual
st.info(f"📊 Analyzing data for the user: **{user}**")

# Si por alguna razón los datos no están disponibles después de la carga
if df_user is None or df_user.empty:
    st.error(f"❌ Data could not be loaded for the user '{user}'. Verify that the user exists on Last.fm and has scrobblings.")
    st.stop()

# Calcular top artistas
top_artists = df_user.groupby('artist').size().reset_index(name='Scrobblings')
top_artists = top_artists.sort_values('Scrobblings', ascending=False).head(10)
top_artists['Artist'] = top_artists['artist']

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Artists", len(df_user['artist'].unique()))
with col2:
    st.metric("Total Scrobblings", f"{len(df_user):,}")
with col3:
    st.metric("Top Artist", top_artists.iloc[0]['Artist'])

# Create and display chart
fig = px.bar(
    top_artists, 
    x="Artist", 
    y="Scrobblings", 
    title=f"Top 10 Artists - {user}",
    color_discrete_sequence=['#ff7f0e']
)
fig.update_layout(
    xaxis_title="Artist",
    yaxis_title="Number of Scrobbles",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Botón para volver a la página principal
st.markdown("---")
if st.button("🏠 Back to Main Page"):
    st.switch_page("Inicio.py")