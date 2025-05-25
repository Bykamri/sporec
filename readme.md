# Emotion-Based Music Recommendation System

This system analyzes facial emotions in real-time to recommend and play Spotify music matching your mood.

---

## Features

- Real-time facial emotion detection via your webcam.
- Music recommendations tailored to detected emotions (e.g., happy, sad, angry).
- Direct integration with Spotify for music playback.
- Multiple GUI options:
    - Basic Tkinter UI (`main.py`)
    - Enhanced CustomTkinter UI with landscape orientation (`gui-landscape.py`)
    - Enhanced CustomTkinter UI with portrait orientation (`gui-potrait.py`)
- Album art display for the currently playing track (in CustomTkinter UIs).
- In-app playback controls: play, pause, next, previous (in CustomTkinter UIs).
- Option to save captured images, including emotion analysis results and detected face frames.
- Configuration script (`spotifyd_config.py`) for the `spotifyd` daemon, facilitating headless Spotify playback.

---

## Prerequisites

1. Python 3.7 or higher.
2. A Spotify Developer account (for API credentials).
3. A webcam.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Bykamri/sporec.git
cd sporec
```

### 2. Create and Activate a Virtual Environment

Isolate project dependencies:

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Set Up a Spotify Developer Account

To use the Spotify API:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Log in or create an account.
3. Click **Create an App**. Provide a name and description.
4. After app creation, go to its settings.
5. Add a **Redirect URI**. For local development, `http://127.0.0.1:8080/callback` is a common choice. **Important:** This URI must exactly match the `SPOTIPY_REDIRECT_URI` you set in your `.env` file (see next step).
6. Note your **Client ID** and **Client Secret**.

### 5. Configure Environment Variables

Create a `.env` file in the project root to store your Spotify API credentials.

1. Copy the example file:
   ```bash
   # On Windows
   copy .env.example .env
   # On macOS/Linux
   cp .env.example .env
   ```
2. Edit the `.env` file and replace the placeholder values with your actual credentials:

   ```properties
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback # Ensure this matches your Spotify App's Redirect URI
   SPOTIFY_USERNAME=your_spotify_username_or_email # Your Spotify username or email
   SPOTIFY_PASSWORD=your_spotify_password # Your Spotify password (optional, for spotifyd_config.py)
   ```

   **Explanation of Variables:**
   - `SPOTIPY_CLIENT_ID`: Your Spotify application's Client ID.
   - `SPOTIPY_CLIENT_SECRET`: Your Spotify application's Client Secret.
   - `SPOTIPY_REDIRECT_URI`: The Redirect URI configured in your Spotify application settings. It must be an exact match.
   - `SPOTIFY_USERNAME`: Your Spotify username or the email associated with your Spotify account.
   - `SPOTIFY_PASSWORD`: Your Spotify password. This is primarily used by the `spotifyd_config.py` script if you choose to configure `spotifyd`.

### 6. Configuring `spotifyd` (Optional)

The `spotifyd_config.py` script helps generate a configuration file (`spotifyd.conf`) for `spotifyd`, a lightweight, open-source Spotify client that runs as a background service (daemon). This is useful for headless setups (e.g., Raspberry Pi, Jetson Nano) or if you prefer not running the full Spotify desktop application.

To use the script:

