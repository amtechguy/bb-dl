# bb-ani 🎌

So you want to watch anime huh? Same. That's literally why this exists.

bb-ani is a command line tool for Linux that lets you search, discover, download and stream anime straight from your terminal like the cool person you are. No browser, no ads, no nonsense. Powered by [ani-cli](https://github.com/pystardust/ani-cli) and [AniList](https://anilist.co).

## What it can do 🔥

- **🔍 Search** any anime by name — results show year, episode count, score and genres
- **🌟 Discover** — browse trending, popular, and new/releasing anime
- **🎭 Browse by Genre** — full paginated catalog for any genre (Action, Horror, Romance, Sci-Fi, and more) — page through the entire AniList library, not just a top 20
- **▶️ Stream** directly in **mpv or VLC** without downloading
- **⬇️ Download** single episodes or full season ranges (e.g. `1-24`)
- Sub or dub — your choice, no judgment
- Quality selection: best, 1080p, 720p, 480p, 360p
- **📜 History** — keeps track of everything you've watched or downloaded, resume with one click
- **⭐ Watchlist** — save anime you want to watch later
- **📁 Local Library** — browse and play your downloaded files from inside the app
- **🔄 Update ani-cli** — keep the scraper up to date without leaving the app
- Auto installs missing Python dependencies on first run
- Arrow-key menus — no typing numbers like it's 1995
- Coloured tables and panels for search results, anime info, and history

## Requirements

- Linux (Arch, Manjaro, Debian, Ubuntu, Zorin, Fedora, and more)
- Windows via **WSL 2** (Windows Subsystem for Linux)
- Python 3.9+
- [ani-cli](https://github.com/pystardust/ani-cli) — handles the actual streaming and downloading
- mpv **or** vlc (for streaming)
- requests, rich, questionary — **auto-installed on first run**

### Install system dependencies

**Arch / Manjaro / EndeavourOS:**
```bash
sudo pacman -S ani-cli mpv
```

**Debian / Ubuntu / Zorin / Pop!_OS:**
```bash
# Install mpv
sudo apt install mpv

# Install ani-cli (not in apt — use the official install script)
bash <(curl -fsSL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli) -U
```

**Fedora:**
```bash
sudo dnf install mpv
bash <(curl -fsSL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli) -U
```

## How to install

**You need Python 3.9+ and ani-cli — that's it. Everything else installs automatically.**

```bash
git clone https://github.com/amtechguy/bb-ani.git
cd bb-ani
./install.sh
```

The install script places a small launcher at `/usr/local/bin/bb-ani` so you can type `bb-ani` from any terminal, anywhere. It only needs to run once — after that, any updates you pull from git are live immediately without reinstalling.

> **What does install.sh do?**  
> It creates a one-line wrapper at `/usr/local/bin/bb-ani` that calls `python3 /path/to/bb-ani.py`. That's it. No compiling, no bundling. Because it points directly at the script, every `git pull` update takes effect instantly.

---

## How to use

Just run `bb-ani` and follow the prompts.

### 🔍 Search & Stream/Download
1. Choose **Search & Stream/Download**
2. Type the anime name
3. Pick from results with arrow keys
4. Choose **Stream** or **Download**
5. Enter episode or range (e.g. `1` or `1-24`)
6. Pick sub/dub and quality
7. Done ✅

### 🌟 Discover
Not sure what to watch? Use **Discover**:
- **🔥 Trending** — what everyone is watching right now
- **⭐ Popular** — all-time popular anime
- **🆕 New / Releasing** — freshest shows currently airing

### 🎭 Browse by Genre
Want to dig through a whole genre and find something new?
1. Choose **Browse by Genre**
2. Pick a genre (Action, Comedy, Horror, Mecha, Romance, Sci-Fi, Slice of Life, etc.)
3. Sort by Score, Popularity, Newest, or no sort
4. Page through the full catalog — 25 at a time, with Previous / Next / Jump to page
5. Pick an anime → stream or download it

### 📜 History & Continue Watching
Every stream and download is saved. From **History**:
- Continue to the next episode automatically
- Re-watch/download the last episode
- Pick a custom episode to jump to

### ⭐ Watchlist
Save any anime to your watchlist while browsing so you don't forget it.

### 📁 Local Library
Browse and play your downloaded anime files directly from within the app.

---

## Updating

```bash
cd bb-ani
git pull
```

That's it. No reinstalling needed.

---

## Troubleshooting 🔧

### `ani-cli: command not found`

ani-cli isn't installed or isn't in your PATH. Install it following the instructions in the Requirements section above.

### Anime not found by ani-cli

When you pick an anime, bb-ani shows you the search term it will pass to ani-cli and lets you edit it before confirming. If the title has a long English subtitle (e.g. *Re:Zero − Starting Life in Another World*), try shortening it to just *Re:Zero*.

### Dub not available

Many anime only have sub available. If you pick dub and get no results, switch to sub.

### Genre browser shows no results

Make sure you have an internet connection. The genre browser uses the AniList API — the same one used for Search and Discover.

---

## Legal stuff 👀

This tool uses ani-cli to fetch anime streams. What you do with it is entirely your business. If anyone asks — especially anyone in a uniform — you found this tool on the internet and you have absolutely no idea who made it. The developer is a ghost. He doesn't exist. Never heard of him.

Stay safe out there 🫡

## Credits

Built with love, broken code, and a lot of patience by **amtechguy** 😄

Powered by [ani-cli](https://github.com/pystardust/ani-cli) by pystardust, and the [AniList](https://anilist.co) API.
