from dotenv import load_dotenv
#!/usr/bin/env python3
"""
Improved lyrics‐to‐slides generator
===================================

load_dotenv()
This script is a drop‐in replacement for ``lyrics_to_slides.py`` that adds two
major enhancements:

1. **Similar song suggestions when a query is ambiguous or not found.**  When
   you enter a song title that isn't an exact match on Genius, the script
   searches for multiple potential matches.  It displays these options and
   prompts you to pick the correct one rather than simply failing with an
   error.  This makes it easier to recover from typos or approximate
   titles.

2. **Prioritising worship songs.**  The script now computes a simple
   ``worship score`` for each candidate match based on keywords in the song
   title and artist name (e.g. ``"praise"``, ``"hillsong"``, ``"faith"``).
   Candidates with higher scores are listed first and will be selected by
   default if you simply press ``Enter`` at the prompt.  This bias reduces
   the likelihood of inadvertently selecting a secular song that shares the
   same title as your desired worship song.

All other functionality remains identical to the original version: it
authenticates against the Google Slides API, fetches lyrics from Genius,
formats them nicely, and produces a beautifully themed slide deck with one
slide per couplet.  See ``lyrics_to_slides.py`` for detailed comments on
the presentation generation logic.
"""

import os
import re
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from lyricsgenius import Genius
import argparse
BACKGROUND_IMAGE_URL = os.getenv('BACKGROUND_IMAGE_URL', 'https://images.unsplash.com/photo-1519681393784-d120267933ba')

SCOPES = ['https://www.googleapis.com/auth/presentations']

# Slide dimensions in points (10in x 5.625in ≈ 720pt x 405pt)
SLIDE_WIDTH = 720
SLIDE_HEIGHT = 405

# Styling parameters
BOX_WIDTH_RATIO = 0.8
BOX_HEIGHT = 50
BOX_SPACING = 20
TEXT_INSET = 10
BOX_ALPHA = 0.35
FONT_SIZE = 18
BACKGROUND_IMAGE_URL = (
    'https://images.squarespace-cdn.com/content/v1/64e4da071aa4df6831dd8569/1693440303265-Y58Y5A8VF5HU68FA4CPY/image-asset.jpeg'
)


def split_title_artist(song_query: str) -> tuple[str, str]:
    """
    Split on either en-dash (–) or hyphen (-), first occurrence.
    Returns (title, artist) with artist='' if none.
    """
    parts = re.split(r'\s+[-–]\s+', song_query, maxsplit=1)
    title = parts[0].strip()
    artist = parts[1].strip() if len(parts) > 1 else ''
    return title, artist


