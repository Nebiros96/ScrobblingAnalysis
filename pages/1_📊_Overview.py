# 1_📊_Overview.py
import streamlit as st
import plotly.express as px
import time
import pandas as pd
from core.data_loader import unique_metrics


st.set_page_config(page_title="Overview - Last.fm Dashboard", layout="wide")

st.title("My Last.fm activity")
st.subheader("A look at your music streams on Last.fm from the beginning to the present")

# --- Lógica de control de estado y carga ---
if "current_user" not in st.session_state:
    st.error("❌ No user has been selected. Return to the main page and enter one.")
    st.stop()

# Si la carga está en curso, muestra el progreso
if "is_loading" in st.session_state and st.session_state["is_loading"]:
    user = st.session_state["current_user"]
    st.info(f"📊 Loading data for user **{user}**...")
    
    # Crear placeholders para la barra de progreso y el texto
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Bucle para actualizar la barra de progreso usando el estado de la sesión
    while st.session_state.get("is_loading"):
        page = st.session_state.get("page", 0)
        total_pages = st.session_state.get("total_pages", 1)
        total_tracks = st.session_state.get("total_tracks", 0)
        
        progress = page / total_pages if total_pages > 0 else 0
        progress_bar.progress(progress)
        
        status_text.text(f"📊 Load page {page}/{total_pages} ({progress:.2%}) - {total_tracks:,} loaded scrobbles.")
        
        # Pequeña pausa para evitar refrescos demasiado rápidos
        time.sleep(0.5)
        
    # Limpiar los elementos de progreso y relanzar para mostrar el contenido completo
    progress_bar.empty()
    status_text.empty()
    st.rerun()

# Si la carga ha terminado y fue exitosa, muestra el contenido
elif "data_loaded_successfully" in st.session_state and st.session_state["data_loaded_successfully"]:
    user = st.session_state["current_user"]

    with st.spinner(f"Loading metrics for {user}..."):
        df_user = st.session_state["df_user"]
        
        # Corrección: Utilizar 'datetime_utc' en lugar de 'date'
        if 'datetime_utc' not in df_user.columns:
            st.error("❌ The 'datetime_utc' column is missing from the loaded data. Please check the data loading process.")
            st.stop()

        # Asegurarse de que la columna es de tipo datetime
        df_user['datetime_utc'] = pd.to_datetime(df_user['datetime_utc'])
        
        scrobblings_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M')).size().reset_index(name='Scrobblings')
        scrobblings_by_month['Year_Month'] = scrobblings_by_month['datetime_utc'].dt.strftime('%Y-%m')
        
        artists_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['artist'].nunique().reset_index(name='Artists')
        artists_by_month['Year_Month'] = artists_by_month['datetime_utc'].dt.strftime('%Y-%m')
        
        albums_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['album'].nunique().reset_index(name='Albums')
        albums_by_month['Year_Month'] = albums_by_month['datetime_utc'].dt.strftime('%Y-%m')

    # Si por alguna razón los datos no están disponibles después de la carga
    if scrobblings_by_month is None:
        st.error(f"❌ Data could not be loaded for the user '{user}'.")
        st.info("💡 **Suggestions:**")
        st.info("- Verify that the username is correct")
        st.info("- The Last.fm API may be unavailable at the moment.")
        st.stop()
    
    # --- Contenido de la página (Métricas y gráficos) ---
    metrics = unique_metrics(user=user, df=df_user)

    col1, col2 = st.columns([1, 1])

    with col1:
        chart_type = st.radio(
            label="Select the metric",
            options=["📊 Scrobblings", "🎵 Artists", "💿 Albums"],
            horizontal=True,
            key="chart_selector"
        )

    with col2:
        time_period = st.radio(
            label="Select time period",
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
            df['Year_Quarter'] = df['Year_Month'].str[:4] + '-Q' + df['Year_Month'].str[5:7].astype(int).apply(lambda x: str((x-1)//3 + 1))
            return df.groupby('Year_Quarter')[data_type].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
        elif period_type == "📈 Year":
            df['Year'] = df['Year_Month'].str[:4]
            return df.groupby('Year')[data_type].sum().reset_index().rename(columns={'Year': 'Year_Month'})

    if chart_type == "📊 Scrobblings":
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
        processed_data = process_data_by_period(scrobblings_by_month, time_period, "Scrobblings")
        fig = px.bar(processed_data, x="Year_Month", y="Scrobblings", title=f"Scrobblings by {time_period.split()[1]} - {user}", color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "🎵 Artists":
        st.markdown("### 🎵 Artists Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Unique Artists",  f"{metrics['unique_artists']:,}")
        with col2:
            st.metric("Monthly Average", f"{metrics['avg_artist_per_month']:.0f}")
        with col3:
            max_month = artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month']
            st.metric("Peak Month", max_month)
        processed_data = process_data_by_period(artists_by_month, time_period, "Artists")
        fig2 = px.bar(processed_data, x="Year_Month", y="Artists", title=f"Unique Artists by {time_period.split()[1]} - {user}", color_discrete_sequence=['#ff7f0e'])
        fig2.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    else:  # Álbumes por mes
        st.markdown("### 💿 Albums Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Unique Albums", metrics["unique_albums"] if metrics else "N/A")
        with col2:
            st.metric("Monthly Average", f"{albums_by_month['Albums'].mean():.0f}")
        with col3:
            max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
            st.metric("Peak Month", max_month)
        processed_data = process_data_by_period(albums_by_month, time_period, "Albums")
        fig3 = px.bar(processed_data, x="Year_Month", y="Albums", title=f"Unique Albums by {time_period.split()[1]} - {user}", color_discrete_sequence=['#2ca02c'])
        fig3.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    if st.button("🏠 Back to Main Page"):
        st.switch_page("Inicio.py")