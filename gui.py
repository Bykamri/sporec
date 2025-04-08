from urllib.request import urlopen
import io
import customtkinter as ctk
import cv2
from PIL import Image, ImageDraw, ImageTk
import threading
from deepface import DeepFace
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # self.title("Camera Preview")
        self.geometry("1024x600")
        self.overrideredirect(True)
        self.configure(fg_color="#172121")
        self.resizable(False, False)

        self.preview_width = 877
        self.preview_height = 566
        self.window_height = 600

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.place(
            x=20, y=(self.window_height - self.preview_height) // 2)

        self.countdown_label = ctk.CTkLabel(
            self,
            text="",
            text_color="white",
            font=ctk.CTkFont(size=50, weight="bold"),
            bg_color="transparent"
        )
        self.countdown_label.place(relx=0.935, rely=0.85, anchor="center")

        self.update_frame()

        self.create_circle_button()
        self.create_quit_button()

        self.analysis_layer = ctk.CTkFrame(
            self, width=1024, height=600, fg_color="#172121", corner_radius=0)
        self.analysis_label = ctk.CTkLabel(
            self.analysis_layer,
            text="",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        self.analysis_label.place(relx=0.5, rely=0.5, anchor="center")
        self.analysis_layer.place_forget()
        self.animate_analysis = False
        self.create_reset_button()
        self.playback_controls_frame = None
        self.playback_buttons = {}
        self.current_track_index = 0
        self.album_image = None
        self.album_image_label = None
        self.album_photo = None
        self.rotation_angle = 0
        self.is_rotating = False
        self.track_buttons = []
        self.current_track_index = -1  # opsional untuk melacak lagu sekarang
        self.captured_image_label = None
        self.captured_image = None

    def create_circle_button(self):
        button_size = 100
        canvas = ctk.CTkCanvas(
            self, width=button_size, height=button_size, highlightthickness=0, bg="#172121")
        y_center = (600 - button_size) // 2
        canvas.place(x=910, y=y_center)

        outer_color = "#BFACB5"
        inner_color = "#E5D0CC"
        canvas.create_oval(5, 5, button_size-5, button_size-5,
                           fill=outer_color, outline=outer_color)
        canvas.create_oval(15, 15, button_size-15, button_size -
                           15, fill=inner_color, outline=inner_color)

        try:
            icon = Image.open(
                "icons/Camera.png").resize((40, 40), Image.LANCZOS)
            self.icon_image = ImageTk.PhotoImage(icon)
            canvas.create_image(button_size//2, button_size //
                                2, image=self.icon_image)
        except Exception as e:
            print("Gagal memuat ikon:", e)

        canvas.bind("<Button-1>", lambda e: self.on_circle_button_click())

    def create_quit_button(self):
        button_size = 80
        spacing = 130
        main_button_size = 100
        main_button_x = 910
        main_button_y = (600 - main_button_size) // 2
        x_position = main_button_x + (main_button_size - button_size) // 2
        y_position = main_button_y - button_size - spacing

        canvas = ctk.CTkCanvas(
            self, width=button_size, height=button_size, highlightthickness=0, bg="#172121")
        canvas.place(x=x_position, y=y_position)

        outer_color = "#BFACB5"
        inner_color = "#E5D0CC"
        canvas.create_oval(5, 5, button_size-5, button_size-5,
                           fill=outer_color, outline=outer_color)
        canvas.create_oval(15, 15, button_size-15, button_size -
                           15, fill=inner_color, outline=inner_color)

        try:
            icon = Image.open("icons/X.png").resize((36, 36), Image.LANCZOS)
            self.quit_icon_image = ImageTk.PhotoImage(icon)
            canvas.create_image(button_size//2, button_size //
                                2, image=self.quit_icon_image)
        except Exception as e:
            print("Gagal memuat ikon untuk tombol quit:", e)

        canvas.bind("<Button-1>", lambda e: self.on_closing())

    def on_circle_button_click(self):
        self.start_countdown(3)

    def start_countdown(self, count=3):
        self.countdown_label.configure(text=str(count))
        if count > 0:
            self.after(1000, self.start_countdown, count - 1)
        else:
            self.countdown_label.configure(text="")
            self.show_analysis_layer()

    def show_analysis_layer(self):
        self.analysis_layer.place(relx=0.5, rely=0.5, anchor="center")
        self.animate_analysis = True
        self.animate_analysis_text(0)
        threading.Thread(target=self.analyze_emotion, daemon=True).start()

    def animate_analysis_text(self, step):
        if self.animate_analysis:
            dots = "." * (step % 4)
            self.analysis_label.configure(
                text=f"Sedang menganalisa emosi anda{dots}")
            self.after(500, lambda: self.animate_analysis_text(step + 1))

    def analyze_emotion(self):
        ret, frame = self.cap.read()
        if not ret:
            self.schedule_result_update("Gagal mengambil gambar.")
            return
        try:
            # Simpan gambar untuk ditampilkan nanti
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Analisa emosi
            result = DeepFace.analyze(
                rgb_frame, actions=['emotion'], enforce_detection=True)

            # Jika tidak error, artinya wajah terdeteksi
            self.captured_face_image = Image.fromarray(rgb_frame)
            image = Image.fromarray(rgb_frame)
            image = image.resize((250, 250))
            self.captured_image = ImageTk.PhotoImage(image)

            emotion = result[0]['dominant_emotion'].capitalize()

            # Rekomendasi lagu
            self.recommended_songs = self.recommend_songs(emotion)

            # Jadwalkan update UI dengan hasil emosi dan gambar
            self.schedule_result_update(f"Emosi Anda: \n" + emotion)
        except ValueError as e:
            # DeepFace throws ValueError when face is not detected
            self.schedule_result_update(
                "Maaf, wajah Anda tidak bisa dianalisa.")
        except Exception as e:
            self.schedule_result_update(f"Analisis gagal: {str(e)}")

    def display_album_cover(self, track_uri):
        try:
            track_id = track_uri.split(":")[-1]
            track_info = sp.track(track_id)
            album_cover_url = track_info['album']['images'][0]['url']

            # Ambil gambar dari URL
            image_bytes = urlopen(album_cover_url).read()
            image_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(image_stream).convert("RGBA")

            # Resize menjadi persegi untuk cover album
            pil_image = pil_image.resize((250, 250))

            # Buat mask lingkaran
            mask = Image.new('L', pil_image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse(
                (0, 0, pil_image.size[0], pil_image.size[1]), fill=255)

            # Terapkan mask ke gambar (jadi lingkaran)
            pil_image.putalpha(mask)

            # Simpan untuk rotasi nanti
            self.album_image = pil_image
            self.album_photo = ImageTk.PhotoImage(pil_image)

            # Tambahkan label kecil seperti piringan hitam di tengah
            center = (pil_image.size[0] // 2, pil_image.size[1] // 2)
            draw = ImageDraw.Draw(pil_image)
            draw.ellipse(
                (center[0]-15, center[1]-15, center[0]+15, center[1]+15),
                fill=(30, 30, 30, 255)  # warna abu tua / hitam
            )

            # Tampilkan dalam label
            if self.album_image_label is None:
                self.album_image_label = ctk.CTkLabel(
                    self.analysis_layer, image=self.album_photo, text="")
                self.album_image_label.place(
                    relx=0.185, rely=0.37, anchor="center")
            else:
                self.album_image_label.configure(image=self.album_photo)
                self.album_image_label.image = self.album_photo

            # Mulai rotasi
            self.is_rotating = True
            self.rotate_album_cover()

        except Exception as e:
            print("Gagal menampilkan cover album:", e)

    def rotate_album_cover(self):
        if not self.is_rotating or self.album_image is None:
            return

        self.rotation_angle = (self.rotation_angle + 2) % 360
        rotated_img = self.album_image.rotate(
            self.rotation_angle, resample=Image.BICUBIC)

        self.album_photo = ImageTk.PhotoImage(rotated_img)
        self.album_image_label.configure(image=self.album_photo)
        self.album_image_label.image = self.album_photo

        self.after(50, self.rotate_album_cover)  # ulangi animasi setiap 50ms

    def stop_album_rotation(self):
        self.is_rotating = False

    def update_analysis_result(self, text):
        self.animate_analysis = False
        self.analysis_label.configure(text=text)
        if text == "Maaf, wajah Anda tidak bisa dianalisa.":
            self.reset_button.place(relx=0.5, rely=0.6, anchor="center")
            return

        # Tampilkan gambar yang di-capture
        if hasattr(self, 'captured_face_image'):
            original = self.captured_face_image

            # Crop tengah menjadi persegi
            width, height = original.size
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            right = (width + min_dim) // 2
            bottom = (height + min_dim) // 2
            cropped = original.crop((left, top, right, bottom))

            # Resize ke ukuran yang pas (misal: 200x200)
            resized = cropped.resize((170, 170), Image.LANCZOS)
            self.face_photo = ImageTk.PhotoImage(resized)

            # Tampilkan di sisi kanan layer analisis
            face_label = ctk.CTkLabel(
                self.analysis_layer, image=self.face_photo, text="")
            face_label.place(relx=0.895, rely=0.195, anchor="center")

        # Tampilkan maksimal 5 rekomendasi lagu dengan layout yang lebih bagus
        self.track_buttons = []
        # Batasi rekomendasi hanya 5 lagu
        songs_to_show = self.recommended_songs[:5]

        # Posisi awal untuk lagu pertama
        y_position = 0.4
        frame_width = 400
        base_frame_height = 50  # Base height for single line
        vertical_spacing = 0.1  # Spacing between song frames

        for i, (song, uri) in enumerate(songs_to_show):
            # Determine if we need one or two lines
            display_text = f"{i+1}. {song}"

            # Check if text is long and needs two lines
            if len(display_text) > 45:
                # Split text with newline for two lines
                display_text = f"{i+1}. {song[:22]}...\n{song[22:45]}..."
                frame_height = base_frame_height + 30  # Taller frame for two lines
            else:
                frame_height = base_frame_height  # Standard height for one line

            # Buat frame untuk setiap lagu dengan ukuran yang disesuaikan
            song_frame = ctk.CTkFrame(
                self.analysis_layer,
                fg_color="#2E2E2E",
                corner_radius=10,
                width=frame_width,
                height=frame_height
            )
            song_frame.place(relx=0.74, rely=y_position, anchor="center")
            # Prevent internal widgets from changing frame size
            song_frame.pack_propagate(False)

            # Create a single button for the entire song entry
            song_button = ctk.CTkButton(
                song_frame,
                text=display_text,
                font=ctk.CTkFont(size=16),
                text_color="white",
                fg_color="#2E2E2E",          # match parent frame color
                hover_color="#3C3C3C",       # slightly lighter when hovering
                anchor="w",                  # left-align text
                corner_radius=5,
                height=frame_height-4,      # Adjust button height to match frame
                width=frame_width-10,
                command=lambda uri=uri, idx=i: self.play_track(uri, idx)
            )
            song_button.place(relx=0.5, rely=0.5, anchor="center")

            # Store reference to the button for highlighting
            self.track_buttons.append(song_button)

            # Update position for next song, accounting for variable height
            y_position += vertical_spacing + \
                (0.02 if frame_height > base_frame_height else 0)

        # Tampilkan kontrol playback Spotify
        self.show_playback_controls()

        self.reset_button.place(relx=0.5, rely=0.9, anchor="center")

    def schedule_result_update(self, text):
        # Tunda update hasil selama 3 detik agar animasi tetap jalan sebentar
        self.after(2000, lambda: self.update_analysis_result(text))

    def recommend_songs(self, emotion):
        genres = EMOTION_GENRE_MAP.get(emotion.lower(), ["pop"])
        genre = random.choice(genres)
        try:
            results = sp.search(q=f'genre:"{genre}"', type='track', limit=10)
            tracks = results['tracks']['items']
            random.shuffle(tracks)
            recommendations = []
            for track in tracks:
                track_name = track['name']
                artists = ", ".join(artist['name']
                                    for artist in track['artists'])
                uri = track['uri']
                recommendations.append((f"{track_name} - {artists}", uri))
            return recommendations
        except Exception as e:
            print("❌ Gagal mendapatkan rekomendasi lagu:", e)
            return []

    def create_reset_button(self):
        self.reset_button = ctk.CTkButton(
            self.analysis_layer,
            text="Reset",
            command=self.reset_to_main_layer,
            width=120,
            height=40,
            fg_color="#E26D5C",
            hover_color="#B2453C",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.reset_button.place(relx=0.5, rely=0.65, anchor="center")
        self.reset_button.place_forget()  # Sembunyikan dulu

    def create_track_buttons(self, track_data):
        for i, (track_name, artist, uri) in enumerate(track_data):
            button_text = f"{i+1}{track_name.upper()}"
            button = ctk.CTkButton(
                self.analysis_layer,
                text=button_text,
                font=ctk.CTkFont(size=16, weight="bold"),
                width=300,
                height=40,
                corner_radius=20,
                fg_color="#2E2E2E",         # warna dasar tombol
                hover_color="#3C3C3C",      # warna saat hover
                text_color="#FFFFFF",       # warna teks
                anchor="w",                 # teks rata kiri
                command=lambda u=uri, idx=i: self.play_track(u, idx),
            )
            button.grid(row=i+1, column=0, pady=5, padx=20, sticky="ew")
            self.track_buttons.append(button)

    def play_track(self, uri, index):
        try:
            sp.start_playback(uris=[uri])

            # Update the current track index
            self.current_track_index = index

            # Remove any existing "Now Playing" label
            if hasattr(self, 'now_playing_label') and self.now_playing_label:
                self.now_playing_label.destroy()

            # Get song name from button text
            current_text = self.track_buttons[index].cget("text")
            song_title = current_text
            if song_title.startswith(f"{index+1}. "):
                song_title = song_title[len(f"{index+1}. "):]

            # Create "Now Playing" label above playback controls
            self.now_playing_label = ctk.CTkLabel(
                self.analysis_layer,
                text=f"Now Playing:\n{song_title}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="white",
                fg_color="transparent"
            )
            self.now_playing_label.place(relx=0.18, rely=0.7, anchor="center")

            # Reset all button texts to original (no indicators)
            for button in self.track_buttons:
                # Remove any highlight or special formatting
                button.configure(fg_color="#2E2E2E", border_width=0)

            self.stop_album_rotation()
            self.display_album_cover(uri)
        except Exception as e:
            print("Gagal memutar lagu:", e)

    def show_playback_controls(self):
        if self.playback_controls_frame:
            self.playback_controls_frame.destroy()

        self.playback_controls_frame = ctk.CTkFrame(
            self.analysis_layer,
            fg_color="transparent"
        )
        self.playback_controls_frame.place(
            relx=0.18, rely=0.8, anchor="center")

        # Tombol-tombol kontrol
        controls = {
            "prev": ("icons/prev.png", self.previous_track),
            "play": ("icons/play.png", self.resume_playback),
            "pause": ("icons/pause.png", self.pause_playback),
            "next": ("icons/next.png", self.next_track)
        }

        col = 0
        for key, (icon_path, command) in controls.items():
            try:
                icon = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
                icon_image = ImageTk.PhotoImage(icon)
                button = ctk.CTkButton(
                    self.playback_controls_frame,
                    text="",
                    image=icon_image,
                    command=command,
                    width=50,
                    height=50,
                    fg_color="#2C2C2C",
                    hover_color="#404040"
                )
                button.image = icon_image  # Simpan agar tidak garbage collected
                button.grid(row=0, column=col, padx=10)
                self.playback_buttons[key] = button
            except Exception as e:
                print(f"Gagal memuat ikon {key}: {e}")
            col += 1

    # Kontrol playback Spotify
    def pause_playback(self):
        try:
            sp.pause_playback()
            self.stop_album_rotation()  # Hapus cover album saat pause
        except Exception as e:
            print("Gagal pause:", e)

    def resume_playback(self):
        try:
            sp.start_playback()
            if not self.is_rotating:
                self.is_rotating = True
                self.rotate_album_cover()
        except Exception as e:
            print("Gagal memutar lagu:", e)

    def next_track(self):
        if not self.recommended_songs:
            return

        self.current_track_index += 1
        if self.current_track_index >= len(self.recommended_songs):
            self.current_track_index = 0

        song_name, uri = self.recommended_songs[self.current_track_index]
        self.play_track(uri, self.current_track_index)

    def previous_track(self):
        if not self.recommended_songs:
            return

        self.current_track_index -= 1
        if self.current_track_index < 0:
            self.current_track_index = len(self.recommended_songs) - 1

        song_name, uri = self.recommended_songs[self.current_track_index]
        self.play_track(uri, self.current_track_index)

    def reset_to_main_layer(self):
        # Pause playback if active
        try:
            sp.pause_playback()
        except:
            pass

        # Sembunyikan layer analisis dan tombol reset
        self.analysis_layer.place_forget()
        self.reset_button.place_forget()

        # Hentikan rotasi album
        self.stop_album_rotation()

        # Hapus semua widgets yang terkait dengan hasil analisis
        if self.album_image_label:
            self.album_image_label.destroy()
            self.album_image_label = None

        if self.playback_controls_frame:
            self.playback_controls_frame.destroy()
            self.playback_controls_frame = None
            self.playback_buttons = {}

        # Hapus label lagu yang sudah ditampilkan
        for widget in self.analysis_layer.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget != self.analysis_label:
                widget.destroy()
            elif isinstance(widget, ctk.CTkFrame):
                widget.destroy()

        # Reset variabel terkait analisis dan rekomendasi
        self.recommended_songs = []
        self.current_track_index = -1
        self.album_image = None
        self.album_photo = None
        self.rotation_angle = 0
        self.is_rotating = False
        self.track_buttons = []

        if hasattr(self, 'captured_face_image'):
            del self.captured_face_image
        if hasattr(self, 'face_photo'):
            del self.face_photo
        if hasattr(self, 'now_playing_label') and self.now_playing_label:
            self.now_playing_label.destroy()
            self.now_playing_label = None

        self.captured_image_label = None
        self.captured_image = None
        self.analysis_label.configure(text="")  # Kosongkan teks analisis

    def rounded_image(self, pil_img, radius=50):
        mask = Image.new("L", pil_img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + pil_img.size, radius, fill=255)
        result = pil_img.convert("RGBA")
        result.putalpha(mask)
        return result

    def crop_to_fit(self, img, target_width, target_height):
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            new_width = int(img.height * target_ratio)
            offset = (img.width - new_width) // 2
            img = img.crop((offset, 0, offset + new_width, img.height))
        else:
            new_height = int(img.width / target_ratio)
            offset = (img.height - new_height) // 2
            img = img.crop((0, offset, img.width, offset + new_height))

        return img.resize((target_width, target_height), Image.LANCZOS)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = self.crop_to_fit(
                img, self.preview_width, self.preview_height)
            img = self.rounded_image(img, radius=50)

            ctk_img = ctk.CTkImage(light_image=img, size=(
                self.preview_width, self.preview_height))
            self.video_label.configure(image=ctk_img)
            self.video_label.image = ctk_img

        self.after(20, self.update_frame)

    def on_closing(self):
        self.cap.release()
        self.destroy()


app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()
