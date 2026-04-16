#!/usr/bin/env python3

import subprocess
import sys
import os
import json
import shutil
from datetime import datetime

HISTORY_FILE = os.path.expanduser("~/.bb-dl/history.json")
CONFIG_FILE  = os.path.expanduser("~/.bb-dl/config.json")

# ─────────────────────────────────────────────
#  Dependencies
# ─────────────────────────────────────────────

def detect_distro():
    """Returns the distro family: 'arch', 'debian', 'fedora', or 'unknown'."""
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        if any(x in content for x in ["arch", "manjaro", "endeavour", "garuda", "artix"]):
            return "arch"
        elif any(x in content for x in ["debian", "ubuntu", "zorin", "mint", "pop", "elementary", "kali", "parrot"]):
            return "debian"
        elif any(x in content for x in ["fedora", "rhel", "centos", "rocky", "alma"]):
            return "fedora"
        elif "opensuse" in content:
            return "suse"
    except Exception:
        pass
    return "unknown"


def install_ani_cli(distro):
    """Install ani-cli using the appropriate method for the detected distro."""
    print("📦 Installing ani-cli...")

    if distro == "arch":
        # Try yay then paru
        for helper in ["yay", "paru"]:
            if shutil.which(helper):
                subprocess.run([helper, "-S", "ani-cli", "--noconfirm"], check=True)
                return
        print("❌ No AUR helper found (yay/paru). Please install one first.")
        sys.exit(1)

    else:
        # Universal: download the script directly from GitHub (works on Debian, Fedora, etc.)
        if not shutil.which("curl"):
            print("❌ curl is required to install ani-cli. Please install curl first.")
            sys.exit(1)
        try:
            subprocess.run(
                "curl -fsSL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli "
                "| sudo tee /usr/local/bin/ani-cli > /dev/null && sudo chmod +x /usr/local/bin/ani-cli",
                shell=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            print("❌ Failed to install ani-cli. Try installing it manually: https://github.com/pystardust/ani-cli")
            sys.exit(1)


def check_dependencies():
    missing = []
    for pkg in ["requests", "rich", "questionary"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"📦 Installing: {', '.join(missing)} ...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing, "--break-system-packages"],
                check=True,
            )
        except subprocess.CalledProcessError:
            # Fallback without --break-system-packages for older distros
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing],
                check=True,
            )
    if not shutil.which("ani-cli"):
        install_ani_cli(detect_distro())

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

