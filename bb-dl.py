#!/usr/bin/env python3

import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

HISTORY_FILE = os.path.expanduser("~/.bb-dl/history.json")
CONFIG_FILE  = os.path.expanduser("~/.bb-dl/config.json")

# ─────────────────────────────────────────────
#  Dependencies
# ─────────────────────────────────────────────

def check_dependencies():
    """Install missing Python packages."""
    missing = []
    for pkg in ["requests", "rich", "questionary", "anipy_api"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        # anipy_api is published as 'anipy-api' on PyPI
        install_names = [
            "anipy-api" if p == "anipy_api" else p for p in missing
        ]
        print(f"📦 Installing: {', '.join(install_names)} ...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *install_names,
                 "--break-system-packages"],
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *install_names],
                check=True,
            )

    # Warn about optional system tools
    needed = {"aria2c": "aria2", "mpv": "mpv", "ffmpeg": "ffmpeg"}
    missing_sys = [pkg for binary, pkg in needed.items()
                   if not shutil.which(binary)]
    if missing_sys:
        print(f"⚠️  Missing optional system deps: {', '.join(missing_sys)}")
        print(f"   Install with your package manager, e.g.: "
              f"sudo pacman -S {' '.join(missing_sys)}")
        print()


# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

CONFIG_DEFAULTS = {
    "default_quality":  "720p",
    "default_sub_dub":  "sub",
    "download_folder":  str(os.path.expanduser("~/Videos")),
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


def save_history(title, episodes, quality, sub_dub, action_type="download",
                 identifier=None, provider_name=None):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = load_history()
    for entry in history:
        if entry["title"] == title:
            entry["episodes"]      = episodes
            entry["quality"]       = quality
            entry["sub_dub"]       = sub_dub
            entry["type"]          = action_type
            entry["date"]          = datetime.now().strftime("%Y-%m-%d %H:%M")
            if identifier:
                entry["identifier"] = identifier
            if provider_name:
                entry["provider"] = provider_name
            break
    else:
        history.append({
            "title":      title,
            "identifier": identifier or title,
            "provider":   provider_name or "allanime",
            "episodes":   episodes,
            "quality":    quality,
            "sub_dub":    sub_dub,
            "type":       action_type,
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ─────────────────────────────────────────────
#  History display
# ─────────────────────────────────────────────

def show_history(console):
    from rich.table import Table
    history = load_history()
    if not history:
        console.print("[dim]📭 No history yet.\n[/]")
        return

    table = Table(title="📜 History", border_style="blue",
                  header_style="bold cyan", show_lines=True)
    table.add_column("#",        style="dim",    width=4,  justify="right")
    table.add_column("",         width=3,                  justify="center")
    table.add_column("Title",    style="bold white")
    table.add_column("Episodes", style="cyan",   width=10, justify="center")
    table.add_column("Sub/Dub",  style="green",  width=8,  justify="center")
    table.add_column("Quality",  style="yellow", width=8,  justify="center")
    table.add_column("Date",     style="dim")

    for i, e in enumerate(history, 1):
        icon = "▶️" if e.get("type") == "stream" else "⬇️"
        table.add_row(str(i), icon, e["title"], str(e["episodes"]),
                      e["sub_dub"].upper(), e["quality"], e["date"])
    console.print(table)
    console.print()


# ─────────────────────────────────────────────
#  Clear history
# ─────────────────────────────────────────────

def clear_history(console):
    import questionary
    history = load_history()
    if not history:
        console.print("[dim]📭 History is already empty.[/]")
        return
    confirm = questionary.confirm(
        f"⚠️  Delete all {len(history)} history entries? This cannot be undone.",
        default=False,
    ).ask()
    if confirm:
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)
        console.print("[green]🗑️  History cleared.[/]")
    else:
        console.print("[dim]Cancelled.[/]")


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
                "🗑️   Clear History",
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
            q = questionary.select("Select default quality:",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"]).ask()
            if q:
                config["default_quality"] = q
                save_config(config)
                console.print(f"[green]✅ Default quality → {q}[/]")
        elif "Sub/Dub" in action:
            sd = questionary.select("Select default:",
                choices=["sub", "dub"],
                default=config["default_sub_dub"]).ask()
            if sd:
                config["default_sub_dub"] = sd
                save_config(config)
                console.print(f"[green]✅ Default sub/dub → {sd}[/]")
        elif "Folder" in action:
            folder = questionary.text("Enter download folder path:",
                default=config["download_folder"]).ask()
            if folder:
                config["download_folder"] = folder
                save_config(config)
                console.print(f"[green]✅ Download folder → {folder}[/]")
        elif "Clear History" in action:
            clear_history(console)


# ─────────────────────────────────────────────
#  anipy-api helpers
# ─────────────────────────────────────────────

def _quality_to_int(quality_str):
    """Convert e.g. '720p' → 720."""
    return int(quality_str.replace("p", "").strip())


def get_provider_and_lang(sub_dub):
    """Return (provider_class, LanguageTypeEnum) for AllAnime.

    Note: get_provider() returns the class directly (not a factory),
    so we use it as-is without instantiation.
    """
    from anipy_api.provider import get_provider, LanguageTypeEnum
    provider = get_provider("allanime")   # returns the class directly
    lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB
    return provider, lang


def search_and_pick(query, sub_dub, console):
    """
    Search AllAnime for query, show results in a rich table,
    let user pick one. Returns an Anime object or None.
    """
    from anipy_api.anime import Anime
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    import questionary

    provider, lang = get_provider_and_lang(sub_dub)

    console.print(f"\n[bold cyan]🔍 Searching for:[/] [yellow]{query}[/]")
    try:
        results = list(provider.get_search(query))
    except Exception as e:
        console.print(f"[red]❌ Search failed: {e}[/]")
        return None

    if not results:
        console.print("[red]❌ No results found.[/]")
        return None

    # Filter to only show those that support the chosen language
    filtered = [r for r in results if lang in r.languages]
    if not filtered:
        filtered = results
        console.print(
            f"[yellow]⚠️  No {sub_dub} results found; showing all.[/]"
        )

    # ── Fetch years in parallel (one get_info per result) ────────────
    from concurrent.futures import ThreadPoolExecutor, as_completed

    console.print("[dim]⏳ Loading details...[/]", end="\r")

    def fetch_year(r):
        try:
            info = provider.get_info(r.identifier)
            return r.identifier, str(info.release_year) if info.release_year else "?"
        except Exception:
            return r.identifier, "?"

    year_map = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_year, r): r for r in filtered}
        for fut in as_completed(futures):
            ident, year = fut.result()
            year_map[ident] = year

    console.print(" " * 30, end="\r")  # clear the loading line

    table = Table(title="Search Results", border_style="cyan",
                  header_style="bold magenta", show_lines=True)
    table.add_column("#",     style="dim",        width=4,  justify="right")
    table.add_column("Title", style="bold white")
    table.add_column("Year",  style="yellow",     width=6,  justify="center")
    table.add_column("Lang",  style="green",      width=10, justify="center")

    for i, r in enumerate(filtered, 1):
        langs = "/".join(sorted(lv.value.upper() for lv in r.languages))
        table.add_row(str(i), r.name, year_map.get(r.identifier, "?"), langs)

    console.print(table)

    choices = [f"{r.name}  [{'/'.join(sorted(lv.value.upper() for lv in r.languages))}]"
               for r in filtered]
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

    idx = choices.index(answer)
    selected_result = filtered[idx]
    anime = Anime.from_search_result(provider, selected_result)

    # ── Fetch & display info for selected anime ──────────────────────
    console.print(f"\n[dim]⏳ Fetching details...[/]", end="\r")
    try:
        info = provider.get_info(selected_result.identifier)
        ep_count = len(anime.get_episodes(lang))

        year    = str(info.release_year) if info.release_year else "?"
        status  = info.status.name.capitalize() if info.status else "?"
        genres  = ", ".join(info.genres[:4]) if info.genres else "?"

        detail = Text()
        detail.append(f"📅 Year: ", style="dim")
        detail.append(f"{year}   ", style="bold yellow")
        detail.append(f"🎬 Episodes: ", style="dim")
        detail.append(f"{ep_count}   ", style="bold cyan")
        detail.append(f"📊 Status: ", style="dim")
        detail.append(f"{status}   ", style="bold green")
        detail.append(f"\n🏷️  Genres: ", style="dim")
        detail.append(genres, style="italic white")

        console.print(Panel(
            detail,
            title=f"[bold magenta]{anime.name}[/]",
            border_style="magenta",
            padding=(0, 2),
        ))
    except Exception:
        pass  # Info fetch is optional — silently skip if it fails

    return anime


def _parse_episode_range(episodes_str):
    """Parse '5' → [5] and '1-12' → [1,2,...,12]."""
    episodes_str = episodes_str.strip()
    if "-" in episodes_str:
        start, end = episodes_str.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(episodes_str)]


