# core/ui_tabs.py
import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import unique_metrics, load_monthly_metrics, calculate_streak_metrics, calculate_all_metrics


# ----------------------------------------
# 📈 Tab: Statistics
# ----------------------------------------
def tab_statistics(user, df_user, all_metrics):
    """
    - Primer bloque: métricas globales.
    - Segundo bloque: métricas recalculadas según rango de fechas con st.date_input o todo el período.
    Args:
        user (str): The Last.fm username.
        df_user (df): User's dataframe
        metrics (dict): A dictionary containing the pre-calculated metrics.
    """
    st.markdown("### 📈 Statistics")

    # --- Statistics ---
    if all_metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scrobblings", f"{all_metrics['total_scrobblings']:,}", border=True)
            st.metric("Unique Artists", f"{all_metrics['unique_artists']:,}", border=True)
            st.metric("Unique Albums", f"{all_metrics['unique_albums']:,}", border=True)
            st.metric("Unique Songs", f"{all_metrics['unique_tracks']:,}", border=True)
        with col2:
            st.metric("Days with scrobbles", f"{all_metrics['unique_days']:,} ({all_metrics['pct_days_with_scrobbles']:.1f} %)", border=True)
            st.metric("Days since first scrobble", f"{all_metrics['days_natural']:,}", border=True)
            st.metric("Avg Scrobbles by total days", f"{all_metrics['avg_scrobbles_per_day']:.1f}", border=True,
                      help="Average scrobbles per day including days of no activity")
            st.metric("Avg Scrobbles by day", f"{all_metrics['avg_scrobbles_per_day_with']:.1f}", border=True,
                      help="Average scrobbles per day (only days with scrobbles)")
        with col3:
            st.metric("Peak Day", f"{all_metrics['peak_day']} ({all_metrics['peak_day_scrobblings']:,})", border=True,
                      help="The day with the highest number of scrobbles.")
            st.metric("First Scrobble", all_metrics['first_date'].strftime("%Y-%m-%d") if pd.notnull(all_metrics['first_date']) else "N/A", border=True)
            st.metric("Last Scrobble", all_metrics['last_date'].strftime("%Y-%m-%d") if pd.notnull(all_metrics['last_date']) else "N/A", border=True)
    else:
        st.error("Metrics could not be loaded for the user.")

    st.markdown("---")
    st.markdown("### 📈 Detailed Statistics")

    # --- 📈 Detailed Statistics ---
    if all_metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔥 Longest Streak (days)", f"{all_metrics['longest_streak']:,}", border=True)
            st.metric("🔥 Current Streak (days)", f"{all_metrics['current_streak']:,}", border=True)
        with col2:
            st.metric(
                f"**🎤 {all_metrics['top_artist_streak']['artist']}** streak",
                f"{all_metrics['top_artist_streak']['days_count']:,} days",
                help=f"{all_metrics['top_artist_streak']['start_date']} → {all_metrics['top_artist_streak']['end_date']}",
                border=True
        )
            st.metric(
                "🎵 Longest Artist Play Streak",
                f"{all_metrics['streak_scrobbles']:,} scrobbles",
                help=f"Artist: {all_metrics['artist']}",
                border=True
        )

        with col3:
            st.metric("Peak Day", f"{all_metrics['peak_day']} ({all_metrics['peak_day_scrobblings']:,})", border=True,
                        help="The day with the highest number of scrobbles.")
            st.metric("First Scrobble", all_metrics['first_date'].strftime("%Y-%m-%d") if pd.notnull(all_metrics['first_date']) else "N/A", border=True)
    else:
        st.error("Metrics could not be loaded for the user.")

    # --- Statistics: Filtered Period ---
    st.markdown("---")
    st.markdown("### 📈 Statistics: Filtered Period")

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
            st.metric("Total Scrobblings", "0", border=True)
            st.metric("Unique Artists", "0", border=True)
            st.metric("Unique Albums", "0", border=True)
            st.metric("Unique Songs", "0", border=True)
        with col2:
            st.metric("Days with scrobbles", "0 (0.00%)", border=True)
            st.metric("Avg Scrobbles by total days", "0.0", border=True)
            st.metric("Avg Scrobbles by day", "0.0", border=True)
            st.metric("Peak Day", "N/A", border=True)
        return

    # Recalcular métricas sobre el subset
    filtered_metrics = calculate_all_metrics(df=filtered_df)
    if filtered_metrics is None:
        st.error("Error computing filtered metrics.")
        return

    # Mostrar métricas filtradas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Scrobblings", f"{filtered_metrics['total_scrobblings']:,}", border=True)
        st.metric("Unique Artists", f"{filtered_metrics['unique_artists']:,}", border=True)
        st.metric("Unique Albums", f"{filtered_metrics['unique_albums']:,}", border=True)
        st.metric("Unique Songs", f"{filtered_metrics['unique_tracks']:,}", border=True)
    with col2:
        st.metric("Days with scrobbles", f"{filtered_metrics['unique_days']:,} ({filtered_metrics['pct_days_with_scrobbles']:.1f}%)", border=True)
        st.metric("Avg Scrobbles by total days", f"{filtered_metrics['avg_scrobbles_per_day']:.1f}", border=True)
        st.metric("Avg Scrobbles by day", f"{filtered_metrics['avg_scrobbles_per_day_with']:.1f}", border=True)
        st.metric("Peak Day", f"{filtered_metrics['peak_day']} ({filtered_metrics['peak_day_scrobblings']:,})", border=True)

    st.markdown("---")