1.  Ensure your Spotify credentials (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIFY_USERNAME`, `SPOTIFY_PASSWORD`) are correctly set in your `.env` file.
2.  Run the configuration script:
    ```bash
    python spotifyd_config.py
    ```
3.  The script attempts to generate `spotifyd.conf` in the default system directory for `spotifyd` (e.g., `~/.config/spotifyd/spotifyd.conf` on Linux/macOS).

**Note:** This script only creates the configuration file. `spotifyd` must be installed and running separately. Refer to the official `spotifyd` documentation for installation and usage.

---

## Running the Program

This project offers multiple graphical user interfaces:

### 1. Basic UI (Tkinter)

-   **Command:** `python main.py`
-   **Description:** A simple interface for core emotion detection and music playback.

### 2. Enhanced UI - Landscape (CustomTkinter)

-   **Command:** `python gui-landscape.py`
-   **Description:** A richer interface with album art, advanced playback controls, and a landscape layout (1024x600). Recommended for most desktop experiences.

### 3. Enhanced UI - Portrait (CustomTkinter)

-   **Command:** `python gui-potrait.py`
-   **Description:** Similar to the landscape UI but adapted for a portrait layout (600x1024). Suitable for specific screen orientations.

### 4. Quitting the Program

To quit, press the **X** button in the GUI's top corner or press the `Q` key on your keyboard.

---

## Troubleshooting

Common issues and solutions:

-   **Webcam Not Detected / No Camera Feed:**
    -   Ensure the webcam is properly connected.
    -   Verify no other application is using the webcam.
    -   Check system camera permissions for applications.
    -   If you have multiple cameras, you might need to change the camera index (e.g., `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`) in the relevant Python script.

-   **Spotify Authentication Errors / Playback Issues:**
    -   Double-check `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` in your `.env` file.
    -   Confirm `SPOTIPY_REDIRECT_URI` in `.env` *exactly* matches the URI in your Spotify Developer Dashboard.
    -   A Spotify Premium account is recommended for full API access and uninterrupted playback.
    -   If using `spotifyd`: ensure it's correctly configured (via `spotifyd_config.py`) and running. Check `spotifyd` logs for errors.
    -   Ensure an active Spotify device is selected. You might need to play a song manually on a device (e.g., Spotify desktop app, web player, `spotifyd` instance) for Spotify to recognize it.

-   **Emotion Detection Inaccurate or "Not Detected":**
    -   Ensure good lighting and clear face visibility, without obstructions.
    -   A relatively neutral background can improve detection.
    -   Emotion detection accuracy varies. `DeepFace` may misinterpret or fail to detect emotions in challenging lighting, with partial visibility, or at extreme angles.
    -   `gui-landscape.py` and `gui-potrait.py` use `enforce_detection=True` for `DeepFace.analyze` (within their `analyze_emotion` functions). If a face isn't confidently detected, it may not return an emotion.
    -   `main.py` uses `enforce_detection=False`. It might attempt emotion classification even if a face isn't strongly detected, potentially leading to less reliable results or errors if no face is found.

-   **Python Dependency Installation Issues:**
    -   Ensure you're using Python 3.7+.
    -   Try upgrading `pip`: `python -m pip install --upgrade pip`.
    -   If a package fails, try installing it individually (e.g., `pip install opencv-python`). Some packages might need system-level dependencies (e.g., `opencv-python` may require certain C++ libraries/build tools). Check the package's documentation.

-   **CustomTkinter Issues (for `gui-landscape.py` / `gui-potrait.py`):**
    -   Ensure `customtkinter` is installed (`pip install customtkinter`).
    -   Some Linux desktop environments might need additional libraries (e.g., X11 development libraries) for `customtkinter` to render correctly. Consult `customtkinter` documentation or GitHub issues.

---

## Contributing

Contributions are welcome! For improvements or bug fixes:

1.  **Fork the repository.**
2.  **Create a new branch:**
    ```bash
    # For features
    git checkout -b feature/your-feature-name
    # For bug fixes
    git checkout -b bugfix/issue-number
    ```
3.  **Make your changes.** Adhere to project style and test thoroughly.
4.  **Commit your changes** with a clear message:
    ```bash
    git commit -m "Add: New feature that does X"
    # or
    git commit -m "Fix: Resolved issue Y by doing Z"
    ```
5.  **Push to your forked repository:**
    ```bash
    git push origin feature/your-feature-name
    ```
6.  **Open a Pull Request** to the main repository, detailing your changes.

Please discuss new features or significant changes in an issue first.

---

## Technologies Used

-   **Python:** Core programming language.
-   **Tkinter:** Standard Python GUI toolkit (for `main.py`).
-   **CustomTkinter:** Modern themed Tkinter extension (for `gui-landscape.py`, `gui-potrait.py`).
-   **OpenCV (`cv2`):** For webcam access, video capture, and image processing.
-   **DeepFace:** For facial attribute analysis, including emotion detection.
-   **Spotipy:** Python library for the Spotify Web API.
-   **Pillow (PIL Fork):** For image manipulation (e.g., album art).
-   **python-dotenv:** For managing environment variables from a `.env` file.

---

## Notes

- Ensure your webcam is connected and accessible.
- The application saves emotion analysis results (images with detected faces and emotions) in the `emotion_analysis_results/` folder.
- For Spotify playback issues, confirm your Spotify account is active and logged in on a device.

Enjoy using the Emotion-Based Music Recommendation System!