def _api_upgrade_hint(console):
    """Print a hint to upgrade anipy-api when things go wrong."""
    console.print(
        "[yellow]💡 If this keeps happening, try upgrading anipy-api:[/]\n"
        "   [dim]pip install --upgrade anipy-api --break-system-packages[/]"
    )


def _try_download_stream(stream, out_file, console):
    """
    Attempt to download a stream. Returns the result Path on success, None on failure.
    Handles HLS/ffmpeg check and gives clear error messages.
    """
    from anipy_api.download import Downloader

    is_hls = "m3u8" in stream.url
    if is_hls and not shutil.which("ffmpeg"):
        console.print(
            "[yellow]⚠️  This stream is HLS but ffmpeg is not installed.\n"
            "   Install it to download HLS streams:\n"
            "   [dim]sudo pacman -S ffmpeg   # Arch[/]\n"
            "   [dim]sudo apt install ffmpeg  # Debian/Ubuntu[/][/]"
        )
        return None

    last_pct = [-1]
    def progress_cb(pct, last=last_pct):
        if int(pct) % 10 == 0 and int(pct) != last[0]:
            last[0] = int(pct)
            console.print(f"[green]   {int(pct)}%...[/]")

    try:
        downloader = Downloader(progress_callback=progress_cb)
        result_path = downloader.download(stream, out_file, container=".mp4")
        return result_path
    except Exception as e:
        err = str(e).lower()
        if "403" in err or "forbidden" in err:
            return None   # signal caller to try next stream
        raise   # re-raise unexpected errors


