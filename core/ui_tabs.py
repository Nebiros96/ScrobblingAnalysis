# core/ui_tabs.py
import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import unique_metrics


# ----------------------------------------
# 📈 Tab: Statistics
# ----------------------------------------
def tab_statistics(user, metrics):
    """
    Renders the statistics tab for the user's scrobbling data.

    Args:
        user (str): The Last.fm username.
        metrics (dict): A dictionary containing the pre-calculated metrics.
    """
    st.markdown("## 📈 Statistics")

    if metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scrobblings", f"{metrics['total_scrobblings']:,}")
            st.metric("Unique Artists", f"{metrics['unique_artists']:,}")
            st.metric("Unique Albums", f"{metrics['unique_albums']:,}")
            st.metric("Unique Songs", f"{metrics['unique_tracks']:,}")
        with col2:
            st.metric("Days with scrobbles", f"{metrics['unique_days']:,} ({metrics['pct_days_with_scrobbles']:.1f} %)")
            st.metric("Days since first scrobble", f"{metrics['days_natural']:,}")
            st.metric(
                "Avg Scrobbles by total days", 
                f"{metrics['avg_scrobbles_per_day']:.1f}", 
                help="Average scrobbles per day including days of no activity"
            )
            st.metric(
                "Avg Scrobbles by day", 
                f"{metrics['avg_scrobbles_per_day_with']:.1f}", 
                help="Average scrobbles per day (only days with scrobbles)"
            )
        with col3:
            st.metric(
                "Peak Day",
                f"{metrics['peak_day']} ({metrics['peak_day_scrobblings']:,})",
                help="The day with the highest number of scrobbles."
            )
            st.metric(
                "First Scrobble",
                metrics['first_date'].strftime("%Y-%m-%d") if pd.notnull(metrics['first_date']) else "N/A"
            )
            st.metric(
                "Last Scrobble",
                metrics['last_date'].strftime("%Y-%m-%d") if pd.notnull(metrics['last_date']) else "N/A"
            )
    else:
        st.error("Metrics could not be loaded for the user.")


