Worship Slides Generator

Create worship lyric decks in minutes. This local Python app lets you enter a setlist, pull lyrics from Genius, and generate a styled Google Slides deck automatically.

Table of Contents

What You Get

Requirements

Quick Start (TL;DR)

Step 1 — Get a Genius Access Token

Step 2 — Google Cloud Setup (Slides API + OAuth)

2A. Create a Google Cloud project

2B. Enable the Google Slides API

2C. Configure the OAuth consent screen (External → Testing)

2D. Create OAuth client credentials (Desktop app)

2E. Place credentials.json in the project folder

Step 3 — Configure Environment Variables

Step 4 — Install & Run

How It Works (high-level)

Troubleshooting

FAQ

Security Notes

Contributing

License

What You Get

🖥️ Local web UI – runs entirely on your machine.

🎵 Lyrics from Genius – you bring your own Genius API token.

📝 Google Slides deck – auto-styled slides created in your Google account.

🖼️ Configurable background – change via an environment variable.

🪟 Cross-platform – Windows, macOS, and Linux.

Requirements

Python 3.10+

A Google Account (Gmail or Google Workspace)

A Genius API Access Token

The repo does not contain any secrets. You will add your own tokens/credentials locally.

Quick Start (TL;DR)
# 1) Clone and enter the project
git clone https://github.com/<you>/<repo>.git
cd <repo>

# 2) Create and activate a virtual environment
python -m venv .venv
# Windows:
#   .venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate

# 3) Install requirements
pip install -r requirements.txt

# 4) Copy env template and fill in your Genius token
cp .env.example .env
# edit .env and set GENIUS_ACCESS_TOKEN=...

# 5) Put your Google OAuth client file at ./credentials.json
# (see detailed Google setup below)

# 6) Run
python interface.py
# First run opens a browser for Google authorization; after success,
# token.json appears locally and the app is ready.

Step 1 — Get a Genius Access Token

Create a Genius account (if you don’t have one).

Visit: https://genius.com/api-clients

Click Create API Client.

App Name: anything (e.g., “Worship Slides Generator”)

App Website URL: your GitHub repo URL (or any URL you control)

App Description: short description of your use case

After creating the client, click Generate Access Token.

Copy the token and put it in your .env file as GENIUS_ACCESS_TOKEN.

The token starts with something like Bearer ... on Genius docs, but do not include the word Bearer. Just paste the raw token string.

Step 2 — Google Cloud Setup (Slides API + OAuth)

The app uses the Google Slides API via OAuth (Installed App / Desktop). You will create your own project and credentials so the app can create decks in your account.

2A. Create a Google Cloud project

Go to https://console.cloud.google.com/

Click the project selector (top-left) → New Project.

Name it (e.g., worship-slides-generator) → Create.

2B. Enable the Google Slides API

In the left sidebar, go to APIs & Services → Library.

Search for Google Slides API.

Click it → Enable.

(Optional: If you later add Drive uploads to Drive, also enable Google Drive API.)

2C. Configure the OAuth consent screen (External → Testing)

Left sidebar → APIs & Services → OAuth consent screen.

User Type: choose External (works for personal @gmail.com).

Fill App name, User support email, and Developer contact information.

Scopes: click Add or Remove Scopes and add:

https://www.googleapis.com/auth/presentations (Google Slides)

(optional, not required now) https://www.googleapis.com/auth/drive.file (create/open files you create)

Test users: add the Google accounts that will use this app (at least your own Gmail).
Click Save and Continue until the screen is done.

In Testing status, only users on the Test users list can authorize. Publishing to Production requires Google app verification; not needed for personal/local use.

2D. Create OAuth client credentials (Desktop app)

Left sidebar → APIs & Services → Credentials.

Click + Create Credentials → OAuth client ID.

Application type: Desktop app.

Name it and click Create.

Click Download JSON on the dialog.

2E. Place credentials.json in the project folder

Rename the downloaded file to credentials.json.

Move it to the project root, next to interface.py.

Do not commit this file (it’s git-ignored).

On first run, Google opens a browser asking for permission. After you authorize, a token.json is created locally to store your refresh token. This file is also git-ignored.

Step 3 — Configure Environment Variables

Copy the template and edit:

cp .env.example .env


Open .env and set:

GENIUS_ACCESS_TOKEN=your_genius_access_token_here
# Optional: override background image for slides
BACKGROUND_IMAGE_URL=https://example.com/your-image.jpg


The app loads .env automatically if you have python-dotenv installed (it’s in requirements.txt).

Step 4 — Install & Run
Option A — Use the included scripts

Windows

run_windows.bat


macOS / Linux

chmod +x run.sh && ./run.sh

Option B — Manual steps
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python interface.py


When the app starts:

Your default browser will open to the local UI.

On first run, Google OAuth will prompt; pick a Gmail that is on your Test users list.