def fetch_lyrics_from_genius(song_query: str) -> str:
    """
    Search for a song on Genius and return its lyrics.

    This implementation expands upon the simple search used previously by
    first retrieving a collection of potential matches, ranking them using a
    set of worship keywords, and then prompting the user to choose the
    correct song when necessary.  If a song cannot be found, similar
    titles are presented before failing.  The function returns the lyrics
    for the chosen song with section headers removed.

    Args:
        song_query: The user supplied query string (e.g. "Oceans – Hillsong UNITED").

    Returns:
        A single string containing the full lyrics for the chosen song.

    Raises:
        RuntimeError: If the Genius API token is not available.
        ValueError: If no lyrics can be retrieved after searching.
    """
    # Fetch the API token either from the environment or fall back to the
    # baked‑in token used previously.  Raising a RuntimeError here clarifies
    # to the caller that authentication is required for any network calls.
    token = os.getenv('GENIUS_ACCESS_TOKEN')
    if not token:
        raise RuntimeError('Please set the GENIUS_ACCESS_TOKEN environment variable.')
    # Instantiate the Genius API client with sensible defaults.  We continue
    # to skip non‑songs and remove section headers to keep the slides clean.
    genius = Genius(
        token,
        skip_non_songs=True,
        excluded_terms=['(Remix)', '(Live)'],
        remove_section_headers=True,
        timeout=15,
        retries=3
    )
    # Define a set of keywords commonly found in worship music.  These
    # keywords are used to rank search results to make worship songs more
    # likely to be selected automatically.  Feel free to expand this list
    # if you find certain artists or themes that are representative of the
    # music you wish to prioritise.
    WORSHIP_KEYWORDS = [
        'worship', 'praise', 'christ', 'jesus', 'god', 'hillsong', 'bethel',
        'church', 'faith', 'grace', 'redeemer', 'lord', 'holy', 'gospel',
        'alive', 'blessing', 'spirit', 'hope', 'saved'
    ]
    # Attempt to find songs matching the query.  We request multiple
    # results so that we can rank and optionally present alternatives.  The
    # search_songs API returns a dictionary containing a list of hits.  If
    # the call fails for any reason, we will fall back to search_song.
    try:
        search_results = genius.search_songs(song_query, per_page=10)
        hits = search_results.get('hits', []) if search_results else []
    except Exception:
        hits = []
    # If no hits were returned, fall back to search_song.  This handles
    # simple queries that might still resolve to a song even when
    # search_songs fails.
    if not hits:
        print(f'Searching for “{song_query}”…')
        song = genius.search_song(song_query)
        if song and song.lyrics:
            return song.lyrics
        # No matches at all – present a message and abort.
        raise ValueError(f'No lyrics found on Genius for “{song_query}”. Please check the spelling or try another song.')
    # Build a list of candidate matches with a worship score.  Each entry
    # stores the title, artist, url and score so that we can later fetch
    # lyrics directly from the result's URL.
    candidates_raw = []
    for hit in hits:
        result = hit.get('result', {})
        title = result.get('title', '')
        artist_name = result.get('primary_artist', {}).get('name', '')
        url = result.get('url', None)
        # Compute a simple heuristic score based on the presence of worship
        # keywords in the title or artist.  The more keywords present, the
        # higher the score.  The scoring is case‑insensitive.
        combined = f'{title} {artist_name}'.lower()
        score = sum(1 for kw in WORSHIP_KEYWORDS if kw in combined)
        candidates_raw.append({'title': title, 'artist': artist_name, 'url': url, 'score': score})
    # Sort candidates by score descending; maintain original order for ties
    # by using enumerate as a secondary key.  Without this stable sort,
    # items with equal scores might shuffle unpredictably.
    candidates = sorted(
        enumerate(candidates_raw),
        key=lambda t: (t[1]['score'], -t[0]),
        reverse=True
    )
    # Flatten the sorted enumeration back into a list of candidate dicts.
    sorted_candidates = [c for _, c in candidates]
    # Determine whether we need to prompt the user.  If the highest score
    # equals zero and there are multiple candidates, we will always prompt
    # because none of the titles appear to be worship songs.  Otherwise,
    # we still prompt but make it clear that pressing Enter will pick
    # the highest scoring option by default.
    print(f'\nPossible matches for “{song_query}”:\n')
    for idx, cand in enumerate(sorted_candidates, start=1):
        print(f'  {idx}. {cand["title"]} – {cand["artist"]}  (score: {cand["score"]})')
    prompt = 'Select the correct song by entering its number' + (
        ' (press Enter to pick the top result): ' if sorted_candidates[0]['score'] > 0 else ' (press Enter to pick the first result): '
    )
    choice = input(prompt).strip()
    selection_index = 0
    if choice:
        try:
            entered = int(choice)
            if 1 <= entered <= len(sorted_candidates):
                selection_index = entered - 1
        except ValueError:
            # If the user input isn't a number, ignore it and use the default
            pass
    chosen = sorted_candidates[selection_index]
    # Fetch lyrics using the chosen candidate's URL.  Using the URL
    # directly avoids relying on Genius.search_song to find the exact
    # version we selected from the search results.  If this fails, we
    # fallback to search_song with the explicit title and artist.
    lyrics = None
    if chosen.get('url'):
        try:
            lyrics = genius.lyrics(song_url=chosen['url'])
        except Exception:
            lyrics = None
    if not lyrics:
        # As a fallback, call search_song with the title and artist to
        # retrieve a Song object, then extract its lyrics.  This is
        # slower but ensures we return something if the direct URL scrape
        # fails.
        song_obj = None
        try:
            song_obj = genius.search_song(chosen['title'], chosen['artist'])
        except Exception:
            song_obj = None
        if song_obj and song_obj.lyrics:
            lyrics = song_obj.lyrics
    if not lyrics:
        raise ValueError(f'Could not retrieve lyrics for {chosen["title"]} by {chosen["artist"]}')
    return lyrics


def format_lyrics(lyrics: str):
    IGNORE_KEYWORDS = [
        'lyrics', 'contributor', 'powered by', 'embed', 'view more',
    ]
    cleaned = []
    for raw in lyrics.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if any(kw in low for kw in IGNORE_KEYWORDS):
            continue
        cleaned.append(line.upper())
    return [cleaned[i:i + 2] for i in range(0, len(cleaned), 2)]


