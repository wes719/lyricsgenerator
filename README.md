# Worship Slides Generator

Create **worship lyric decks in minutes**.\
This local Python app lets you enter a setlist, pull lyrics from Genius,
and generate a styled Google Slides deck automatically.

------------------------------------------------------------------------

## Table of Contents

-   [What You Get](#what-you-get)
-   [Requirements](#requirements)
-   [Quick Start (TL;DR)](#quick-start-tldr)
-   [Step 1 --- Get a Genius Access
    Token](#step-1--get-a-genius-access-token)
-   [Step 2 --- Google Cloud Setup (Slides API +
    OAuth)](#step-2--google-cloud-setup-slides-api--oauth)
    -   [2A. Create a Google Cloud
        project](#2a-create-a-google-cloud-project)
    -   [2B. Enable the Google Slides
        API](#2b-enable-the-google-slides-api)
    -   [2C. Configure the OAuth consent
        screen](#2c-configure-the-oauth-consent-screen-external--testing)
    -   [2D. Create OAuth client
        credentials](#2d-create-oauth-client-credentials-desktop-app)
    -   [2E. Place credentials.json in the project
        folder](#2e-place-credentialsjson-in-the-project-folder)
-   [Step 3 --- Configure Environment
    Variables](#step-3--configure-environment-variables)
-   [Step 4 --- Install & Run](#step-4--install--run)
-   [How It Works (high-level)](#how-it-works-high-level)
-   [Troubleshooting](#troubleshooting)
-   [FAQ](#faq)
-   [Security Notes](#security-notes)
-   [Contributing](#contributing)
-   [License](#license)

------------------------------------------------------------------------

## What You Get

-   Local web UI -- runs entirely on your machine\
-   Lyrics from Genius -- requires your own Genius API token\
-   Google Slides deck -- auto-styled slides created in your Google
    account\
-   Configurable background -- change via an environment variable\
-   Cross-platform -- Windows, macOS, and Linux

------------------------------------------------------------------------

## Requirements

-   Python **3.10+**
-   A Google Account (Gmail or Google Workspace)
-   A Genius API Access Token

Note: The repo does not contain any secrets. You will add your own
tokens/credentials locally.

------------------------------------------------------------------------

## Quick Start (TL;DR)

``` bash
# 1) Clone and enter the project
git clone https://github.com/wes719/lyricsgenerator.git
cd lyricsgenerator

# 2) Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Install requirements
pip install -r requirements.txt

# 4) Copy env template and fill in your Genius token
cp .env.example .env
# edit .env and set GENIUS_ACCESS_TOKEN=...

# 5) Put your Google OAuth client file at ./credentials.json

# 6) Run
python interface.py
```

On first run, your browser opens for Google authorization. After
success, `token.json` appears locally and the app is ready.

------------------------------------------------------------------------

## Step 1 --- Get a Genius Access Token

1.  Create a Genius account (if you don't have one).\
2.  Visit: <https://genius.com/api-clients>\
3.  Click **Create API Client**.
    -   App Name: anything (e.g., Worship Slides Generator)\
    -   Website URL: your GitHub repo URL (or any URL you control)\
    -   App Description: short description\
4.  After creating, click **Generate Access Token**.\
5.  Copy the token into `.env`:

``` env
GENIUS_ACCESS_TOKEN=your_raw_token_here
```

Do not include `Bearer`. Just paste the raw token.

------------------------------------------------------------------------

## Step 2 --- Google Cloud Setup (Slides API + OAuth)

The app uses the Google Slides API via OAuth (Desktop client).

### 2A. Create a Google Cloud project

-   Go to [Google Cloud Console](https://console.cloud.google.com/)\
-   Project selector → **New Project** → name it → **Create**

### 2B. Enable the Google Slides API

-   Sidebar → **APIs & Services → Library**\
-   Search **Google Slides API** → **Enable**

(Optional: enable Google Drive API if you want Drive uploads later)

### 2C. Configure the OAuth consent screen (External → Testing)

-   Sidebar → **APIs & Services → OAuth consent screen**\
-   User Type → **External**\
-   Fill in app info (name, support email, dev contact)\
-   Add scope:
    -   `https://www.googleapis.com/auth/presentations`\
    -   (optional) `https://www.googleapis.com/auth/drive.file`\
-   Add yourself under **Test users**

### 2D. Create OAuth client credentials (Desktop app)

-   Sidebar → **APIs & Services → Credentials**\
-   Click **+ Create Credentials → OAuth client ID**\
-   App type: **Desktop app** → Name it → **Create**\
-   Download JSON

### 2E. Place `credentials.json` in the project folder

-   Rename to **credentials.json**\
-   Place next to `interface.py`\
-   Do not commit it (it's in `.gitignore`)

On first run, Google asks for authorization. After success, `token.json`
is created (also ignored).

------------------------------------------------------------------------

## Step 3 --- Configure Environment Variables

``` bash
cp .env.example .env
```

Edit `.env`:

``` env
GENIUS_ACCESS_TOKEN=your_genius_access_token_here
BACKGROUND_IMAGE_URL=https://example.com/your-image.jpg   # optional
```

------------------------------------------------------------------------

## Step 4 --- Install & Run

### Option A --- Scripts

**Windows**

``` bash
run_windows.bat
```

**macOS/Linux**

``` bash
chmod +x run.sh && ./run.sh
```

### Option B --- Manual

``` bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python interface.py
```

------------------------------------------------------------------------

## How It Works (high-level)

-   `interface.py`: serves a local web UI + API endpoints\
-   `lyrics_to_slides_improved.py`: calls Google Slides API → builds
    deck\
-   Lyrics: pulled from Genius using `GENIUS_ACCESS_TOKEN`\
-   `token.json`: stores Google OAuth refresh token

------------------------------------------------------------------------

## Troubleshooting

-   **403 access_denied** → Add your account to Test users in Google
    Console → Delete `token.json` → Retry\

-   **NameError: load_dotenv not defined** → Install deps + ensure
    import exists:

    ``` python
    try:
        from dotenv import load_dotenv
    except Exception:
        def load_dotenv(*a, **k): return None
    load_dotenv()
    ```

-   **redirect_uri_mismatch** → Must be a **Desktop app** client\

-   **invalid_grant / token issues** → Delete `token.json` and retry
    auth\

-   **Slides API not enabled** → Enable in Google Console\

-   **Genius 401 / No lyrics** → Check `.env` → Remove quotes/`Bearer` →
    Restart app

------------------------------------------------------------------------

## FAQ

**Does this post lyrics publicly?**\
No. Decks are created in your Google account. Share like any normal
Slides file.

**Can I change background per deck?**\
Yes --- set `BACKGROUND_IMAGE_URL` in `.env`.

**Do I need to publish the Google app?**\
No --- keep **Testing** and add yourself under Test users.

**Where are credentials stored?**\
- `credentials.json` (your client)\
- `token.json` (your session)\
Both are git-ignored.

------------------------------------------------------------------------

## Security Notes

-   Never commit `.env`, `credentials.json`, or `token.json`\
-   `.gitignore` already excludes them\
-   Revoke access anytime in Google Account → Security → Third-party
    access

------------------------------------------------------------------------

## Contributing

PRs welcome! Open an issue first for major changes.\
For UI contributions, include a screenshot or GIF.

------------------------------------------------------------------------

## License

MIT

------------------------------------------------------------------------
