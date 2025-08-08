import streamlit as st
from core.data_loader import load_user_data, get_cached_data, clear_cache
import altair as alt
import plotly.express as px
import time

from core.data_loader import load_monthly_metrics, unique_metrics

st.title("My Last.fm activity")
st.subheader("A look at your music streams on Last.fm from the beginning to the present")

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

# Cargar métricas mensuales
with st.spinner(f"Loading metrics for {user}..."):
    scrobblings_by_month, artists_by_month, albums_by_month = load_monthly_metrics(user, progress_handler.update_progress)

# Limpiar contenedores de progreso
progress_handler.cleanup()

if scrobblings_by_month is None:
    st.error(f"❌ Data could not be loaded for the user '{user}'. Verify that the user exists on Last.fm and has scrobblings.")
    st.info("💡 **Suggestions:**")
    st.info("- Verify that the username is correct")
    st.info("- Try a different user")
    st.info("- The Last.fm API may be unavailable at the moment.")
    st.stop()

# Mostrar resumen de datos
total_scrobblings = scrobblings_by_month['Scrobblings'].sum()
total_artists = artists_by_month['Artists'].sum()
total_albums = albums_by_month['Albums'].sum()

# Opciones de eje X
col1, col2 = st.columns([1, 1])

with col1:
    chart_type = st.radio(
        label="Select the metric", # Etiqueta vacía para ocultar el texto
        options=["📊 Scrobblings", "🎵 Artists", "💿 Albums"],
        horizontal=True,
        key="chart_selector"
    )

with col2:
    time_period = st.radio(
        label="Select time period", # Etiqueta vacía para ocultar el texto
        options=["📅 Month", "📊 Quarter", "📈 Year"],
        horizontal=True,
        key="time_selector"
    )
# Función para procesar datos según el período de tiempo
def process_data_by_period(df, period_type, data_type):
    """Procesa los datos según el período de tiempo seleccionado"""
    if period_type == "📅 Month":
        return df
    elif period_type == "📊 Quarter":
        # Agrupar por trimestre (Year-Quarter)
        df['Year_Quarter'] = df['Year_Month'].str[:4] + '-Q' + df['Year_Month'].str[5:7].astype(int).apply(lambda x: str((x-1)//3 + 1))
        if data_type == "Scrobblings":
            return df.groupby('Year_Quarter')['Scrobblings'].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
        elif data_type == "Artists":
            return df.groupby('Year_Quarter')['Artists'].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
        elif data_type == "Albums":
            return df.groupby('Year_Quarter')['Albums'].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
    elif period_type == "📈 Year":
        # Agrupar por año
        df['Year'] = df['Year_Month'].str[:4]
        if data_type == "Scrobblings":
            return df.groupby('Year')['Scrobblings'].sum().reset_index().rename(columns={'Year': 'Year_Month'})
        elif data_type == "Artists":
            return df.groupby('Year')['Artists'].sum().reset_index().rename(columns={'Year': 'Year_Month'})
        elif data_type == "Albums":
            return df.groupby('Year')['Albums'].sum().reset_index().rename(columns={'Year': 'Year_Month'})

# Show metrics immediately after chart selection
# Metricas
metrics = unique_metrics(user)

if chart_type == "📊 Scrobblings":
    # Metrics right after selection
    st.markdown("### 📊 Scrobblings Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Scrobblings", f"{metrics['total_scrobblings']:,}")
    with col2:
        st.metric("Monthly Average", f"{metrics['avg_scrobbles_per_month']:.1f}")
    with col3:
        st.metric(
            label=f"Peak Month ({metrics['peak_month_scrobblings']:,} scrobbles)",
            value=f"{metrics['peak_month']}",
            help="The month with the highest number of scrobbles."
        )
    
    # Procesar datos según el período seleccionado
    processed_data = process_data_by_period(scrobblings_by_month, time_period, "Scrobblings")
    
    # Chart after metrics
    fig = px.bar(
        processed_data, 
        x="Year_Month", 
        y="Scrobblings", 
        title=f"Scrobblings by {time_period.split()[1]} - {user}",
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "🎵 Artists":
    # Metrics right after selection
    st.markdown("### 🎵 Artists Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Unique Artists",  f"{metrics['unique_artists']:,}")
    with col2:
        st.metric("Monthly Average", f"{metrics['avg_artist_per_month']:.0f}")
    with col3:
        max_month = artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month']
        st.metric("Peak Month", max_month)
    
    # Procesar datos según el período seleccionado
    processed_data = process_data_by_period(artists_by_month, time_period, "Artists")
    
    # Chart after metrics
    fig2 = px.bar(
        processed_data, 
        x="Year_Month", 
        y="Artists", 
        title=f"Unique Artists by {time_period.split()[1]} - {user}",
        color_discrete_sequence=['#ff7f0e']
    )
    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

else:  # Álbumes por mes
    # Metrics right after selection
    st.markdown("### 💿 Albums Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Unique Albums", metrics["unique_albums"] if metrics else "N/A")
    with col2:
        st.metric("Monthly Average", f"{albums_by_month['Albums'].mean():.0f}")
    with col3:
        max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
        st.metric("Peak Month", max_month)
    
    # Procesar datos según el período seleccionado
    processed_data = process_data_by_period(albums_by_month, time_period, "Albums")
    
    # Chart after metrics
    fig3 = px.bar(
        processed_data, 
        x="Year_Month", 
        y="Albums", 
        title=f"Unique Albums by {time_period.split()[1]} - {user}",
        color_discrete_sequence=['#2ca02c']
    )
    fig3.update_layout(
        xaxis_title="Date",
        yaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)

# Botón para volver a la página principal
st.markdown("---")
if st.button("🏠 Back to Main Page"):
    st.switch_page("Inicio.py")
