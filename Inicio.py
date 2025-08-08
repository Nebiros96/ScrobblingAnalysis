import streamlit as st
from core.data_loader import load_user_data, clear_cache, unique_metrics
import pandas as pd
import plotly.express as px
import time

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
</style>
""", unsafe_allow_html=True)

# --- Título---
st.title("🎵 Last.fm Scrobblings Dashboard")
st.markdown("#### Explore Your Last.fm Activity")

# --- 🧪 Formulario de búsqueda de usuario ---
with st.form("user_search_form"):
    input_user = st.text_input("Enter your Last.fm user:", placeholder="ej. Brenoritvrezork")
    submitted = st.form_submit_button("Load Lastfm data")

if submitted and input_user:
    st.session_state.clear()
    clear_cache(input_user)
    st.session_state["current_user"] = input_user

    with st.status(f"📊 Loading data for user **{input_user}**...", expanded=True) as status_container:
        progress_bar = st.progress(0)  # ✅ Se crea una sola barra
        progress_text = st.empty()     # ✅ Un solo texto dinámico

        def progress_callback(page, total_pages, total_tracks):
            progress_percent = page / total_pages if total_pages > 0 else 0
            progress_bar.progress(progress_percent)
            progress_text.markdown(
                f"📊 Page {page}/{total_pages} ({progress_percent:.2%}) - {total_tracks:,} scrobbles."
            )

        df = load_user_data(input_user, progress_callback)

        if df is not None and not df.empty:
            st.session_state["df_user"] = df
            st.session_state["data_loaded_successfully"] = True
            status_container.update(label="Data extracted successfully!", state="complete", expanded=False)
        else:
            st.session_state["data_loaded_successfully"] = False
            status_container.update(label="❌ Data loading failed", state="error", expanded=True)
            st.error("❌ Data could not be loaded. Please check the username or try again.")


# --- Lógica de renderizado de las pestañas ---
if "current_user" in st.session_state and st.session_state.get("data_loaded_successfully"):
    st.success(f"Data extracted successfully! **{len(st.session_state['df_user']):,}** scrobbings were found for the user **{st.session_state['current_user']}**")

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistics", "📊 Overview", "🎵 Top Artists", "ℹ️ Info"])

    # ----------------------------------------
    # 📈 Tab: Statistics
    # ----------------------------------------
    with tab1:
        st.markdown("## 📈 Statistics")
        user = st.session_state["current_user"]
        cached_data = st.session_state["df_user"]
        metrics = unique_metrics(user=user, df=cached_data)

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
            st.markdown("---")

    # ----------------------------------------
    # 📊 Tab: Overview
    # ----------------------------------------
    with tab2:
        st.markdown("## 📈 Overview")
        user = st.session_state["current_user"]
        df_user = st.session_state["df_user"]

        with st.spinner(f"Loading metrics for {user}..."):
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

        metrics = unique_metrics(user=user, df=df_user)

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

        def process_data_by_period(df, period_type, data_type):
            if period_type == "📅 Month":
                return df
            elif period_type == "📊 Quarter":
                df['Year_Quarter'] = df['Year_Month'].str[:4] + '-Q' + df['Year_Month'].str[5:7].astype(int).apply(lambda x: str((x-1)//3 + 1))
                return df.groupby('Year_Quarter')[data_type].sum().reset_index().rename(columns={'Year_Quarter': 'Year_Month'})
            elif period_type == "📈 Year":
                df['Year'] = df['Year_Month'].str[:4]
                return df.groupby('Year')[data_type].sum().reset_index().rename(columns={'Year': 'Year_Month'})

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
            with col1: st.metric("Unique Artists",  f"{metrics['unique_artists']:,}")
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
            with col1: st.metric("Unique Albums", metrics["unique_albums"] if metrics else "N/A")
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
    with tab3:
        st.markdown("## 🎵 Top Artists")
        user = st.session_state["current_user"]
        df_user = st.session_state["df_user"]
        
        top_artists = df_user.groupby('artist').size().reset_index(name='Scrobblings')
        top_artists = top_artists.sort_values('Scrobblings', ascending=False).head(10)
        top_artists['Artist'] = top_artists['artist']
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Unique Artists",  f"{metrics['unique_artists']:,}")
        with col2: st.metric("Total Scrobblings", f"{len(df_user):,}")
        with col3: st.metric("Top Artist", top_artists.iloc[0]['Artist'])
        
        fig = px.bar(top_artists, x="Artist", y="Scrobblings", title=f"Top 10 Artists - {user}", color_discrete_sequence=['#ff7f0e'])
        fig.update_layout(xaxis_title="Artist", yaxis_title="Number of Scrobblings", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

    # ----------------------------------------
    # ℹ️ Tab: Info
    # ----------------------------------------
@st.cache_data
def load_help_md():
    try:
        with open("help.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

with tab4:
    st.markdown("#### ℹ️ Info")

    help_content = load_help_md()
    if help_content:
        st.markdown(help_content, unsafe_allow_html=False)
    else:
        st.error("⚠️ help.md file not found.")

