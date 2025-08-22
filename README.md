# Worship Slides Generator

A local, single-file web UI that fetches song lyrics and creates a styled Google Slides deck for your setlist.

## Features
- Add songs to a setlist and select the correct match.
- Pull lyrics from Genius (requires your own Genius token).
- Generate a Google Slides deck with pre-styled slides.
- Background image is configurable via the `BACKGROUND_IMAGE_URL` environment variable.

## Prerequisites
- Python 3.10+
- A Google account
- A Genius API access token

## 1) Clone and install
```bash
git clone https://github.com/<you>/slides.git
cd slides
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Configure environment
```bash
cp .env.example .env
# edit .env and insert your GENIUS_ACCESS_TOKEN
```

## 3) Google Slides API setup
1. Go to Google Cloud Console → enable **Google Slides API**.
2. Create OAuth client credentials: **Desktop App**.
3. Download the JSON and save it as `credentials.json` in the project root (same folder as `interface.py`).
4. On first run, a browser window will prompt you to authorize. This will create a local `token.json`.

> **Do not commit** `credentials.json` or `token.json`. They are git-ignored already.

## 4) Run
```bash
python interface.py
```

The server will print a local URL and open your browser. Use the UI to add songs, pick matches, and generate the deck.

## One-liner run scripts
- Windows: double-click `run_windows.bat`
- macOS/Linux: `chmod +x run.sh && ./run.sh`

## Configuration
- `GENIUS_ACCESS_TOKEN` (**required**): Your Genius API token.
- `BACKGROUND_IMAGE_URL` (optional): URL used as slide background. Defaults to a generic Unsplash image.

## Security Notes
- Never commit `credentials.json` or `token.json`.
- Your Google OAuth token is stored locally in `token.json` and can be revoked in your Google account if needed.

## License
MIT