After success, token.json appears in the project folder.

How It Works (high-level)

Front-end (interface.py) serves a simple local web UI and endpoints for suggestions, song info, and generation.

Back-end (lyrics_to_slides_improved.py) calls the Google Slides API to create a deck and insert lyric slides.

Lyrics are pulled from Genius using your GENIUS_ACCESS_TOKEN.

A persistent token.json keeps your Google session authorized until revoked/expired.

Troubleshooting
“Access blocked: app has not completed the Google verification process (Error 403: access_denied)”

Your OAuth consent screen is External → Testing and your account is not in Test users.

Fix:

Google Console → APIs & Services → OAuth consent screen

Add your Google account to Test users, Save

Delete token.json locally

Run the app again and authorize with that account

NameError: name 'load_dotenv' is not defined

You are calling load_dotenv() but the import failed or the package isn’t installed.

Fix:

Install: pip install -r requirements.txt

Ensure the import is present at the top of both files:

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs): return None
load_dotenv()

redirect_uri_mismatch or can’t authorize

Make sure your OAuth client type is “Desktop app”. Don’t add custom redirect URIs for desktop clients.

invalid_grant or token issues

Delete token.json and run again to force a fresh OAuth flow.

Ensure you authorize with an email that’s on Test users.

Slides API “not enabled” errors

In APIs & Services → Library, ensure Google Slides API is Enabled for your project.

Genius 401 / No lyrics

Confirm .env has GENIUS_ACCESS_TOKEN without quotes.

Restart the app after changing .env.

Some songs may have incomplete or protected lyrics; try a different match.

Virtual environment confusion on Windows

If you have multiple Pythons, run commands with:

py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py interface.py

FAQ

Does this post lyrics publicly?
No. It creates a Slides deck in your Google account. Share it like any normal deck if you choose.

Can I change the background per deck?
Yes—set BACKGROUND_IMAGE_URL in .env (or edit the variable in lyrics_to_slides_improved.py).

Do I need to publish the app to Production?
No, not for personal/local use. Keep External → Testing and add your own account under Test users.

Where are credentials stored?
credentials.json (your client) and token.json (your session) are on your machine and git-ignored.

Security Notes

Never commit credentials.json, token.json, or your .env. The .gitignore here already excludes them.

Revoke access anytime in your Google Account → Security → Third-party access.

Contributing

PRs are welcome! Please open an issue first for major changes. For UI changes, include a screenshot or short GIF.

License

MIT

You said:
print the readme.md file i can paste into replace the current readme in github
ChatGPT said:
Thought for 16s
Worship Slides Generator

Create worship lyric decks in minutes. This local Python app lets you enter a setlist, pull lyrics from Genius, and generate a styled Google Slides deck automatically.

Table of Contents

What You Get

Requirements

Quick Start (TL;DR)

Step 1 — Get a Genius Access Token

Step 2 — Google Cloud Setup (Slides API + OAuth)

2A. Create a Google Cloud project

2B. Enable the Google Slides API

2C. Configure the OAuth consent screen (External → Testing)

2D. Create OAuth client credentials (Desktop app)

2E. Place credentials.json in the project folder

Step 3 — Configure Environment Variables

Step 4 — Install & Run

How It Works (high-level)

Troubleshooting

FAQ

Security Notes

Contributing

License

What You Get

🖥️ Local web UI – runs entirely on your machine.

🎵 Lyrics from Genius – you bring your own Genius API token.

📝 Google Slides deck – auto-styled slides created in your Google account.

🖼️ Configurable background – change via an environment variable.

🪟 Cross-platform – Windows, macOS, and Linux.

Requirements

Python 3.10+

A Google Account (Gmail or Google Workspace)

A Genius API Access Token

The repo does not contain any secrets. You will add your own tokens/credentials locally.

Quick Start (TL;DR)
# 1) Clone and enter the project
git clone https://github.com/wes719/lyricsgenerator.git
cd lyricsgenerator

# 2) Create and activate a virtual environment
python -m venv .venv
# Windows:
#   .venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate

# 3) Install requirements
pip install -r requirements.txt

# 4) Copy env template and fill in your Genius token
cp .env.example .env
# edit .env and set GENIUS_ACCESS_TOKEN=...

# 5) Put your Google OAuth client file at ./credentials.json
# (see detailed Google setup below)

# 6) Run
python interface.py
# First run opens a browser for Google authorization; after success,
# token.json appears locally and the app is ready.

Step 1 — Get a Genius Access Token

Create a Genius account (if you don’t have one).

Go to https://genius.com/api-clients
 and click Create API Client.

App Name: anything (e.g., “Worship Slides Generator”)

App Website URL: your GitHub repo URL (or any URL you control)

App Description: short description of your use case

After creating the client, click Generate Access Token.

Copy the token and put it in your .env file as:

GENIUS_ACCESS_TOKEN=your_raw_token_here


