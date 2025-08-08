import streamlit as st
from core.data_loader import load_user_data, get_cached_data, clear_cache, load_monthly_metrics
import plotly.express as px
import time

st.title("🎵 Top Artists")
st.subheader("Your most listened artists in your Last.fm history")

# Verifica si el usuario está en sesión
if "current_user" not in st.session_state:
    st.error("❌ No user has been selected. Return to the main page and enter one.")
    st.stop()

user = st.session_state["current_user"]

# Mostrar información del usuario actual
st.info(f"📊 Analyzing data for the user: **{user}**")

# Verificar si hay datos en caché y si es la primera vez que se cargan
cached_data = get_cached_data(user)
if cached_data is not None:
    # Solo mostrar mensajes si es la primera vez que se cargan los datos
    if "data_loaded_shown" not in st.session_state:
        success_msg = st.success(f"✅ Using cached data: {len(cached_data):,} previously loaded scrobbles")
        
        # Botón para recargar datos
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Reload data", help="Refresh your Last.fm data from the API"):
                clear_cache(user)
                st.session_state.pop("data_loaded_shown", None)  # Reset flag
                st.rerun()
        with col2:
            info_msg = st.info("💡 The data is cached. Click 'Reload data' if you want updated information.")
            
            # Borrar mensajes después de 1 segundo
            time.sleep(1)
            success_msg.empty()
            info_msg.empty()
        
        # Marcar que ya se mostraron los mensajes
        st.session_state["data_loaded_shown"] = True

# Crear contenedores para el progreso
progress_container = st.container()
status_container = st.container()

class ProgressHandler:
    def __init__(self):
        self.progress_bar = None
        self.status_text = None
    
    def update_progress(self, page, total_pages, total_tracks):
        """Función para actualizar el progreso"""
        if self.progress_bar is None:
            self.progress_bar = progress_container.progress(0)
            self.status_text = status_container.empty()
        
        progress = page / total_pages
        self.progress_bar.progress(progress)
        self.status_text.text(f"📊 Loading page {page}/{total_pages} - {total_tracks:,} loaded scrobbles")
    
    def cleanup(self):
        """Limpia los contenedores de progreso"""
        if self.progress_bar:
            self.progress_bar.empty()
        if self.status_text:
            self.status_text.empty()

# Crear manejador de progreso
progress_handler = ProgressHandler()

# Cargar datos del usuario
with st.spinner(f"Loading data for {user}..."):
    df_user = load_user_data(user, progress_handler.update_progress)

# Limpiar contenedores de progreso
progress_handler.cleanup()

if df_user is None or df_user.empty:
    st.error(f"❌ Data could not be loaded for the user '{user}'. Verify that the user exists on Last.fm and has scrobblings.")
    st.info("💡 **Suggestions:**")
    st.info("- Verify that the username is correct")
    st.info("- Try a different user")
    st.info("- The Last.fm API may be unavailable at the moment.")
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
    yaxis_title="Number of Scrobblings",
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Botón para volver a la página principal
st.markdown("---")
if st.button("🏠 Back to Main Page"):
    st.switch_page("Inicio.py")
