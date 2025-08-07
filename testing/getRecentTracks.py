import requests
import xml.etree.ElementTree as ET
import csv
import time
import os
import toml

# 📁 Detectar ruta absoluta del archivo secrets.toml en .streamlit
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sube desde /testing
secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")

# 🔐 Leer API key desde secrets.toml
secrets = toml.load(secrets_path)
api_key = secrets["lastfmAPI"]["api_key"]

# 🔧 Parámetros de usuario
user = 'Brenoritvrezork'  # Puedes leerlo del .toml si lo deseas
page = 1
total_pages = 1

# 📁 Ruta de salida: carpeta assets/
output_folder = os.path.join(base_dir, "assets")
os.makedirs(output_folder, exist_ok=True)  # crea si no existe
output_path = os.path.join(output_folder, f"{user}.csv")

# 📝 Abrir CSV para escritura
with open(output_path, mode="w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["user", "date", "artist", "album", "track", "url"])

    while page <= total_pages:
        print(f"\n🔄 Cargando página {page} de {total_pages}...")

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
                continue  # reintenta la misma página

            if page == 1:
                total_pages_attr = recenttracks.attrib.get("totalPages")
                total_pages = int(total_pages_attr) if total_pages_attr else 1
                print(f"✅ Detectadas {total_pages} páginas (~{total_pages * 200} scrobbles)")

            for track in root.findall(".//track"):
                date_elem = track.find("date")
                if date_elem is None:
                    continue  # omitir canciones nowplaying

                artist_elem = track.find("artist")
                album_elem = track.find("album")
                name_elem = track.find("name")
                url_elem = track.find("url")

                writer.writerow([
                    user,
                    date_elem.text,
                    artist_elem.text if artist_elem is not None else "",
                    album_elem.text if album_elem is not None else "",
                    name_elem.text if name_elem is not None else "",
                    url_elem.text if url_elem is not None else "",
                ])

            page += 1
            time.sleep(0.25)  # para evitar ser bloqueado

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
