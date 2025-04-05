# (Semua import tetap)
import cv2
import time
import os
import argparse
from deepface import DeepFace
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import numpy as np  # Tambahkan ini untuk stack channel

# Load .env
load_dotenv()
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

# Argument parser
parser = argparse.ArgumentParser(
    description="Emotion Detector with Spotify Recommendation")
parser.add_argument("--play", action="store_true",
                    help="Play the top recommended song on active Spotify device")
parser.add_argument("--camera", type=int, default=0,
                    help="Camera index to use (default: 0)")
args = parser.parse_args()

# Spotify Setup
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state"
))

# Emotion to genre map
EMOTION_GENRE_MAP = {
    "happy": ["pop", "dance", "electropop", "indie pop"],
    "sad": ["acoustic", "blues", "singer-songwriter", "folk"],
    "angry": ["metal", "hard rock", "punk", "alternative metal"],
    "surprise": ["dance", "experimental", "psychedelic", "electronic"],
    "fear": ["ambient", "dark ambient", "industrial", "minimal"],
    "neutral": ["indie", "chillout", "trip-hop", "lo-fi"],
    "disgust": ["punk", "grunge", "garage rock", "hardcore"]
}


def recommend_songs(emotion):
    if emotion not in EMOTION_GENRE_MAP:
        return [], []

    genres = EMOTION_GENRE_MAP[emotion]
    genre = random.choice(genres)
    results = sp.search(q=f'genre:"{genre}"', type='track', limit=50)
    tracks = results['tracks']['items']
    random.shuffle(tracks)

    selected_tracks = tracks[:5]
    track_names = [
        f"{track['name']} - {', '.join(artist['name'] for artist in track['artists'])}" for track in selected_tracks]
    track_uris = [track['uri'] for track in selected_tracks]
    return track_names, track_uris


def play_song(uri):
    devices = sp.devices()
    jetson_device = None

    for device in devices['devices']:
        if "jetson" in device['name'].lower() or device['type'].lower() == 'computer':
            jetson_device = device['id']
            break

    if jetson_device:
        sp.start_playback(device_id=jetson_device, uris=[uri])
        print("▶️ Memutar lagu di Jetson Nano...")
    elif devices['devices']:
        fallback_device = devices['devices'][0]['id']
        sp.start_playback(device_id=fallback_device, uris=[uri])
        print("▶️ Memutar lagu di perangkat fallback:",
              devices['devices'][0]['name'])
    else:
        print("❌ Tidak ada perangkat Spotify aktif ditemukan.")


# UI
CAMERA_INDEX = args.camera
BUTTONS = {
    "capture": {"x": 10, "y": 10, "w": 150, "h": 40},
    "quit": {"x": 10, "y": 60, "w": 150, "h": 40}
}

click_pos = (0, 0)
click_flag = False
last_emotion = None
recommended_songs = []
recommended_uris = []
timer_started = False
timer_start_time = None
countdown = 3


def draw_button(frame, text, button, color=(0, 255, 0)):
    x, y, w, h = button["x"], button["y"], button["w"], button["h"]
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, text, (x + 10, y + h // 2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def is_inside_button(x, y, button):
    bx, by, bw, bh = button["x"], button["y"], button["w"], button["h"]
    return bx <= x <= bx + bw and by <= y <= by + bh


def mouse_callback(event, x, y, flags, param):
    global click_pos, click_flag
    if event == cv2.EVENT_LBUTTONDOWN:
        click_pos = (x, y)
        click_flag = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--play", action="store_true",
                        help="Play the top recommended song")
    args = parser.parse_args()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Tidak dapat membuka kamera.")
        return

    countdown = 3
    sidebar_width = 300
    last_emotion = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Gagal membaca frame dari kamera.")
            break

        # Tampilkan countdown
        for i in range(countdown, 0, -1):
            countdown_frame = frame.copy()
            cv2.putText(countdown_frame, f"Scan dalam {i} detik...", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Emotion Detection", countdown_frame)
            cv2.waitKey(1000)

        try:
            # Ambil bagian frame untuk deteksi wajah (tanpa sidebar)
            face_area = frame[:, :-sidebar_width]

            # Konversi ke RGB
            rgb_frame = cv2.cvtColor(face_area, cv2.COLOR_BGR2RGB)

            # Deteksi emosi
            result = DeepFace.analyze(
                rgb_frame,
                actions=['emotion'],
                enforce_detection=True,
                detector_backend='opencv'
            )

            # Ambil emosi dominan
            if isinstance(result, list) and result:
                last_emotion = result[0]['dominant_emotion']
            elif isinstance(result, dict):
                last_emotion = result['dominant_emotion']
            else:
                last_emotion = "Tidak Terdeteksi"
                raise ValueError("Hasil analisis tidak valid.")

            print("😄 Emosi Terdeteksi:", last_emotion)

            # Rekomendasi lagu
            recommended_songs, recommended_uris = recommend_songs(last_emotion)
            print("🎶 Lagu Rekomendasi:")
            for song in recommended_songs:
                print(" -", song)

            # Putar lagu jika diminta
            if args.play and recommended_uris:
                play_song(recommended_uris[0])

        except Exception as e:
            print("❌ Gagal menganalisis emosi:", str(e))
            last_emotion = "Tidak Terdeteksi"

        # Tampilkan hasil di layar
        sidebar = np.zeros((frame.shape[0], sidebar_width, 3), dtype=np.uint8)
        cv2.putText(sidebar, "Emosi:", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        if last_emotion:
            cv2.putText(sidebar, last_emotion, (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        combined_frame = cv2.hconcat([frame[:, :-sidebar_width], sidebar])
        cv2.imshow("Emotion Detection", combined_frame)

        # Tunggu input ESC (27)
        key = cv2.waitKey(0)
        if key == 27:
            print("👋 Keluar dari program.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
