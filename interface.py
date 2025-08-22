
load_dotenv()
#!/usr/bin/env python3
"""
frontend.py – polished UI for the worship slides generator

This build refreshes the *entire* interface to match the song cards:
- Glassy cards & gradient accents for the header, add-song bar, and result panel
- Nicer input with focus ring, subtle glow, and icon
- Primary buttons use a clean gradient with hover glow
- Modal styling matches the overall look
(Logic stays identical.)

Run:  python frontend4_fixed.py
"""

import base64
import datetime
import http.server
import json
import os
import socketserver
import threading
import urllib.parse
from zoneinfo import ZoneInfo

import lyrics_to_slides_improved
from lyricsgenius import Genius

import requests
import tempfile
from dotenv import load_dotenv
import subprocess
import re
from string import Template

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

BACKGROUND_JPEG_PATH = os.path.join(os.path.dirname(__file__), 'abstract_bg.jpg')
if os.path.exists(BACKGROUND_JPEG_PATH):
    with open(BACKGROUND_JPEG_PATH, 'rb') as f:
        BACKGROUND_DATA = base64.b64encode(f.read()).decode('ascii')
else:
    BACKGROUND_DATA = ''

INDEX_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Worship Slides Generator</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0d0f12;
      --surface: rgba(255,255,255,0.06);
      --surface-strong: rgba(255,255,255,0.12);
      --text: #f5f7fb;
      --muted: #c8cbd3;
      --accent1: #7c5cff;
      --accent2: #00d1d1;
      --shadow: 0 8px 30px rgba(0,0,0,0.35);
      --radius: 14px;
      --surface-darker: rgba(255,255,255,0.04);
      --menu-bg: #141820;
      --menu-fg: #f0f3f8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body, html { height: 100%; width: 100%; font-family: 'Poppins', sans-serif; min-height: 100vh; color: var(--text); }
    body {
      /* Layered background: animated aurora + subtle grid + optional photo */
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(124,92,255,0.18), transparent 60%),
        radial-gradient(900px 500px at 110% 110%, rgba(0,209,209,0.18), transparent 60%),
        linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.00)),
        url('data:image/jpeg;base64,$bg_data');
      background-color: var(--bg);
      background-attachment: fixed, fixed, fixed, fixed;
      background-size: cover, cover, cover, cover;
      background-position: center, center, center, center;
      overflow-x: hidden;
    }
    /* Ambient animated blobs */
    .fx { position: fixed; inset: -20%; pointer-events: none; z-index: 0; }
    .fx-aurora {
      background:
        radial-gradient(600px 350px at 20% 30%, rgba(124,92,255,0.25), transparent 55%),
        radial-gradient(520px 320px at 80% 70%, rgba(0,209,209,0.22), transparent 55%);
      filter: blur(60px);
      animation: driftA 16s ease-in-out infinite alternate;
      mix-blend-mode: screen;
    }
    .fx-aurora2 {
      background:
        radial-gradient(540px 320px at 70% 20%, rgba(255,120,180,0.16), transparent 55%),
        radial-gradient(600px 360px at 30% 80%, rgba(100,220,255,0.12), transparent 55%);
      filter: blur(70px);
      animation: driftB 22s ease-in-out infinite alternate;
      mix-blend-mode: screen;
    }
    @keyframes driftA { 
      from { transform: translate3d(-2%, 0, 0) rotate(0.001deg); }
      to   { transform: translate3d(2%, 1.5%, 0) rotate(0.001deg); }
    }
    @keyframes driftB { 
      from { transform: translate3d(1%, -1%, 0) scale(1.02); }
      to   { transform: translate3d(-2%, 2%, 0) scale(1.05); }
    }
    /* Subtle grid texture */
    .fx-grid { 
      background-image:
        linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
      background-size: 38px 38px, 38px 38px;
      opacity: .04;
      mix-blend-mode: overlay;
    }

    .container { position: relative; z-index: 2; }

    .container { max-width: 960px; margin: 0 auto; padding: 48px 20px; }
    .overlay {
      background: rgba(13,15,18,0.6);
      padding: 36px;
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255,255,255,0.08);
    }

    .header { display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 6px; margin-bottom: 20px; }
    h1 { font-size: 2.6em; font-weight: 700; letter-spacing: .5px; text-align: center; }
    .subtitle { color: var(--muted); font-weight: 400; font-size: 0.98em; text-align: center; }

    .card {
      position: relative; border-radius: var(--radius);
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), var(--shadow);
    }
    .card::before {
      content: ""; position: absolute; inset: 0; border-radius: inherit;
      background: radial-gradient(1200px 200px at -10% -20%, rgba(255,255,255,0.12), transparent 55%);
      pointer-events: none;
    }
    .section { margin-bottom: 18px; }

    #add-bar { display: grid; grid-template-columns: 1fr auto; gap: 12px; padding: 14px; }
    .input-wrap { position: relative; }
    .input-wrap svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); opacity: .7; }
    #song-input {
      width: 100%; padding: 12px 14px 12px 40px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.08); color: var(--text); font-size: 1em; outline: none;
      transition: box-shadow .2s, border-color .2s, background .2s;
    }
    #song-input::placeholder { color: #d3d7e0; opacity: .8; }
    #song-input:focus {
      border-color: rgba(255,255,255,0.28);
      box-shadow: 0 0 0 3px rgba(124,92,255,0.25);
      background: rgba(255,255,255,0.1);
    }
    .btn { padding: 12px 22px; border: none; border-radius: 12px; cursor: pointer; font-weight: 600; }
    .btn-primary {
      color: white;
      background: linear-gradient(90deg, var(--accent1), var(--accent2));
      box-shadow: 0 6px 24px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.08) inset;
      transition: transform .08s ease, box-shadow .2s ease, filter .2s ease;
    }
    .btn-primary:hover { filter: brightness(1.05); }
    .btn-primary:active { transform: translateY(1px); }

    #songs-list { list-style: none; padding: 0; margin: 16px 0 0 0; }
    .song-item {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 16px; margin-bottom: 12px; border-radius: 12px; position: relative;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
      transition: transform .06s ease, box-shadow .2s ease;
    }
    .song-item:hover { box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1), 0 6px 16px rgba(0,0,0,0.25); }
    .song-item::before {
      content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15)); border-radius: 12px; pointer-events: none;
    }
    .song-main { display: flex; align-items: center; flex: 1; overflow: hidden; gap: 10px; }
    .song-index { width: 28px; height: 28px; flex: 0 0 28px; display: inline-flex; align-items: center; justify-content: center;
      border-radius: 999px; font-weight: 600; font-size: 0.9em; background: rgba(0,0,0,0.35); color: #fff;
      box-shadow: 0 0 0 1px rgba(255,255,255,0.25) inset; }
    .song-art { width: 40px; height: 40px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
    .song-title { flex: 1; font-size: 1.08em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.55); }
    .pill { margin-left: 10px; font-size: .75em; padding: 2px 8px; border-radius: 999px; background: rgba(255,255,255,0.16); }
    .song-controls button { background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2em; padding: 4px; margin-left: 6px; filter: drop-shadow(0 1px 1px rgba(0,0,0,0.6)); }
    .song-controls button.info-indicator { padding: 6px 8px; border-radius: 999px; background: rgba(255,255,255,0.18); }
    
    .song-controls button:hover { opacity: 0.9; }

    .actions { margin-top: 18px; }
    #generate-btn { width: 100%; padding: 16px; font-size: 1.15em; border-radius: 12px; border: none; cursor: pointer; color: #fff;
      background: linear-gradient(90deg, var(--accent1), var(--accent2)); box-shadow: 0 10px 28px rgba(0,0,0,0.35); transition: filter .2s, transform .06s; }
    #generate-btn:hover { filter: brightness(1.06); }
    #generate-btn:active { transform: translateY(1px); }
    #generate-btn:disabled { opacity: 0.6; cursor: not-allowed; }
    #loading { display: none; text-align: center; margin-top: 16px; font-size: 1.05em; color: var(--muted); }
    #result-link { margin-top: 16px; padding: 14px 16px; border-radius: 12px;
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
      border: 1px solid rgba(255,255,255,0.08); text-align: center; box-shadow: var(--shadow);
    }
    #result-link a { color: #e7fbff; font-weight: 600; }

    .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(12px); }
    .modal-content { background: linear-gradient(180deg, rgba(30,34,39,0.95), rgba(22,24,28,0.95)); border: 1px solid rgba(255,255,255,0.08);
      padding: 18px; border-radius: 12px; max-width: 820px; width: 94%; max-height: 90vh; overflow-y: auto; box-shadow: var(--shadow); 
      backdrop-filter: blur(14px) saturate(120%);
      -webkit-backdrop-filter: blur(14px) saturate(120%);
    }
    .modal h2 { margin-top: 0; font-weight: 600; margin-bottom: 10px; }
    .suggestion-item { padding: 10px 12px; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; background: rgba(255,255,255,0.04); cursor: pointer; margin-bottom: 8px; }
    .suggestion-item:hover { background: rgba(255,255,255,0.07); }
    
    /* Redesigned suggestion cards (match song cards) */
    .sugg-card {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      margin-bottom: 10px;
      border-radius: 12px;
      position: relative;
      cursor: pointer;
      overflow: hidden;
      color: var(--text);
      background: linear-gradient(90deg, #3a3a3a, #1e1e1e);
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), var(--shadow);
      transition: transform .06s ease, box-shadow .2s ease, filter .2s ease;
    }
    .sugg-card:hover { box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1), 0 6px 16px rgba(0,0,0,0.25); filter: brightness(1.02); }
    .sugg-card::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: 12px;
      background: linear-gradient(90deg, rgba(0,0,0,0.18), rgba(0,0,0,0.18));
      pointer-events: none;
    }
    .sugg-art {
      width: 44px; height: 44px; border-radius: 8px; object-fit: cover; flex-shrink: 0;
      box-shadow: 0 0 0 1px rgba(255,255,255,0.18) inset;
    }
    .sugg-meta { display: flex; flex-direction: column; min-width: 0; flex: 1; }
    .sugg-title {
      font-weight: 600; font-size: 1.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      text-shadow: 0 1px 2px rgba(0,0,0,0.55);
    }
    .sugg-sub { font-size: .85em; opacity: .9; }
    .sugg-star {
      position: absolute; right: 10px; top: 10px;
      width: 26px; height: 26px; border-radius: 999px; display: none; align-items: center; justify-content: center;
      background: rgba(255,255,255,0.18);
      box-shadow: 0 0 0 1px rgba(255,255,255,0.28) inset;
      font-size: 0.95em; line-height: 1; filter: drop-shadow(0 1px 1px rgba(0,0,0,0.6));
    }