# ----------------------------------------
# 📊 Tab: Overview
# ----------------------------------------
def tab_overview(user, df_user, all_metrics):
    """
    Renders the overview tab showing all three metrics (Scrobblings, Artists, Albums)
    with selectable time period and optional artist filter.
    """
    st.markdown("### 📈 Overview")

    # 🎯 Selección de periodo y artistas
    col_time, col_artists = st.columns([1, 2])

    with col_time:
        time_period = st.radio(
            label="Select time period",
            options=["📅 Month", "📊 Quarter", "📈 Year"],
            horizontal=True,
            key="time_selector"
        )

    with col_artists:
        artist_options = sorted(df_user['artist'].unique())
        selected_artists = st.multiselect(
            label="Filter by artists",
            options=artist_options,
            default=[],
            key="artist_selector",
            help="You can select as many as you want"
        )

    # Filtrar por artistas si hay selección
    if selected_artists:
        df_user = df_user[df_user['artist'].isin(selected_artists)]

    # 📊 Recalcular métricas basadas en el dataframe filtrado
    total_scrobbles = len(df_user)
    avg_scrobbles_per_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M')).size().mean()
    peak_month_scrobbles = df_user.groupby(df_user['datetime_utc'].dt.to_period('M')).size().max()
    peak_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M')).size().idxmax().strftime('%Y-%m')

    unique_artists = df_user['artist'].nunique()
    avg_artist_per_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['artist'].nunique().mean()

    unique_albums = df_user['album'].nunique()
    avg_albums_per_month = df_user.groupby(df_user['datetime_utc'].dt.to_period('M'))['album'].nunique().mean()

    # 📊 Obtener métricas mensuales filtradas
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

    # 1️⃣ Scrobblings
    st.markdown("### 📊 Scrobblings Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Scrobblings", f"{total_scrobbles:,}", border=True)
    with col2: st.metric("Monthly Average", f"{avg_scrobbles_per_month:.1f}", border=True)
    with col3: st.metric(f"Peak Month ({peak_month_scrobbles:,} scrobbles)", peak_month, border=True)
    processed_data = process_data_by_period(scrobblings_by_month, time_period, "Scrobblings")
    fig = px.bar(processed_data, x="Year_Month", y="Scrobblings", title=f"Scrobblings by {time_period.split()[1]} - {user}", color_discrete_sequence=['#1f77b4'])
    fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # 2️⃣ Artists
    st.markdown("### 🎵 Artists Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Artists", f"{unique_artists:,}", border=True)
    with col2: st.metric("Monthly Average", f"{avg_artist_per_month:.0f}", border=True)
    with col3:
        if not artists_by_month.empty:
            max_month = artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month']
        else:
            max_month = "N/A"
        st.metric("Peak Month", max_month, border=True)
    processed_data = process_data_by_period(artists_by_month, time_period, "Artists")
    fig2 = px.bar(processed_data, x="Year_Month", y="Artists", title=f"Unique Artists by {time_period.split()[1]} - {user}", color_discrete_sequence=['#ff7f0e'])
    fig2.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    # 3️⃣ Albums
    st.markdown("### 💿 Albums Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Albums", f"{unique_albums:,}", border=True)
    with col2: st.metric("Monthly Average", f"{avg_albums_per_month:.0f}", border=True)
    with col3:
        if not albums_by_month.empty:
            max_month = albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month']
        else:
            max_month = "N/A"
        st.metric("Peak Month", max_month, border=True)
    processed_data = process_data_by_period(albums_by_month, time_period, "Albums")
    fig3 = px.bar(processed_data, x="Year_Month", y="Albums", title=f"Unique Albums by {time_period.split()[1]} - {user}", color_discrete_sequence=['#2ca02c'])
    fig3.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")


