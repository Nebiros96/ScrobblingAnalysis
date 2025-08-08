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

from datetime import datetime, timezone
import pandas as pd
import requests
import xml.etree.ElementTree as ET

def fetch_user_data_from_api(user: str, progress_callback=None) -> pd.DataFrame:
    """Obtiene TODOS los datos del usuario desde la API de Last.fm"""
    api_key = get_api_key()
    page = 1
    total_pages = 1
    all_rows = []

    while True:
        url = (
            f"http://ws.audioscrobbler.com/2.0/"
            f"?method=user.getrecenttracks&user={user}&api_key={api_key}&limit=200&page={page}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            # Manejo de errores API
            error = root.find(".//error")
            if error is not None:
                error_msg = error.text
                if "User not found" in error_msg:
                    raise ValueError(f"User '{user}' not found in Last.fm")
                else:
                    raise ValueError(f"API Error: {error_msg}")

            recenttracks = root.find(".//recenttracks")
            if recenttracks is None:
                break

            if page == 1:
                total_pages = int(recenttracks.attrib.get("totalPages", "1"))
                print(f"📊 Total pages: {total_pages}")

            tracks_in_page = 0
            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None or date_elem.get("uts") is None:
                    continue  # skip "now playing" o sin fecha válida

                try:
                    uts_timestamp = int(date_elem.get("uts"))
                    fecha_dt = datetime.fromtimestamp(uts_timestamp, tz=timezone.utc)
                except ValueError:
                    continue

                all_rows.append({
                    "user": user,
                    "datetime_utc": fecha_dt,
                    "artist": track.findtext("artist", default=""),
                    "album": track.findtext("album", default=""),
                    "track": track.findtext("name", default=""),
                    "url": track.findtext("url", default="")
                })
                tracks_in_page += 1

            if progress_callback:
                progress_callback(page, total_pages, len(all_rows))
            else:
                print(f"📄 Page {page}/{total_pages} - {tracks_in_page} loaded scrobbles (Total: {len(all_rows)})")

            page += 1
            if page > total_pages:
                break

        except requests.RequestException as e:
            raise ConnectionError(f"Connection error: {e}")
        except ET.ParseError as e:
            raise ValueError(f"Error when processing API response: {e}")
        except Exception as e:
            raise Exception(f"Unexpected Error: {e}")

    # Construir DataFrame
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

def load_user_data(user, progress_callback=None):
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

def load_monthly_metrics(user, progress_callback=None):
    """Carga métricas mensuales para el usuario
    
    Args:
        user: Nombre de usuario de Last.fm
        progress_callback: Función para mostrar progreso (opcional)
    """
    df = load_user_data(user, progress_callback)
    if df is None or df.empty:
        return None, None, None

    df["Year_Month"] = df["datetime_utc"].dt.to_period("M").astype(str)

    scrobblings_by_month = df.groupby("Year_Month").size().reset_index(name="Scrobblings")
    artists_by_month = df.groupby("Year_Month")["artist"].nunique().reset_index(name="Artists")
    albums_by_month = df.groupby("Year_Month")["album"].nunique().reset_index(name="Albums")

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
        days_natural = (datetime.now(timezone.utc) - first_date).days + 1
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