.close-btn { display: flex; justify-content: flex-end; margin-top: 10px; }
    .close-btn button { background: linear-gradient(90deg, #ff6b6b, #ff9a7b); border: none; color: #fff; padding: 8px 12px; border-radius: 8px; cursor: pointer; }

    /* Section editor modal */
    /* Centering & scrollbar polish */
    .modal-content { 
      margin: 0 auto; 
      max-width: 900px; 
      width: min(96%, 900px); 
      border-radius: 16px;
    
      backdrop-filter: blur(14px) saturate(120%);
      -webkit-backdrop-filter: blur(14px) saturate(120%);
    }
    .section-list { 
      max-width: 860px; 
      margin: 0 auto; 
    }
    /* Better scrollbars (webkit) */
    .modal-content::-webkit-scrollbar, .section-item textarea::-webkit-scrollbar { width: 10px; }
    .modal-content::-webkit-scrollbar-track, .section-item textarea::-webkit-scrollbar-track {
      background: rgba(255,255,255,0.06); border-radius: 10px;
    }
    .modal-content::-webkit-scrollbar-thumb, .section-item textarea::-webkit-scrollbar-thumb {
      background: rgba(255,255,255,0.28); border-radius: 10px; border: 2px solid rgba(0,0,0,0);
    }
    /* Firefox */
    .section-item select:focus, .section-item input[type="text"]:focus, .section-item textarea:focus { border-color: rgba(124,92,255,0.7); box-shadow: 0 0 0 3px rgba(124,92,255,0.18); }
    .section-item select option, .section-item select optgroup { background: var(--menu-bg); color: var(--menu-fg); }
    .section-item textarea { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.35) rgba(255,255,255,0.08);  overflow: hidden;  height: auto; display: block; }

    .flow-toolbar { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:12px; }
    .flow-toolbar .left { display:flex; gap:8px; align-items:flex-start; flex-wrap: wrap; }
    .btn-ghost { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: var(--text); }
    .btn-danger { background: linear-gradient(90deg, #ff6b6b, #ff9a7b); color:#fff; border:none; }

    .section-list { display: grid; gap: 12px; }
    .section-item {
      padding:14px;
      border-radius:14px;
      display:grid;
      grid-template-areas: 'label controls' 'text text';
      grid-template-columns: 1fr auto;
      gap:12px;
      align-items:flex-start;
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
      border: 1px solid rgba(255,255,255,0.08);
    }
    .section-label { grid-area: label; display:flex; align-items:flex-start; gap:12px; }
    .section-controls { grid-area: controls; display:flex; align-items:flex-start; }
    .section-item select:focus, .section-item input[type="text"]:focus, .section-item textarea:focus { border-color: rgba(124,92,255,0.7); box-shadow: 0 0 0 3px rgba(124,92,255,0.18); }
    .section-item select option, .section-item select optgroup { background: var(--menu-bg); color: var(--menu-fg); }
    .section-item textarea { grid-area: text;  overflow: hidden;  height: auto; display: block; }
    .section-item select, .section-item input[type="text"] {
      width: 100%; padding:10px 12px; border-radius:10px; border:1px solid rgba(255,255,255,0.12); box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
      appearance:none; -webkit-appearance:none; -moz-appearance:none;
      background: rgba(255,255,255,0.08); color: var(--text); outline:none;
      color-scheme: dark;
    }
    .section-item select:focus, .section-item input[type="text"]:focus, .section-item textarea:focus { border-color: rgba(124,92,255,0.7); box-shadow: 0 0 0 3px rgba(124,92,255,0.18); }
    .section-item select option, .section-item select optgroup { background: var(--menu-bg); color: var(--menu-fg); }
    .section-item textarea {
      width: 100%; min-height: 96px; padding:10px 12px; border-radius:10px; border:1px solid rgba(255,255,255,0.12); box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
      appearance:none; -webkit-appearance:none; -moz-appearance:none;
      background: rgba(255,255,255,0.08); color: var(--text); outline:none;
      color-scheme: dark; resize: none;   vertical; font-family: 'Poppins', sans-serif; 
     overflow: hidden;  height: auto; display: block;  height: auto; }
    .section-controls button { margin-left:6px; background:none; border:none; cursor:pointer; font-size:1.1em; color:var(--text); }
    .section-controls button:hover { opacity:.9; }
    .hint { color: var(--muted); font-size: .9em; margin-bottom: 10px; }

    @media (max-width: 720px) {
      .section-item { grid-template-areas: 'label' 'controls' 'text'; grid-template-columns: 1fr; }
    }
  
    /* Song Info modal */
    #song-info-modal .modal-content {
      padding: 0;
      overflow: hidden;
    }
    
    /* Compact corner close (X) */
    .modal-x {
      position: absolute;
      top: 10px;
      right: 10px;
      width: 30px;
      height: 30px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.22);
      background: rgba(0,0,0,0.35);
      color: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      backdrop-filter: blur(8px) saturate(120%);
      -webkit-backdrop-filter: blur(8px) saturate(120%);
      box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }
    .modal-x:hover { filter: brightness(1.1); }
.song-info-header {
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 16px;
      padding: 18px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .song-info-cover {
      width: 140px; height: 140px; border-radius: 12px; object-fit: cover;
      box-shadow: 0 2px 14px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.18) inset;
    }
    .song-info-meta {
      display: grid;
      align-content: center;
      gap: 6px;
      min-width: 0;
    }
    .song-info-title { font-size: 1.3em; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,0.45); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .song-info-sub { color: var(--muted); font-size: .95em; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .song-info-pill { padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.14); font-size: .82em; }
    .song-info-actions {
      display: flex; gap: 12px; margin-top: 8px; flex-wrap: wrap; align-items: stretch;
    }
    .btn-small {
      padding: 0 18px; min-height: 54px; border-radius: 14px; font-weight: 600;
      border: 1px solid rgba(255,255,255,0.16);
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
      color: var(--text); cursor: pointer; box-shadow: 0 2px 10px rgba(0,0,0,0.25);
      display: inline-flex; align-items: center; justify-content: center; letter-spacing: .2px;
      flex: 0 0 auto;
    }
    /* Primary actions grow to the same size for symmetry */
    .song-info-actions .btn-small.primary { flex: 1 1 240px; color: #fff; border: none; background: linear-gradient(90deg, var(--accent1), var(--accent2)); }
    /* Remove is secondary emphasis, a fixed comfortable width */
    .song-info-actions .btn-small.btn-danger { flex: 0 0 160px; background: linear-gradient(90deg, #ff6b6b, #ff9a7b); color: #fff; border: none; }
    /* Close is compact */
    
    .btn-small:hover { filter: brightness(1.06); }
    .btn-link { text-decoration: none; color: var(--text); }
    .song-info-body { padding: 16px; max-height: 58vh; overflow: auto; }
    .song-info-lyrics {
      white-space: pre-wrap;
      font-family: 'Poppins', sans-serif;
      line-height: 1.35;
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 12px 14px;
    }
    #song-info-close { margin: 12px; align-self: flex-end; }

  
    /* --- Song info actions layout fix (GUI5) --- */
    .song-info-actions {
      display: grid !important;
      grid-template-columns: repeat(4, 1fr) !important;
      gap: 10px !important;
      margin-top: 10px !important;
      align-items: stretch !important;
    }
    @media (max-width: 900px) {
      .song-info-actions { grid-template-columns: repeat(2, 1fr) !important; }
    }
    .song-info-actions .btn-small {
      width: 100% !important;
      min-height: 56px !important;
      border-radius: 12px !important;
      padding: 0 16px !important;
    }
    .song-info-actions .btn-small.primary {
      border: none !important;
      background: linear-gradient(90deg, var(--accent1), var(--accent2)) !important;
      color: #fff !important;
    }
    .song-info-actions .btn-small.btn-danger {
      border: none !important;
      background: linear-gradient(90deg, #ff6b6b, #ff9a7b) !important;
      color: #fff !important;
    }
    


/* --- GUI5.1 compact song-info action bar --- */
.song-info-actions { display:flex !important; gap:10px !important; flex-wrap:wrap !important; align-items:center !important; }
.song-info-actions .btn-small { min-height:44px !important; padding:0 14px !important; border-radius:10px !important; font-size:.95em !important; }
.song-info-actions .btn-small.primary { flex:0 0 auto !important; }
.song-info-actions .btn-small.btn-danger { flex:0 0 auto !important; }
#song-info-close.btn-small { flex:0 0 auto !important; }


    /* GUI7: refined song-info actions */
    .song-info-actions {
      display: grid !important;
      grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
      gap: 10px !important;
      margin-top: 10px !important;
      align-items: stretch !important;
    }
    .song-info-actions .btn-small { 
      min-height: 46px !important; 
      padding: 0 14px !important; 
      border-radius: 12px !important;
      font-size: .95em !important; 
    }

    /* GUI7: clearer lyrics preview and stronger hierarchy */
    .song-info-title { font-size: 1.5em !important; }
    .song-info-lyrics {
      backdrop-filter: blur(6px) saturate(120%) !important;
      -webkit-backdrop-filter: blur(6px) saturate(120%) !important;
    }
</style>
</head>
<body>
  <!-- Backdrop effects -->
  <div class="fx fx-aurora"></div>
  <div class="fx fx-aurora2"></div>
  <div class="fx fx-grid"></div>

  <div class="container">
    <div class="overlay">
      <div class="header">
        <h1>Worship Slides Generator</h1>
        <div class="subtitle">Build your setlist • Match songs • Generate Slides</div>
      </div>

      <div class="card section" id="add-bar">
        <div class="input-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M21 21l-4.35-4.35" stroke="white" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>
            <circle cx="11" cy="11" r="7" stroke="white" stroke-opacity=".7" stroke-width="2" fill="none"/>
          </svg>
          <input type="text" id="song-input" placeholder="Enter song title (optional: title – artist)" autocomplete="off">
        </div>
        <button class="btn btn-primary" id="add-btn">Add Song</button>
      </div>

      <ul id="songs-list"></ul>

      <div class="actions">
        <button id="generate-btn">Generate Slides</button>
        <div id="loading">Creating presentation... Please wait.</div>
        <div id="result-link" style="display:none;"></div>
      </div>
    </div>
  </div>

  <div id="suggestion-modal" class="modal">
    <div class="modal-content">
      <h2>Select a song</h2>
      <div id="suggestion-list"></div>
      <div class="close-btn"><button id="cancel-suggestions">Close</button></div>
    </div>
  </div>

  <!-- Section/Flow editor modal -->
  <div id="flow-modal" class="modal">
    <div class="modal-content">
      <div class="flow-toolbar">
        <h2>Edit Song Sections</h2>
        <div class="left">
          <button class="btn btn-ghost" id="add-section">Add Section</button>
          <button class="btn btn-ghost" id="reset-flow">Reset</button>
          <button class="btn btn-primary" id="apply-flow">Apply</button>
          <button class="btn btn-danger" id="close-flow">Close</button>
        </div>
      </div>
      <div class="subtitle" id="flow-song-label" style="margin-bottom:6px;"></div>
      <div class="hint">Reorder, duplicate, or delete sections. Edit the text inside each section (one lyric line per line). When you apply, slides will be auto‑chunked into two‑line slides.</div>
      <div id="section-list" class="section-list"></div>
    </div>
  </div>


  <!-- Song info modal -->
  <div id="song-info-modal" class="modal">
    <div class="modal-content" id="song-info-card">
      <button class="modal-x" id="song-info-x" aria-label="Close">✕</button>
      <div class="song-info-header" id="song-info-header">
        <img class="song-info-cover" id="song-info-cover" src="" alt="">
        <div class="song-info-meta">
          <div class="song-info-title" id="song-info-title"></div>
          <div class="song-info-sub">
            <span class="song-info-pill" id="song-info-album" style="display:none;"></span>
            <span class="song-info-pill" id="song-info-date" style="display:none;"></span>
            <a class="song-info-pill btn-link" id="song-info-genius" href="#" target="_blank" rel="noopener" style="display:none;">View on Genius ↗</a>
          </div>
          <div class="song-info-actions">
            <button class="btn-small primary" id="song-info-edit">Edit sections</button>
            <button class="btn-small primary" id="song-info-replace">Replace match</button>
            <button class="btn-small btn-danger" id="song-info-remove">Remove</button>
</div>
        </div>
      </div>
      <div class="song-info-body">
        <div class="subtitle" style="margin-bottom:8px;">Lyrics preview</div>
        <div class="song-info-lyrics" id="song-info-lyrics">Loading…</div>
      </div>
    </div>
  </div>

  <script>
    const songs = [];

    function hexToRgb(hex) {
      const res = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex);
      return res ? { r: parseInt(res[1], 16), g: parseInt(res[2], 16), b: parseInt(res[3], 16) } : {r:0,g:0,b:0};
    }

    function hexToRgba(hex, a) {
      const {r,g,b} = hexToRgb(hex);
      return `rgba(${r}, ${g}, ${b}, ${a})`;
    }
    function autoGrow(ta) { if (!ta) return; ta.style.height = 'auto'; ta.style.height = (ta.scrollHeight + 2) + 'px'; ta.style.overflowY = 'hidden'; }
    function relLuminance({r,g,b}) {
      const sr = r/255, sg = g/255, sb = b/255;
      const R = sr <= 0.03928 ? sr/12.92 : Math.pow((sr+0.055)/1.055, 2.4);
      const G = sg <= 0.03928 ? sg/12.92 : Math.pow((sg+0.055)/1.055, 2.4);
      const B = sb <= 0.03928 ? sb/12.92 : Math.pow((sb+0.055)/1.055, 2.4);
      return 0.2126*R + 0.7152*G + 0.0722*B;
    }
    function contrastRatio(L1, L2) { const [a, b] = L1 > L2 ? [L1, L2] : [L2, L1]; return (a + 0.05) / (b + 0.05); }
    function pickTextColor(lightHex, darkHex) {
      const L_light = relLuminance(hexToRgb(lightHex));
      const L_dark  = relLuminance(hexToRgb(darkHex));
      const L_white = 1.0;
      const L_black = relLuminance(hexToRgb('#111111'));
      const minWhiteContrast = Math.min(contrastRatio(L_light, L_white), contrastRatio(L_dark, L_white));
      const minBlackContrast = Math.min(contrastRatio(L_light, L_black), contrastRatio(L_dark, L_black));
      return (minWhiteContrast >= minBlackContrast) ? '#ffffff' : '#111111';
    }

    function renderSongs() {
      const list = document.getElementById('songs-list');
      list.innerHTML = '';
      songs.forEach((song, idx) => {
        const li = document.createElement('li');
        li.className = 'song-item';
        const light = song.lightColor || '#444444';
        const dark = song.darkColor || '#222222';
        li.style.background = `linear-gradient(90deg, ${light}, ${dark})`;
        const textColor = pickTextColor(light, dark);
        li.style.color = textColor;

        const mainDiv = document.createElement('div');
        mainDiv.className = 'song-main';

        const badge = document.createElement('div');
        badge.className = 'song-index';
        badge.textContent = (idx + 1);
        mainDiv.appendChild(badge);

        if (song.thumbnail) {
          const img = document.createElement('img');
          img.className = 'song-art';
          img.src = song.thumbnail;
          img.alt = '';
          mainDiv.appendChild(img);
        }
        const titleSpan = document.createElement('span');
        titleSpan.className = 'song-title';
        let display = song.title;
        if (song.artist) { display += ' – ' + song.artist; }
        titleSpan.textContent = display;
        mainDiv.appendChild(titleSpan);
        // Info moved to indicator; card click no longer opens modal

        if ((song.customSlides && song.customSlides.length) || (song.customSections && song.customSections.length)) {
          const pill = document.createElement('span');
          pill.className = 'pill';
          pill.textContent = 'Edited';
          mainDiv.appendChild(pill);
        }

        li.appendChild(mainDiv);

        const controls = document.createElement('div');
        controls.className = 'song-controls';
        const editBtn = document.createElement('button'); editBtn.innerHTML = '✎'; editBtn.title = 'Edit sections'; editBtn.onclick = () => openFlowEditor(idx);
        const upBtn = document.createElement('button'); upBtn.innerHTML = '▲'; upBtn.title = 'Move up'; upBtn.onclick = () => moveSong(idx, -1);
        const downBtn = document.createElement('button'); downBtn.innerHTML = '▼'; downBtn.title = 'Move down'; downBtn.onclick = () => moveSong(idx, 1);
        const delBtn = document.createElement('button'); delBtn.innerHTML = '✖'; delBtn.title = 'Remove'; delBtn.onclick = () => removeSong(idx);
        controls.appendChild(editBtn); controls.appendChild(upBtn); controls.appendChild(downBtn); controls.appendChild(delBtn);
        const infoBtn = document.createElement('button'); infoBtn.className='info-indicator'; infoBtn.innerHTML = 'ℹ️'; infoBtn.title = 'Info'; infoBtn.onclick = () => openSongInfo(idx); controls.appendChild(infoBtn); li.appendChild(controls);
        list.appendChild(li);
      });
    }

    function moveSong(index, direction) {
      const newIndex = index + direction;
      if (newIndex < 0 || newIndex >= songs.length) return;
      const tmp = songs[index]; songs[index] = songs[newIndex]; songs[newIndex] = tmp; 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
    }
    function removeSong(index) { songs.splice(index, 1); 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs(); }

    document.getElementById('add-btn').addEventListener('click', () => {
      const input = document.getElementById('song-input');
      const query = input.value.trim();
      if (!query) return;
      fetch('/suggest?q=' + encodeURIComponent(query))
        .then(resp => resp.json())
        .then(data => {
          if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(query, data.suggestions);
          } else {
            const song = { title: query, artist: '', url: null, thumbnail: null, lightColor: '#444444', darkColor: '#222222', customSlides: null, customSections: null };
            songs.push(song); input.value = ''; 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
          }
        })
        .catch(err => { console.error(err); });
    });

    
    function showSuggestions(original, suggestions) {
      const modal = document.getElementById('suggestion-modal');
      const list = document.getElementById('suggestion-list');
      list.innerHTML = '';

      // Keep the "Use as typed" as a simple option at the top
      const typedItem = document.createElement('div');
      typedItem.className = 'suggestion-item';
      typedItem.textContent = 'Use "' + original + '" as typed';
      typedItem.onclick = () => {
        songs.push({ title: original, artist: '', url: null, thumbnail: null, lightColor: '#444444', darkColor: '#222222', customSlides: null, customSections: null });
        document.getElementById('song-input').value = ''; hideSuggestions(); 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
      };
      list.appendChild(typedItem);

      // Candidate cards matching the beauty of the song list
      suggestions.forEach((sug, i) => {
        const card = document.createElement('div');
        card.className = 'sugg-card';

        const art = document.createElement('img');
        art.className = 'sugg-art';
        if (sug.thumbnail) { art.src = sug.thumbnail; } else { art.style.display = 'none'; }

        const meta = document.createElement('div');
        meta.className = 'sugg-meta';

        const title = document.createElement('div');
        title.className = 'sugg-title';
        title.textContent = sug.title + (sug.artist ? ' – ' + sug.artist : '');

        const sub = document.createElement('div');
        sub.className = 'sugg-sub';
        sub.textContent = 'Tap to select';

        meta.appendChild(title);
        meta.appendChild(sub);

        const star = document.createElement('div');
        star.className = 'sugg-star';
        star.textContent = '★';
        if (i === 0) { star.style.display = 'flex'; star.title = 'Most likely match'; }

        card.appendChild(art);
        card.appendChild(meta);
        card.appendChild(star);

        card.onclick = () => {
          const song = { title: sug.title, artist: sug.artist || '', url: sug.url || null, thumbnail: sug.thumbnail || null, gid: sug.gid || null,
            lightColor: '#444444', darkColor: '#222222', customSlides: null, customSections: null };
          songs.push(song); document.getElementById('song-input').value = ''; hideSuggestions(); 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
          if (song.thumbnail) {
            fetch('/color?url=' + encodeURIComponent(song.thumbnail))
              .then(resp => resp.json())
              .then(data => { if (data.light && data.dark) { song.lightColor = data.light; song.darkColor = data.dark; 
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs(); } })
              .catch(err => console.error(err));
          }
        };

        list.appendChild(card);

        // Theme the card using album art colours, match song cards
        if (sug.thumbnail) {
          fetch('/color?url=' + encodeURIComponent(sug.thumbnail))
            .then(resp => resp.json())
            .then(data => {
              if (data.light && data.dark) {
                card.style.background = 'linear-gradient(90deg, ' + data.light + ', ' + data.dark + ')';
                const textColor = pickTextColor(data.light, data.dark);
                card.style.color = textColor;
              }
            })
            .catch(() => {});
        }
      });

      modal.style.display = 'flex'; autosizeSoon();
    }
    function hideSuggestions() { document.getElementById('suggestion-modal').style.display = 'none'; }

    document.getElementById('cancel-suggestions').addEventListener('click', hideSuggestions);

    // ---------- Section editor ----------
    let editingIndex = null;
    let sectionData = []; // array of {label, text}

    const SECTION_CHOICES = ['VERSE','CHORUS','PRE-CHORUS','BRIDGE','TAG','INSTRUMENTAL','REFRAIN','INTRO','OUTRO','CUSTOM'];
    // lookup of source sections by canonical label + a round-robin cursor
    let sourceLookup = {};
    let sourceCursor = {};
    function canonicalLabelBase(lbl) {
      const u = (lbl || '').toUpperCase();
      for (const opt of SECTION_CHOICES) {
        if (u.startsWith(opt)) return opt;
      }
      return 'CUSTOM';
    }
    function getDefaultTextForLabel(lbl) {
      const canon = canonicalLabelBase(lbl);
      const arr = sourceLookup[canon] || [];
      if (arr.length === 0) return '';
      const idx = (sourceCursor[canon] || 0) % arr.length;
      sourceCursor[canon] = idx + 1;
      return arr[idx];
    }


    function openFlowEditor(idx) {
      editingIndex = idx;
      const song = songs[idx];
      document.getElementById('flow-song-label').textContent = (song.artist ? `${song.title} – ${song.artist}` : song.title);

      const seed = (song.customSections && song.customSections.length)
        ? Promise.resolve({sections: song.customSections})
        : fetch(`/lyrics?title=${encodeURIComponent(song.title)}&artist=${encodeURIComponent(song.artist||'')}&url=${encodeURIComponent(song.url||'')}`).then(r=>r.json());

      
      // Theme the modal using album art colors
      try {
        const light = song.lightColor || '#444444';
        const dark = song.darkColor || '#222222';
        const modalContent = document.querySelector('#flow-modal .modal-content');
        if (modalContent) {
          modalContent.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
          modalContent.style.border = `1px solid ${hexToRgba(dark,0.25)}`;
        }
      } catch(e) { console.warn('Theme apply failed', e); }
seed.then(data => {
        // Build a catalog of original sections for quick switching by label
        sourceLookup = {}; sourceCursor = {};
        if (data.sections && data.sections.length) {
          data.sections.forEach(s => {
            const canon = canonicalLabelBase(s.label || '');
            const t = (s.text || '').trim();
            if (!sourceLookup[canon]) sourceLookup[canon] = [];
            if (t) sourceLookup[canon].push(t);
          });
        }

        if (data.sections && data.sections.length) {
          sectionData = data.sections.map(s => ({label: s.label || 'SECTION', text: (s.text || '').trim()}));
        } else if (data.slides && data.slides.length) {
          const lines = [];
          data.slides.forEach(p => { p.forEach(line => lines.push(line)); });
          sectionData = [{label:'SECTION', text: lines.join('\\n')}];
        } else {
          sectionData = [{label:'SECTION', text:''}];
        }
        renderSectionList();
        document.getElementById('flow-modal').style.display = 'flex';
      }).catch(err => {
        console.error(err);
        sectionData = [{label:'SECTION', text:''}];
        renderSectionList();
        document.getElementById('flow-modal').style.display = 'flex';
      });
    }

    function renderSectionList() {
      const list = document.getElementById('section-list');
      list.innerHTML = '';
      sectionData.forEach((sec, i) => {
        const wrap = document.createElement('div');
        wrap.className = 'section-item';
        try {
          const song = songs[editingIndex] || {};
          const light = song.lightColor || '#444444';
          const dark = song.darkColor || '#222222';
          wrap.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.16)}, ${hexToRgba(dark,0.10)})`;
          wrap.style.borderColor = `${hexToRgba(dark,0.28)}`;
        } catch(e) {}


        const labelWrap = document.createElement('div');
        labelWrap.className = 'section-label';
        const sel = document.createElement('select');
        SECTION_CHOICES.forEach(opt => {
          const o = document.createElement('option');
          o.value = opt; o.textContent = opt;
          if ((sec.label||'').toUpperCase().startsWith(opt) && opt!=='CUSTOM') o.selected = true;
          sel.appendChild(o);
        });
        const customInput = document.createElement('input');
        customInput.type = 'text'; customInput.placeholder = 'Custom label'; customInput.style.marginTop = '8px';

        function syncCustomVisibility() {
          if (sel.value === 'CUSTOM') {
            customInput.style.display = 'block';
            customInput.value = (sec.label && !SECTION_CHOICES.some(c=>sec.label.toUpperCase().startsWith(c))) ? sec.label : '';
          } else {
            customInput.style.display = 'none';
          }
        }
        sel.onchange = () => {
          const newLabel = sel.value;
          if (newLabel !== 'CUSTOM') sec.label = newLabel;
          const suggestion = getDefaultTextForLabel(newLabel);
          if (suggestion) { sec.text = suggestion; ta.value = suggestion; autoGrow(ta); }
          syncCustomVisibility();
        };
        syncCustomVisibility();

        labelWrap.appendChild(sel);
        labelWrap.appendChild(customInput);

        const ta = document.createElement('textarea');
        ta.placeholder = 'Enter lyrics for this section (one line per lyric line)';
        ta.value = sec.text || ''; autoGrow(ta);
        ta.oninput = e => { sec.text = e.target.value; autoGrow(e.target); };

        const ctrls = document.createElement('div');
        ctrls.className = 'section-controls';
        const up = document.createElement('button'); up.title='Move up'; up.textContent='▲'; up.onclick=()=>{ if(i>0){ [sectionData[i-1], sectionData[i]]=[sectionData[i], sectionData[i-1]]; renderSectionList(); } };
        const down = document.createElement('button'); down.title='Move down'; down.textContent='▼'; down.onclick=()=>{ if(i<sectionData.length-1){ [sectionData[i+1], sectionData[i]]=[sectionData[i], sectionData[i+1]]; renderSectionList(); } };
        const dup = document.createElement('button'); dup.title='Duplicate'; dup.textContent='⧉'; dup.onclick=()=>{ sectionData.splice(i+1,0,{label:sec.label, text:sec.text}); renderSectionList(); };
        const del = document.createElement('button'); del.title='Delete'; del.textContent='✖'; del.onclick=()=>{ sectionData.splice(i,1); if(sectionData.length===0) sectionData=[{label:'SECTION', text:''}]; renderSectionList(); };
        ctrls.appendChild(up); ctrls.appendChild(down); ctrls.appendChild(dup); ctrls.appendChild(del);

        wrap.appendChild(labelWrap);
        wrap.appendChild(ta);
        wrap.appendChild(ctrls);
        list.appendChild(wrap);

        customInput.addEventListener('input', e => { sec.label = e.target.value || 'SECTION'; });
      });
    }

    document.getElementById('add-section').addEventListener('click', ()=>{ sectionData.push({label:'VERSE', text:getDefaultTextForLabel('VERSE')||''}); renderSectionList(); });
    document.getElementById('apply-flow').addEventListener('click', ()=>{
      const cleanedSections = sectionData.map(s => ({
        label: (s.label||'SECTION').toUpperCase(),
        text: (s.text||'').split(/\\r?\\n/).map(t=>t.trim()).filter(Boolean).join('\\n')
      })).filter(s => s.text.length>0);
      const slides = [];
      cleanedSections.forEach(sec => {
        const lines = sec.text.split(/\\r?\\n/).filter(Boolean);
        for (let i=0;i<lines.length;i+=2) {
          const pair = [lines[i]];
          if (i+1 < lines.length) pair.push(lines[i+1]);
          slides.push(pair);
        }
      });
      songs[editingIndex].customSections = cleanedSections;
      songs[editingIndex].customSlides = slides;
      document.getElementById('flow-modal').style.display = 'none';
      
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
    });
    document.getElementById('reset-flow').addEventListener('click', ()=>{
      songs[editingIndex].customSections = null;
      songs[editingIndex].customSlides = null;
      document.getElementById('flow-modal').style.display = 'none';
      
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
    });
    document.getElementById('close-flow').addEventListener('click', ()=>{ document.getElementById('flow-modal').style.display = 'none'; });
    window.addEventListener('keydown', (e)=>{ if(e.key==='Escape'){ document.getElementById('flow-modal').style.display = 'none'; } });

    document.getElementById('generate-btn').addEventListener('click', () => {
      if (songs.length === 0) return;
      const btn = document.getElementById('generate-btn'); btn.disabled = true;
      document.getElementById('loading').style.display = 'block';
      const payloadSongs = songs.map(s => ({ title: s.title, artist: s.artist, url: s.url, customSlides: s.customSlides || null }));
      fetch('/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ songs: payloadSongs }) })
      .then(resp => resp.json())
      .then(data => {
        document.getElementById('loading').style.display = 'none'; btn.disabled = false;
        const linkDiv = document.getElementById('result-link');
        if (data.status === 'ok') { linkDiv.style.display = 'block'; linkDiv.innerHTML = 'Your presentation is ready: <a href="' + data.url + '" target="_blank">Open in Google Slides</a>'; }
        else { linkDiv.style.display = 'block'; linkDiv.innerHTML = 'Error: ' + (data.message || 'Unknown error'); }
      })
      .catch(err => { document.getElementById('loading').style.display = 'none'; btn.disabled = false; alert('An error occurred generating slides.'); });
    });

    
    // --- Song Info modal ---
    function setInfoBG(light, dark) {
      try {
        const card = document.getElementById('song-info-card');
        card.style.background = `linear-gradient(180deg, ${hexToRgba(light,0.18)}, ${hexToRgba(dark,0.14)})`;
        card.style.border = `1px solid ${hexToRgba(dark,0.28)}`;
      } catch {}
    }

    function openSongInfo(index) {
      const s = songs[index];
      const modal = document.getElementById('song-info-modal');
      const cover = document.getElementById('song-info-cover');
      const title = document.getElementById('song-info-title');
      const album = document.getElementById('song-info-album');
      const date = document.getElementById('song-info-date');
      const genius = document.getElementById('song-info-genius');
      const lyricsBox = document.getElementById('song-info-lyrics');

      // Theme + basic fields
      const display = s.artist ? `${s.title} – ${s.artist}` : s.title;
      title.textContent = display;
      cover.src = s.thumbnail || '';
      lyricsBox.textContent = 'Loading…';
      album.style.display = 'none'; date.style.display = 'none'; genius.style.display = 'none';
      setInfoBG(s.lightColor || '#444444', s.darkColor || '#222222');

      // Wire actions
      document.getElementById('song-info-edit').onclick = () => { modal.style.display = 'none'; openFlowEditor(index); };
      document.getElementById('song-info-replace').onclick = async () => {
        modal.style.display = 'none';
        const query = s.artist ? `${s.title} – ${s.artist}` : s.title;
        const resp = await fetch('/suggest?q=' + encodeURIComponent(query));
        const data = await resp.json();
        showSuggestions(query, data.suggestions || []);
      };
      document.getElementById('song-info-remove').onclick = () => { modal.style.display = 'none'; removeSong(index); };
      document.getElementById('song-info-x').onclick = () => { modal.style.display = 'none'; };
      modal.onclick = e => { if (e.target === modal) modal.style.display = 'none'; };

      // Fetch metadata
      const params = new URLSearchParams();
      if (s.gid) params.set('gid', s.gid);
      if (s.url) params.set('url', s.url);
      if (s.title) params.set('title', s.title);
      if (s.artist) params.set('artist', s.artist);

      fetch('/songinfo?' + params.toString())
        .then(r => r.json())
        .then(info => {
          if (info.error) throw new Error(info.error);
          // Apply album/date/genius
          if (info.album) { album.textContent = info.album; album.style.display = 'inline-flex'; }
          if (info.release_date) { date.textContent = info.release_date; date.style.display = 'inline-flex'; }
          if (info.url) { genius.href = info.url; genius.style.display = 'inline-flex'; }
          // Update cover and theme if better art provided
          if (info.thumbnail && !s.thumbnail) cover.src = info.thumbnail;
          if (info.colors && info.colors.light && info.colors.dark) setInfoBG(info.colors.light, info.colors.dark);
          // Lyrics preview
          const preview = (info.preview || '').trim();
          lyricsBox.textContent = preview ? preview : 'No lyrics preview available.';
        }).catch(() => {
          lyricsBox.textContent = 'Could not load metadata.';
        });

      modal.style.display = 'flex';
    }

    renderSongs();
  </script>
</body>
</html>

"""

_template_str = INDEX_HTML_TEMPLATE.replace('{{', '{').replace('}}', '}')
INDEX_HTML = Template(_template_str).safe_substitute(bg_data=BACKGROUND_DATA)

import io

def _lighten(r, g, b, factor=0.35):
    lr = int(r + (255 - r) * factor); lg = int(g + (255 - g) * factor); lb = int(b + (255 - b) * factor)
    return lr, lg, lb

def _darken(r, g, b, factor=0.35):
    dr = int(r * (1 - factor)); dg = int(g * (1 - factor)); db = int(b * (1 - factor))
    return dr, dg, db

def _to_hex(rgb_tuple):
    r, g, b = rgb_tuple; return f"#{r:02x}{g:02x}{b:02x}"

def compute_gradient_colors(image_url: str):
    if PIL_AVAILABLE:
        try:
            resp = requests.get(image_url, timeout=10); resp.raise_for_status()
            from PIL import Image
            with Image.open(io.BytesIO(resp.content)) as im:
                im = im.convert('RGB').resize((1, 1))
                r, g, b = im.getpixel((0, 0))
            return _to_hex(_lighten(r, g, b)), _to_hex(_darken(r, g, b))
        except Exception:
            pass
    try:
        resp = requests.get(image_url, timeout=10); resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
            tmp.write(resp.content); tmp.flush()
            output = subprocess.check_output(['convert', tmp.name, '-resize', '1x1!', 'txt:-'],
                                             stderr=subprocess.DEVNULL, text=True)
        match = re.search(r'\((\d+),\s*(\d+),\s*(\d+)\)', output)
        if not match: raise ValueError('Could not parse colour')
        r, g, b = map(int, match.groups())
        return _to_hex(_lighten(r, g, b)), _to_hex(_darken(r, g, b))
    except Exception:
        return '#444444', '#222222'

def get_suggestions(query: str, max_results: int = 5):
    token = os.getenv('GENIUS_ACCESS_TOKEN')
    genius = Genius(token, skip_non_songs=True, excluded_terms=['(Remix)', '(Live)'], remove_section_headers=True, timeout=15, retries=3)
    try:
        search_results = genius.search_songs(query, per_page=max_results); hits = search_results.get('hits', []) if search_results else []
    except Exception: hits = []
    suggestions = []
    if not hits:
        try: song_obj = genius.search_song(query)
        except Exception: song_obj = None
        if song_obj: suggestions.append({'title': song_obj.title, 'artist': song_obj.artist, 'url': song_obj.url})
        return suggestions
    WORSHIP_KEYWORDS = ['worship','praise','christ','jesus','god','hillsong','bethel','church','faith','grace','redeemer','lord','holy','gospel','alive','blessing','spirit','hope','saved']
    for hit in hits:
        result = hit.get('result', {})
        title = result.get('title', ''); artist = result.get('primary_artist', {}).get('name', '')
        url = result.get('url', None); art = result.get('song_art_image_thumbnail_url') or result.get('header_image_thumbnail_url') or None
        combined = f"{title} {artist}".lower(); score = sum(1 for kw in WORSHIP_KEYWORDS if kw in combined)
        suggestions.append({'title': title, 'artist': artist, 'url': url, 'thumbnail': art, 'gid': result.get('id'), 'score': score})
    suggestions.sort(key=lambda s: s['score'], reverse=True)
    for s in suggestions: s.pop('score', None)
    return suggestions[:max_results]

def fetch_lyrics_by_selection(title: str, artist: str, url: str | None) -> str:
    token = os.getenv('GENIUS_ACCESS_TOKEN')
    genius = Genius(token, skip_non_songs=True, excluded_terms=['(Remix)', '(Live)'], remove_section_headers=True, timeout=15, retries=3)
    lyrics = None
    if url:
        try: lyrics = genius.lyrics(song_url=url)
        except Exception: lyrics = None
    if not lyrics:
        try: song_obj = genius.search_song(title, artist)
        except Exception: song_obj = None
        if song_obj and song_obj.lyrics: lyrics = song_obj.lyrics
    if not lyrics: raise ValueError(f"Could not retrieve lyrics for {title} {('by ' + artist) if artist else ''}")
    return lyrics


def fetch_lyrics_with_headers(title: str, artist: str, url: str | None) -> str:
    """Fetch lyrics from Genius but KEEP section headers (e.g., [Verse 1], [Chorus])."""
    token = os.getenv('GENIUS_ACCESS_TOKEN')
    genius = Genius(token, skip_non_songs=True, excluded_terms=[..., '(Live)'], remove_section_headers=False, timeout=15, retries=3)
    lyrics = None
    if url:
        try:
            lyrics = genius.lyrics(song_url=url)
        except Exception:
            lyrics = None
    if not lyrics:
        try:
            song_obj = genius.search_song(title, artist)
        except Exception:
            song_obj = None
        if song_obj and song_obj.lyrics:
            lyrics = song_obj.lyrics
    if not lyrics:
        raise ValueError(f"Could not retrieve lyrics (with headers) for {title} {('by ' + artist) if artist else ''}")
    return lyrics


SECTION_ALIASES = {
    'VERSE': ['VERSE', 'VS', 'V'],
    'CHORUS': ['CHORUS', 'CHO', 'C', 'REFRAIN'],
    'PRE-CHORUS': ['PRE-CHORUS', 'PRECHORUS', 'PRE CHORUS', 'PRE-CHO', 'PRE', 'BUILD'],
    'BRIDGE': ['BRIDGE', 'BRG', 'B'],
    'TAG': ['TAG', 'OUTRO', 'CODA', 'ENDING'],
    'INTRO': ['INTRO', 'INSTRUMENTAL', 'INTERLUDE'],
    'INSTRUMENTAL': ['INSTRUMENTAL', 'INTERLUDE'],
    'REFRAIN': ['REFRAIN'],
    'OUTRO': ['OUTRO'],
}

def _normalize_section_label(raw: str) -> str:
    s = re.sub(r'[^A-Za-z0-9\-\s]', '', raw or '').strip().upper()
    s = s.replace('  ', ' ')
    for canon, aliases in SECTION_ALIASES.items():
        for a in aliases:
            if s.startswith(a):
                return s  # keep any numbering, e.g., "VERSE 2"
    return s or 'SECTION'

def parse_lyrics_sections(lyrics: str) -> list[dict]:
    """
    Parse Genius-style lyrics with headers like [Verse 1], [Chorus].
    Returns a list of dicts: {{'label': 'VERSE 1', 'text': 'LINE\nLINE\n...'}}
    """
    IGNORE_PATTERNS = [
        r'you might also like', r'translation', r'translations', r'contributors?', r'lyrics\b',
        r'embed$', r'copyright', r'contributor', r'powered by',
        r'^\s*produced by\b',
        r'^\s*writ(?:ten|er)s?\s+by\b',
        r'^\s*release date\b',
        r'^\s*album\b',
        r'^\s*genius\b',
        r'^\s*urlcopyembed\b',
        r'^\s*embedshare\b',
        r'^\s*\d+\s*embed$',
        r'^\s*\d+\s*$',
        r'^\s*\[[^\]]*official[^\]]*\]\s*$',
        r'^\s*\([^)]+\)\s*$',
    ]
    lines = [ln.strip() for ln in lyrics.splitlines()]
    # remove empty and ignored
    cleaned = []
    for ln in lines:
        if not ln:
            continue
        low = ln.lower()
        if any(re.search(pat, low) for pat in IGNORE_PATTERNS):
            continue
        cleaned.append(ln)

    sections = []
    current_label = 'SECTION'
    buf = []
    header_re = re.compile(r'^\[(.+?)\]\s*$')
    for ln in cleaned:
        m = header_re.match(ln)
        if m:
            # flush previous
            if buf:
                sections.append({'label': _normalize_section_label(current_label), 'text': '\n'.join(buf).strip()})
                buf = []
            current_label = m.group(1)
            continue
        buf.append(ln)
    if buf:
        sections.append({'label': _normalize_section_label(current_label), 'text': '\n'.join(buf).strip()})

    # If we didn't find headers, return a single section
    if not sections:
        joined = '\n'.join(cleaned).strip().upper()
        if joined:
            sections = [{'label': 'SECTION', 'text': joined}]
    else:
        # uppercase text for consistency with slides
        for s in sections:
            s['text'] = '\n'.join([t.upper() for t in s['text'].splitlines() if t.strip()])

    return sections


def create_setlist_presentation_no_launch(service, setlist_title: str, songs_slides: list[tuple[str, list[list[str]]]]):
    try:
        presentation = service.presentations().create(body={'title': setlist_title}).execute()
        pres_id = presentation['presentationId']; default_id = presentation['slides'][0]['objectId']
        requests: list[dict] = []; requests.append({'deleteObject': {'objectId': default_id}})
        requests += lyrics_to_slides_improved._make_title_slide('deck_title', setlist_title)
        for sidx, (song_query, slides_content) in enumerate(songs_slides, start=1):
            song_title, _ = lyrics_to_slides_improved.split_title_artist(song_query)
            requests += lyrics_to_slides_improved._make_title_slide(f'song_title_{sidx}', song_title)
            for idx, lines in enumerate(slides_content):
                base_id = f'song{sidx}_slide{idx}'
                requests += [
                    {'createSlide': {'objectId': base_id, 'slideLayoutReference': {'predefinedLayout': 'BLANK'}}},
                    {'updatePageProperties': {'objectId': base_id, 'pageProperties': {'pageBackgroundFill': {'stretchedPictureFill': {'contentUrl': lyrics_to_slides_improved.BACKGROUND_IMAGE_URL}}}, 'fields': 'pageBackgroundFill.stretchedPictureFill.contentUrl'}}
                ]
                bar_width = lyrics_to_slides_improved.SLIDE_WIDTH * lyrics_to_slides_improved.BOX_WIDTH_RATIO
                x_off = (lyrics_to_slides_improved.SLIDE_WIDTH - bar_width) / 2
                count = len(lines); total_h = count * lyrics_to_slides_improved.BOX_HEIGHT + (count - 1) * lyrics_to_slides_improved.BOX_SPACING
                y_off = (lyrics_to_slides_improved.SLIDE_HEIGHT - total_h) / 2
                for j, line in enumerate(lines):
                    bar_id = f'{base_id}_bar{j}'; txt_id = f'{base_id}_txt{j}'
                    y = y_off + j * (lyrics_to_slides_improved.BOX_HEIGHT + lyrics_to_slides_improved.BOX_SPACING)
                    requests += [
                        {'createShape': {'objectId': bar_id, 'shapeType': 'RECTANGLE', 'elementProperties': {'pageObjectId': base_id, 'size': {'width': {'magnitude': bar_width, 'unit': 'PT'}, 'height': {'magnitude': lyrics_to_slides_improved.BOX_HEIGHT, 'unit': 'PT'}}, 'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': x_off, 'translateY': y, 'unit': 'PT'}}}},
                        {'updateShapeProperties': {'objectId': bar_id, 'shapeProperties': {'shapeBackgroundFill': {'solidFill': {'color': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}, 'alpha': lyrics_to_slides_improved.BOX_ALPHA}}, 'outline': {'propertyState': 'NOT_RENDERED'}}, 'fields': 'shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha,outline.propertyState'}},
                        {'createShape': {'objectId': txt_id, 'shapeType': 'TEXT_BOX', 'elementProperties': {'pageObjectId': base_id, 'size': {'width': {'magnitude': bar_width - 2 * lyrics_to_slides_improved.TEXT_INSET, 'unit': 'PT'}, 'height': {'magnitude': lyrics_to_slides_improved.BOX_HEIGHT - 2 * lyrics_to_slides_improved.TEXT_INSET, 'unit': 'PT'}}, 'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': x_off + lyrics_to_slides_improved.TEXT_INSET, 'translateY': y + lyrics_to_slides_improved.TEXT_INSET, 'unit': 'PT'}}}},
                        {'updateShapeProperties': {'objectId': txt_id, 'shapeProperties': {'shapeBackgroundFill': {'solidFill': {'alpha': 0}}, 'outline': {'propertyState': 'NOT_RENDERED'}, 'contentAlignment': 'MIDDLE'}, 'fields': 'shapeBackgroundFill.solidFill.alpha,outline.propertyState,contentAlignment'}},
                        {'insertText': {'objectId': txt_id, 'insertionIndex': 0, 'text': line}},
                        {'updateTextStyle': {'objectId': txt_id, 'style': {'fontFamily': 'Calibri', 'fontSize': {'magnitude': lyrics_to_slides_improved.FONT_SIZE, 'unit': 'PT'}, 'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}}, 'bold': False}, 'textRange': {'type': 'ALL'}, 'fields': 'fontFamily,fontSize,foregroundColor,bold'}},
                        {'updateParagraphStyle': {'objectId': txt_id, 'style': {'alignment': 'CENTER', 'lineSpacing': 100}, 'textRange': {'type': 'ALL'}, 'fields': 'alignment,lineSpacing'}}
                    ]
        service.presentations().batchUpdate(presentationId=pres_id, body={'requests': requests}).execute()
        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
        return url
    except Exception as e:
        raise

class SongRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path); path = parsed.path
        if path == '/':
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
            self.wfile.write(INDEX_HTML.encode('utf-8'))
        elif path == '/suggest':
            params = urllib.parse.parse_qs(parsed.query); query = params.get('q', [''])[0]
            try:
                suggestions = get_suggestions(query)
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'suggestions': suggestions}).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif path == '/color':
            params = urllib.parse.parse_qs(parsed.query); art_url = params.get('url', [''])[0]
            if not art_url:
                self.send_response(400); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'error': 'No url provided'}).encode('utf-8')); return
            try:
                light, dark = compute_gradient_colors(art_url)
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'light': light, 'dark': dark}).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        
        elif path == '/lyrics':
            params = urllib.parse.parse_qs(parsed.query)
            title = params.get('title', [''])[0]
            artist = params.get('artist', [''])[0]
            url = params.get('url', [''])[0] or None
            try:
                # fetch WITH headers to preserve [Chorus], [Bridge], etc.
                lyrics_raw = fetch_lyrics_with_headers(title, artist, url)
                sections = parse_lyrics_sections(lyrics_raw)
                # Also provide default slides as a fallback
                slides = lyrics_to_slides_improved.format_lyrics(lyrics_raw)
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'sections': sections, 'slides': slides}).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif path == '/songinfo':
            params = urllib.parse.parse_qs(parsed.query)
            gid = params.get('gid', [''])[0]
            title = params.get('title', [''])[0]
            artist = params.get('artist', [''])[0]
            url = params.get('url', [''])[0] or None
            try:
                token = os.getenv('GENIUS_ACCESS_TOKEN')
                genius = Genius(token, skip_non_songs=True, remove_section_headers=False, timeout=15, retries=3)
                data = {}
                # Prefer song endpoint when id is present
                if gid:
                    try:
                        resp = genius.song(gid)
                        song_json = (resp or {}).get('song', {})
                        data['title'] = song_json.get('title') or title
                        data['artist'] = (song_json.get('primary_artist') or {}).get('name') or artist
                        data['album'] = (song_json.get('album') or {}).get('name')
                        data['release_date'] = song_json.get('release_date_for_display') or song_json.get('release_date')
                        data['url'] = song_json.get('url') or url
                        data['thumbnail'] = song_json.get('song_art_image_url') or song_json.get('header_image_thumbnail_url')
                    except Exception:
                        pass
                # Fallback via search if we still lack basics
                if not data.get('url'):
                    try:
                        song_obj = genius.search_song(title, artist)
                        if song_obj:
                            data['title'] = data.get('title') or song_obj.title
                            data['artist'] = data.get('artist') or getattr(song_obj, 'artist', artist)
                            data['url'] = data.get('url') or getattr(song_obj, 'url', None)
                            data['thumbnail'] = data.get('thumbnail') or getattr(song_obj, 'song_art_image_url', None)
                    except Exception:
                        pass
                # Lyrics preview (short, clean)
                preview = ''
                try:
                    lyr = fetch_lyrics_with_headers(data.get('title') or title,
                                                   data.get('artist') or artist,
                                                   data.get('url') or url)
                    sections = parse_lyrics_sections(lyr)
                    if sections:
                        # take first non-empty section's first ~12 lines (filtering any leftover non-lyrics)
                        for sec in sections:
                            raw_lines = [ln.strip() for ln in sec.get('text','').splitlines() if ln.strip()]
                            filt = []
                            for ln in raw_lines:
                                low = ln.lower()
                                # drop any lingering metadata-like lines
                                if low.startswith(('produced by','written by','release date','album','genius')):
                                    continue
                                if low.endswith('embed') or low.endswith('lyrics'):
                                    continue
                                if len(ln) <= 2 and not ln.isalpha():
                                    continue
                                if ln.startswith('[') and ln.endswith(']'):
                                    continue
                                filt.append(ln)
                            if filt:
                                preview = '\n'.join(filt[:12]).strip()
                                break
                except Exception:
                    pass
                data['preview'] = preview
                # Extract palette from thumbnail for theming
                colors = None
                try:
                    art = data.get('thumbnail') or ''
                    if art:
                        light, dark = compute_gradient_colors(art)
                        colors = {'light': light, 'dark': dark}
                except Exception:
                    pass
                data['colors'] = colors
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        else:
            self.send_response(404); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/generate':
            try:
                content_length = int(self.headers.get('Content-Length', '0')); body = self.rfile.read(content_length)
                payload = json.loads(body.decode('utf-8')); songs = payload.get('songs', [])
                if not isinstance(songs, list) or not songs: raise ValueError('No songs provided')
                
                songs_slides: list[tuple[str, list[list[str]]]] = []

                def _sanitize_slides(slides_obj):
                    out = []
                    for pair in slides_obj or []:
                        if not isinstance(pair, list):
                            continue
                        lines = []
                        for s in pair:
                            if isinstance(s, str):
                                t = s.strip()
                                if t:
                                    lines.append(t.upper())
                            if len(lines) == 2:
                                break
                        if lines:
                            out.append(lines)
                    return out

                for song in songs:
                    title = song.get('title', '').strip()
                    artist = song.get('artist', '').strip()
                    url = song.get('url')
                    custom = song.get('customSlides')
                    if custom and isinstance(custom, list) and len(custom) > 0:
                        slides = _sanitize_slides(custom)
                        if not slides:
                            lyrics = fetch_lyrics_by_selection(title, artist, url)
                            slides = lyrics_to_slides_improved.format_lyrics(lyrics)
                    else:
                        lyrics = fetch_lyrics_by_selection(title, artist, url)
                        slides = lyrics_to_slides_improved.format_lyrics(lyrics)
                    query_string = f"{title} – {artist}".strip(' –'); songs_slides.append((query_string, slides))
                svc = lyrics_to_slides_improved.authenticate()
                try:
                    tz = ZoneInfo('America/Toronto'); now = datetime.datetime.now(tz)
                except Exception:
                    now = datetime.datetime.now()
                time_str = now.strftime('%I:%M%p').lstrip('0').lower()
                deck_title = f"{now.strftime('%B')} {now.day} Setlist Generated at {time_str}"
                url = create_setlist_presentation_no_launch(svc, deck_title, songs_slides)
                response = {'status': 'ok', 'url': url}
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
        else:
            self.send_response(404); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

def run_server():
    with socketserver.TCPServer(('127.0.0.1', 0), SongRequestHandler) as httpd:
        port = httpd.server_address[1]; url = f'http://127.0.0.1:{port}/'
        try:
            import webbrowser; threading.Timer(0.5, lambda: webbrowser.open_new(url)).start()
        except Exception: pass
        print(f"★ Worship Slides Generator running on {url}"); print("Press Ctrl+C to stop the server.")
        try: httpd.serve_forever()
        except KeyboardInterrupt: print("\\nStopping server...")

if __name__ == '__main__':
    run_server()