# ----------------------------------------
# 🎵 Tab: Top Artists
# ----------------------------------------
def tab_top_artists(user, df_user, all_metrics):
    """
    Renders the Top Artists tab with a bar chart and key metrics,
    plus a listening pattern chart (relative days or natural dates) for multiple artists.
    """

    st.markdown("### 🎵 Top Artists")
    
    # --- Pre-procesar Top 10 ---
    top_artists = df_user.groupby('artist').size().reset_index(name='Scrobblings')
    top_artists = top_artists.sort_values('Scrobblings', ascending=False).head(10)
    top_artists['Artist'] = top_artists['artist']
    
    # --- Métricas generales ---
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("Unique Artists", f"{all_metrics['unique_artists']:,}")
    with col2: 
        st.metric("Total Scrobblings", f"{len(df_user):,}")
    with col3: 
        if not top_artists.empty:
            st.metric("Top Artist", top_artists.iloc[0]['Artist'])
        else:
            st.metric("Top Artist", "N/A")
    
    # --- Gráfico Top 10 ---
    if not top_artists.empty:
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
    else:
        st.info("No data to show")
        return
        
    st.markdown("---")
    
    # --- Bloque patrón de escucha ---
    st.subheader("📈 Listening Pattern for Top Artists")

    # 🎯 Selector de patrón y artistas en la misma fila
    col1, col2 = st.columns([1, 2])
    with col1:
        pattern_type = st.selectbox(
            "Pattern Type", 
            options=["Relative Days", "Natural Dates"], 
            help="Relative: Number of days since first scrobble | Natural: Cumulative scrobbles since first day"
        )
    with col2:
        selected_artists = st.multiselect(
            "Select Top 10 Artists", 
            options=top_artists['Artist'].tolist(),
            default=top_artists['Artist'].head(3).tolist()
        )

    if not selected_artists:
        st.warning("Please select at least one artist.")
        st.stop()
    
    all_data = []
    if pattern_type == "Relative Days":
        for artist in selected_artists:
            artist_df = df_user[df_user['artist'] == artist].copy()
            artist_df = artist_df.sort_values("datetime_utc")
            first_date = artist_df['datetime_utc'].min().normalize()
            artist_df['Relative Day'] = (
                artist_df['datetime_utc'].dt.normalize() - first_date
            ).dt.days + 1
            artist_df['Cumulative Scrobbles'] = range(1, len(artist_df) + 1)
            artist_df['Artist'] = artist
            all_data.append(
                artist_df[['Relative Day', 'Cumulative Scrobbles', 'Artist']]
            )

        combined_df = pd.concat(all_data, ignore_index=True)

        fig_pattern = px.line(
            combined_df,
            x="Relative Day",
            y="Cumulative Scrobbles",
            color="Artist",
            title="Listening Pattern (Relative Days)"
        )
        fig_pattern.update_layout(
            xaxis_title="Days since first scrobble",
            yaxis_title="Cumulative Scrobbles"
        )

    else:  # Natural Dates
        for artist in selected_artists:
            artist_df = df_user[df_user['artist'] == artist].copy()
            artist_df['Date'] = artist_df['datetime_utc'].dt.date
            artist_df = artist_df.groupby('Date').size().reset_index(name='Daily Scrobbles')
            artist_df['Cumulative Scrobbles'] = artist_df['Daily Scrobbles'].cumsum()
            artist_df['Artist'] = artist
            all_data.append(artist_df)

        combined_df = pd.concat(all_data, ignore_index=True)

        fig_pattern = px.line(
            combined_df,
            x="Date",
            y="Cumulative Scrobbles",
            color="Artist",
            title="Listening Pattern (Natural Dates)"
        )
        fig_pattern.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Scrobbles"
        )

    st.plotly_chart(fig_pattern, use_container_width=True)


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