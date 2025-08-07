import streamlit as st
from core.data_loader import load_user_data, get_cached_data, clear_cache
import altair as alt
import plotly.express as px
import time

from core.data_loader import load_monthly_metrics

st.title("Visión general del uso de Last.fm")
st.subheader("Un recorrido a las reproducciones de música realizadas en Last.fm desde octubre de 2014 hasta la actualidad")

# Verifica si el usuario está en sesión
if "current_user" not in st.session_state:
    st.error("❌ No se ha seleccionado un usuario. Vuelve a la página principal e ingresa uno.")
    st.stop()

user = st.session_state["current_user"]

# Mostrar información del usuario actual
st.info(f"📊 Analizando datos para el usuario: **{user}**")

# Verificar si hay datos en caché
cached_data = get_cached_data(user)
if cached_data is not None:
    success_msg = st.success(f"✅ Usando datos en caché: {len(cached_data):,} tracks cargados previamente")
    
    # Botón para recargar datos
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Recargar datos", help="Cargar datos frescos desde la API"):
            clear_cache(user)
            st.rerun()
    with col2:
        info_msg = st.info("💡 Los datos están en caché. Haz clic en 'Recargar datos' si quieres obtener información actualizada.")
        
        # Borrar mensajes después de 1 segundo
        time.sleep(1)
        success_msg.empty()
        info_msg.empty()

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

# Cargar métricas mensuales
with st.spinner(f"Cargando métricas para {user}..."):
    scrobblings_by_month, artists_by_month, albums_by_month = load_monthly_metrics(user, progress_handler.update_progress)

# Limpiar contenedores de progreso
progress_handler.cleanup()

if scrobblings_by_month is None:
    st.error(f"❌ No se pudieron cargar datos para el usuario '{user}'. Verifica que el usuario existe en Last.fm y tiene scrobblings.")
    st.info("💡 **Sugerencias:**")
    st.info("- Verifica que el nombre de usuario sea correcto")
    st.info("- Asegúrate de que el usuario tenga scrobblings en Last.fm")
    st.info("- Intenta con un usuario diferente")
    st.stop()

# Mostrar resumen de datos
total_scrobblings = scrobblings_by_month['Scrobblings'].sum()
total_artists = artists_by_month['Artists'].sum()
total_albums = albums_by_month['Albums'].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Scrobblings", f"{total_scrobblings:,}")
with col2:
    st.metric("Total Artistas", f"{total_artists:,}")
with col3:
    st.metric("Total Álbumes", f"{total_albums:,}")

# Chart selection buttons
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### Selecciona la visualización:")
    chart_type = st.radio(
        "Tipo de gráfica:",
        ["📊 Scrobblings por mes", "🎵 Artistas por mes", "💿 Álbumes por mes"],
        horizontal=True,
        key="chart_selector"
    )

# Show metrics immediately after chart selection
if chart_type == "📊 Scrobblings por mes":
    # Metrics right after selection
    st.markdown("### 📊 Métricas de Scrobblings")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Scrobblings", f"{scrobblings_by_month['Scrobblings'].sum():,}")
    with col2:
        st.metric("Promedio mensual", f"{scrobblings_by_month['Scrobblings'].mean():.0f}")
    with col3:
        max_month = scrobblings_by_month.loc[scrobblings_by_month['Scrobblings'].idxmax(), 'Year_Month']
        st.metric("Mes con más scrobblings", max_month)
    
    # Chart after metrics
    fig = px.bar(
        scrobblings_by_month, 
        x="Year_Month", 
        y="Scrobblings", 
        title=f"Scrobblings por mes - {user}",
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Número de Scrobblings",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "🎵 Artistas por mes":
    # Metrics right after selection
    st.markdown("### 🎵 Métricas de Artistas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Artistas únicos", f"{artists_by_month['Artists'].sum():,}")
    with col2:
        st.metric("Promedio mensual", f"{artists_by_month['Artists'].mean():.0f}")
    with col3:
        max_month = artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month']
        st.metric("Mes con más artistas", max_month)
    
    # Chart after metrics
    fig2 = px.bar(
        artists_by_month, 
        x="Year_Month", 
        y="Artists", 
        title=f"Artistas únicos por mes - {user}",
        color_discrete_sequence=['#ff7f0e']
    )
    fig2.update_layout(
        xaxis_title="Mes",
        yaxis_title="Número de Artistas Únicos",
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

else:  # Álbumes por mes
    # Metrics right after selection
    st.markdown("### 💿 Métricas de Álbumes")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Álbumes únicos", f"{albums_by_month['Albums'].sum():,}")
    with col2:
        st.metric("Promedio mensual", f"{albums_by_month['Albums'].mean():.0f}")
    with col3:
        max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
        st.metric("Mes con más álbumes", max_month)
    
    # Chart after metrics
    fig3 = px.bar(
        albums_by_month, 
        x="Year_Month", 
        y="Albums", 
        title=f"Álbumes únicos por mes - {user}",
        color_discrete_sequence=['#2ca02c']
    )
    fig3.update_layout(
        xaxis_title="Mes",
        yaxis_title="Número de Álbumes Únicos",
        showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)
