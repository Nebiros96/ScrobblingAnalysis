import streamlit as st
from core.data_loader import load_user_data, get_cached_data, clear_cache
import time
import threading

st.set_page_config(page_title="Last.fm Scrobblings Dashboard", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
    width: 100%;
}
.clickable-info {
    cursor: pointer;
    transition: all 0.3s ease;
}
.clickable-info:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- 🧪 Formulario de búsqueda de usuario ---
st.markdown("### 🔎 Explora tu actividad en Last.fm")
with st.form("user_search_form"):
    input_user = st.text_input("Ingresa tu usuario de Last.fm:", placeholder="ej. Brenoritvrezork")
    submitted = st.form_submit_button("Load Lastfm data")

if submitted and input_user:
    # Verificar si hay datos en caché
    cached_data = get_cached_data(input_user)
    if cached_data is not None:
        success_msg = st.success(f"✅ Usando datos en caché: {len(cached_data):,} tracks cargados previamente")
        st.session_state["current_user"] = input_user
        
        # Borrar mensaje después de 3 segundos
        time.sleep(3)
        success_msg.empty()
    else:
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
                self.status_text.text(f"📊 Cargando página {page}/{total_pages} - {total_tracks:,} tracks cargados...")
            
            def cleanup(self):
                """Limpia los contenedores de progreso"""
                if self.progress_bar:
                    self.progress_bar.empty()
                if self.status_text:
                    self.status_text.empty()
        
        # Crear manejador de progreso
        progress_handler = ProgressHandler()
        
        # Cargar datos con progreso
        with st.spinner("Iniciando carga de datos..."):
            df_user = load_user_data(input_user, progress_handler.update_progress)
        
        # Limpiar contenedores de progreso
        progress_handler.cleanup()
        
        if df_user is None or df_user.empty:
            st.error("No se encontraron scrobblings para este usuario.")
        else:
            success_msg = st.success(f"✅ ¡Datos cargados exitosamente! Se encontraron {len(df_user):,} scrobblings para {input_user}")
            st.session_state["current_user"] = input_user
            
            # Borrar mensaje después de 3 segundos
            time.sleep(3)
            success_msg.empty()

# Mostrar información del usuario actual si existe
if "current_user" in st.session_state:
    user = st.session_state["current_user"]
    cached_data = get_cached_data(user)
    
    if cached_data is not None:
        # Crear contenedor para la información del usuario
        user_info_container = st.container()
        
        with user_info_container:
            st.info(f"Current user: **{user}** ({len(cached_data):,} scrobbles)")
            
            # Botón para limpiar caché
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🗑️ Clean data", help="Eliminar datos en caché"):
                    clear_cache(user)
                    st.rerun()
            with col2:
                info_msg = st.info("💡 Los datos están guardados en caché")
                
                # Borrar mensaje informativo después de 5 segundos
                time.sleep(1)
                info_msg.empty()

# --- Título y ayuda ---
st.title("🎵 Last.fm Scrobblings Dashboard")

with open("help.md", "r", encoding="utf-8") as f:
    help_content = f.read()
st.markdown(help_content)

# --- Navegación rápida ---
st.markdown("### 🚀 Navegación rápida")
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.info("📊 **Visión General**\n\nAnaliza tendencias y patrones de escucha")
        if st.button("Ir a Visión General", key="nav_vision"):
            st.switch_page("pages/1_📊_Visión_General.py")

with col2:
    with st.container():
        st.info("🎵 **Top Artistas**\n\nDescubre los artistas favoritos")
        if st.button("Ir a Top Artistas", key="nav_artists"):
            st.switch_page("pages/2_��_Top_Artistas.py")
