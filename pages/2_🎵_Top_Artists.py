import streamlit as st
from core.data_loader import load_data
import plotly.express as px

st.title("🎵 Top 10 Artistas")
st.subheader("Los artistas más escuchados en tu historial de Last.fm")

# Load data
df = load_data("top_artists")

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de artistas", len(df))
with col2:
    st.metric("Total scrobblings", f"{df['Scrobblings'].sum():,}")
with col3:
    st.metric("Artista más escuchado", df.iloc[0]['Artist'])

# Create and display chart
fig = px.bar(
    df, 
    x="Artist", 
    y="Scrobblings", 
    title="Artistas más reproducidos",
    color_discrete_sequence=['#ff7f0e']
)
fig.update_layout(
    xaxis_title="Artista",
    yaxis_title="Número de Scrobblings",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Display data table
st.subheader("📊 Datos detallados")
st.dataframe(df, use_container_width=True)
