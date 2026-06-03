# bb-dl 🎌

So you want to watch anime huh? Same. That's literally why this exists.

bb-dl is a command line tool for Linux that lets you search, download and stream anime straight from your terminal like the cool person you are. No browser, no ads, no nonsense. Powered by [anipy-api](https://github.com/sdaqo/anipy-cli) and AllAnime — no external CLI tools required.

## What it can do 🔥

- Search any anime by name and get results with **release year** and **language availability**
- Pick your anime from a clean table — see year, episode count, status, and genres before committing
- Download single episodes or entire season ranges (e.g. `1-24`)
- Stream directly in **mpv or VLC** without downloading
- Sub or dub — your choice, no judgment
- Quality selection: 360p, 480p, 720p, 1080p
- **Auto stream fallback** — if a CDN blocks one stream, it tries the next automatically
- **Provider fallback** — if AllAnime fails, automatically retries on **AnimeKai** without any extra steps
- **HLS detection** — warns you if ffmpeg is needed before attempting download
- Automatically organises downloads into `~/Videos/<anime-name>/`
- Keeps a download/stream history so you never lose your place
- Continue from where you stopped with one click
- Auto installs missing Python dependencies on first run
- **🌟 Discover menu** — browse top airing, currently airing this season, or this week's schedule powered by the Jikan API
- **Arrow-key menus** — no typing numbers like it's 1995
- **Coloured tables and panels** for search results, anime info, and history
- **Config file** — set default quality, sub/dub, player and download folder once and forget it
- **Settings menu** — change defaults anytime without touching config files
- **🗑️ Clear History** — wipe your watch history cleanly from Settings with a confirmation prompt

## Requirements

- Linux (Arch, Manjaro, Debian, Ubuntu, Zorin, Fedora, and more)
- Python 3.9+
- mpv **or** vlc (for streaming — pick your preferred player)
- ffmpeg (for HLS/m3u8 stream downloads)
- requests, rich, questionary, anipy-api — **auto-installed on first run**

### Install system deps (if not already installed)

**Arch / Manjaro:**
```bash
sudo pacman -S mpv ffmpeg
```

**Debian / Ubuntu / Zorin:**
```bash
sudo apt install mpv ffmpeg
```

**Fedora:**
```bash
sudo dnf install mpv ffmpeg
```

## How to install

> **Not sure which option to pick?** Use this table:
>
> | Your distro                                             | Recommended method          |
> | ------------------------------------------------------- | --------------------------- |
> | Arch, Manjaro, EndeavourOS                              | ✅ Option 1 — Binary        |
> | Ubuntu 22.04+, Fedora 38+, Zorin 17+, Pop!\_OS 22.04+  | ✅ Option 1 — Binary        |
> | Ubuntu 20.04, Debian Stable, older Mint, any old distro | ⚠️ Option 2 — Python source |
> | Unsure / anything else                                  | ✅ Option 2 — always works  |
>
> The binary was compiled on Arch Linux. On older distros it may fail with a `GLIBC_X.XX not found` error — if that happens, just use Option 2 instead.

### Option 1 — Download the compiled binary (easiest) 🚀

Go to the [Releases](../../releases) page, download the latest `bb-dl` binary, then:

```bash
chmod +x bb-dl
sudo mv bb-dl /usr/local/bin/bb-dl
```

Then just type `bb-dl` from anywhere. No Python needed.

---

### Option 2 — Run from source (works on every distro)

You need **Python 3.9+** — that's it. Everything else installs automatically.

```bash
git clone https://github.com/amtechguy/bb-dl.git
cd bb-dl
python3 bb-dl.py
```

#### Optional — make it available as a command anywhere

```bash
chmod +x bb-dl.py
sudo ln -s "$(pwd)/bb-dl.py" /usr/local/bin/bb-dl
```

Then just type `bb-dl` from anywhere 😄

---

### Option 3 — Build it yourself from source

Requires **PyInstaller**:

```bash
git clone https://github.com/amtechguy/bb-dl.git
cd bb-dl
./build.sh
sudo ln -s "$(pwd)/dist/bb-dl" /usr/local/bin/bb-dl
```

#### Auto-rebuild on save (for developers)

```bash
./watch.sh
```

This runs in the background and rebuilds the binary instantly whenever `bb-dl.py` changes.

---

## How to use

Just run `bb-dl` and follow the prompts:

### Download or Stream
1. Choose **Download** or **Stream**
2. Type anime name
3. Pick from results with arrow keys (shows year + language)
4. View the info panel (year, episode count, status, genres)
5. Choose sub or dub
6. Enter episode or range (e.g. `1` or `1-24`)
7. Pick quality
8. Done ✅

### 🌟 Discover
Not sure what to watch? Use **Discover** from the main menu:
- **🔥 Top airing this week** — pulls the current top 10 airing anime from MyAnimeList via Jikan
- **📺 Currently airing this season** — browse everything airing right now
- **📅 This week's schedule** — pick a day and see what's airing

Pick an anime from the list and go straight into Download or Stream — no typing needed.

## Config

bb-dl saves a config file at `~/.bb-dl/config.json`. Change settings anytime from the **Settings** menu inside the app.

| Setting         | Default  | Options                 |
| --------------- | -------- | ----------------------- |
| Quality         | 720p     | 360p, 480p, 720p, 1080p |
| Sub/Dub         | sub      | sub, dub                |
| Download Folder | ~/Videos | any path                |
| Player          | mpv      | mpv, vlc                |

## Troubleshooting 🔧

### `❌ All streams failed. The CDN may be blocking requests right now.`

This means every available stream for that episode returned a 403. This is a CDN-side block, not a bug in bb-dl.

**Things to try:**
- Wait 10-30 minutes and try again — CDN bans are often temporary
- Try a different quality (720p instead of 1080p)
- Try a different episode to confirm the issue is episode-specific

---

### `🔄 AnimeKai fallback triggered`

If AllAnime returns broken responses (common during outages), bb-dl will automatically search AnimeKai for the same anime and episode. You'll see a message like:

```
🔄 Trying fallback: animekai...
✅ Got streams from animekai
```

This is normal — just let it run. No action needed.

---

### `⚠️ This stream is HLS but ffmpeg is not installed`

HLS (`.m3u8`) streams require ffmpeg to download. Install it:

```bash
# Arch
sudo pacman -S ffmpeg

# Debian / Ubuntu
sudo apt install ffmpeg
```

---

### `❌ Could not fetch episode list` or search returning errors

The AllAnime API may have changed. Try upgrading anipy-api:

```bash
pip install --upgrade anipy-api --break-system-packages
```

If that doesn't fix it, check the [anipy-cli releases page](https://github.com/sdaqo/anipy-cli/releases) to see if a new version was pushed.

---

### Episode not found (e.g. you asked for ep 5 but it says not found)

AllAnime sometimes uses non-integer episode numbers for specials (e.g. `4.5`, `0`). bb-dl will show you the available list when this happens — just enter the exact number shown.

---

### Dub not available

Many anime only have sub on AllAnime. If you pick dub and get no results, switch to sub.

---

## Legal stuff 👀

This tool uses anipy-api to fetch anime from AllAnime. What you do with it is entirely your business. If anyone asks — especially anyone in a uniform — you found this tool on the internet and you have absolutely no idea who made it. The developer is a ghost. He doesn't exist. Never heard of him.

Stay safe out there 🫡

## Credits

Built with love, broken code, and a lot of patience by **amtechguy** 😄

Powered by [anipy-api](https://github.com/sdaqo/anipy-cli) by sdaqo, and the [AllAnime](https://allanime.day) source.
