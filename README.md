# WebScraper2Dropbox — eGela → Dropbox Sync & Transfer Pipeline

A desktop GUI application that scrapes PDF course materials from the **eGela** (Moodle-based LMS of the University of the Basque Country / EHU) and transfers them directly to a user's **Dropbox** account, with file management capabilities.

> **Academic context:** Lab Practice 4 — Web Systems (*Sistemas Web*), EHU/UPV 

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Known Limitations](#known-limitations)

---

## Overview

This tool automates the tedious process of downloading PDFs from a university Moodle platform (eGela) and organizing them in Dropbox. It presents a dual-panel GUI where the left panel lists all PDFs found in the *Sistemas Web* course and the right panel shows the current Dropbox directory — files can be transferred with a single click.

---

## Features

**Core functionality**
- Authenticate against eGela (Moodle) via a standard username/password login flow
- Automatically discover and list all PDF resources across every section of the *Sistemas Web* course
- Authenticate with Dropbox using OAuth 2.0 (authorization code flow with a local redirect server)
- Transfer selected PDFs from eGela directly into any Dropbox folder

**Dropbox file management**
- Browse Dropbox directories with double-click navigation (including `..` to go up)
- Create folders
- Delete files
- Move files to a new path
- Rename files (implemented via Dropbox's move API)
- Download files from Dropbox to a local path
- Search files and folders within Dropbox

---

## Architecture

```
main.py          — Application entry point; builds the Tkinter GUI and wires all components
├── eGela.py     — Moodle/eGela HTTP client (login, PDF discovery, PDF download)
├── Dropbox.py   — Dropbox API client (OAuth, list, upload, delete, create folder, search, move, download)
└── helper.py    — Shared UI utilities (window centering, progress bars, listbox population)
```

The application runs three sequential windows:

1. **eGela Login** — credentials are submitted, a Moodle session is established, and all course PDF references are collected.
2. **Dropbox Login** — a local HTTP server on port 8070 captures the OAuth redirect and exchanges the auth code for an access token.
3. **Main Transfer Window** — dual-panel interface for browsing and transferring files.

---

## Prerequisites

- Python 3.8+
- A Dropbox account and a registered Dropbox app (App Key + App Secret)
- An active eGela account enrolled in the *Sistemas Web* course

### Python dependencies

```
requests
beautifulsoup4
tkinter   # included in standard Python distributions
```

Install with:

```bash
pip install requests beautifulsoup4
```

---

## Installation

```bash
git clone https://github.com/muulti/WebScraper2Dropbox_SyncNTransfer_pipeline.git
cd WebScraper2Dropbox_SyncNTransfer_pipeline
pip install requests beautifulsoup4
```

---

## Configuration

Open `Dropbox.py` and fill in your Dropbox app credentials:

```python
app_key    = 'YOUR_APP_KEY'
app_secret = 'YOUR_APP_SECRET'
```

You can create a Dropbox app at [https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps).

**Required OAuth 2 settings for the Dropbox app:**
- Permission type: **Full Dropbox** or **App Folder**
- Redirect URI: `http://localhost:8070`

> **Important:** The OAuth redirect listener binds to `localhost:8070`. Make sure this port is free before launching the app.

---

## Usage

```bash
python main.py
```

**Step 1 — eGela login**  
Enter your EHU/UPV username and password, then click *Login*. The app will log in, follow all Moodle redirects, and crawl all course sections to collect PDF links.

**Step 2 — Dropbox authorization**  
Click *Login*. Your browser will open the Dropbox authorization page. After granting access, the local server captures the redirect and exchanges the code for an access token automatically.

**Step 3 — Transfer & manage**  
- Select one or more PDFs in the left panel and click **>>>** to upload them to the current Dropbox folder.
- Navigate Dropbox folders by double-clicking (folders are highlighted in blue, the `..` parent entry in pink).
- Use the right-side buttons to **Delete**, **Create folder**, **Move**, **Download**, or **Rename** files.
- Use the **Buscar** search box to find files anywhere in your Dropbox.

---

## Project Structure

```
.
├── main.py          # GUI layout, event handlers, application flow
├── eGela.py         # eGela/Moodle HTTP client
├── Dropbox.py       # Dropbox API v2 client
├── helper.py        # Tkinter utilities (centering, progress bars, listbox)
└── README.md
```

---

## How It Works

### eGela authentication (5-step flow)

1. `GET /login/index.php` → obtain `MoodleSession` cookie and `logintoken`
2. `POST /login/index.php` with credentials → receive 303 redirect
3. Follow first redirect with session cookie
4. Follow final redirect to land on the Moodle dashboard; scrape the *Sistemas Web* course link
5. Verify login by fetching the user profile page

### PDF discovery

For each navigation section of the course page, the scraper follows links ending in `start`, finds all `/mod/resource/` links, and resolves each resource page to extract its `pluginfile` PDF download URL.

### Dropbox OAuth 2.0

A minimal raw TCP server is opened on port 8070 before the browser is launched. When Dropbox redirects back after user authorization, the server captures the `code` parameter from the GET request line and immediately exchanges it for an access/refresh token via `POST /oauth2/token`.

### File transfer

PDFs are fetched as raw bytes from eGela using the stored Moodle session cookie and pushed to Dropbox via the `/files/upload` endpoint with `mode: overwrite`.

---

## Known Limitations

- The eGela scraper is hardcoded to look for a course named **"Sistemas Web"**. To use it with a different course, update the course-name filter in `eGela.py → check_credentials()`.
- The OAuth redirect server uses plain TCP (not HTTPS). This is safe for `localhost` but would need upgrading for any remote deployment.
- Credentials are held in memory only; there is no token persistence between sessions.
- Folder downloads are not supported — only individual files can be downloaded.