def download_episodes(anime, episodes_str, quality, sub_dub, download_folder, console):
    """Download one or more episodes using anipy-api + ffmpeg/aria2c."""
    from anipy_api.provider import LanguageTypeEnum

    lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB

    try:
        available_eps = anime.get_episodes(lang)
    except Exception as e:
        console.print(f"[red]❌ Could not fetch episode list: {e}[/]")
        _api_upgrade_hint(console)
        return False

    if not available_eps:
        console.print("[red]❌ No episodes available for this anime/language.[/]")
        return False

    ep_numbers = _parse_episode_range(episodes_str)

    # Find closest matching Episode objects
    target_eps = []
    for num in ep_numbers:
        match = next((ep for ep in available_eps if float(ep) == float(num)), None)
        if match is None:
            console.print(f"[yellow]⚠️  Episode {num} not found, skipping.[/]")
        else:
            target_eps.append(match)

    if not target_eps:
        console.print("[red]❌ None of the requested episodes were found.[/]")
        console.print(f"[dim]   Available: {[str(e) for e in available_eps[:15]]}[/]")
        return False

    preferred_q = _quality_to_int(quality)
    success_count = 0

    for ep in target_eps:
        console.print(f"\n[cyan]⬇️  Fetching streams for episode {ep}...[/]")

        # ── Failsafe 1: get ALL streams, try each until one works ────
        try:
            all_streams = anime.get_videos(ep, lang)
        except Exception as e:
            console.print(f"[red]❌ Could not fetch streams for ep {ep}: {e}[/]")
            _api_upgrade_hint(console)
            continue

        if not all_streams:
            console.print(f"[red]❌ No streams found for episode {ep}.[/]")
            continue

        # Sort: prefer requested quality, then best available
        all_streams.sort(
            key=lambda s: abs(s.resolution - preferred_q)
        )

        safe_name = anime.name.replace("/", "-").replace("\\", "-")
        out_file = Path(download_folder) / f"{safe_name} - E{str(ep).zfill(2)}"

        downloaded = False
        for attempt, stream in enumerate(all_streams, 1):
            stream_type = "HLS" if "m3u8" in stream.url else "Direct"
            console.print(
                f"[dim]   Trying stream {attempt}/{len(all_streams)}: "
                f"{stream.resolution}p {stream_type}[/]"
            )
            try:
                result_path = _try_download_stream(stream, out_file, console)
                if result_path is not None:
                    console.print(f"[green]✅ Saved: {result_path.name}[/]")
                    success_count += 1
                    downloaded = True
                    break
                else:
                    console.print(f"[yellow]   ⚠️  Stream blocked (403), trying next...[/]")
            except Exception as e:
                console.print(f"[red]   ❌ Stream failed: {e}[/]")

        if not downloaded:
            console.print(
                f"[red]❌ All streams failed for episode {ep}. "
                f"The CDN may be blocking requests right now.[/]"
            )

    return success_count > 0