Genius docs sometimes show Bearer .... Do not include the word Bearer—just the raw token string.

Step 2 — Google Cloud Setup (Slides API + OAuth)

The app uses the Google Slides API via OAuth (Installed App / Desktop). You’ll create your own project and credentials so the app can create decks in your account.

2A. Create a Google Cloud project

Go to https://console.cloud.google.com/

Click the project selector (top-left) → New Project.

Name it (e.g., worship-slides-generator) → Create.

2B. Enable the Google Slides API

Left sidebar → APIs & Services → Library.

Search Google Slides API.

Click it → Enable.

(Optional: If you later add Drive uploads, also enable Google Drive API.)

2C. Configure the OAuth consent screen (External → Testing)

Left sidebar → APIs & Services → OAuth consent screen.

User Type: choose External (works for personal @gmail.com).

Fill App name, User support email, and Developer contact information.

Scopes → Add or Remove Scopes:

https://www.googleapis.com/auth/presentations (Slides)

(optional for future) https://www.googleapis.com/auth/drive.file (create/open files you create)

Test users: add the Google accounts that will use this app (at least your own Gmail).

Save and Continue through the remaining steps.

In Testing status, only users on the Test users list can authorize. Publishing to Production requires Google app verification; not needed for personal/local use.

2D. Create OAuth client credentials (Desktop app)

Left sidebar → APIs & Services → Credentials.

+ Create Credentials → OAuth client ID.

Application type: Desktop app.

Name it → Create.

Click Download JSON.

2E. Place credentials.json in the project folder

Rename the downloaded file to credentials.json.

Move it to the project root (same folder as interface.py).

Do not commit this file (it’s in .gitignore).

On first run, a browser opens for permission. After authorizing, token.json is created locally (also .gitignored).

Step 3 — Configure Environment Variables

Copy the template and edit:

cp .env.example .env


Open .env and set:

GENIUS_ACCESS_TOKEN=your_genius_access_token_here
# Optional: override background image for slides
BACKGROUND_IMAGE_URL=https://example.com/your-image.jpg


The app loads .env automatically via python-dotenv (included in requirements.txt).

Step 4 — Install & Run
Option A — Use the included scripts

Windows

run_windows.bat


macOS / Linux

chmod +x run.sh && ./run.sh

Option B — Manual steps
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python interface.py


When the app starts:

Your default browser opens to the local UI.

On first run, Google OAuth prompts; sign in with an account on your Test users list.

After success, token.json appears in the project folder.

How It Works (high-level)

interface.py serves a local web UI and endpoints for suggestions, song info, and deck generation.

lyrics_to_slides_improved.py calls the Google Slides API to create the deck and insert lyric slides.

Lyrics are pulled from Genius using your GENIUS_ACCESS_TOKEN.

token.json stores your Google refresh token for subsequent runs.

Troubleshooting
“Access blocked: app has not completed the Google verification process (Error 403: access_denied)”

Your OAuth project is External → Testing, and your account is not in Test users.

Fix

Google Console → APIs & Services → OAuth consent screen

Add your Google account under Test users, Save

Delete token.json locally

Run the app again and authorize with that account

NameError: name 'load_dotenv' is not defined

You’re calling load_dotenv() before importing it or without the package installed.

Fix

Install deps: pip install -r requirements.txt

Ensure the import exists at the top of both Python files:

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs): return None
load_dotenv()

redirect_uri_mismatch / can’t authorize

Your OAuth client must be Desktop app. Don’t add custom redirect URIs for desktop clients.

invalid_grant or token issues

Delete token.json and run again to force a fresh OAuth flow.
Make sure you authorize with an email on Test users.

Slides API “not enabled”

APIs & Services → Library → ensure Google Slides API is Enabled.

Genius 401 / No lyrics

Confirm .env has GENIUS_ACCESS_TOKEN (no quotes, no “Bearer ”).

Restart the app after changing .env.

Some songs may have incomplete or protected lyrics; try a different match.

Virtual environment confusion on Windows

If you have multiple Pythons:

py -m venv .venv
.\.venv\Scripts\activate
py -m pip install -r requirements.txt
py interface.py

FAQ

Does this post lyrics publicly?
No—decks are created in your Google account. Share them like any normal Slides deck if you choose.

Can I change the background per deck?
Yes—set BACKGROUND_IMAGE_URL in .env (or edit the variable in lyrics_to_slides_improved.py).

Do I need to publish the app to Production?
No. Keep External → Testing and add your own account under Test users.

Where are credentials stored?
credentials.json (your client) and token.json (your session) live on your machine and are git-ignored.

Security Notes

Never commit credentials.json, token.json, or your .env. .gitignore already excludes them.

You can revoke access anytime in Google Account → Security → Third-party access.

Contributing

PRs are welcome! Open an issue first for major changes. For UI changes, include a screenshot or short GIF.

License

MIT
