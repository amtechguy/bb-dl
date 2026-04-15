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

- Linux ONLY 😄
- Python 3
- ani-cli
- requests
- rich
- questionary

Don't worry too much about installing these manually — bb-dl checks for them at startup and handles it for you.

## How to install

### Easy way (recommended) 🚀
No Python needed — just download and run!

1. Go to [Releases]
2. Download the latest `bb-dl` file
3. Open terminal where the file is and run:
```bash
chmod +x bb-dl
./bb-dl
```

Or make it runnable from anywhere:
```bash
sudo ln -s /path/to/bb-dl /usr/local/bin/bb-dl
```

Then just type `bb-dl` from anywhere in your terminal 😄


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
