import pandas as pd
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import toml
import streamlit as st
import time
import json


# 🔐 Leer API key desde secrets.toml
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")

def get_api_key():
    """Obtiene la API key desde secrets.toml"""
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        return secrets["lastfmAPI"]["api_key"]
    else:
        raise FileNotFoundError(".toml file not found")


def fetch_user_data_from_api(user: str, progress_callback=None, resume=True) -> pd.DataFrame:
    api_key = get_api_key()
    temp_dir = "temp_checkpoints"
    os.makedirs(temp_dir, exist_ok=True)
    checkpoint_file = os.path.join(temp_dir, f"{user}_checkpoint.parquet")

    all_rows = []
    start_page = 1

    # Reanudar si hay checkpoint
    if resume and os.path.exists(checkpoint_file):
        df_checkpoint = pd.read_parquet(checkpoint_file)
        all_rows = df_checkpoint.to_dict("records")
        start_page = (len(all_rows) // 200) + 1
        print(f"♻️ Resuming from page {start_page} ({len(all_rows):,} scrobbles loaded)")

    page = start_page
    total_pages = 1
    max_retries = 3
    retry_delay = 5  # segundos

    while True:
        url = (
            f"http://ws.audioscrobbler.com/2.0/"
            f"?method=user.getrecenttracks&user={user}&api_key={api_key}&limit=200&page={page}&format=json"
        )

        attempt = 1
        while attempt <= max_retries:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                break  # éxito, salimos del retry loop
            except (requests.RequestException, ValueError) as e:
                print(f"⚠️ Error en página {page}, intento {attempt}/{max_retries}: {e}")
                if attempt == max_retries:
                    pd.DataFrame(all_rows).to_parquet(checkpoint_file, index=False)
                    return {"incomplete": True}
                time.sleep(retry_delay)
                attempt += 1

        # Verificar si la API devolvió un error
        if isinstance(data, dict) and data.get("error"):
            raise ValueError(f"API Error: {data.get('error')} - {data.get('message')}")

        recenttracks = data.get("recenttracks", {})
        if page == start_page:
            total_pages = int(recenttracks.get("@attr", {}).get("totalPages", "1"))
            print(f"📊 Total pages: {total_pages}")

        tracks = recenttracks.get("track", [])
        if isinstance(tracks, dict):  # cuando es un solo track
            tracks = [tracks]

        for t in tracks:
            uts = (t.get("date") or {}).get("uts")
            if not uts:
                continue
            fecha_dt = datetime.fromtimestamp(int(uts), tz=timezone.utc)
            all_rows.append({
                "user": user,
                "datetime_utc": fecha_dt,
                "artist": (t.get("artist") or {}).get("#text", ""),
                "album": (t.get("album") or {}).get("#text", ""),
                "track": t.get("name", ""),
                "url": t.get("url", "")
            })

        if page % 50 == 0:
            pd.DataFrame(all_rows).to_parquet(checkpoint_file, index=False)
            print(f"💾 Checkpoint saved at page {page}")

        if progress_callback:
            progress_callback(page, total_pages, len(all_rows))

        page += 1
        if page > total_pages:
            break

    df = pd.DataFrame(all_rows)

    if not df.empty:
        df["year"] = df["datetime_utc"].dt.year
        df["quarter"] = (df["datetime_utc"].dt.month - 1) // 3 + 1
        df["month"] = df["datetime_utc"].dt.month
        df["day"] = df["datetime_utc"].dt.day
        df["hour"] = df["datetime_utc"].dt.hour
        df["year_month"] = df["datetime_utc"].dt.strftime("%Y-%m")
        df["year_month_day"] = df["datetime_utc"].dt.strftime("%Y-%m-%d")
        df["weekday"] = df["datetime_utc"].dt.strftime("%A")

    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    return df


def get_cached_data(user: str) -> pd.DataFrame:
    """Obtiene datos del caché de la sesión"""
    cache_key = f"user_data_{user}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    return None

def set_cached_data(user: str, data: pd.DataFrame):
    """Guarda datos en el caché de la sesión"""
    cache_key = f"user_data_{user}"
    st.session_state[cache_key] = data

def load_user_data(user, progress_callback=None, resume=False):
    """Carga datos del usuario desde la API o caché
    
    Args:
        user: Nombre de usuario de Last.fm
        progress_callback: Función para mostrar progreso (opcional)
    """
    # Verificar si los datos están en caché
    cached_data = get_cached_data(user)
    if cached_data is not None:
        print(f"🔋 Using cached data for {user} ({len(cached_data):,} scrobbles.)")
        return cached_data
    
    try:
        print(f"🔄 Retrieving Last.fm data from the API for {user}...")
        df = fetch_user_data_from_api(user, progress_callback)
        if not df.empty:
            # Convertir datetime_utc a datetime
            df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
            # Guardar en caché
            set_cached_data(user, df)
            print(f"✅ Saved data in cache for {user}")
        return df
    except ValueError as e:
        print(f"User validation error: {user}: {e}")
        return None
    except ConnectionError as e:
        print(f"User connection error: {user}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading data for {user}: {e}")
        return None


# ========================
# FUNCIONES DE CACHÉ OPTIMIZADAS
# ========================

@st.cache_data
def get_basic_metrics(df_hash: str, user: str):
    """Calcula métricas básicas con caché basado en hash del dataframe"""
    # Recuperar el dataframe desde session_state usando el user
    df = get_cached_data(user)
    if df is None or df.empty:
        return None
    
    unique_artists = df['artist'].nunique()
    unique_albums = df['album'].nunique()
    unique_tracks = df['track'].nunique()
    total_scrobblings = len(df)

    first_date = pd.to_datetime(df['datetime_utc']).min()
    last_date = pd.to_datetime(df['datetime_utc']).max()
    unique_days = df["year_month_day"].nunique()

    # Averages    
    avg_scrobbles_per_day_with = df["datetime_utc"].count()/df["year_month_day"].nunique()
    avg_scrobbles_per_month = df.groupby("year_month").size().mean()
    avg_artist_per_month = df.groupby("year_month")["artist"].nunique().mean()
    avg_albums_per_month = df.groupby("year_month")["album"].nunique().mean()

    # Cálculo del mes con más scrobbles 
    if 'year_month' in df:
        peak_month = df['year_month'].value_counts().idxmax()
        peak_month_scrobblings = df['year_month'].value_counts().max()
    else:
        peak_month = None
        peak_month_scrobblings = 0

    # Días naturales y promedio
    if pd.notnull(first_date):
        days_natural = (last_date - first_date).days + 1
        avg_scrobbles_per_day = total_scrobblings / days_natural
        pct_days_with_scrobbles = (unique_days / days_natural) * 100
    else:
        days_natural = 0
        avg_scrobbles_per_day = 0
        pct_days_with_scrobbles = 0

    # Día con más scrobbles
    if 'year_month_day' in df:
        peak_day = df['year_month_day'].value_counts().idxmax()
        peak_day_scrobblings = df['year_month_day'].value_counts().max()
    else:
        peak_day = None
        peak_day_scrobblings = 0

    return {
        "unique_artists": unique_artists,
        "unique_albums": unique_albums,
        "unique_tracks": unique_tracks,
        "total_scrobblings": total_scrobblings,
        "first_date": first_date,
        "last_date": last_date,
        "unique_days": unique_days,
        "avg_scrobbles_per_day_with": avg_scrobbles_per_day_with,
        "avg_scrobbles_per_month": avg_scrobbles_per_month,
        "avg_artist_per_month": avg_artist_per_month,
        "avg_albums_per_month": avg_albums_per_month,
        "peak_month": peak_month,
        "peak_month_scrobblings": peak_month_scrobblings,
        "days_natural": days_natural,
        "avg_scrobbles_per_day": avg_scrobbles_per_day,
        "pct_days_with_scrobbles": pct_days_with_scrobbles,
        "peak_day": peak_day,
        "peak_day_scrobblings": peak_day_scrobblings,
    }


@st.cache_data
def get_streak_metrics(df_hash: str, user: str):
    """Calcula métricas de rachas con caché"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return None
    
    # Asegurar formato de fecha
    df['date'] = pd.to_datetime(df['datetime_utc']).dt.date
    
    # --- Racha global ---
    unique_dates = pd.to_datetime(sorted(df['date'].unique()))
    if len(unique_dates) == 1:
        longest_streak = 1
        current_streak_days = 1
    else:
        diffs = (unique_dates[1:] - unique_dates[:-1]).days
        streaks = []
        current_streak = 1
        for d in diffs:
            if d == 1:
                current_streak += 1
            else:
                streaks.append(current_streak)
                current_streak = 1
        streaks.append(current_streak)
        longest_streak = max(streaks)
        current_streak_days = streaks[-1]
    
    # --- Racha por artista (Top 1) ---
    df_artist = (
        df.groupby(['artist', 'date'])
        .size()
        .reset_index(name='scrobbles')
    )
    df_artist = df_artist.sort_values(['artist', 'date'])
    
    df_artist['last_date'] = df_artist.groupby('artist')['date'].shift(1)
    df_artist['days_diff'] = (pd.to_datetime(df_artist['date']) - pd.to_datetime(df_artist['last_date'])).dt.days
    
    df_artist['streak_group'] = (
        df_artist['days_diff'].gt(1)
        .groupby(df_artist['artist'])
        .cumsum()
    )
    
    rachas = (
        df_artist.groupby(['artist', 'streak_group'])
        .agg(
            start_date=('date', 'min'),
            end_date=('date', 'max'),
            days_count=('date', 'count'),
            total_scrobbles=('scrobbles', 'sum')
        )
        .reset_index()
    )
    
    top_artist_streak = (
        rachas.sort_values(['days_count', 'total_scrobbles'], ascending=False)
        .iloc[0]
    )
    
    return {
        "longest_streak": int(longest_streak),
        "current_streak": int(current_streak_days),
        "top_artist_streak": {
            "artist": top_artist_streak['artist'],
            "start_date": top_artist_streak['start_date'],
            "end_date": top_artist_streak['end_date'],
            "days_count": int(top_artist_streak['days_count']),
            "total_scrobbles": int(top_artist_streak['total_scrobbles'])
        }
    }


@st.cache_data
def get_artist_play_streak(df_hash: str, user: str):
    """Calcula la racha más larga de reproducciones consecutivas por artista"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return None

    # Ordenar por tiempo
    df = df.sort_values("datetime_utc").reset_index(drop=True)

    # Crear columna de cambio de artista
    df["prev_artist"] = df["artist"].shift(1)
    df["artist_change"] = (df["artist"] != df["prev_artist"]).astype(int)

    # Asignar un ID de grupo para cada bloque consecutivo
    df["group_id"] = df["artist_change"].cumsum()

    # Contar tamaño de cada grupo
    streaks = (
        df.groupby(["artist", "group_id"])
        .agg(
            streak_len=("artist", "size"),
            start_time=("datetime_utc", "min"),
            end_time=("datetime_utc", "max")
        )
        .reset_index()
    )

    # Tomar la racha más larga
    top_streak = streaks.sort_values("streak_len", ascending=False).iloc[0]

    return {
        "artist": top_streak["artist"],
        "streak_scrobbles": top_streak["streak_len"],
        "start_time": top_streak["start_time"],
        "end_time": top_streak["end_time"]
    }


@st.cache_data
def get_top_artists(df_hash: str, user: str, limit: int = 10):
    """Obtiene los top artistas con caché"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return pd.DataFrame()
    
    top_artists = df.groupby('artist').size().reset_index(name='Scrobblings')
    top_artists = top_artists.sort_values('Scrobblings', ascending=False).head(limit)
    top_artists['Artist'] = top_artists['artist']
    
    return top_artists


@st.cache_data  
def get_detailed_streaks(df_hash: str, user: str):
    """Calcula streaks detallados para la tab de estadísticas"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return None, None, None
    
    # 1. Top streaks por rango de fechas
    df_days = df.copy()
    df_days["date"] = pd.to_datetime(df_days["datetime_utc"]).dt.date

    df_unique_days = (
        df_days.groupby("date")
        .size()
        .reset_index(name="scrobbles")
        .sort_values("date")
    )

    df_unique_days["prev_date"] = df_unique_days["date"].shift(1)
    df_unique_days["days_diff"] = (pd.to_datetime(df_unique_days["date"]) - pd.to_datetime(df_unique_days["prev_date"])).dt.days
    df_unique_days["streak_group"] = (df_unique_days["days_diff"] != 1).cumsum()

    streaks_df = (
        df_unique_days.groupby("streak_group")
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            streak_days=("date", "count"),
            total_scrobbles=("scrobbles", "sum")
        )
        .reset_index(drop=True)
    )

    streaks_df["listens_per_day"] = streaks_df["total_scrobbles"] / streaks_df["streak_days"]
    streaks_df = streaks_df[streaks_df["streak_days"] > 6]
    streaks_df["streak_label"] = streaks_df["start_date"].astype(str) + " → " + streaks_df["end_date"].astype(str)
    streaks_df = streaks_df.sort_values(["streak_days", "total_scrobbles", "start_date"], ascending=[False, False, True]).head(10)
    
    # 2. Longest streak days por artista
    df_artist_days = df.copy()
    df_artist_days["date"] = pd.to_datetime(df_artist_days["datetime_utc"]).dt.date

    df_artist_days = (
        df_artist_days.groupby(["artist", "date"])
        .size()
        .reset_index(name="scrobbles")
    )

    df_artist_days = df_artist_days.sort_values(["artist", "date"])
    df_artist_days["last_date"] = df_artist_days.groupby("artist")["date"].shift(1)
    df_artist_days["days_diff"] = (
        pd.to_datetime(df_artist_days["date"]) - pd.to_datetime(df_artist_days["last_date"])
    ).dt.days

    df_artist_days["streak_group"] = (
        df_artist_days["days_diff"].gt(1).fillna(True)
        .groupby(df_artist_days["artist"])
        .cumsum()
    )

    rachas = (
        df_artist_days.groupby(["artist", "streak_group"])
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            streak_days=("date", "count"),
            total_scrobbles=("scrobbles", "sum")
        )
        .reset_index()
    )

    artist_streak_days = (
        rachas.sort_values(["streak_days", "start_date", "total_scrobbles"], ascending=False)
        .groupby("artist")
        .head(1)
        .sort_values(["streak_days", "total_scrobbles", "start_date"], ascending=False)
        .head(10)
    )

    # 3. Longest streak scrobbles por artista
    df_artist_scrobbles = df.copy()
    df_artist_scrobbles["prev_artist"] = df_artist_scrobbles["artist"].shift(1)
    df_artist_scrobbles["artist_change"] = (df_artist_scrobbles["artist"] != df_artist_scrobbles["prev_artist"]).astype(int)
    df_artist_scrobbles["group_id"] = df_artist_scrobbles["artist_change"].cumsum()
    artist_streak_scrobbles = (
        df_artist_scrobbles.groupby(["artist", "group_id"])
        .agg(streak_scrobbles=("artist", "size"))
        .reset_index()
        .groupby("artist")["streak_scrobbles"].max()
        .reset_index()
        .sort_values("streak_scrobbles", ascending=False)
        .head(10)
    )
    
    return streaks_df, artist_streak_days, artist_streak_scrobbles


