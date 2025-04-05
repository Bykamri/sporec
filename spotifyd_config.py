import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

config_path = Path.home() / ".config" / "spotifyd"
config_path.mkdir(parents=True, exist_ok=True)

config_file = config_path / "spotifyd.conf"

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
username = os.getenv("SPOTIFY_USERNAME")
password = os.getenv("SPOTIFY_PASSWORD")

if not all([client_id, client_secret, username, password]):
    print("❌ Pastikan semua variabel di .env sudah diisi dengan benar.")
    exit(1)

config_content = f"""
[global]
username = "{username}"
password = "{password}"
backend = "pulseaudio"
device_name = "jetson-nano"
bitrate = 160
volume_normalisation = true
use_mpris = false

[spotifyd]
client_id = "{client_id}"
client_secret = "{client_secret}"
"""

with config_file.open("w") as f:
    f.write(config_content.strip())

print(f"✅ Konfigurasi spotifyd berhasil dibuat di: {config_file}")