# ----------------------------------------
# 📊 Tab: Overview
# ----------------------------------------
def tab_overview(user, df_user, metrics):
    """
    Renders the overview tab with charts and metrics based on scrobbling data.

    Args:
        user (str): The Last.fm username.
        df_user (pd.DataFrame): The user's preprocessed scrobbling data.
        metrics (dict): A dictionary containing the pre-calculated metrics.
    """
    st.markdown("## 📈 Overview")

    # Pre-procesamiento de datos para los gráficos.
    # Esta lógica está contenida aquí para mantener el código de la pestaña modular.
    if 'datetime_utc' not in df_user.columns:
        st.error("❌ The 'datetime_utc' column is missing from the loaded data.")
        st.stop()
    df_user['datetime_utc'] = pd.to_datetime(df_user['datetime_utc'])

    scrobblings_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M')).size().reset_index(name='Scrobblings')
    scrobblings_by_month['Year_Month'] = scrobblings_by_month['datetime_utc'].dt.strftime('%Y-%m')

    artists_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['artist'].nunique().reset_index(name='Artists')
    artists_by_month['Year_Month'] = artists_by_month['datetime_utc'].dt.strftime('%Y-%m')

    albums_by_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['album'].nunique().reset_index(name='Albums')
    albums_by_month['Year_Month'] = albums_by_month['datetime_utc'].dt.strftime('%Y-%m')

    # Helper function para procesar datos por periodo
    def process_data_by_period(df, period_type, data_type):
        if period_type == "📅 Month":
            return df
        elif period_type == "📊 Quarter":
            df['Year_Quarter'] = df['Year_Month'].str[:4] + '-Q' + df['Year_Month'].str[5:7].astype(int).apply(lambda x: str((x - 1) // 3 + 1))
            return df.groupby('Year_Quarter')[data_type].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
        elif period_type == "📈 Year":
            df['Year'] = df['Year_Month'].str[:4]
            return df.groupby('Year')[data_type].sum().reset_index().rename(columns={'Year': 'Year_Month'})

    # Controles de UI para seleccionar tipo de gráfico y periodo
    col1_chart, col2_chart = st.columns([1, 1])
    with col1_chart:
        chart_type = st.radio(
            label="Select the metric",
            options=["📊 Scrobblings", "🎵 Artists", "💿 Albums"],
            horizontal=True,
            key="chart_selector"
        )
    with col2_chart:
        time_period = st.radio(
            label="Select time period",
            options=["📅 Month", "📊 Quarter", "📈 Year"],
            horizontal=True,
            key="time_selector"
        )

    # Generación de gráficos basada en la selección del usuario
    if chart_type == "📊 Scrobblings":
        st.markdown("#### Scrobblings Overview")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Scrobblings", f"{metrics['total_scrobblings']:,}")
        with col2: st.metric("Monthly Average", f"{metrics['avg_scrobbles_per_month']:.1f}")
        with col3: st.metric(label=f"Peak Month ({metrics['peak_month_scrobblings']:,} scrobbles)", value=f"{metrics['peak_month']}")
        processed_data = process_data_by_period(scrobblings_by_month, time_period, "Scrobblings")
        fig = px.bar(processed_data, x="Year_Month", y="Scrobblings", title=f"Scrobblings by {time_period.split()[1]} - {user}", color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "🎵 Artists":
        st.markdown("### 🎵 Artists Overview")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Unique Artists", f"{metrics['unique_artists']:,}")
        with col2: st.metric("Monthly Average", f"{metrics['avg_artist_per_month']:.0f}")
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
        with col1: st.metric("Unique Albums", f"{metrics['unique_albums']:,}" if 'unique_albums' in metrics else "N/A")
        with col2: st.metric("Monthly Average", f"{albums_by_month['Albums'].mean():.0f}")
        with col3:
            max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
            st.metric("Peak Month", max_month)
        processed_data = process_data_by_period(albums_by_month, time_period, "Albums")
        fig3 = px.bar(processed_data, x="Year_Month", y="Albums", title=f"Unique Albums by {time_period.split()[1]} - {user}", color_discrete_sequence=['#2ca02c'])
        fig3.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    st.markdown("---")


# ----------------------------------------
# 🎵 Tab: Top Artists
# ----------------------------------------
def tab_top_artists(user, df_user, metrics):
    """
    Renders the Top Artists tab with a bar chart and key metrics.

    Args:
        user (str): The Last.fm username.
        df_user (pd.DataFrame): The user's scrobbling data.
        metrics (dict): A dictionary containing pre-calculated metrics.
    """
    st.markdown("## 🎵 Top Artists")
    
    # Pre-procesamiento para encontrar los Top 10 artistas
    top_artists = df_user.groupby('artist').size().reset_index(name='Scrobblings')
    top_artists = top_artists.sort_values('Scrobblings', ascending=False).head(10)
    top_artists['Artist'] = top_artists['artist']
    
    # Visualización de métricas
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("Unique Artists", f"{metrics['unique_artists']:,}")
    with col2: 
        st.metric("Total Scrobblings", f"{len(df_user):,}")
    with col3: 
        # Asegúrate de que top_artists no esté vacío antes de acceder a iloc
        if not top_artists.empty:
            st.metric("Top Artist", top_artists.iloc[0]['Artist'])
        else:
            st.metric("Top Artist", "N/A")
    
    # Creación y visualización del gráfico de barras
    if not top_artists.empty:
        fig = px.bar(top_artists, x="Artist", y="Scrobblings", title=f"Top 10 Artists - {user}", color_discrete_sequence=['#ff7f0e'])
        fig.update_layout(xaxis_title="Artist", yaxis_title="Number of Scrobblings", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de artistas para mostrar.")
        
    st.markdown("---")

# ----------------------------------------
# ℹ️ Tab: Info
# ----------------------------------------
def tab_info():
    """
    Renders the Info tab, including the logic to load and display content 
    from the help.md file.
    """
    st.markdown("#### ℹ️ Info")

    @st.cache_data
    def load_help_md():
        try:
            with open("help.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    help_content = load_help_md()
    if help_content:
        st.markdown(help_content, unsafe_allow_html=False)
    else:
        st.error("⚠️ help.md file not found.")