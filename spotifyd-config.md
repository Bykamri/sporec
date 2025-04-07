# Sporec 🎵 — Spotify Daemon for Jetson Nano

**Sporec** adalah setup khusus `spotifyd` yang dikompilasi dari source untuk berjalan sebagai Spotify Connect client di perangkat seperti Jetson Nano, Raspberry Pi, atau device headless lainnya. Cocok untuk dijalankan di speaker pintar, robot musik, atau sistem audio rumah!

---

## ✨ Fitur

- Spotify Connect client (terlihat dari HP / PC)
- Dukungan untuk PulseAudio
- Konfigurasi otomatis dengan `.env`
- Playback headless via CLI atau Spotify mobile/desktop

---

## 🚀 Instalasi dari Source

### 1. Clone repo

```bash
git clone https://github.com/Spotifyd/spotifyd
cd spotifyd
```

### 2. Install dependency

```bash
sudo apt update
sudo apt install -y curl pkg-config libasound2-dev libssl-dev dbus libpulse-dev build-essential

curl https://sh.rustup.rs -sSf | sh     # install Rust compiler
source $HOME/.cargo/env
```

> ⚠️ Pastikan `PulseAudio` aktif:  
> Cek dengan `pulseaudio --check || pulseaudio --start`

### 3. Build `spotifyd`

```bash
cargo build --release --features pulseaudio_backend
```

Binary akan berada di:

```bash
./target/release/spotifyd --no-daemon
```

---

## ⚙️ Konfigurasi Otomatis

### 2. Jalankan script konfigurasi

```bash
python3 spotifyd_config.py
```

Script akan membuat file:

```
~/.config/spotifyd/spotifyd.conf
```

---

## ▶️ Menjalankan spotifyd

Jalankan secara manual:

```bash
cd spotifyd

./target/release/spotifyd --no-daemon
```

Jika semua sukses, akan muncul log seperti:

```
[INFO] Authenticated as 'username'
[INFO] Device ready: jetson-nano
```

---

## 📱 Memutar Lagu dari HP / PC

1. Buka Spotify di HP / PC
2. Tap ikon device (🔈)
3. Pilih `jetson-nano`
4. Putar lagu 🎵

---

## 🛠️ (Opsional) Setup Autostart dengan systemd

### 1. 📁 Buat folder `~/.config/systemd/user` jika belum ada

```bash
mkdir -p ~/.config/systemd/user
```

### 2. 📄 Buat file `spotifyd.service`

```bash
nano ~/.config/systemd/user/spotifyd.service
```

### 3. ✍️ Masukkan isi berikut:

```ini
[Unit]
Description=A spotify playing daemon
After=network.target sound.target

[Service]
ExecStart=/home/jetson/spotifyd/target/release/spotifyd --no-daemon
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=default.target
```

> ⚠️ Ganti path `ExecStart=` sesuai lokasi `spotifyd` kamu. Tes dulu pakai:

```bash
which spotifyd
# atau
realpath ./spotifyd
```

---

### 4. 🔄 Reload systemd user daemon

```bash
systemctl --user daemon-reload
```

### 5. ✅ Enable & start service

```bash
systemctl --user enable spotifyd
systemctl --user start spotifyd
```

---

### 6. 🔍 Cek status

```bash
systemctl --user status spotifyd
```

Kalau aktif dan running, artinya sukses!

---

### 🛠 Tips Tambahan

Kalau kamu melihat error seperti `Failed to connect to bus: No such file or directory`, artinya kamu harus mengaktifkan user systemd session:

```bash
loginctl enable-linger $USER
```

Lalu logout dan login ulang (atau restart).

## 🧪 Troubleshooting

### Device tidak muncul di Spotify Connect?

- Pastikan `spotifyd` berjalan dan login sukses
- Pastikan `avahi-daemon` aktif:

```bash
sudo apt install avahi-daemon
sudo systemctl start avahi-daemon
```

- Cek broadcast:

```bash
avahi-browse -a | grep spotify
```

### Gagal login?

- Pastikan `username/password` benar (akun Spotify Premium disarankan)
- Pastikan `client_id` dan `client_secret` aktif

---
