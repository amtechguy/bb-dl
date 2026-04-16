# bb-dl 🎌

So you want to watch anime huh? Same. That's literally why this exists.

bb-dl is a command line tool for Linux that lets you search, download and stream anime straight from your terminal like the cool person you are. No browser, no ads, no nonsense. Now with a proper TUI that actually looks good.

## What it can do 🔥

- Search for any anime by name (even if your spelling is a bit off)
- Download single episodes or entire season ranges
- Stream directly without downloading
- Sub or dub — your choice, no judgment
- Quality selection from 360p all the way to 1080p
- Automatically creates organised folders in ~/Videos for each anime
- Keeps a download history so you never forget where you left off
- Continue from where you stopped with one click
- Auto installs dependencies so you don't have to stress
- **Arrow-key menus** — no more typing numbers like it's 1995
- **Coloured tables and panels** for search results and history
- **Config file** — set your default quality, sub/dub and download folder once and forget about it
- **Settings menu** — change your defaults anytime without touching a config file manually

## Requirements

- Linux (Arch, Debian, Ubuntu, Zorin, Fedora, and more)
- Python 3
- curl (pre-installed on most distros)
- ani-cli — auto-installed for you
- requests, rich, questionary — auto-installed for you

bb-dl detects your distro at startup and installs everything the right way:
- **Arch-based** (Arch, Manjaro, EndeavourOS, etc.) → uses `yay` or `paru`
- **Debian/Ubuntu-based** (Ubuntu, Zorin, Mint, Pop!_OS, etc.) → downloads ani-cli directly from GitHub
- **Fedora/RHEL-based** → downloads ani-cli directly from GitHub
- **Other distros** → universal fallback via curl

The only thing you need beforehand is **Python 3** and **curl**. Everything else is handled.

## How to install

### The right way (works on every distro) 🚀

You need **Python 3** and **git** installed — that's it. Everything else is handled automatically.

```bash
git clone https://github.com/amtechguy/bb-dl.git
cd bb-dl
python3 bb-dl.py
```

### Optional — run bb-dl from anywhere in your terminal

```bash
chmod +x bb-dl.py
sudo ln -s "$(pwd)/bb-dl.py" /usr/local/bin/bb-dl
```

Then just type `bb-dl` from anywhere 😄

> **Note:** Avoid running the compiled binary from Releases if you are on Ubuntu, Zorin, Mint or any non-Arch distro — use the Python script above instead. It works better and has no compatibility issues.


## How to use

Just run `bb-dl` and follow the prompts. It's literally:

1. Type anime name
2. Pick from results with arrow keys
3. Choose sub or dub
4. Pick quality
5. Choose episodes
6. Done

It's so simple even your grandma could use it. Probably.

## Config

bb-dl saves a config file at `~/.bb-dl/config.json` with your preferences. You can change these at any time from the **Settings** menu inside the app — no need to manually edit any files.

| Setting | Default |
|---|---|
| Quality | 720p |
| Sub/Dub | sub |
| Download Folder | ~/Videos |

## Legal stuff 👀

This tool relies on ani-cli to fetch anime from various sources on the internet. What you do with it is entirely your business. If anyone asks — especially anyone in a uniform — you found this tool on the internet and you have absolutely no idea who made it. The developer is a ghost. He doesn't exist. Never heard of him.

Stay safe out there 🫡

## Credits

Built with love, broken code, and a lot of patience by **amtechguy** 😄

Shoutout to ani-cli and the AniList API for making this possible.