def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return build('slides', 'v1', credentials=creds)


def create_setlist_presentation(service, setlist_title: str, songs_slides: list[tuple[str, list[list[str]]]]):
    try:
        # create deck
        presentation = service.presentations().create(body={'title': setlist_title}).execute()
        pres_id = presentation['presentationId']
        default_id = presentation['slides'][0]['objectId']
        requests = [{'deleteObject': {'objectId': default_id}}]

        # Deck title slide
        requests += _make_title_slide('deck_title', setlist_title)

        # For each song: a title slide then its lyric slides
        for sidx, (song_query, slides_content) in enumerate(songs_slides, start=1):
            song_title, _ = split_title_artist(song_query)
            # Song title slide (title only)
            requests += _make_title_slide(f'song_title_{sidx}', song_title)

            # Lyric slides
            for idx, lines in enumerate(slides_content):
                base_id = f'song{sidx}_slide{idx}'
                # blank slide + background
                requests += [
                    {'createSlide': {
                        'objectId': base_id,
                        'slideLayoutReference': {'predefinedLayout': 'BLANK'}
                    }},
                    {'updatePageProperties': {
                        'objectId': base_id,
                        'pageProperties': {
                            'pageBackgroundFill': {
                                'stretchedPictureFill': {'contentUrl': BACKGROUND_IMAGE_URL}
                            }
                        },
                        'fields': 'pageBackgroundFill.stretchedPictureFill.contentUrl'
                    }}
                ]
                # compute bar positions
                bar_width = SLIDE_WIDTH * BOX_WIDTH_RATIO
                x_off = (SLIDE_WIDTH - bar_width) / 2
                count = len(lines)
                total_h = count * BOX_HEIGHT + (count - 1) * BOX_SPACING
                y_off = (SLIDE_HEIGHT - total_h) / 2

                for j, line in enumerate(lines):
                    bar_id = f'{base_id}_bar{j}'
                    txt_id = f'{base_id}_txt{j}'
                    y = y_off + j * (BOX_HEIGHT + BOX_SPACING)
                    # shape + styling
                    requests += [
                        {'createShape': {
                            'objectId': bar_id,
                            'shapeType': 'RECTANGLE',
                            'elementProperties': {
                                'pageObjectId': base_id,
                                'size': {
                                    'width': {'magnitude': bar_width, 'unit': 'PT'},
                                    'height': {'magnitude': BOX_HEIGHT, 'unit': 'PT'}
                                },
                                'transform': {
                                    'scaleX': 1, 'scaleY': 1,
                                    'translateX': x_off, 'translateY': y, 'unit': 'PT'
                                }
                            }
                        }},
                        {'updateShapeProperties': {
                            'objectId': bar_id,
                            'shapeProperties': {
                                'shapeBackgroundFill': {
                                    'solidFill': {
                                        'color': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}},
                                        'alpha': BOX_ALPHA
                                    }
                                },
                                'outline': {'propertyState': 'NOT_RENDERED'}
                            },
                            'fields': 'shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha,outline.propertyState'
                        }},
                        {'createShape': {
                            'objectId': txt_id,
                            'shapeType': 'TEXT_BOX',
                            'elementProperties': {
                                'pageObjectId': base_id,
                                'size': {
                                    'width': {'magnitude': bar_width - 2 * TEXT_INSET, 'unit': 'PT'},
                                    'height': {'magnitude': BOX_HEIGHT - 2 * TEXT_INSET, 'unit': 'PT'}
                                },
                                'transform': {
                                    'scaleX': 1, 'scaleY': 1,
                                    'translateX': x_off + TEXT_INSET,
                                    'translateY': y + TEXT_INSET,
                                    'unit': 'PT'
                                }
                            }
                        }},
                        {'updateShapeProperties': {
                            'objectId': txt_id,
                            'shapeProperties': {
                                'shapeBackgroundFill': {'solidFill': {'alpha': 0}},
                                'outline': {'propertyState': 'NOT_RENDERED'},
                                'contentAlignment': 'MIDDLE'
                            },
                            'fields': 'shapeBackgroundFill.solidFill.alpha,outline.propertyState,contentAlignment'
                        }},
                        {'insertText': {'objectId': txt_id, 'insertionIndex': 0, 'text': line}},
                        {'updateTextStyle': {
                            'objectId': txt_id,
                            'style': {
                                'fontFamily': 'Calibri',
                                'fontSize': {'magnitude': FONT_SIZE, 'unit': 'PT'},
                                'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}},
                                'bold': False
                            },
                            'textRange': {'type': 'ALL'},
                            'fields': 'fontFamily,fontSize,foregroundColor,bold'
                        }},
                        {'updateParagraphStyle': {
                            'objectId': txt_id,
                            'style': {'alignment': 'CENTER', 'lineSpacing': 100},
                            'textRange': {'type': 'ALL'},
                            'fields': 'alignment,lineSpacing'
                        }}
                    ]

        service.presentations().batchUpdate(
            presentationId=pres_id,
            body={'requests': requests}
        ).execute()
        print(f"✅ Presentation ready: https://docs.google.com/presentation/d/{pres_id}/edit")

        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"

        # ── magic to open Chrome ──
        import sys, subprocess, webbrowser

        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', '-a', 'Google Chrome', url])
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.run(['google-chrome', url], check=True)
            elif sys.platform.startswith('win'):  # Windows
                # note: needs shell=True to let `start` launch properly
                subprocess.run(['start', 'chrome', url], shell=True)
            else:
                # falls back to your system default browser
                webbrowser.open_new_tab(url)
        except Exception as e:
            print(f"⚠️  Couldn’t auto-launch Chrome: {e}")

    except HttpError as e:
        print(f"An error occurred: {e}")