@st.cache_data
def process_data_by_period_cached(df_hash: str, user: str, period_type: str, data_type: str, selected_artists: list = None):
    """Procesa datos por periodo con caché optimizado"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Aplicar filtro de artistas si se especifica
    if selected_artists:
        df = df[df['artist'].isin(selected_artists)]
    
    d = df.copy()
    d["Year"] = d["datetime_utc"].dt.year.astype(str)
    d["Quarter"] = d["datetime_utc"].dt.to_period("Q").astype(str)
    d["Year_Month"] = d["datetime_utc"].dt.strftime("%Y-%m")

    if data_type == "Scrobblings":
        if period_type == "📅 Month":
            return d.groupby("Year_Month").size().reset_index(name="Scrobblings")
        elif period_type == "📊 Quarter":
            return d.groupby("Quarter").size().reset_index(name="Scrobblings").rename(columns={"Quarter": "Year_Month"})
        elif period_type == "📈 Year":
            return d.groupby("Year").size().reset_index(name="Scrobblings").rename(columns={"Year": "Year_Month"})

    elif data_type == "Artists":
        if period_type == "📅 Month":
            return d.groupby("Year_Month")["artist"].nunique().reset_index(name="Artists")
        elif period_type == "📊 Quarter":
            return d.groupby("Quarter")["artist"].nunique().reset_index(name="Artists").rename(columns={"Quarter": "Year_Month"})
        elif period_type == "📈 Year":
            return d.groupby("Year")["artist"].nunique().reset_index(name="Artists").rename(columns={"Year": "Year_Month"})

    elif data_type == "Albums":
        if period_type == "📅 Month":
            return d.groupby("Year_Month")["album"].nunique().reset_index(name="Albums")
        elif period_type == "📊 Quarter":
            return d.groupby("Quarter")["album"].nunique().reset_index(name="Albums").rename(columns={"Quarter": "Year_Month"})
        elif period_type == "📈 Year":
            return d.groupby("Year")["album"].nunique().reset_index(name="Albums").rename(columns={"Year": "Year_Month"})


# Función helper para generar hash del dataframe
def get_df_hash(user: str) -> str:
    """Genera un hash único basado en el dataframe del usuario"""
    df = get_cached_data(user)
    if df is None or df.empty:
        return ""
    
    # Usamos el tamaño del dataframe y las fechas como hash simple
    return f"{user}_{len(df)}_{df['datetime_utc'].min()}_{df['datetime_utc'].max()}"


# Funciones principales optimizadas
def calculate_all_metrics(user=None, df=None, progress_callback=None):
    """
    Calcula todas las métricas principales del usuario usando caché optimizado.
    """
    if df is None:
        df = load_user_data(user, progress_callback)

    if df is None or df.empty:
        return None

    # Generar hash para el caché
    df_hash = get_df_hash(user)
    
    all_metrics = {}

    # Usar las funciones con caché
    basic_metrics = get_basic_metrics(df_hash, user)
    if basic_metrics:
        all_metrics.update(basic_metrics)

    streak_metrics = get_streak_metrics(df_hash, user)
    if streak_metrics:
        all_metrics.update(streak_metrics)

    artist_streak = get_artist_play_streak(df_hash, user)
    if artist_streak:
        all_metrics.update(artist_streak)

    return all_metrics


# Mantener funciones legacy para compatibilidad
def unique_metrics(user=None, df=None, progress_callback=None):
    """Wrapper para mantener compatibilidad con código existente"""
    df_hash = get_df_hash(user)
    return get_basic_metrics(df_hash, user)


def calculate_streak_metrics(user=None, df=None, progress_callback=None):
    """Wrapper para mantener compatibilidad con código existente"""
    df_hash = get_df_hash(user)
    return get_streak_metrics(df_hash, user)


def calculate_artist_play_streak(user=None, df=None, progress_callback=None):
    """Wrapper para mantener compatibilidad con código existente"""
    df_hash = get_df_hash(user)
    return get_artist_play_streak(df_hash, user)


def load_monthly_metrics(user=None, df=None, progress_callback=None):
    """
    Carga métricas mensuales de scrobblings, artistas y álbumes.
    """
    if df is None:
        df = load_user_data(user, progress_callback)

    if df is None or df.empty:
        return None, None, None

    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
    df["Year_Month"] = df["datetime_utc"].dt.strftime("%Y-%m")

    scrobblings_by_month = (
        df.groupby("Year_Month").size().reset_index(name="Scrobblings")
    )
    artists_by_month = (
        df.groupby("Year_Month")["artist"].nunique().reset_index(name="Artists")
    )
    albums_by_month = (
        df.groupby("Year_Month")["album"].nunique().reset_index(name="Albums")
    )

    return scrobblings_by_month, artists_by_month, albums_by_month


# Caché
def clear_cache(user: str = None):
    """Limpia el caché de datos
    
    Args:
        user: Usuario específico a limpiar. Si es None, limpia todo el caché
    """
    if user:
        cache_key = f"user_data_{user}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
            print(f"🗑️ Caché limpiado para {user}")
    else:
        # Limpiar todo el caché
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("user_data_")]
        for key in keys_to_remove:
            del st.session_state[key]
        print(f"🗑️ Cache is cleaned!")
    
    # Limpiar también el caché de Streamlit
    st.cache_data.clear()