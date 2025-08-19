# core/ui_tabs.py
import streamlit as st
import plotly.express as px
import pandas as pd
from core.data_loader import (
    get_df_hash, get_top_artists, get_detailed_streaks, 
    process_data_by_period_cached, get_cached_data
)


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
        all_metrics (dict): A dictionary containing the pre-calculated metrics.
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
            st.metric("Streak days", f"{all_metrics['longest_streak']:,}", border=True)
    else:
        st.error("Metrics could not be loaded for the user.")

    st.markdown("---")
    st.markdown("### 🔥 Streak Statistics")

    # --- 📈 Detailed Statistics (usando caché optimizado) ---
    df_hash = get_df_hash(user)
    streaks_df, artist_streak_days, artist_streak_scrobbles = get_detailed_streaks(df_hash, user)

    if streaks_df is not None and not streaks_df.empty:
        # === Visualización ===
        col1, col2, col3 = st.columns(3)

        with col1:
            fig1 = px.bar(
                streaks_df,
                x="streak_days",
                y="streak_label",
                orientation="h",
                title="Top Listening Streaks by Date Range",
                labels={"streak_days": "Days", "streak_label": "Date Range"},
                text="streak_days",
                color_discrete_sequence=["#d51007"]
            )
            fig1.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            if not artist_streak_days.empty:
                fig2 = px.bar(
                    artist_streak_days.sort_values("streak_days", ascending=True),
                    x="streak_days",
                    y="artist",
                    orientation="h",
                    title="Longest Streak (Days) by Artist",
                    labels={
                        "streak_days": "Days",
                        "artist": "Artist"
                    },
                    text="streak_days",
                    color_discrete_sequence=["#d51007"]
                )
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)

        with col3:
            if not artist_streak_scrobbles.empty:
                fig3 = px.bar(
                    artist_streak_scrobbles, 
                    x="streak_scrobbles", 
                    y="artist", 
                    orientation="h",
                    title="Longest Streak Scrobbles by Artist",
                    labels={"streak_scrobbles": "Scrobbles", "artist": "Artist"},
                    text="streak_scrobbles",
                    color_discrete_sequence=["#d51007"]
                )
                fig3.update_yaxes(categoryorder="total ascending")
                st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No streak data available.")

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
        # Usar caché para obtener lista de artistas
        df_hash = get_df_hash(user)
        top_artists_df = get_top_artists(df_hash, user, limit=100)  # Top 100 para el filtro
        
        if not top_artists_df.empty:
            artist_options = sorted(top_artists_df['artist'].tolist())
        else:
            artist_options = []
            
        selected_artists = st.multiselect(
            label="Filter by artists",
            options=artist_options,
            default=[],
            key="artist_selector",
            help="You can select as many as you want"
        )

    # Generar hash para el caché considerando los filtros
    filter_hash = f"{df_hash}_{str(sorted(selected_artists))}"

    # 📊 Calcular métricas filtradas usando caché
    @st.cache_data
    def get_filtered_metrics(filter_hash: str, user: str, selected_artists: list):
        df = get_cached_data(user)
        if df is None or df.empty:
            return None
            
        # Aplicar filtro de artistas si hay selección
        if selected_artists:
            df_filtered = df[df['artist'].isin(selected_artists)]
        else:
            df_filtered = df
            
        if df_filtered.empty:
            return None
            
        total_scrobbles = len(df_filtered)
        avg_scrobbles_per_month = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M')).size().mean()
        
        monthly_scrobbles = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M')).size()
        if not monthly_scrobbles.empty:
            peak_month_scrobbles = monthly_scrobbles.max()
            peak_month = monthly_scrobbles.idxmax().strftime('%Y-%m')
        else:
            peak_month_scrobbles = 0
            peak_month = "N/A"

        unique_artists = df_filtered['artist'].nunique()
        avg_artist_per_month = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M'))['artist'].nunique().mean()
        
        monthly_artists = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M'))['artist'].nunique()
        if not monthly_artists.empty:
            max_artist_month = monthly_artists.idxmax().strftime('%Y-%m')
        else:
            max_artist_month = "N/A"

        unique_albums = df_filtered['album'].nunique()
        avg_albums_per_month = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M'))['album'].nunique().mean()
        
        monthly_albums = df_filtered.groupby(df_filtered['datetime_utc'].dt.to_period('M'))['album'].nunique()
        if not monthly_albums.empty:
            max_album_month = monthly_albums.idxmax().strftime('%Y-%m')
        else:
            max_album_month = "N/A"

        return {
            "total_scrobbles": total_scrobbles,
            "avg_scrobbles_per_month": avg_scrobbles_per_month,
            "peak_month_scrobbles": peak_month_scrobbles,
            "peak_month": peak_month,
            "unique_artists": unique_artists,
            "avg_artist_per_month": avg_artist_per_month,
            "max_artist_month": max_artist_month,
            "unique_albums": unique_albums,
            "avg_albums_per_month": avg_albums_per_month,
            "max_album_month": max_album_month
        }

    metrics = get_filtered_metrics(filter_hash, user, selected_artists)
    
    if metrics is None:
        st.warning("No data available for the selected filters.")
        return

    # 1️⃣ Scrobblings
    st.markdown("### 📊 Scrobblings Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Scrobbles", f"{metrics['total_scrobbles']:,}", border=True)
    with col2: st.metric("Monthly Average", f"{metrics['avg_scrobbles_per_month']:,.0f}", border=True)
    with col3: st.metric(f"Peak Month ({metrics['peak_month_scrobbles']:,} scrobbles)", metrics['peak_month'], border=True)

    processed_data = process_data_by_period_cached(df_hash, user, time_period, "Scrobblings", selected_artists)
    if not processed_data.empty:
        fig = px.bar(processed_data, x="Year_Month", y="Scrobblings", 
                     title=f"Scrobbles by {time_period.split()[1]}", 
                     color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # 2️⃣ Artists
    st.markdown("### 🎵 Artists Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Artists", f"{metrics['unique_artists']:,}", border=True)
    with col2: st.metric("Monthly Average", f"{metrics['avg_artist_per_month']:.0f}", border=True)
    with col3: st.metric("Peak Month", metrics['max_artist_month'], border=True)

    processed_data = process_data_by_period_cached(df_hash, user, time_period, "Artists", selected_artists)
    if not processed_data.empty:
        fig2 = px.bar(processed_data, x="Year_Month", y="Artists", 
                      title=f"Unique Artists by {time_period.split()[1]}", 
                      color_discrete_sequence=['#ff7f0e'])
        fig2.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # 3️⃣ Albums
    st.markdown("### 💿 Albums Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Unique Albums", f"{metrics['unique_albums']:,}", border=True)
    with col2: st.metric("Monthly Average", f"{metrics['avg_albums_per_month']:.0f}", border=True)
    with col3: st.metric("Peak Month", metrics['max_album_month'], border=True)

    processed_data = process_data_by_period_cached(df_hash, user, time_period, "Albums", selected_artists)
    if not processed_data.empty:
        fig3 = px.bar(processed_data, x="Year_Month", y="Albums", 
                      title=f"Unique Albums by {time_period.split()[1]}", 
                      color_discrete_sequence=['#2ca02c'])
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
    
    # --- Usar caché para Top 10 ---
    df_hash = get_df_hash(user)
    top_artists = get_top_artists(df_hash, user, limit=10)
    
    if top_artists.empty:
        st.info("No data to show")
        return
    
    # --- Métricas generales ---
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.metric("Unique Artists", f"{all_metrics['unique_artists']:,}")
    with col2: 
        st.metric("Total Scrobblings", f"{len(df_user):,}")
    with col3: 
        st.metric("Top Artist", top_artists.iloc[0]['Artist'])
    
    # --- Gráfico Top 10 ---
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
        return

    # Función con caché para generar datos del patrón
    @st.cache_data
    def get_listening_pattern_data(df_hash: str, user: str, selected_artists: list, pattern_type: str):
        df = get_cached_data(user)
        if df is None or df.empty:
            return pd.DataFrame()
            
        all_data = []
        if pattern_type == "Relative Days":
            for artist in selected_artists:
                artist_df = df[df['artist'] == artist].copy()
                if artist_df.empty:
                    continue
                    
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
        else:  # Natural Dates
            for artist in selected_artists:
                artist_df = df[df['artist'] == artist].copy()
                if artist_df.empty:
                    continue
                    
                artist_df['Date'] = artist_df['datetime_utc'].dt.date
                artist_df = artist_df.groupby('Date').size().reset_index(name='Daily Scrobbles')
                artist_df['Cumulative Scrobbles'] = artist_df['Daily Scrobbles'].cumsum()
                artist_df['Artist'] = artist
                all_data.append(artist_df)

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()

    # Generar hash incluyendo artistas seleccionados
    pattern_hash = f"{df_hash}_{pattern_type}_{str(sorted(selected_artists))}"
    combined_df = get_listening_pattern_data(pattern_hash, user, selected_artists, pattern_type)

    if combined_df.empty:
        st.warning("No data available for selected artists.")
        return

    # Crear gráfico según el tipo de patrón
    if pattern_type == "Relative Days":
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
        st.markdown(help_content, unsafe_allow_html=True)
    else:
        st.error("⚠️ help.md file not found.")