def _make_title_slide(obj_id: str, text: str) -> list[dict]:
    """
    Helper to generate the 6 requests needed for a big title slide
    """
    txt = text.upper()
    return [
        {'createSlide': {
            'objectId': obj_id,
            'slideLayoutReference': {'predefinedLayout': 'BLANK'}
        }},
        {'updatePageProperties': {
            'objectId': obj_id,
            'pageProperties': {
                'pageBackgroundFill': {
                    'stretchedPictureFill': {'contentUrl': BACKGROUND_IMAGE_URL}
                }
            },
            'fields': 'pageBackgroundFill.stretchedPictureFill.contentUrl'
        }},
        {'createShape': {
            'objectId': f'{obj_id}_box',
            'shapeType': 'TEXT_BOX',
            'elementProperties': {
                'pageObjectId': obj_id,
                'size': {
                    'height': {'magnitude': 50, 'unit': 'PT'},
                    'width': {'magnitude': SLIDE_WIDTH, 'unit': 'PT'}
                },
                'transform': {
                    'scaleX': 1, 'scaleY': 1,
                    'translateX': 0,
                    'translateY': (SLIDE_HEIGHT - 33) / 2,
                    'unit': 'PT'
                }
            }
        }},
        {'insertText': {
            'objectId': f'{obj_id}_box',
            'insertionIndex': 0,
            'text': txt
        }},
        {'updateTextStyle': {
            'objectId': f'{obj_id}_box',
            'style': {
                'fontFamily': 'Calibri',
                'fontSize': {'magnitude': 33, 'unit': 'PT'},
                'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}}
            },
            'textRange': {'type': 'ALL'},
            'fields': 'fontFamily,fontSize,foregroundColor'
        }},
        {'updateParagraphStyle': {
            'objectId': f'{obj_id}_box',
            'textRange': {'type': 'ALL'},
            'style': {'alignment': 'CENTER'},
            'fields': 'alignment'
        }}
    ]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a Google Slides deck of lyrics for a full setlist.'
    )
    parser.add_argument(
        '-f', '--file',
        help='Path to text file with one song per line',
        default=None
    )
    parser.add_argument(
        'songs',
        nargs='*',
        help='Song names (you can add "– artist" or "- artist" for accuracy)'
    )
    args = parser.parse_args()

    # build the list of song queries
    if args.file:
        if not os.path.exists(args.file):
            raise FileNotFoundError(f'Setlist file not found: {args.file}')
        with open(args.file, encoding='utf-8') as f:
            songs = [line.strip() for line in f if line.strip()]
    else:
        songs = args.songs

    if not songs:
        parser.error('No songs specified. Pass song names or use -f setlist.txt')

    # fetch & format every song
    songs_slides = []
    for song in songs:
        raw = fetch_lyrics_from_genius(song)
        slides = format_lyrics(raw)
        songs_slides.append((song, slides))

    svc = authenticate()
    # include today's date in the deck title
    today = datetime.datetime.now()
    # build an “h:mmam/pm” string without %-I
    time_str = today.strftime('%I:%M%p').lstrip('0').lower()
    deck_title = f"{today.strftime('%B')} {today.day} Setlist Generated at {time_str}"

    create_setlist_presentation(svc, deck_title, songs_slides)