def stream_episode(anime, episode_str, quality, sub_dub, console):
    """Stream a single episode in mpv, with fallback across all streams."""
    from anipy_api.provider import LanguageTypeEnum

    lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB

    try:
        available_eps = anime.get_episodes(lang)
    except Exception as e:
        console.print(f"[red]❌ Could not fetch episode list: {e}[/]")
        _api_upgrade_hint(console)
        return False

    ep_num = float(episode_str.strip())
    ep = next((e for e in available_eps if float(e) == ep_num), None)

    if ep is None:
        console.print(f"[red]❌ Episode {episode_str} not found.[/]")
        console.print(f"[dim]   Available: {[str(e) for e in available_eps[:15]]}[/]")
        return False

    preferred_q = _quality_to_int(quality)
    console.print(f"\n[cyan]🔗 Fetching streams for episode {ep}...[/]")

    # ── Failsafe 1: get ALL streams, try each until one opens ────────
    try:
        all_streams = anime.get_videos(ep, lang)
    except Exception as e:
        console.print(f"[red]❌ Could not fetch streams: {e}[/]")
        _api_upgrade_hint(console)
        return False

    if not all_streams:
        console.print("[red]❌ No streams found.[/]")
        return False

    all_streams.sort(key=lambda s: abs(s.resolution - preferred_q))

    if not shutil.which("mpv"):
        console.print("[red]❌ mpv not found. Install it to stream.[/]")
        console.print(f"[yellow]   Direct URL: {all_streams[0].url}[/]")
        return False

    referrer = getattr(all_streams[0], "referrer", None) or "https://allanime.day"
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    for attempt, stream in enumerate(all_streams, 1):
        stream_type = "HLS" if "m3u8" in stream.url else "Direct"
        console.print(
            f"[dim]   Trying stream {attempt}/{len(all_streams)}: "
            f"{stream.resolution}p {stream_type}[/]"
        )
        console.print(f"\n[bold green]▶️  Opening in mpv...[/]\n")

        mpv_cmd = [
            "mpv",
            stream.url,
            "--no-ytdl",
            f"--title={anime.name} - Episode {ep}",
            f"--referrer={referrer}",
            f"--user-agent={user_agent}",
        ]
        if stream.subtitle:
            mpv_cmd.append(f"--sub-file={stream.subtitle}")

        result = subprocess.run(mpv_cmd)

        # mpv exit code 2 = file couldn't be opened (e.g. 403)
        if result.returncode != 2:
            return True

        console.print(f"[yellow]⚠️  Stream failed (blocked?), trying next...[/]")

    console.print(
        "[red]❌ All streams failed. The CDN may be blocking requests right now.[/]"
    )
    return False


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

    # ── Banner ──────────────────────────────
    banner = Text()
    banner.append("🎌  bb-dl", style="bold magenta")
    banner.append("   Anime Downloader & Streamer  ", style="dim white")
    banner.append("[AllAnime via anipy-api]", style="dim cyan")
    console.print(Panel(banner, border_style="magenta", padding=(0, 2)))
    console.print()

    show_history(console)

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

        if action is None or "Exit" in action:
            console.print("\n[bold magenta]👋  Goodbye![/]\n")
            break

        # ── Download ─────────────────────────
        elif "Download" in action:
            query = questionary.text("Enter anime name:").ask()
            if not query:
                continue

            sub_dub = questionary.select("Sub or Dub?",
                choices=["sub", "dub"],
                default=config["default_sub_dub"]).ask() or config["default_sub_dub"]

            anime = search_and_pick(query, sub_dub, console)
            if not anime:
                continue

            episodes = questionary.text("Episode or range (e.g. 1 or 1-12):").ask()
            if not episodes:
                continue

            quality = questionary.select("Quality?",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"]).ask() or config["default_quality"]

            download_folder = get_download_folder(anime.name, config)
            console.print(f"[dim]📁 Saving to: {download_folder}[/]")

            ok = download_episodes(
                anime, episodes, quality, sub_dub, download_folder, console
            )
            if ok:
                save_history(
                    anime.name, episodes, quality, sub_dub, "download",
                    identifier=anime.identifier,
                    provider_name=anime.provider.NAME,
                )
                console.print(f"\n[green]✅ Saved to history![/]")    

        # ── Stream ───────────────────────────
        elif "Stream" in action:
            query = questionary.text("Enter anime name:").ask()
            if not query:
                continue

            sub_dub = questionary.select("Sub or Dub?",
                choices=["sub", "dub"],
                default=config["default_sub_dub"]).ask() or config["default_sub_dub"]

            anime = search_and_pick(query, sub_dub, console)
            if not anime:
                continue

            episode = questionary.text("Episode number:").ask()
            if not episode:
                continue

            quality = questionary.select("Quality?",
                choices=["360p", "480p", "720p", "1080p"],
                default=config["default_quality"]).ask() or config["default_quality"]

            console.print(
                f"\n[bold green]▶️  Streaming {anime.name} episode {episode}...[/]\n"
            )
            ok = stream_episode(anime, episode, quality, sub_dub, console)
            if ok:
                save_history(
                    anime.name, episode, quality, sub_dub, "stream",
                    identifier=anime.identifier,
                    provider_name=anime.provider.NAME,
                )

        # ── Continue from history ─────────────
        elif "history" in action:
            history = load_history()
            if not history:
                console.print("[red]❌ No history yet. Download something first![/]")
                continue

            choices = [
                f"{e['title']}  |  Ep: {e['episodes']}  |  "
                f"{e['sub_dub'].upper()}  |  {e['quality']}  |  {e['date']}"
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

            sub_dub  = entry["sub_dub"]
            quality  = entry["quality"]
            provider_name = entry.get("provider", "allanime")
            identifier    = entry.get("identifier", entry["title"])

            resume = questionary.select("What do you want to do?", choices=[
                f"▶️   Continue from episode {next_ep}",
                f"🔁   Redownload last episode ({last_ep})",
            ]).ask()

            if resume is None:
                continue

            if "Redownload" in resume:
                episodes = str(last_ep)
                console.print(
                    f"\n[cyan]🔁 Redownloading: {entry['title']} episode {last_ep}[/]"
                )
            else:
                console.print(
                    f"\n[cyan]▶️  Continuing: {entry['title']} from episode {next_ep}[/]"
                )
                episodes = questionary.text("Episode or range:",
                    default=str(next_ep)).ask()
                if not episodes:
                    continue

            # Re-create the Anime object from saved identifier
            try:
                from anipy_api.provider import get_provider, LanguageTypeEnum
                from anipy_api.anime import Anime

                provider = get_provider(provider_name)  # class, not instance
                lang = (LanguageTypeEnum.DUB if sub_dub == "dub"
                        else LanguageTypeEnum.SUB)

                # Rebuild Anime from identifier (search to get full result)
                results = list(provider.get_search(entry["title"]))
                match = next(
                    (r for r in results if r.identifier == identifier), None
                )
                if match is None and results:
                    match = results[0]  # best guess

                if match is None:
                    console.print("[red]❌ Could not find anime. Try downloading fresh.[/]")
                    continue

                anime = Anime.from_search_result(provider, match)
            except Exception as e:
                console.print(f"[red]❌ Error restoring anime: {e}[/]")
                continue

            download_folder = get_download_folder(anime.name, config)

            ok = download_episodes(
                anime, episodes, quality, sub_dub, download_folder, console
            )
            if ok:
                save_history(
                    anime.name, episodes, quality, sub_dub, "download",
                    identifier=anime.identifier,
                    provider_name=anime.provider.NAME,
                )
                console.print(f"\n[green]✅ History updated![/]")

        # ── Settings ─────────────────────────
        elif "Settings" in action:
            settings_menu(console, config)


if __name__ == "__main__":
    main()
