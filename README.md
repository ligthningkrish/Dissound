# 🔊 Dissound (MemeSound Bot)

> **A Smart Discord Bot for Discovering, Managing, and Adding Sounds to Server Soundboards**

[![Project Status](https://img.shields.io/badge/status-active%20testing-orange.svg)]()
[![Discord.py](https://img.shields.io/badge/discord.py-v2.5%2B-5865F2.svg)](https://discordpy.readthedocs.io/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> [!NOTE]
> **Active Testing & Development Phase**  
> Dissound is currently in its private testing and prototype phase. Public deployment and bot setup guides will be made available upon general release.

Dissound solves the tedious, multi-step hassle of expanding Discord Server Soundboards. Instead of having to leave Discord, search multiple meme websites, download audio clips, manually trim or convert them to Discord's strict audio limits, and upload them via server settings, Dissound provides an **integrated sound discovery, preview, automated audio processing, and upload experience directly inside Discord and through a dedicated Web Dashboard**.

---

## 🌟 Key Features

- 🔍 **Instant Sound Discovery**: Search an extensive meme catalog using `/search` with live autocomplete by keywords, tags, or categories.
- 🔊 **Direct Audio Previews**: Listen to audio clips right in your text channels via `/preview` before deciding to add them.
- ➕ **One-Click Soundboard Upload**: Add any sound to your guild's soundboard with a single button click using Discord's official Soundboard API.
- ⚡ **Automated Audio Processing**: Automatically converts incoming audio to Discord-compatible MP3, trims clips > 5.2s, optimizes file sizes to <= 512 KB, and normalizes playback volume.
- 📤 **Custom Audio Upload**: Upload your own audio files via `/upload`; Dissound will auto-trim, optimize, and install them into your server soundboard.
- 📊 **Soundboard Capacity & Status Tracking**: Run `/soundboard status` to monitor used/available slots according to your server's boost tier (Tier 0: 8 slots, Tier 1: 24 slots, Tier 2: 36 slots, Tier 3: 48 slots).
- 📜 **Server Audit & Upload History**: Full audit trail via `/history` showing which members added which sounds, timestamps, and status.
- 🌐 **Web Control Dashboard**: Dedicated Next.js web application with Discord OAuth2 + Mail OTP two-factor verification to manage soundboards from your browser.
- ⚙️ **Customization Modal**: Fine-tune volume (0.1 to 1.0) and custom display names before installing.

---

## 🏗️ System Architecture

```
User in Discord / Web Dashboard
       │
       ▼ (Discord Slash Commands / Web OAuth Dashboard)
┌─────────────────────────────────────────────────────────────┐
│                    Dissound Platform                        │
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

## 🗄️ Database Schema

The system tracks sounds, servers, users, and upload logs with the following core entities:

- **`sounds`**: `sound_id`, `sound_name`, `category`, `file_path`, `duration`, `file_size`, `file_format`, `source_url`, `tags`, `created_at`
- **`servers`**: `server_id`, `server_name`, `sound_limit`, `created_at`
- **`users`**: `user_id`, `username`, `permissions`
- **`upload_history`**: `upload_id`, `server_id`, `user_id`, `sound_id`, `sound_name`, `upload_status`, `error_message`, `timestamp`

---

## 📜 License
MIT License. Built for fun and entertaining Discord voice communities!
