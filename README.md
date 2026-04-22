# bb-dl 🎌

So you want to watch anime huh? Same. That's literally why this exists.

bb-dl is a command line tool for Linux that lets you search, download and stream anime straight from your terminal like the cool person you are. No browser, no ads, no nonsense. Now with a proper TUI that actually looks good.

## What it can do 🔥

- Search for any anime by name (even if your spelling is a bit off)
- Download single episodes or entire season ranges
- Stream directly without downloading
- Sub or dub — your choice, no judgment
- Quality selection from 360p all the way to 1080p
- Automatically creates organised folders in `~/Videos` for each anime
- Keeps a download history so you never forget where you left off
- Continue from where you stopped with one click
- Auto installs missing dependencies so you don't have to stress
- **Arrow-key menus** — no more typing numbers like it's 1995
- **Coloured tables and panels** for search results and history
- **Config file** — set your default quality, sub/dub and download folder once and forget about it
- **Settings menu** — change your defaults anytime without touching a config file manually
- **🔄 Auto ani-cli updater** — checks GitHub master on startup, compares version strings, and silently updates ani-cli via curl only when a newer version is actually available (throttled to once per 24h so it's never annoying)
- **🗑️ Clear History** — wipe your watch history cleanly from Settings with a confirmation prompt so you can't do it by accident

## Requirements

- Linux (Arch, Manjaro, Debian, Ubuntu, Zorin, Fedora, and more)
- Python 3
- curl (pre-installed on most distros)
- ani-cli, fzf, aria2, mpv — auto-installed for you
- requests, rich, questionary — auto-installed for you

bb-dl detects your distro at startup and installs everything the right way:

| Distro Family | Package Manager Used |
|---|---|
| Arch, Manjaro, EndeavourOS | yay or paru (AUR) |
| Ubuntu, Zorin, Mint, Pop!_OS | apt |
| Fedora, RHEL, CentOS | dnf |
| openSUSE | zypper |

The only thing you need beforehand is **Python 3** and **curl**. Everything else is handled.

## How to install

> **Not sure which option to pick?** Use this table:
>
> | Your distro | Recommended method |
> |---|---|
> | Arch, Manjaro, EndeavourOS | ✅ Option 1 — Binary |
> | Ubuntu 22.04+, Fedora 38+, Zorin 17+, Pop!_OS 22.04+ | ✅ Option 1 — Binary |
> | Ubuntu 20.04, Debian Stable, older Mint, any old distro | ⚠️ Option 2 — Python source |
> | Unsure / anything else | ✅ Option 2 — always works |
>
> The binary was compiled on Arch Linux. On older distros it may fail with a `GLIBC_X.XX not found` error — if that happens, just use Option 2 instead. It works identically.

### Option 1 — Download the compiled binary (easiest) 🚀

Go to the [Releases](../../releases) page, download the latest `bb-dl` binary, then:

```bash
chmod +x bb-dl
sudo mv bb-dl /usr/local/bin/bb-dl
```

Then just type `bb-dl` from anywhere. No Python needed.

---

### Option 2 — Run from source (works on every distro)

You need **Python 3** and **curl** installed — that's it.

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

If you're actively editing `bb-dl.py` and want it to recompile automatically every time you save:

```bash
./watch.sh
```

This runs in the background and rebuilds the binary instantly whenever `bb-dl.py` changes.

---

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

| Setting | Default | Options |
|---|---|---|
| Quality | 720p | 360p, 480p, 720p, 1080p |
| Sub/Dub | sub | sub, dub |
| Download Folder | ~/Videos | any path |

> **Tip:** If an anime shows "no valid sources", bb-dl will automatically check for and apply the latest ani-cli update on next startup. You can also force it by deleting `last_update_check` from `~/.bb-dl/config.json`.

## Troubleshooting 🔧

### `Episode is released, but no valid sources!`

This is the most common error and it comes from ani-cli's upstream source (allanime) changing or breaking — not from bb-dl itself.

**bb-dl will try to fix this automatically** on next startup by pulling the latest ani-cli from GitHub. But if the official ani-cli repo hasn't caught up yet, follow the manual steps below.

---

#### Step 1 — Update yt-dlp

An outdated yt-dlp is often the real culprit. The version from `apt` on Debian/Ubuntu is usually way behind — replace it with the official binary:

```bash
# Remove the old apt version (Debian/Ubuntu only)
sudo rm -f /usr/bin/yt-dlp

# Install the latest binary directly
sudo curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod +x /usr/local/bin/yt-dlp

# Verify
yt-dlp --version
```

On **Arch/Manjaro**, just run: `sudo pacman -S yt-dlp`

---

#### Step 2 — Manually patch ani-cli (if Step 1 didn't fix it)

When the official ani-cli repo is lagging behind on a fix, you can install the patched version from a community fork:

```bash
# 1. Back up your current ani-cli
target="$(readlink -f "$(command -v ani-cli)")"
cp "$target" ~/ani-cli-backup

# 2. Clone the fix branch
git clone -b allanime-fix https://github.com/justchokingaround/ani-cli.git /tmp/ani-cli-fix

# 3. Install it
sudo install -m 755 /tmp/ani-cli-fix/ani-cli "$target"

# 4. Verify
ani-cli --version
```

> **Note:** This replaces your ani-cli with a community-patched version. Once the official repo catches up, bb-dl's auto-updater will switch you back to the official one on the next 24h check. To force it sooner, delete `last_update_check` from `~/.bb-dl/config.json` and restart bb-dl.

---

#### Still broken?

Check the [ani-cli issues page](https://github.com/pystardust/ani-cli/issues) — if the source is down, you'll usually find other people reporting it there along with any latest fix.

---

## Legal stuff 👀

This tool relies on ani-cli to fetch anime from various sources on the internet. What you do with it is entirely your business. If anyone asks — especially anyone in a uniform — you found this tool on the internet and you have absolutely no idea who made it. The developer is a ghost. He doesn't exist. Never heard of him.

Stay safe out there 🫡

## Credits

Built with love, broken code, and a lot of patience by **amtechguy** 😄

Shoutout to ani-cli and the AniList API for making this possible.
