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


def capture_and_analyze_emotion():
    global click_pos, click_flag, last_emotion, recommended_songs, recommended_uris
    global timer_started, timer_start_time

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"❌ Tidak bisa membuka kamera dengan index {CAMERA_INDEX}")
        return

    cv2.namedWindow("Emotion Detector")
    cv2.setMouseCallback("Emotion Detector", mouse_callback)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        sidebar_width = 400
        frame = cv2.copyMakeBorder(
            frame, 0, 0, 0, sidebar_width, cv2.BORDER_CONSTANT, value=(40, 40, 40))

        draw_button(frame, "Capture", BUTTONS["capture"])
        draw_button(frame, "Quit", BUTTONS["quit"])

        if last_emotion:
            cv2.putText(frame, f"Emosi: {last_emotion}", (frame.shape[1] - sidebar_width + 20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, "Rekomendasi Lagu:", (frame.shape[1] - sidebar_width + 20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

            for i, song in enumerate(recommended_songs):
                y = 110 + (i * 30)
                color = (200, 200, 200)
                cv2.putText(frame, f"{i+1}. {song[:35]}", (frame.shape[1] - sidebar_width + 20, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

        if click_flag:
            x, y = click_pos
            click_flag = False

            if is_inside_button(x, y, BUTTONS["capture"]) and not timer_started:
                timer_started = True
                timer_start_time = time.time()
            elif is_inside_button(x, y, BUTTONS["quit"]):
                break

            if args.play and last_emotion and recommended_uris:
                sidebar_x = frame.shape[1] - sidebar_width
                for i in range(len(recommended_uris)):
                    text_y = 110 + (i * 30)
                    if sidebar_x + 20 <= x <= sidebar_x + 350 and text_y - 20 <= y <= text_y:
                        print(f"▶️ Klik lagu #{i+1}: {recommended_songs[i]}")
                        play_song(recommended_uris[i])
                        break

        if timer_started:
            elapsed = time.time() - timer_start_time
            remaining = int(countdown - elapsed)
            if remaining > 0:
                cv2.putText(frame, f"Capturing in {remaining}...",
                            (200, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                timer_started = False
                try:
                    rgb_frame = cv2.cvtColor(
                        frame[:, :-sidebar_width], cv2.COLOR_BGR2RGB)

                    # ✅ Tambahan perbaikan di sini:
                    if rgb_frame.ndim == 2:
                        rgb_frame = np.stack((rgb_frame,) * 3, axis=-1)
                    elif rgb_frame.ndim == 3 and rgb_frame.shape[2] == 1:
                        rgb_frame = np.concatenate([rgb_frame]*3, axis=-1)

                    result = DeepFace.analyze(
                        rgb_frame,
                        actions=['emotion'],
                        enforce_detection=False,
                        detector_backend='opencv'
                    )
                    last_emotion = result[0]['dominant_emotion']
                    print("😄 Emosi Terdeteksi:", last_emotion)

                    recommended_songs, recommended_uris = recommend_songs(
                        last_emotion)
                    print("🎶 Lagu Rekomendasi:")
                    for song in recommended_songs:
                        print(" -", song)

                    if args.play and recommended_uris:
                        play_song(recommended_uris[0])

                except Exception as e:
                    print("❌ Gagal menganalisis emosi:", str(e))
                    last_emotion = "Tidak Terdeteksi"
                    recommended_songs = []
                    recommended_uris = []

        cv2.imshow("Emotion Detector", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture_and_analyze_emotion()
