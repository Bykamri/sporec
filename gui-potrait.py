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
from datetime import datetime
from PIL import ImageDraw, ImageFont
import numpy as np
import time

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
        self.geometry("600x1024")
        self.overrideredirect(False)
        self.configure(fg_color="#172121")
        self.resizable(False, False)

        # Tambahkan variabel throttling untuk update_frame
        self._last_frame_update = time.time()
        self._frame_interval = 1/60  # 30 FPS target
        # Tambahkan cache mask untuk fungsi rounded_image
        self._mask_cache = {}
        self.preview_width = 566
        self.preview_height = 877
        self.window_height = 1024

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.place(
            x=16, y=(self.window_height - self.preview_height) // 8)

        self.countdown_label = ctk.CTkLabel(
            self,
            text="",
            text_color="white",
            font=ctk.CTkFont(size=50, weight="bold"),
            bg_color="transparent"
        )
        self.countdown_label.place(relx=0.18, rely=0.937, anchor="center")

        self.update_frame()

        self.create_circle_button()
        self.create_quit_button()

        self.analysis_layer = ctk.CTkFrame(
            self, width=600, height=1024, fg_color="#172121", corner_radius=0)
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
        self.recommended_songs = []  # Tambahkan ini di awal
        self.current_track_index = -1

    def create_circle_button(self):
        button_size = 100
        canvas = ctk.CTkCanvas(
            self, width=button_size, height=button_size, highlightthickness=0, bg="#172121")
        x_center = (600 - button_size) // 2
        y_bottom = (1024 - button_size) - 13
        canvas.place(x=x_center, y=y_bottom)

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
        main_button_y = (1024 - main_button_size) - 13
        main_button_x = (600 - main_button_size) // 2
        y_position = main_button_y + (main_button_size - button_size) - 13
        x_position = main_button_x + spacing + button_size

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

    def create_reset_button(self):
        try:
            # Load the camera icon
            camera_icon = Image.open(
                "icons/loader-pinwheel.png").resize((24, 24), Image.LANCZOS)
            self.camera_icon_image = ImageTk.PhotoImage(camera_icon)

            # Create button with icon and new text
            self.reset_button = ctk.CTkButton(
                self.analysis_layer,
                text="Ambil Foto",
                image=self.camera_icon_image,  # Add the camera icon
                compound="left",               # Position icon to the left of text
                command=self.reset_to_main_layer,
                width=140,                     # Increased width to fit text and icon
                height=40,
                fg_color="#2C2C2C",           # Changed from red to dark gray
                hover_color="#404040",         # Dark gray hover color
                font=ctk.CTkFont(size=16, weight="bold"),
                corner_radius=10               # Rounded corners
            )
        except Exception as e:
            print(f"Failed to load camera icon: {e}")
            # Fallback without icon
            self.reset_button = ctk.CTkButton(
                self.analysis_layer,
                text="Ambil Foto",
                command=self.reset_to_main_layer,
                width=140,
                height=40,
                fg_color="#2C2C2C",
                hover_color="#404040",
                font=ctk.CTkFont(size=16, weight="bold"),
                corner_radius=10
            )

        # Initially hidden
        self.reset_button.place(relx=0.5, rely=0.9, anchor="center")
        self.reset_button.place_forget()

    def create_track_buttons(self, track_data):
        # Clear any existing buttons
        for button in self.track_buttons:
            button.destroy()
        self.track_buttons = []

        for i, (track_name, artist, uri) in enumerate(track_data):
            # Create a frame to hold each button
            frame = ctk.CTkFrame(
                self.analysis_layer,
                fg_color="transparent"  # Make frame invisible
            )
            frame.grid(row=i+1, column=0, pady=10, padx=20, sticky="ew")

            # Check if title has more than 3 words
            title_words = track_name.split()

            if len(title_words) > 3:
                # For titles with more than 3 words, place artist on next line
                button_text = f"{i+1}. {track_name}\n - {artist}"
            else:
                # For shorter titles, keep artist on same line
                button_text = f"{i+1}. {track_name} - {artist}"

            # Calculate display width
            max_width = 38  # Characters per line, adjust as needed

            # Improved word-based text wrapping if text is still too long
            lines = []
            for line in button_text.split('\n'):
                words = line.split()
                current_line = ""

                for word in words:
                    # Check if adding this word would exceed the max width
                    test_line = current_line + \
                        (" " if current_line else "") + word
                    if len(test_line) > max_width and current_line:
                        # Add current line to lines and start a new one
                        lines.append(current_line)
                        # If this is a continuation line, add some indentation
                        if not current_line.strip().startswith(f"{i+1}."):
                            current_line = "    " + word
                        else:
                            current_line = word
                    else:
                        # Add word to current line
                        current_line = test_line

                # Add the last line if it's not empty
                if current_line:
                    lines.append(current_line)

            # Join lines with newline character
            button_text = "\n".join(lines)

            # Calculate height based on number of lines
            base_height = 45  # Base height for single line
            line_height = 20  # Additional height per line
            num_lines = len(lines)
            button_height = base_height + (num_lines - 1) * line_height

            # Create button within the frame
            button = ctk.CTkButton(
                frame,
                text=button_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=300,
                height=button_height,
                corner_radius=10,
                fg_color="#2E2E2E",
                hover_color="#3C3C3C",
                text_color="#FFFFFF",
                anchor="w",
                command=lambda u=uri, idx=i: self.play_track(u, idx),
            )
            button.pack(fill="both", expand=True)
            self.track_buttons.append(button)

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

    def rounded_image(self, pil_img, radius=50):
        # Gunakan cache untuk mask
        cache_key = (pil_img.width, pil_img.height, radius)

        if cache_key not in self._mask_cache:
            # Buat mask baru hanya jika diperlukan
            mask = Image.new("L", pil_img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0) + pil_img.size, radius, fill=255)
            self._mask_cache[cache_key] = mask
        else:
            mask = self._mask_cache[cache_key]

        # Aplikasikan mask
        result = pil_img.convert("RGBA")
        result.putalpha(mask)
        return result

    def update_frame(self):
        # Batasi framerate dengan throttling sederhana
        current_time = time.time()
        if current_time - self._last_frame_update < self._frame_interval:
            self.after(5, self.update_frame)  # Cek lagi dalam 5ms
            return

        # Update frame hanya jika interval tercapai
        self._last_frame_update = current_time

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

        # Tetap responsif dengan interval pendek
        self.after(10, self.update_frame)

    def on_circle_button_click(self):
        self.start_countdown(3)

    def on_closing(self):
        self.cap.release()
        self.destroy()

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

        # Add force close button
        self.force_close_button = ctk.CTkButton(
            self.analysis_layer,
            text="X",
            command=self.on_closing,
            width=40,
            height=40,
            fg_color="#E26D5C",
            hover_color="#B2453C",
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=20
        )
        self.force_close_button.place(relx=0.975, rely=0.03, anchor="ne")

        threading.Thread(target=self.analyze_emotion, daemon=True).start()

    def analyze_emotion(self):
        # Capture gambar hanya sekali
        ret, frame = self.cap.read()
        if not ret:
            self.schedule_result_update("Gagal mengambil gambar.")
            return

        try:
            # Convert ke RGB sekali
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Pre-process frame sebelum analisis
            # Kecilkan ukuran untuk kecepatan
            processed_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

            # Analisa emosi dengan frame yang lebih kecil untuk performa
            result = DeepFace.analyze(processed_frame, actions=[
                                      'emotion'])

            # Simpan original frame untuk tampilan
            self.captured_face_image = Image.fromarray(rgb_frame)

            # Resize image sekali saja dan simpan
            image = self.captured_face_image.copy()
            image = image.resize((250, 250), Image.LANCZOS)
            self.captured_image = ImageTk.PhotoImage(image)

            # Dapatkan emosi
            emotion = result[0]['dominant_emotion'].capitalize()

            # Format text sekali
            result_text = f"Emosi Anda: \n{emotion}"

            # Dispatch tugas-tugas berat ke thread terpisah
            threading.Thread(
                target=self.recommend_songs_and_save,
                args=(emotion, result_text),
                daemon=True
            ).start()

            # Update UI dengan hasil awal
            self.schedule_result_update(result_text)
        except ValueError as e:
            self.schedule_result_update(
                "Maaf, wajah Anda tidak bisa dianalisa.")
        except Exception as e:
            self.schedule_result_update(f"Analisis gagal: {str(e)}")

    # Tambahkan fungsi helper untuk memisahkan pekerjaan berat
    def recommend_songs_and_save(self, emotion, result_text):
        # Cari rekomendasi lagu (API call berat)
        self.recommended_songs = self.recommend_songs(emotion)

        # Simpan hasil analisis (disk I/O berat)
        self.save_analysis_results(result_text)

    def animate_analysis_text(self, step):
        if self.animate_analysis:
            dots = "." * (step % 4)
            self.analysis_label.configure(
                text=f"Sedang menganalisa emosi anda{dots}")
            # Make sure animation text stays centered
            self.analysis_label.place(relx=0.5, rely=0.5, anchor="center")
            self.after(500, lambda: self.animate_analysis_text(step + 1))

    def schedule_result_update(self, text):
        # Tunda update hasil selama 3 detik agar animasi tetap jalan sebentar
        self.after(2000, lambda: self.update_analysis_result(text))

    def update_analysis_result(self, text):
        self.animate_analysis = False

        # Clear previous text
        self.analysis_label.configure(text="")

        # Split text if it contains a result
        if "Emosi Anda: \n" in text:
            # Create or update title label
            if not hasattr(self, 'emotion_title_label'):
                self.emotion_title_label = ctk.CTkLabel(
                    self.analysis_layer,
                    text="Emosi Anda:",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color="#E5D0CC",  # Light color for title
                    anchor="w"  # Left-align the text
                )

            # Move the title to the top-left portion
            self.emotion_title_label.place(
                relx=0.15, rely=0.05, anchor="w")  # Changed from center to west anchor

            # Extract and display the emotion result in a separate label
            emotion_result = text.split("\n")[1]

            # Create or update result label
            if not hasattr(self, 'emotion_result_label'):
                self.emotion_result_label = ctk.CTkLabel(
                    self.analysis_layer,
                    text=emotion_result,
                    font=ctk.CTkFont(size=42, weight="bold"),
                    text_color="white",
                    anchor="w"  # Left-align the text
                )
            else:
                self.emotion_result_label.configure(text=emotion_result)

            # Position the result below the title, also left-aligned
            self.emotion_result_label.place(
                relx=0.15, rely=0.1, anchor="w")  # Changed from center to west anchor
        else:
            # For error messages or other text, use the original label
            self.analysis_label.configure(text=text)
            self.analysis_label.place(relx=0.5, rely=0.08, anchor="center")

        if text == "Maaf, wajah Anda tidak bisa dianalisa.":
            # Keep error message centered
            self.analysis_label.configure(text=text)
            self.analysis_label.place(relx=0.5, rely=0.5, anchor="center")
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
            resized = cropped.resize((220, 220), Image.LANCZOS)
            self.face_photo = ImageTk.PhotoImage(resized)

            # Tampilkan di sisi kanan layer analisis
            face_label = ctk.CTkLabel(
                self.analysis_layer, image=self.face_photo, text="")
            face_label.place(relx=0.69, rely=0.12, anchor="center")

            # Tampilkan maksimal 5 rekomendasi lagu dengan layout yang lebih bagus
        self.track_buttons = []
        # Batasi rekomendasi hanya 5 lagu
        songs_to_show = self.recommended_songs[:5]

        # Posisi awal untuk lagu pertama
        y_position = 0.28
        frame_width = 400
        base_frame_height = 50  # Base height for single line
        vertical_spacing = 0.07  # Spacing between song frames

        for i, (song, uri) in enumerate(songs_to_show):
            # Determine if we need one or two lines
            display_text = f"{i+1}. {song}"

            # Check if text is long and needs truncating or multiple lines
            max_line_length = 45  # Maximum characters per line

            if len(display_text) > max_line_length:
                # Split into two lines with proper truncation
                first_line = display_text[:max_line_length]
                second_line = display_text[max_line_length:max_line_length*2]

                # Add ellipsis if text is too long
                if len(display_text) > max_line_length*2:
                    second_line = second_line + "..."

                display_text = f"{first_line}\n{second_line}"
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
            song_frame.place(relx=0.5, rely=y_position, anchor="center")
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

            # Update position for next song, ensuring proper spacing between items
            y_spacing = vertical_spacing + \
                (0.01 if frame_height > base_frame_height else 0)
            y_position += y_spacing
            # Make sure force close button remains in its position
        if hasattr(self, 'force_close_button'):
            self.force_close_button.destroy()

        # Tampilkan kontrol playback Spotify
        self.show_playback_controls()

        self.reset_button.place(relx=0.15, rely=0.16, anchor="w")

    def save_analysis_results(self, emotion_text=None):
        """Silently save the captured face image with emotion analysis results and face frame"""
        try:
            # Create a directory to store captured images if it doesn't exist
            save_dir = "captured_emotions"
            os.makedirs(save_dir, exist_ok=True)

            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if hasattr(self, 'captured_face_image') and self.captured_face_image:
                # Create a copy of the image to add text and frame
                img_with_text = self.captured_face_image.copy()

                # Convert PIL Image to OpenCV format for face detection
                opencv_image = np.array(img_with_text)
                opencv_image = opencv_image[:, :, ::-1].copy()  # RGB to BGR

                # Load face detection model
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

                # Detect faces
                gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                draw = ImageDraw.Draw(img_with_text)

                # Add emotion text and face frame if faces were detected
                if len(faces) > 0 and emotion_text and "Emosi Anda: \n" in emotion_text:
                    emotion = emotion_text.split("\n")[1]

                    # Try to find a suitable font
                    font_size = 28
                    try:
                        # Try common fonts
                        for font_name in ['arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', 'FreeSans.ttf']:
                            try:
                                font = ImageFont.truetype(font_name, font_size)
                                break
                            except:
                                continue
                    except:
                        # If no font works, use default
                        font = ImageFont.load_default()

                    for (x, y, w, h) in faces:
                        # Draw rectangle around face
                        draw.rectangle([(x, y), (x+w, y+h)],
                                       outline=(0, 255, 0), width=3)

                        # Add emotion text above the face frame
                        text = f"Emotion: {emotion}"
                        text_width = font.getsize(text)[0] if hasattr(
                            font, 'getsize') else draw.textlength(text, font)

                        # Center text above the face frame
                        text_x = x + (w - text_width) // 2
                        # Position text above frame with padding
                        text_y = max(0, y - 40)

                        # Draw background rectangle for better text visibility
                        text_bg = (text_x - 5, text_y - 5, text_x +
                                   text_width + 5, text_y + font_size + 5)
                        # Semi-transparent black
                        draw.rectangle(text_bg, fill=(0, 0, 0, 160))

                        # Add text
                        draw.text((text_x, text_y), text,
                                  fill=(255, 255, 255), font=font)

                # Save the image with timestamp in filename
                filename = f"{save_dir}/emotion_{timestamp}.jpg"
                img_with_text.save(filename)

                return filename
            return None
        except Exception as e:
            print(
                f"Error silently saving analysis results with face frame: {e}")
            return None

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

    def display_album_cover(self, track_uri):
        try:
            track_id = track_uri.split(":")[-1]
            track_info = sp.track(track_id)
            album_cover_url = track_info['album']['images'][0]['url']

            # Ambil gambar dari URL
            image_bytes = urlopen(album_cover_url).read()
            image_stream = io.BytesIO(image_bytes)
            # Resize langsung saat membuka untuk menghemat memori
            pil_image = Image.open(image_stream).resize(
                (200, 200)).convert("RGBA")

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
                (center[0]-10, center[1]-10, center[0]+10, center[1]+10),
                fill=(30, 30, 30, 255)  # warna abu tua / hitam
            )

            # Tampilkan dalam label
            if self.album_image_label is None:
                self.album_image_label = ctk.CTkLabel(
                    self.analysis_layer, image=self.album_photo, text="")
                self.album_image_label.place(
                    relx=0.5, rely=0.7, anchor="center")
            else:
                self.album_image_label.configure(image=self.album_photo)

            # Siapkan cache rotasi untuk optimasi
            self.rotation_cache = {}
            # Mulai rotasi
            self.is_rotating = True
            self.rotation_angle = 0
            self.rotate_album_cover()

        except Exception as e:
            print("Gagal menampilkan cover album:", e)

    def rotate_album_cover(self):
        if not self.is_rotating or not hasattr(self, 'album_image') or self.album_image is None:
            return

        # Kurangi frekuensi rotasi dan tingkatkan increment untuk Jetson Nano
        self.rotation_angle = (self.rotation_angle +
                               5) % 360  # Increment 5 derajat

        # Gunakan cache untuk mengurangi perhitungan
        if self.rotation_angle in self.rotation_cache:
            rotated_photo = self.rotation_cache[self.rotation_angle]
        else:
            # Gunakan NEAREST untuk kecepatan alih-alih BICUBIC
            rotated_img = self.album_image.rotate(
                self.rotation_angle, resample=Image.NEAREST)
            rotated_photo = ImageTk.PhotoImage(rotated_img)

            # Cache maksimal 36 gambar (jadi tiap 10 derajat)
            if self.rotation_angle % 10 == 0:
                self.rotation_cache[self.rotation_angle] = rotated_photo

        # Update gambar
        if hasattr(self, 'album_image_label') and self.album_image_label:
            self.album_image_label.configure(image=rotated_photo)
            self.album_image_label.image = rotated_photo

        # Interval yang lebih lambat untuk Jetson Nano (100ms alih-alih 50ms)
        self.after(100, self.rotate_album_cover)

    def stop_album_rotation(self):
        self.is_rotating = False

    def show_playback_controls(self):
        if self.playback_controls_frame:
            self.playback_controls_frame.destroy()

        self.playback_controls_frame = ctk.CTkFrame(
            self.analysis_layer,
            fg_color="transparent"
        )
        self.playback_controls_frame.place(
            relx=0.5, rely=0.95, anchor="center")

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
            if current_text.startswith(f"{index+1}. "):
                current_text = current_text[len(f"{index+1}. "):]

            # Split the song title and artist
            parts = current_text.split(" - ", 1)
            song_title = parts[0]
            artist = parts[1] if len(parts) > 1 else "Unknown Artist"

            # Create a frame to hold both labels
            self.now_playing_frame = ctk.CTkFrame(
                self.analysis_layer,
                fg_color="transparent"
            )
            self.now_playing_frame.place(relx=0.5, rely=0.86, anchor="center")

            # Create "Now Playing" header
            header_label = ctk.CTkLabel(
                self.now_playing_frame,
                text="Now Playing:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#E5D0CC",  # Light color for header
                fg_color="transparent"
            )
            header_label.pack(anchor="center")

            # Create song title label
            title_label = ctk.CTkLabel(
                self.now_playing_frame,
                text=song_title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="white",
                fg_color="transparent"
            )
            title_label.pack(anchor="center")

            # Create artist label
            artist_label = ctk.CTkLabel(
                self.now_playing_frame,
                text=artist,
                font=ctk.CTkFont(size=14),  # Smaller size for artist
                text_color="#CCCCCC",  # Slightly dimmer color
                fg_color="transparent"
            )
            artist_label.pack(anchor="center")

            # Store reference to the frame for cleanup
            self.now_playing_label = self.now_playing_frame

            # Reset all button texts to original (no indicators)
            for button in self.track_buttons:
                # Remove any highlight or special formatting
                button.configure(fg_color="#2E2E2E", border_width=0)

            self.stop_album_rotation()
            self.display_album_cover(uri)
        except Exception as e:
            print("Gagal memutar lagu:", e)
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
        if hasattr(self, 'force_close_button'):
            self.force_close_button.destroy()
        if hasattr(self, 'emotion_title_label'):
            self.emotion_title_label.destroy()
            delattr(self, 'emotion_title_label')

        if hasattr(self, 'emotion_result_label'):
            self.emotion_result_label.destroy()
            delattr(self, 'emotion_result_label')
        if hasattr(self, 'now_playing_label') and self.now_playing_label:
            self.now_playing_label.destroy()
            self.now_playing_label = None
        self.captured_image_label = None
        self.captured_image = None
        self.analysis_label.configure(text="")  # Kosongkan teks analisis


app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()
