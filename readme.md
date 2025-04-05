# Emotion Detector with Spotify Recommendation

## Overview

Program ini mendeteksi emosi dari kamera secara langsung dan merekomendasikan lagu berdasarkan emosi yang terdeteksi menggunakan API Spotify. Program ini juga dapat memutar lagu yang direkomendasikan pada perangkat Spotify aktif.

---

## Prerequisites

### 1. **Python Environment**

- Python 3.7 atau lebih tinggi.
- Instal pustaka yang diperlukan menggunakan requirements.txt:
  ```bash
  pip install -r requirements.txt
  ```

### 2. **Spotify API Credentials**

- Buat akun pengembang Spotify di [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
- Buat aplikasi dan dapatkan kredensial berikut:
  - `SPOTIPY_CLIENT_ID`
  - `SPOTIPY_CLIENT_SECRET`
  - `SPOTIPY_REDIRECT_URI`

### 3. **Environment Variables**

- Gunakan file .env.example yang telah disediakan untuk membuat file .env Anda.
- Salin isi file .env.example ke file .env dan isi dengan kredensial Spotify Anda:
  ```
  SPOTIPY_CLIENT_ID=your_client_id
  SPOTIPY_CLIENT_SECRET=your_client_secret
  SPOTIPY_REDIRECT_URI=your_redirect_uri
  ```

---

## How to Run the Program

### 1. **Run the Script**

Jalankan skrip menggunakan perintah berikut:

```bash
python main.py
```

- Tambahkan flag `--play` untuk mengaktifkan pemutaran lagu pada perangkat Spotify aktif:

  ```bash
  python main.py --play
  ```

- Gunakan argumen `--camera` untuk memilih kamera tertentu (default: `0`):
  ```bash
  python main.py --camera 1
  ```

### 2. **UI Buttons**

- **Capture**: Mengambil frame saat ini dan menganalisis emosi dominan.
- **Quit**: Keluar dari program.

### 3. **Emotion Detection**

- Program menggunakan pustaka `DeepFace` untuk mendeteksi emosi dari kamera.
- Emosi yang didukung:
  - `happy`
  - `sad`
  - `angry`
  - `surprise`
  - `fear`
  - `neutral`
  - `disgust`

### 4. **Song Recommendation**

- Berdasarkan emosi yang terdeteksi, program merekomendasikan lagu menggunakan API pencarian Spotify.
- Lagu yang direkomendasikan ditampilkan di sidebar.

### 5. **Play Songs**

- Jika flag `--play` digunakan, klik pada lagu yang direkomendasikan untuk memutarnya di perangkat Spotify aktif.

---

## Troubleshooting

### 1. **Kamera Tidak Terdeteksi**

- Pastikan kamera Anda terhubung dan dapat diakses.
- Gunakan argumen `--camera` untuk mencoba kamera lain:
  ```bash
  python main.py --camera 1
  ```

### 2. **Kesalahan API Spotify**

- Pastikan file .env Anda berisi kredensial Spotify yang valid.
- Periksa koneksi internet Anda.
- Pastikan akun Spotify Anda masuk dan memiliki perangkat aktif.

### 3. **Tidak Ada Lagu yang Direkomendasikan**

- Verifikasi bahwa genre dalam `EMOTION_GENRE_MAP` adalah genre Spotify yang valid.
- Perbarui `EMOTION_GENRE_MAP` dengan genre yang valid jika diperlukan.

---

## Customization

### 1. **Ubah Pemetaan Emosi ke Genre**

- Perbarui dictionary `EMOTION_GENRE_MAP` untuk menyesuaikan genre yang terkait dengan setiap emosi:
  ```python
  EMOTION_GENRE_MAP = {
      "happy": ["pop", "dance"],
      "sad": ["acoustic", "blues"],
      "angry": ["metal", "punk"],
      "surprise": ["electronic", "experimental"],
      "fear": ["ambient", "dark ambient"],
      "neutral": ["lo-fi", "indie"],
      "disgust": ["grunge", "garage rock"]
  }
  ```

### 2. **Ubah Jumlah Lagu yang Direkomendasikan**

- Ubah parameter `limit` dalam fungsi `recommend_songs`:
  ```python
  results = sp.search(q=f'genre:"{genre}"', type='track', limit=50)
  ```

---

## Example Output

### Console Output

```plaintext
😄 Emosi Terdeteksi: happy
🎶 Lagu Rekomendasi:
 - Song 1 - Artist 1
 - Song 2 - Artist 2
 - Song 3 - Artist 3
```

### UI

- Emosi yang terdeteksi dan lagu yang direkomendasikan ditampilkan di sidebar.
- Klik pada lagu untuk memutarnya (jika `--play` diaktifkan).
