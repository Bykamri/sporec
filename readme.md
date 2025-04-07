# Emotion-Based Music Recommendation System

This project uses facial emotion analysis to recommend music tracks based on the detected emotion. It integrates with Spotify's API to fetch and play songs.

---

## Prerequisites

1. Python 3.7 or higher installed on your system.
2. A Spotify Developer account to get the required API credentials.
3. A webcam for emotion detection.

---

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/Bykamri/sporec.git
cd sporec
```

### 2. Create a Virtual Environment

Create and activate a virtual environment to isolate dependencies:

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Set Up a Spotify Developer Account

To use Spotify's API, you need to set up a developer account and create an app:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Log in with your Spotify account or create a new one.
3. Click **Create an App** and provide a name and description for your app.
4. After creating the app, navigate to the app's settings.
5. Add the following **Redirect URI**:  
   `http://127.0.0.1:8080/callback`
6. Copy the **Client ID** and **Client Secret** from the app settings.

### 5. Configure Environment Variables

Create a `.env` file in the project root directory (if it doesn't already exist) and add your Spotify API credentials. Use the `.env.example` file as a reference:

```properties
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback
SPOTIFY_USERNAME=your_spotify_username_or_email
SPOTIFY_PASSWORD=your_spotify_password
```

Replace `your_spotify_client_id`, `your_spotify_client_secret`, `your_spotify_username_or_email`, and `your_spotify_password` with your actual Spotify credentials.

---

## Running the Program

### 1. Start the Program

Run the program using the following command:

```bash
python main.py
```

### 2. Quit the Program

To quit the program, press the **X** button in the top-left corner of the GUI or press the `Q` key on your keyboard.

---

## Notes

- Ensure your webcam is connected and accessible by the program.
- The program saves emotion analysis results in the `emotion_analysis_results/` folder.
- If you encounter issues with Spotify playback, ensure your Spotify account is active and logged in on a device.

Enjoy using the Emotion-Based Music Recommendation System!
