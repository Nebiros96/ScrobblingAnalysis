import requests
import xml.etree.ElementTree as ET
import csv
import time
import os
import toml
import sys
from datetime import datetime, timedelta

# 📁 Detectar ruta absoluta del archivo secrets.toml en .streamlit
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sube desde /testing
secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")

# 🔐 Leer API key desde secrets.toml
secrets = toml.load(secrets_path)
api_key = secrets["lastfmAPI"]["api_key"]

# 🔧 Parámetros
user = 'Brenoritvrezork'
page = 1

# ✅ Leer cantidad de páginas desde argumentos del script (opcional)
try:
    max_pages_arg = int(sys.argv[1])
    print(f"📌 Se usará un límite de {max_pages_arg} páginas")
except (IndexError, ValueError):
    max_pages_arg = None  # None significa "sin límite" (usa total real de API)
    print("📌 No se indicó límite de páginas. Se usará el total detectado por la API.")

total_pages = 1  # será actualizado al inicio

# 📁 Ruta de salida: carpeta assets/
output_folder = os.path.join(base_dir, "assets")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, f"{user}.csv")

# 📝 Abrir CSV para escritura con columnas enriquecidas
with open(output_path, mode="w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow([
        "user", "date", "artist", "album", "track", "url",
        "gmt_date", "year", "quarter", "month", "day", "hour",
        "year_month", "year_month_day", "weekday"
    ])

    while True:
        print(f"\n🔄 Cargando página {page}...")

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
                print(f"❌ Error: no se encontró la etiqueta <recenttracks> en la página {page}")
                print("🔁 Esperando 5 segundos antes de reintentar...")
                time.sleep(5)
                continue

            if page == 1:
                total_pages_attr = recenttracks.attrib.get("totalPages")
                total_pages = int(total_pages_attr) if total_pages_attr else 1
                print(f"✅ Total de páginas según API: {total_pages}")

                if max_pages_arg:
                    total_pages = min(total_pages, max_pages_arg)
                    print(f"📉 Se usará un máximo de {total_pages} páginas")

            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None:
                    continue  # omitir canciones "now playing"

                try:
                    fecha_dt = datetime.strptime(date_elem.text, "%d %b %Y, %H:%M")
                except Exception as e:
                    print(f"⚠️ Fecha inválida en página {page}: {e}")
                    continue

                gmt_date = fecha_dt - timedelta(hours=5)

                writer.writerow([
                    user,
                    date_elem.text,
                    track.findtext("artist", default=""),
                    track.findtext("album", default=""),
                    track.findtext("name", default=""),
                    track.findtext("url", default=""),
                    gmt_date.strftime("%Y-%m-%d %H:%M:%S"),
                    gmt_date.year,
                    (gmt_date.month - 1) // 3 + 1,
                    gmt_date.month,
                    gmt_date.day,
                    gmt_date.hour,
                    gmt_date.strftime("%Y-%m"),
                    gmt_date.strftime("%Y-%m-%d"),
                    gmt_date.strftime("%A")
                ])

            page += 1
            if page > total_pages:
                print("\n✅ Descarga completada.")
                break

            time.sleep(0.25)

        except requests.RequestException as e:
            print(f"❌ Error de red en página {page}: {e}")
            print("🔁 Esperando 5 segundos antes de reintentar...")
            time.sleep(5)
            continue

        except ET.ParseError as e:
            print(f"❌ Error al parsear XML en página {page}: {e}")
            print("🛑 Saltando esta página para continuar...")
            page += 1
            continue
