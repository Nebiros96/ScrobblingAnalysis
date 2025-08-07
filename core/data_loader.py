import pandas as pd
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
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

def fetch_user_data_from_api(user: str, progress_callback=None) -> pd.DataFrame:
    """Obtiene TODOS los datos del usuario desde la API de Last.fm
    
    Args:
        user: Nombre de usuario de Last.fm
        progress_callback: Función para mostrar progreso (opcional)
    """
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

            # Verificar si hay error en la respuesta
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
                total_pages_attr = recenttracks.attrib.get("totalPages")
                total_pages = int(total_pages_attr) if total_pages_attr else 1
                print(f"📊 Total pages: {total_pages}")

            # Contar tracks en esta página
            tracks_in_page = 0
            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None:
                    continue  # skip "now playing"

                try:
                    fecha_dt = datetime.strptime(date_elem.text, "%d %b %Y, %H:%M")
                except Exception:
                    continue

                gmt_date = fecha_dt - timedelta(hours=5)

                all_rows.append({
                    "user": user,
                    "date": date_elem.text,
                    "artist": track.findtext("artist", default=""),
                    "album": track.findtext("album", default=""),
                    "track": track.findtext("name", default=""),
                    "url": track.findtext("url", default=""),
                    "gmt_date": gmt_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "year": gmt_date.year,
                    "quarter": (gmt_date.month - 1) // 3 + 1,
                    "month": gmt_date.month,
                    "day": gmt_date.day,
                    "hour": gmt_date.hour,
                    "year_month": gmt_date.strftime("%Y-%m"),
                    "year_month_day": gmt_date.strftime("%Y-%m-%d"),
                    "weekday": gmt_date.strftime("%A")
                })
                tracks_in_page += 1

            # Mostrar progreso si hay callback
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

    return pd.DataFrame(all_rows)

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
            # Convertir gmt_date a datetime
            df['gmt_date'] = pd.to_datetime(df['gmt_date'])
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

    df["Year_Month"] = df["gmt_date"].dt.to_period("M").astype(str)

    scrobblings_by_month = df.groupby("Year_Month").size().reset_index(name="Scrobblings")
    artists_by_month = df.groupby("Year_Month")["artist"].nunique().reset_index(name="Artists")
    albums_by_month = df.groupby("Year_Month")["album"].nunique().reset_index(name="Albums")

    return scrobblings_by_month, artists_by_month, albums_by_month

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
