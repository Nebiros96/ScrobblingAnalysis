import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
from datetime import datetime, timedelta
import toml
import os
import streamlit as st

# 🔐 Leer API key desde .streamlit/secrets.toml
base_dir = os.path.dirname(os.path.abspath(__file__))
secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")
secrets = toml.load(secrets_path)
api_key = secrets["lastfmAPI"]["api_key"]

def fetch_user_data(user: str, max_pages: int = None) -> pd.DataFrame:
    """
    Descarga y transforma los datos de scrobblings de un usuario desde la API de Last.fm
    sin guardar localmente. Devuelve un DataFrame.
    """
    all_data = []
    page = 1
    total_pages = 1  # se actualizará en la primera iteración

    while True:
        url = (
            f"http://ws.audioscrobbler.com/2.0/"
            f"?method=user.getrecenttracks&user={user}&api_key={api_key}&limit=200&page={page}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            recenttracks = root.find(".//recenttracks")
            if recenttracks is None:
                st.warning(f"No se encontraron datos en la página {page}")
                break

            if page == 1:
                total_pages_attr = recenttracks.attrib.get("totalPages")
                total_pages = int(total_pages_attr) if total_pages_attr else 1
                if max_pages:
                    total_pages = min(total_pages, max_pages)

            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None:
                    continue  # omitir canciones "now playing"

                try:
                    fecha_dt = datetime.strptime(date_elem.text, "%d %b %Y, %H:%M")
                except Exception:
                    continue

                gmt_date = fecha_dt - timedelta(hours=5)

                all_data.append({
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

            page += 1
            if page > total_pages:
                break

            time.sleep(0.25)

        except (requests.RequestException, ET.ParseError):
            st.error(f"Error al obtener datos de la página {page}. Intentando siguiente...")
            page += 1
            continue

    df = pd.DataFrame(all_data)
    return df
