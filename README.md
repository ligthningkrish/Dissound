# 🔊 Dissound (MemeSound Bot)

> **A Smart Discord Bot for Discovering, Managing, and Adding Sounds to Server Soundboards**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-v2.5%2B-5865F2.svg)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Dissound solves the tedious, multi-step hassle of expanding Discord Server Soundboards. Instead of having to leave Discord, search multiple meme websites, download audio clips, manually trim or convert them to Discord's strict audio limits, and upload them via server settings, Dissound provides an **integrated sound discovery, preview, and automated upload experience directly inside Discord**.

---

## 🌟 Key Features

- 🔍 **Instant Sound Discovery**: Search an extensive meme catalog using `/search` with live autocomplete by keywords, tags, or categories.
- 🔊 **Direct Audio Previews**: Listen to audio clips right in your text channels via `/preview` before deciding to add them.
- ➕ **One-Click Soundboard Upload**: Add any sound to your guild's soundboard with a single button click using Discord's official Soundboard API.
- ⚡ **Automated Audio Processing**: Automatically converts incoming audio to Discord-compatible MP3, trims clips > 5.2s, optimizes file sizes to <= 512 KB, and normalizes playback volume.
- 📤 **Custom Audio Upload**: Upload your own audio files via `/upload`; Dissound will auto-trim, optimize, and install them into your server soundboard.
- 📊 **Soundboard Capacity & Status Tracking**: Run `/soundboard status` to monitor used/available slots according to your server's boost tier (Tier 0: 8 slots, Tier 1: 24 slots, Tier 2: 36 slots, Tier 3: 48 slots).
- 📜 **Server Audit & Upload History**: Full audit trail via `/history` showing which members added which sounds, timestamps, and status.
- ⚙️ **Customization Modal**: Fine-tune volume (0.1 to 1.0) and custom display names before installing.

---

## 🏗️ System Architecture

```
User in Discord Channel
       │
       ▼ (Slash Commands: /search, /preview, /add, /upload)
┌─────────────────────────────────────────────────────────────┐
│                       Dissound Bot                          │
│                                                             │
│   ┌────────────────────┐       ┌────────────────────────┐   │
│   │   Discovery Cog    │       │     Soundboard Cog     │   │
│   │ (Search/Browse/UI) │       │ (Upload/Delete/Status) │   │
│   └─────────┬──────────┘       └───────────┬────────────┘   │
│             │                              │                │
│             ▼                              ▼                │
│   ┌────────────────────┐       ┌────────────────────────┐   │
│   │ Database / SQLite  │       │ Audio Processor Engine │   │
│   │ (aiosqlite / DAO)  │       │  (FFmpeg & Loudnorm)   │   │
│   └────────────────────┘       └───────────┬────────────┘   │
└────────────────────────────────────────────┼────────────────┘
                                             ▼
                              ┌─────────────────────────────┐
                              │     Discord REST API        │
                              │ (POST /guilds/../soundboard)│
                              └─────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14)
- **Git**

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/ligthningkrish/Dissound.git
cd Dissound

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Create Discord Bot & Configure `.env`
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give it a name (e.g. `Dissound`).
3. Navigate to the **Bot** tab on the left menu:
   - Click **Reset Token** to copy your bot token.
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env   # On Windows: copy .env.example .env
   ```
5. Open `.env` and paste your bot token:
   ```ini
   DISCORD_TOKEN=your_token_here
   # Optional: set your testing server ID for instant slash command registration:
   DEV_GUILD_ID=123456789012345678
   ```

### 4. Bot Permissions & Invite Link
Navigate to **OAuth2 ➔ URL Generator** in the Discord Developer Portal:
- **Scopes**: `bot`, `applications.commands`
- **Bot Permissions**:
  - `Create Expressions` (Required to upload Soundboard sounds)
  - `Manage Expressions` (Required to delete Soundboard sounds)
  - `Send Messages`
  - `Embed Links`
  - `Attach Files` (Required to send audio preview clips)
  - `Read Message History`

Copy the generated URL and open it in your browser to invite Dissound to your server.

### 5. Seed Initial Sound Library & Run
Dissound comes bundled with synthesized starter meme sounds (Vine Boom, Metal Pipe, Windows XP Error, Airhorn, Roblox Oof, Bruh, Bonk, Among Us, and Anime Wow).

```bash
# Seed default meme catalog into the database
python assets/seed_data.py

# Start the bot
python main.py
```

---

## 📖 Command Reference

| Command | Description |
| :--- | :--- |
| `/search <query>` | Search sound library by name, category, or tags with live autocomplete |
| `/browse [category]` | Browse categorized collections via interactive menus |
| `/preview <sound>` | Play an audio preview in chat with an interactive **Add to Soundboard** button |
| `/add <sound> [name] [vol]` | Directly add a library sound to your server's soundboard |
| `/upload <file> [name]` | Upload custom audio (auto-trimmed to <=5.2s, normalized, and compressed) |
| `/categories` | List all available sound categories and sound counts |
| `/trending` | View the most added sounds across servers |
| `/recent` | View newly added sounds in the catalog |
| `/soundboard list` | List all active sounds currently in the server soundboard |
| `/soundboard status` | View soundboard capacity, used/free slots, and boost tier |
| `/soundboard delete <name>` | Delete a sound from the server soundboard (requires Manage Expressions) |
| `/history [limit]` | View recent soundboard upload history and audit log |
| `/help` | Complete in-app guide and troubleshooting information |

---

## 🧪 Testing

Dissound includes a suite of unit and integration tests covering audio processing, Discord Soundboard limits, and database operations:

```bash
python -m unittest discover tests
```

---

## 🗄️ Database Schema

The database uses SQLite via asynchronous `aiosqlite` with the following schema:

- **`sounds`**: `sound_id`, `sound_name`, `category`, `file_path`, `duration`, `file_size`, `file_format`, `source_url`, `tags`, `created_at`
- **`servers`**: `server_id`, `server_name`, `sound_limit`, `created_at`
- **`users`**: `user_id`, `username`, `permissions`
- **`upload_history`**: `upload_id`, `server_id`, `user_id`, `sound_id`, `sound_name`, `upload_status`, `error_message`, `timestamp`

---

## 📜 License
MIT License. Built for fun and entertaining Discord voice communities!
