import cv2
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
from deepface import DeepFace
import numpy as np
import time
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# Load .env untuk Spotify
load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state"
))

EMOTION_GENRE_MAP = {
    "happy": ["pop", "dance", "electropop", "indie pop"],
    "sad": ["acoustic", "blues", "singer-songwriter", "folk"],
    "angry": ["metal", "hard rock", "punk", "alternative metal"],
    "surprise": ["dance", "experimental", "psychedelic", "electronic"],
    "fear": ["ambient", "dark ambient", "industrial", "minimal"],
    "neutral": ["indie", "chillout", "trip-hop", "lo-fi"],
    "disgust": ["punk", "grunge", "garage rock", "hardcore"]
}


class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1024x600")
        self.root.overrideredirect(True)
        self.root.resizable(False, False)

        self.camera_active = True
        self.captured = False
        self.paused = False
        self.emotion = None
        self.recommended_songs = []
        self.loading = False

        self.video_label = tk.Label(self.root, bg="black")
        self.video_label.pack(fill="both", expand=True)

        self.countdown_label = tk.Label(self.root, text="", font=(
            "Arial", 72, "bold"), bg="black", fg="white")
        # Posisi di atas tombol Capture
        self.countdown_label.place(x=452, y=460)
        self.countdown_label.lower()

        self.loading_label = tk.Label(self.root, text="🔍 Menganalisis emosi...", font=(
            "Arial", 28), bg="black", fg="white")
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.loading_label.lower()

        self.emotion_label = tk.Label(self.root, text="", font=(
            "Arial", 24), bg="black", fg="white")
        self.emotion_label.place(x=20, y=20)

        self.song_labels = [tk.Label(self.root, text="", font=(
            "Arial", 16), bg="black", fg="white") for _ in range(10)]
        for i, label in enumerate(self.song_labels):
            label.place(x=20, y=60 + i * 30)
            label.lower()

        self.capture_icon = self.load_icon("icons/capture.png")
        self.pause_icon = self.load_icon("icons/pause.png")
        self.play_icon = self.load_icon("icons/play.png")
        self.reset_icon = self.load_icon("icons/reset.png")

        self.capture_btn = self.make_button(
            " Capture", self.capture_icon, self.start_countdown)
        self.capture_btn.place(x=452, y=520, width=120, height=50)

        self.pause_btn = self.make_button(
            " Pause", self.pause_icon, self.on_pause)
        self.play_btn = self.make_button(" Play", self.play_icon, self.on_play)
        self.reset_btn = self.make_button(
            " Reset", self.reset_icon, self.reset_view)

        self.pause_btn.place_forget()
        self.play_btn.place_forget()
        self.reset_btn.place_forget()

        self.cap = cv2.VideoCapture(0)
        self.update_frame()

        # Kotak hitam dengan tombol "X" untuk quit
        self.quit_frame = tk.Frame(
            self.root, bg="black", width=500, height=500)
        # Posisi di pojok kiri atas dengan jarak 10px dari atas dan kiri
        self.quit_frame.place(x=10, y=10)

        self.quit_button = tk.Button(
            self.quit_frame, text="X", font=("Arial", 20, "bold"),
            bg="red", fg="white", bd=0, relief="flat",
            command=self.on_quit
        )
        self.quit_button.pack(fill="both", expand=True)

        self.root.bind('<q>', lambda event: self.on_quit())
        self.root.bind('<Q>', lambda event: self.on_quit())

    def load_icon(self, path):
        try:
            return ImageTk.PhotoImage(Image.open(path).resize((32, 32)))
        except Exception as e:
            print(f"⚠️ Gagal memuat ikon {path}:", e)
            return None

    def make_button(self, text, icon, command):
        return tk.Button(
            self.root, text=text, font=("Arial", 14, "bold"),
            image=icon if icon else None,
            compound="left" if icon else None,
            bg="#222222", fg="white", bd=0, relief="flat",
            activebackground="#333333", highlightthickness=0,
            command=command
        )

    def start_countdown(self):
        self.capture_btn.place_forget()
        # Persegi dengan ukuran angka lebih kecil
        self.countdown_label.config(
            width=4, height=2, font=("Arial", 48, "bold"))
        self.countdown_label.lift()
        self.countdown(3)

    def countdown(self, count):
        if count > 0:
            self.countdown_label.config(text=str(count))
            self.root.after(1000, self.countdown, count - 1)
        else:
            self.countdown_label.lower()
            self.on_capture()

    def on_capture(self):
        self.captured = True
        self.camera_active = False
        self.loading = True
        self.loading_label.lift()

        # Sembunyikan tombol "X"
        self.quit_frame.place_forget()

        self.pause_btn.place(x=382, y=520, width=120, height=50)
        self.play_btn.place(x=522, y=520, width=120, height=50)
        self.reset_btn.place(x=892, y=540, width=120, height=40)

        threading.Thread(target=self.analyze_emotion, daemon=True).start()

    def save_frame(self, frame):
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # Format timestamp
        folder_name = "emotion_analysis_results"
        os.makedirs(folder_name, exist_ok=True)  # Buat folder jika belum ada
        filename = os.path.join(
            folder_name, f"emotion_analysis_{timestamp}.png")
        try:
            # Konversi frame dari BGR (OpenCV) ke RGB (PIL)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)

            # Deteksi wajah menggunakan OpenCV
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Tambahkan kotak di sekitar wajah
            draw = ImageDraw.Draw(image)
            for (x, y, w, h) in faces:
                draw.rectangle([x, y, x + w, y + h], outline="red", width=5)

            # Tambahkan teks emosi pada gambar
            text = f"Emotion: {self.emotion}"
            # Pastikan font tersedia
            font = ImageFont.truetype("arial.ttf", 32)
            draw.text((10, 10), text, fill="white", font=font)

            # Simpan gambar
            image.save(filename)
            print(f"✅ Gambar disimpan di folder '{folder_name}': {filename}")
        except Exception as e:
            print(f"❌ Gagal menyimpan gambar: {e}")

    def analyze_emotion(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            result = DeepFace.analyze(
                rgb, actions=['emotion'], enforce_detection=False)[0]
            self.emotion = result['dominant_emotion']
            self.recommended_songs = self.recommend_songs(self.emotion)

            # Simpan frame dengan hasil analisis emosi dan kotak wajah
            self.save_frame(frame)
        except Exception as e:
            print("❌ Gagal analisa emosi:", str(e))
            self.emotion = "Tidak Terdeteksi"
            self.recommended_songs = []

        self.loading = False
        self.update_emotion_ui()

    def update_emotion_ui(self):
        if self.emotion:
            self.emotion_label.config(text=f"Emosi: {self.emotion}")

        for i, label in enumerate(self.song_labels):
            if i < len(self.recommended_songs):
                text, uri = self.recommended_songs[i]
                label.config(
                    text=f"{i + 1}. {text}",  # Tambahkan angka di depan lagu
                    cursor="hand2",
                    fg="white",  # Ubah warna teks menjadi putih
                    font=("Arial", 18, "bold")  # Perbesar ukuran font
                )
                label.bind("<Button-1>", lambda e,
                           uri=uri: self.play_track(uri))
                label.lift()
            else:
                label.config(text="", cursor="", fg="white")
                label.unbind("<Button-1>")
                label.lower()

    def recommend_songs(self, emotion):
        genres = EMOTION_GENRE_MAP.get(emotion.lower(), ["pop"])
        genre = random.choice(genres)
        try:
            results = sp.search(q=f'genre:"{genre}"', type='track', limit=15)
            tracks = results['tracks']['items']
            random.shuffle(tracks)
            seen = set()
            recommendations = []
            for track in tracks:
                track_id = track['id']
                if track_id not in seen:
                    seen.add(track_id)
                    recommendations.append(
                        (f"{track['name']} - {', '.join(artist['name'] for artist in track['artists'])}", track['uri'])
                    )
                if len(recommendations) >= 10:
                    break
            return recommendations
        except Exception as e:
            print("❌ Gagal rekomendasi lagu:", e)
            return []

    def play_track(self, uri):
        try:
            sp.start_playback(uris=[uri])
            print(f"▶️ Memutar: {uri}")
        except Exception as e:
            print("❌ Gagal memutar lagu:", e)

    def on_play(self):
        self.paused = False
        try:
            sp.start_playback()
            print("▶️ Playback dilanjutkan")
        except Exception as e:
            print("❌ Gagal memulai playback:", e)

    def on_pause(self):
        self.paused = True
        try:
            sp.pause_playback()
            print("⏸️ Playback dijeda")
        except Exception as e:
            print("❌ Gagal menjeda playback:", e)

    def reset_view(self):
        self.camera_active = True
        self.captured = False
        self.paused = False
        self.emotion = None
        self.recommended_songs = []

        self.pause_btn.place_forget()
        self.play_btn.place_forget()
        self.reset_btn.place_forget()
        self.capture_btn.place(x=452, y=520, width=120, height=50)

        # Tampilkan kembali tombol "X"
        self.quit_frame.place(x=10, y=10)

        self.emotion_label.config(text="")
        for label in self.song_labels:
            label.config(text="", cursor="", fg="white")
            label.unbind("<Button-1>")
            label.lower()

    def update_frame(self):
        if self.camera_active and not self.paused:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = frame.shape
                target_w, target_h = 1024, 600
                scale = max(target_w / w, target_h / h)
                resized = cv2.resize(frame, (int(w * scale), int(h * scale)))
                x_start = (resized.shape[1] - target_w) // 2
                y_start = (resized.shape[0] - target_h) // 2
                cropped = resized[y_start:y_start +
                                  target_h, x_start:x_start + target_w]
                image = Image.fromarray(cropped)
                photo = ImageTk.PhotoImage(image=image)
                self.video_label.config(image=photo)
                self.video_label.image = photo

        elif self.captured:
            black_img = Image.new("RGB", (1024, 600), color="black")
            black_photo = ImageTk.PhotoImage(black_img)
            self.video_label.config(image=black_photo)
            self.video_label.image = black_photo
            if not self.loading:
                self.loading_label.lower()

        self.root.after(10, self.update_frame)

    def on_quit(self):
        self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
