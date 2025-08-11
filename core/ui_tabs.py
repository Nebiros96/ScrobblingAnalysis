# core/ui_tabs.py
import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import unique_metrics, load_monthly_metrics


# ----------------------------------------
# 📈 Tab: Statistics
# ----------------------------------------
def tab_statistics(user, df_user, metrics):
    """
    - Primer bloque: métricas globales.
    - Segundo bloque: métricas recalculadas según rango de fechas con st.date_input o todo el período.
    Args:
        user (str): The Last.fm username.
        df_user (df): User's dataframe
        metrics (dict): A dictionary containing the pre-calculated metrics.
    """
    st.markdown("## 📈 Statistics")

    # --- Bloque global ---
    if metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scrobblings", f"{metrics['total_scrobblings']:,}", border=True)
            st.metric("Unique Artists", f"{metrics['unique_artists']:,}", border=True)
            st.metric("Unique Albums", f"{metrics['unique_albums']:,}", border=True)
            st.metric("Unique Songs", f"{metrics['unique_tracks']:,}", border=True)
        with col2:
            st.metric("Days with scrobbles", f"{metrics['unique_days']:,} ({metrics['pct_days_with_scrobbles']:.1f} %)", border=True)
            st.metric("Days since first scrobble", f"{metrics['days_natural']:,}", border=True)
            st.metric("Avg Scrobbles by total days", f"{metrics['avg_scrobbles_per_day']:.1f}", border=True,
                      help="Average scrobbles per day including days of no activity")
            st.metric("Avg Scrobbles by day", f"{metrics['avg_scrobbles_per_day_with']:.1f}", border=True,
                      help="Average scrobbles per day (only days with scrobbles)")
        with col3:
            st.metric("Peak Day", f"{metrics['peak_day']} ({metrics['peak_day_scrobblings']:,})", border=True,
                      help="The day with the highest number of scrobbles.")
            st.metric("First Scrobble", metrics['first_date'].strftime("%Y-%m-%d") if pd.notnull(metrics['first_date']) else "N/A", border=True)
            st.metric("Last Scrobble", metrics['last_date'].strftime("%Y-%m-%d") if pd.notnull(metrics['last_date']) else "N/A", border=True)
    else:
        st.error("Metrics could not be loaded for the user.")

    # --- Segundo bloque ---
    st.markdown("## 📈 Statistics: Filtered Period")

    df_user = df_user.copy()
    df_user['datetime_utc'] = pd.to_datetime(df_user['datetime_utc'])
    min_date = df_user['datetime_utc'].dt.date.min()
    max_date = df_user['datetime_utc'].dt.date.max()

    if pd.isna(min_date) or pd.isna(max_date):
        st.info("No hay fechas disponibles para filtrar.")
        return

    # Checkbox para mostrar todo el período
    show_full_period = st.checkbox(
        "📅 Show entire time period, instead.", 
        value=True, 
        key=f"full_period_{user}",
        help="Disable this option to select a custom date range.")

    if show_full_period:
        start_date, end_date = min_date, max_date
    else:
        date_selection = st.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"stats_dateinput_{user}"
        )

        if not (isinstance(date_selection, (list, tuple)) and len(date_selection) == 2):
            st.warning("Please also select the end date for calculating the metrics.")
            return

        start_date, end_date = date_selection

        if start_date > end_date:
            st.warning("The start date is greater than the end date. Please correct the range.")
            return

    # Filtrar por rango
    mask = (df_user['datetime_utc'].dt.date >= start_date) & (df_user['datetime_utc'].dt.date <= end_date)
    filtered_df = df_user.loc[mask]

    if filtered_df.empty:
        st.info("No scrobbles found in the selected range.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Scrobblings", "0")
            st.metric("Unique Artists", "0")
            st.metric("Unique Albums", "0")
            st.metric("Unique Songs", "0")
        with col2:
            st.metric("Days with scrobbles", "0 (0.00%)")
            st.metric("Avg Scrobbles by total days", "0.0")
            st.metric("Avg Scrobbles by day", "0.0")
            st.metric("Peak Day", "N/A")
        return

    # Recalcular métricas sobre el subset
    filtered_metrics = unique_metrics(df=filtered_df)
    if filtered_metrics is None:
        st.error("Error computing filtered metrics.")
        return

    # Mostrar métricas filtradas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Scrobblings", f"{filtered_metrics['total_scrobblings']:,}")
        st.metric("Unique Artists", f"{filtered_metrics['unique_artists']:,}")
        st.metric("Unique Albums", f"{filtered_metrics['unique_albums']:,}")
        st.metric("Unique Songs", f"{filtered_metrics['unique_tracks']:,}")
    with col2:
        st.metric("Days with scrobbles", f"{filtered_metrics['unique_days']:,} ({filtered_metrics['pct_days_with_scrobbles']:.1f}%)")
        st.metric("Avg Scrobbles by total days", f"{filtered_metrics['avg_scrobbles_per_day']:.1f}")
        st.metric("Avg Scrobbles by day", f"{filtered_metrics['avg_scrobbles_per_day_with']:.1f}")
        st.metric("Peak Day", f"{filtered_metrics['peak_day']} ({filtered_metrics['peak_day_scrobblings']:,})")

    st.markdown("---")