CONFIG_DEFAULTS = {
    "default_quality":    "720p",
    "default_sub_dub":   "sub",
    "download_folder":   str(os.path.expanduser("~/Videos")),
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return dict(CONFIG_DEFAULTS)
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)
    return {**CONFIG_DEFAULTS, **cfg}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ─────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(title, episodes, quality, sub_dub, type="download", query=None):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = load_history()
    for entry in history:
        if entry["title"] == title:
            entry["episodes"] = episodes
            entry["quality"]  = quality
            entry["sub_dub"]  = sub_dub
            entry["type"]     = type
            entry["date"]     = datetime.now().strftime("%Y-%m-%d %H:%M")
            if query:
                entry["query"] = query
            break
    else:
        history.append({
            "title":    title,
            "query":    query or title,
            "episodes": episodes,
            "quality":  quality,
            "sub_dub":  sub_dub,
            "type":     type,
            "date":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ─────────────────────────────────────────────
#  Search
# ─────────────────────────────────────────────

def search_anime(query, console):
    import requests
    console.print(f"\n[bold cyan]🔍 Searching for:[/] [yellow]{query}[/]")

    # Try AniList first
    try:
        anilist_query = """
        query ($search: String) {
            Page(page: 1, perPage: 10) {
                media(search: $search, type: ANIME) {
                    title { romaji english }
                    episodes
                    seasonYear
                }
            }
        }
        """
        response = requests.post(
            "https://graphql.anilist.co",
            json={"query": anilist_query, "variables": {"search": query}},
            timeout=10,
        )
        media = response.json()["data"]["Page"]["media"]
        if media:
            return [
                {
                    "title":    a["title"]["english"] or a["title"]["romaji"],
                    "episodes": a.get("episodes", "?"),
                    "year":     a.get("seasonYear", "?"),
                }
                for a in media
            ]
    except Exception:
        console.print("[yellow]⚠️  AniList failed, trying backup...[/]")

    # Fall back to Jikan
    try:
        response = requests.get(
            f"https://api.jikan.moe/v4/anime?q={query}&limit=10",
            timeout=10,
        )
        data = response.json()
        if "data" not in data:
            console.print("[red]❌ Both search sources failed.[/]")
            return []
        return [
            {
                "title":    a["titles"][0]["title"],
                "episodes": a.get("episodes", "?"),
                "year":     a.get("year", "?"),
            }
            for a in data["data"]
        ]
    except Exception:
        console.print("[red]❌ Both search sources failed.[/]")
        return []

# ─────────────────────────────────────────────
#  Anime picker
# ─────────────────────────────────────────────

def pick_anime(results, console):
    from rich.table import Table
    import questionary

    table = Table(
        title="Search Results",
        border_style="cyan",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#",        style="dim",        width=4,  justify="right")
    table.add_column("Title",    style="bold white")
    table.add_column("Episodes", style="cyan",        width=10, justify="center")
    table.add_column("Year",     style="yellow",      width=8,  justify="center")

    for i, anime in enumerate(results, 1):
        table.add_row(str(i), anime["title"], str(anime["episodes"]), str(anime["year"]))

    console.print(table)

    choices = [f"{a['title']}  ({a['year']})" for a in results]
    choices.append("❌  Cancel")

    answer = questionary.select(
        "Select an anime:",
        choices=choices,
        style=questionary.Style([
            ("selected",    "fg:cyan bold"),
            ("pointer",     "fg:magenta bold"),
            ("highlighted", "fg:cyan"),
        ]),
    ).ask()

    if answer is None or answer.startswith("❌"):
        return None
    return results[choices.index(answer)]

# ─────────────────────────────────────────────
#  History display
# ─────────────────────────────────────────────

def show_history(console):
    from rich.table import Table

    history = load_history()
    if not history:
        console.print("[dim]📭 No history yet.\n[/]")
        return

    table = Table(
        title="📜 History",
        border_style="blue",
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("#",        style="dim",  width=4,  justify="right")
    table.add_column("",         width=3,                justify="center")
    table.add_column("Title",    style="bold white")
    table.add_column("Episodes", style="cyan",  width=10, justify="center")
    table.add_column("Sub/Dub",  style="green", width=8,  justify="center")
    table.add_column("Quality",  style="yellow",width=8,  justify="center")
    table.add_column("Date",     style="dim")

    for i, e in enumerate(history, 1):
        icon = "▶️" if e.get("type") == "stream" else "⬇️"
        table.add_row(
            str(i), icon,
            e["title"],
            str(e["episodes"]),
            e["sub_dub"].upper(),
            e["quality"],
            e["date"],
        )

    console.print(table)
    console.print()

# ─────────────────────────────────────────────
#  Download folder helper
# ─────────────────────────────────────────────

def get_download_folder(anime_title, config):
    base   = os.path.expanduser(config.get("download_folder", "~/Videos"))
    folder = os.path.join(base, anime_title)
    os.makedirs(folder, exist_ok=True)
    return folder

# ─────────────────────────────────────────────
#  Settings menu
# ─────────────────────────────────────────────

def settings_menu(console, config):
    import questionary

    while True:
        console.print()
        action = questionary.select(
            "⚙️  Settings — what would you like to change?",
            choices=[
                f"🎬  Default Quality      [{config['default_quality']}]",
                f"🗣️  Default Sub/Dub      [{config['default_sub_dub']}]",
                f"📁  Download Folder      [{config['download_folder']}]",
                "← Back",
            ],
            style=questionary.Style([
                ("selected", "fg:yellow bold"),
                ("pointer",  "fg:yellow bold"),
            ]),
        ).ask()

        if action is None or "Back" in action:
            break

        elif "Quality" in action:
            q = questionary.select(
                "Select default quality:",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"],
            ).ask()
            if q:
                config["default_quality"] = q
                save_config(config)
                console.print(f"[green]✅ Default quality → {q}[/]")

        elif "Sub/Dub" in action:
            sd = questionary.select(
                "Select default:",
                choices=["sub", "dub"],
                default=config["default_sub_dub"],
            ).ask()
            if sd:
                config["default_sub_dub"] = sd
                save_config(config)
                console.print(f"[green]✅ Default sub/dub → {sd}[/]")

        elif "Folder" in action:
            folder = questionary.text(
                "Enter download folder path:",
                default=config["download_folder"],
            ).ask()
            if folder:
                config["download_folder"] = folder
                save_config(config)
                console.print(f"[green]✅ Download folder → {folder}[/]")

# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main():
    check_dependencies()

    from rich.console import Console
    from rich.panel   import Panel
    from rich.text    import Text
    import questionary

    console = Console()
    config  = load_config()

    # ── Banner ───────────────────────────────
    banner = Text()
    banner.append("🎌  bb-dl", style="bold magenta")
    banner.append("   Anime Downloader & Streamer", style="dim white")
    console.print(Panel(banner, border_style="magenta", padding=(0, 2)))
    console.print()

    show_history(console)

    # ── Main loop ────────────────────────────
    while True:
        action = questionary.select(
            "What do you want to do?",
            choices=[
                "⬇️   Download anime",
                "▶️   Stream anime",
                "🔁   Continue from history",
                "⚙️   Settings",
                "👋   Exit",
            ],
            style=questionary.Style([
                ("selected", "fg:magenta bold"),
                ("pointer",  "fg:magenta bold"),
            ]),
        ).ask()

        # ── Exit ─────────────────────────────
        if action is None or "Exit" in action:
            console.print("\n[bold magenta]👋  Goodbye![/]\n")
            break

        # ── Download ─────────────────────────
        elif "Download" in action:
            query = questionary.text("Enter anime name:").ask()
            if not query:
                continue

            results = search_anime(query, console)
            if not results:
                console.print("[red]❌ No results found.[/]")
                continue

            selected = pick_anime(results, console)
            if not selected:
                continue

            sub_dub = questionary.select(
                "Sub or Dub?",
                choices=["sub", "dub"],
                default=config["default_sub_dub"],
            ).ask() or config["default_sub_dub"]

            episodes = questionary.text("Episode or range (e.g. 1 or 1-12):").ask()
            if not episodes:
                continue

            quality = questionary.select(
                "Quality?",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"],
            ).ask() or config["default_quality"]

            download_folder = get_download_folder(selected["title"], config)
            console.print(f"[dim]📁 Saving to: {download_folder}[/]")

            command = ["ani-cli", "-d", query, "-e", episodes, "-q", quality]
            if sub_dub == "dub":
                command.append("--dub")

            console.print(f"\n[bold green]⬇️  Starting download...[/]\n")
            os.chdir(download_folder)
            subprocess.run(command)
            save_history(selected["title"], episodes, quality, sub_dub, "download", query=query)
            console.print(f"\n[green]✅ Saved to history![/]")

        # ── Stream ───────────────────────────
        elif "Stream" in action:
            query = questionary.text("Enter anime name:").ask()
            if not query:
                continue

            results = search_anime(query, console)
            if not results:
                console.print("[red]❌ No results found.[/]")
                continue

            selected = pick_anime(results, console)
            if not selected:
                continue

            sub_dub = questionary.select(
                "Sub or Dub?",
                choices=["sub", "dub"],
                default=config["default_sub_dub"],
            ).ask() or config["default_sub_dub"]

            episode = questionary.text("Episode number:").ask()
            if not episode:
                continue

            quality = questionary.select(
                "Quality?",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"],
            ).ask() or config["default_quality"]

            command = ["ani-cli", query, "-e", episode, "-q", quality]
            if sub_dub == "dub":
                command.append("--dub")

            console.print(f"\n[bold green]▶️  Streaming {selected['title']} episode {episode}...[/]\n")
            subprocess.run(command)

        # ── Continue from history ─────────────
        elif "history" in action:
            history = load_history()
            if not history:
                console.print("[red]❌ No history yet. Download something first![/]")
                continue

            choices = [
                f"{e['title']}  |  Ep: {e['episodes']}  |  {e['sub_dub'].upper()}  |  {e['quality']}  |  {e['date']}"
                for e in history
            ]
            choices.append("← Cancel")

            pick = questionary.select(
                "Select from history to continue:",
                choices=choices,
                style=questionary.Style([
                    ("selected", "fg:blue bold"),
                    ("pointer",  "fg:blue bold"),
                ]),
            ).ask()

            if pick is None or pick == "← Cancel":
                continue

            entry   = history[choices.index(pick)]
            last_ep = entry["episodes"]

            try:
                next_ep = int(str(last_ep).split("-")[-1]) + 1
            except (ValueError, TypeError):
                next_ep = 1
                console.print("[yellow]⚠️  Could not determine last episode, starting from 1[/]")

            sub_dub = entry["sub_dub"]
            quality = entry["quality"]

            resume = questionary.select(
                "What do you want to do?",
                choices=[
                    f"▶️   Continue from episode {next_ep}",
                    f"🔁   Redownload last episode ({last_ep})",
                ],
            ).ask()

            if resume is None:
                continue

            if "Redownload" in resume:
                episodes = str(last_ep)
                console.print(f"\n[cyan]🔁 Redownloading: {entry['title']} episode {last_ep}[/]")
            else:
                console.print(f"\n[cyan]▶️  Continuing: {entry['title']} from episode {next_ep}[/]")
                episodes = questionary.text(
                    "Episode or range:",
                    default=str(next_ep),
                ).ask()
                if not episodes:
                    continue

            download_folder = get_download_folder(entry["title"], config)
            ani_query = entry.get("query", entry["title"])
            command = ["ani-cli", "-d", ani_query, "-e", episodes, "-q", quality]
            if sub_dub == "dub":
                command.append("--dub")

            console.print(f"\n[bold green]⬇️  Starting download...[/]\n")
            os.chdir(download_folder)
            subprocess.run(command)
            save_history(entry["title"], episodes, quality, sub_dub, "download", query=ani_query)
            console.print(f"\n[green]✅ History updated![/]")

        # ── Settings ─────────────────────────
        elif "Settings" in action:
            settings_menu(console, config)


if __name__ == "__main__":
    main()