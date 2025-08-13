import pandas as pd
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import toml
import streamlit as st

# 📁 Leer API key desde secrets.toml
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
    """Obtiene TODOS los datos del usuario desde la API de Last.fm con soporte de reanudación."""
    api_key = get_api_key()
    temp_dir = "temp_checkpoints"
    os.makedirs(temp_dir, exist_ok=True)
    checkpoint_file = os.path.join(temp_dir, f"{user}_checkpoint.parquet")

    # Si existe checkpoint y resume=True
    all_rows = []
    start_page = 1
    if resume and os.path.exists(checkpoint_file):
        df_checkpoint = pd.read_parquet(checkpoint_file)
        all_rows = df_checkpoint.to_dict("records")
        start_page = (len(all_rows) // 200) + 1
        print(f"♻️ Resuming from page {start_page} ({len(all_rows):,} scrobbles already loaded)")

    page = start_page
    total_pages = 1

    while True:
        url = (
            f"http://ws.audioscrobbler.com/2.0/"
            f"?method=user.getrecenttracks&user={user}&api_key={api_key}&limit=200&page={page}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            error = root.find(".//error")
            if error is not None:
                raise ValueError(f"API Error: {error.text}")

            recenttracks = root.find(".//recenttracks")
            if recenttracks is None:
                break

            if page == start_page:
                total_pages = int(recenttracks.attrib.get("totalPages", "1"))
                print(f"📊 Total pages: {total_pages}")

            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None or date_elem.get("uts") is None:
                    continue
                uts_timestamp = int(date_elem.get("uts"))
                fecha_dt = datetime.fromtimestamp(uts_timestamp, tz=timezone.utc)
                all_rows.append({
                    "user": user,
                    "datetime_utc": fecha_dt,
                    "artist": track.findtext("artist", default=""),
                    "album": track.findtext("album", default=""),
                    "track": track.findtext("name", default=""),
                    "url": track.findtext("url", default="")
                })

            # Guardar checkpoint cada 50 páginas
            if page % 50 == 0:
                pd.DataFrame(all_rows).to_parquet(checkpoint_file, index=False)
                print(f"💾 Checkpoint saved at page {page}")

            if progress_callback:
                progress_callback(page, total_pages, len(all_rows))

            page += 1
            if page > total_pages:
                break

        except requests.RequestException as e:
            # Guardar al fallar para reanudar luego
            pd.DataFrame(all_rows).to_parquet(checkpoint_file, index=False)
            raise ConnectionError(f"Connection lost at page {page}. Progress saved to resume later.")

    # Guardar datos completos y eliminar checkpoint
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
        print(f"📋 Using cached data for {user} ({len(cached_data):,} scrobbles.)")
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


def load_monthly_metrics(user=None, df=None, progress_callback=None):
    """
    Carga métricas mensuales de scrobblings, artistas y álbumes.
    Si se proporciona df, se usa directamente en lugar de llamar a la API.

    Args:
        user (str): Nombre de usuario de Last.fm (opcional si se pasa df).
        df (pd.DataFrame): DataFrame ya cargado con scrobbles del usuario.
        progress_callback (function, optional): Callback de progreso.

    Returns:
        tuple: (scrobblings_by_month, artists_by_month, albums_by_month)
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


# Funciones para definir medidas de agrupación
def unique_metrics(user=None, df=None, progress_callback=None):
    """Métricas únicas (conteos únicos y periodos)

    Args:
        user: Nombre de usuario de Last.fm (opcional si se pasa df)
        df: DataFrame de scrobbles (opcional si se pasa user)
        progress_callback: Función para mostrar progreso (opcional)
    """
    if df is None:
        from core.data_loader import load_user_data
        df = load_user_data(user, progress_callback)

    if df is None or df.empty:
        return None

    unique_artists = df['artist'].nunique()
    unique_albums = df['album'].nunique()
    unique_tracks = df['track'].nunique()
    total_scrobblings = df["datetime_utc"].count()

    first_date = pd.to_datetime(df['datetime_utc']).min()
    last_date = pd.to_datetime(df['datetime_utc']).max()
    unique_days = df["year_month_day"].nunique()

    # Averages    
    avg_scrobbles_per_day_with = df["datetime_utc"].count()/df["year_month_day"].nunique()
    avg_scrobbles_per_month = df.groupby("year_month").size().mean()
    avg_artist_per_month = df.groupby("year_month")["artist"].nunique().mean()

    # Cálculo del mes con más scrobbles 
    if 'year_month' in df:
        peak_month = df['year_month'].value_counts().idxmax()
        peak_month_scrobblings = df['year_month'].value_counts().max()
    else:
        peak_month = None
        peak_month_scrobblings = 0

    # Días naturales y promedio
    if pd.notnull(first_date):
        days_natural = (last_date - first_date).days + 1  # Usar rango filtrado
        avg_scrobbles_per_day = total_scrobblings / days_natural
        pct_days_with_scrobbles = (unique_days / days_natural) * 100
    else:
        days_natural = 0
        avg_scrobbles_per_day = 0
        pct_days_with_scrobbles = 0

    # Día con más scrobbles (top 1 por 'year_month_day')
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
        "peak_month": peak_month,
        "peak_month_scrobblings": peak_month_scrobblings,
        "days_natural": days_natural,
        "avg_scrobbles_per_day": avg_scrobbles_per_day,
        "pct_days_with_scrobbles": pct_days_with_scrobbles,
        "peak_day": peak_day,
        "peak_day_scrobblings": peak_day_scrobblings,
    }


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


# Métricas Detalladas (Detailed Statistics)
def calculate_streak_metrics(user=None, df=None, progress_callback=None):
    """
    Calcula métricas de rachas:
    - Racha actual y más larga (global)
    - Mayor racha para un artista individual (Top 1)
    """
    
    if df is None:
        from core.data_loader import load_user_data
        df = load_user_data(user, progress_callback)

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
    # Ordenar por artista y fecha
    df_artist = df_artist.sort_values(['artist', 'date'])
    
    # Calcular diferencia de días por artista
    df_artist['last_date'] = df_artist.groupby('artist')['date'].shift(1)
    df_artist['days_diff'] = (pd.to_datetime(df_artist['date']) - pd.to_datetime(df_artist['last_date'])).dt.days
    
    # Bandera de corte cuando hay huecos > 1 día
    df_artist['streak_group'] = (
        df_artist['days_diff'].gt(1)
        .groupby(df_artist['artist'])
        .cumsum()
    )
    
    # Calcular rachas por artista
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
    
    # Elegir Top 1 por mayor cantidad de días (y scrobbles como desempate)
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


# Racha por artista
def calculate_artist_play_streak(user=None, df=None, progress_callback=None):
    """
    Calcula la racha más larga de reproducciones consecutivas para un artista.
    Similar al SQL con LAG().
    """
    if df is None:
        from core.data_loader import load_user_data
        df = load_user_data(user, progress_callback)

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


# Todas las métricas
def calculate_all_metrics(user=None, df=None, progress_callback=None):
    """
    Calcula todas las métricas principales del usuario en una sola llamada.
    Esto permite evitar cálculos repetidos y simplifica el flujo en Streamlit.
    """
    if df is None:
        from core.data_loader import load_user_data
        df = load_user_data(user, progress_callback)

    if df is None or df.empty:
        return None

    all_metrics = {}

    # --- Métricas únicas ---
    unique_data = unique_metrics(user=user, df=df)
    if unique_data:
        all_metrics.update(unique_data)

    # --- Métricas de racha general ---
    streak_data = calculate_streak_metrics(user=user, df=df)
    if streak_data:
        all_metrics.update(streak_data)

    # --- Métricas de racha por artista ---
    streak_data_artist = calculate_artist_play_streak(user=user, df=df)
    if streak_data:
        all_metrics.update(streak_data_artist)

    return all_metrics