# ----------------------------------------
# 📊 Tab: Overview
# ----------------------------------------
def tab_overview(user, df_user, metrics):
    """
    Renders the overview tab showing all three metrics (Scrobblings, Artists, Albums)
    with only the time period selectable.
    """
    st.markdown("### 📈 Overview")

    # 📊 Obtener métricas mensuales ya calculadas desde df_user (sin nueva llamada a la API)
    scrobblings_by_month, artists_by_month, albums_by_month = load_monthly_metrics(df=df_user)

    if scrobblings_by_month is None:
        st.error("No data available to display.")
        return

    # Helper para procesar datos por periodo
    def process_data_by_period(df, period_type, data_type):
        if period_type == "📅 Month":
            return df
        elif period_type == "📊 Quarter":
            df['Year_Quarter'] = (
                df['Year_Month'].str[:4] + '-Q' +
                df['Year_Month'].str[5:7].astype(int).apply(lambda x: str((x - 1) // 3 + 1))
            )
            return df.groupby('Year_Quarter')[data_type].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
        elif period_type == "📈 Year":
            df['Year'] = df['Year_Month'].str[:4]
            return df.groupby('Year')[data_type].sum().reset_index().rename(columns={'Year': 'Year_Month'})

    # 🎯 Selección única de periodo
    time_period = st.radio(
        label="Select time period",
        options=["📅 Month", "📊 Quarter", "📈 Year"],
        horizontal=True,
        key="time_selector"
    )

    # 1️⃣ Scrobblings
    st.markdown("### 📊 Scrobblings Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Scrobblings", f"{metrics['total_scrobblings']:,}", border=True)
    with col2: st.metric("Monthly Average", f"{metrics['avg_scrobbles_per_month']:.1f}", border=True)
    with col3: st.metric(label=f"Peak Month ({metrics['peak_month_scrobblings']:,} scrobbles)", value=f"{metrics['peak_month']}", border=True)
    processed_data = process_data_by_period(scrobblings_by_month, time_period, "Scrobblings")
    fig = px.bar(processed_data, x="Year_Month", y="Scrobblings", title=f"Scrobblings by {time_period.split()[1]} - {user}", color_discrete_sequence=['#1f77b4'])
    fig.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # 2️⃣ Artists
    st.markdown("### 🎵 Artists Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Artists", f"{metrics['unique_artists']:,}", border=True)
    with col2: st.metric("Monthly Average", f"{metrics['avg_artist_per_month']:.0f}", border=True)
    with col3:
        max_month = artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month']
        st.metric("Peak Month", max_month, border=True)
    processed_data = process_data_by_period(artists_by_month, time_period, "Artists")
    fig2 = px.bar(processed_data, x="Year_Month", y="Artists", title=f"Unique Artists by {time_period.split()[1]} - {user}", color_discrete_sequence=['#ff7f0e'])
    fig2.update_layout(xaxis_title="Date", yaxis_title="", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    # 3️⃣ Albums
    st.markdown("### 💿 Albums Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Albums", f"{metrics['unique_albums']:,}" if 'unique_albums' in metrics else "N/A", border=True)
    with col2: st.metric("Monthly Average", f"{albums_by_month['Albums'].mean():.0f}", border=True)
    with col3:
        max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
        st.metric("Peak Month", max_month, border=True)
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
    st.markdown("### 🎵 Top Artists")
    
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