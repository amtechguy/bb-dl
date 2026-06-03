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
    missing = []
    for pkg in ["requests", "rich", "questionary", "anipy_api"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
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

    needed = {"mpv": "mpv", "ffmpeg": "ffmpeg", "vlc": "vlc"}
    missing_sys = [pkg for binary, pkg in needed.items() if not shutil.which(binary)]
    if missing_sys:
        print(f"⚠️  Missing optional system deps: {', '.join(missing_sys)}")
        print(f"   Install with: sudo pacman -S {' '.join(missing_sys)}")
        print()


# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

CONFIG_DEFAULTS = {
    "default_quality":  "720p",
    "default_sub_dub":  "sub",
    "download_folder":  str(os.path.expanduser("~/Videos")),
    "player":           "mpv",
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
                f"🎮  Default Player       [{config.get('player', 'mpv')}]",
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
        elif "Player" in action:
            p = questionary.select("Select default player:",
                choices=["mpv", "vlc"],
                default=config.get("player", "mpv")).ask()
            if p:
                config["player"] = p
                save_config(config)
                console.print(f"[green]✅ Default player → {p}[/]")
        elif "Clear History" in action:
            clear_history(console)


# ─────────────────────────────────────────────
#  anipy-api helpers
# ─────────────────────────────────────────────

def _quality_to_int(quality_str):
    return int(quality_str.replace("p", "").strip())


# AllAnime is primary; AnimeKai is the fallback.
FALLBACK_PROVIDERS = ["allanime", "animekai"]


def get_provider_and_lang(sub_dub, provider_name="allanime"):
    from anipy_api.provider import get_provider, LanguageTypeEnum
    provider = get_provider(provider_name)
    lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB
    return provider, lang


def _search_with_fallback(query, sub_dub, console, preferred_provider="allanime"):
    """Search a specific provider. Returns (anime, provider_name) or (None, None)."""
    from anipy_api.anime import Anime
    from difflib import get_close_matches
    try:
        provider, lang = get_provider_and_lang(sub_dub, preferred_provider)
        results = list(provider.get_search(query))
        if not results:
            return None, None
        filtered = [r for r in results if lang in r.languages] or results
        names = [r.name for r in filtered]
        close = get_close_matches(query, names, n=1, cutoff=0.3)
        match = next((r for r in filtered if r.name == close[0]), filtered[0]) if close else filtered[0]
        anime = Anime.from_search_result(provider, match)
        return anime, preferred_provider
    except Exception:
        return None, None


def search_and_pick(query, sub_dub, console):
    """Search AllAnime, show results, let user pick. Returns Anime or None."""
    from anipy_api.anime import Anime
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import questionary

    provider, lang = get_provider_and_lang(sub_dub)

    console.print(f"\n[bold cyan]🔍 Searching for:[/] [yellow]{query}[/]")
    try:
        results = list(provider.get_search(query))
    except Exception as e:
        console.print(f"[red]❌ Search failed: {e}[/]")
        console.print("[yellow]💡 Try: pip install --upgrade anipy-api --break-system-packages[/]")
        return None

    if not results:
        console.print("[red]❌ No results found.[/]")
        return None

    filtered = [r for r in results if lang in r.languages]
    if not filtered:
        filtered = results
        console.print(f"[yellow]⚠️  No {sub_dub} results; showing all.[/]")

    # Fetch years in parallel
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

    console.print(" " * 30, end="\r")

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

    choices = [
        f"{r.name}  [{'/'.join(sorted(lv.value.upper() for lv in r.languages))}]"
        for r in filtered
    ]
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

    # Show details for selected anime
    console.print("[dim]⏳ Fetching details...[/]", end="\r")
    try:
        info = provider.get_info(selected_result.identifier)
        ep_count = len(anime.get_episodes(lang))
        year    = str(info.release_year) if info.release_year else "?"
        status  = info.status.name.capitalize() if info.status else "?"
        genres  = ", ".join(info.genres[:4]) if info.genres else "?"

        detail = Text()
        detail.append(f"📅 Year: ",      style="dim")
        detail.append(f"{year}   ",      style="bold yellow")
        detail.append(f"🎬 Episodes: ",  style="dim")
        detail.append(f"{ep_count}   ",  style="bold cyan")
        detail.append(f"📊 Status: ",    style="dim")
        detail.append(f"{status}   ",    style="bold green")
        detail.append(f"\n🏷️  Genres: ", style="dim")
        detail.append(genres,            style="italic white")

        console.print(Panel(
            detail,
            title=f"[bold magenta]{anime.name}[/]",
            border_style="magenta",
            padding=(0, 2),
        ))
    except Exception:
        pass

    return anime


def _parse_episode_range(episodes_str):
    episodes_str = episodes_str.strip()
    if "-" in episodes_str:
        start, end = episodes_str.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(episodes_str)]


def _api_upgrade_hint(console):
    console.print(
        "[yellow]💡 Try upgrading anipy-api:[/]\n"
        "   [dim]pip install --upgrade anipy-api --break-system-packages[/]"
    )


def _is_provider_error(exc):
    """Detect AllAnime/AnimeKai server-side episode errors."""
    msg = str(exc)
    return (
        "NoneType' object is not subscriptable" in msg
        or "'episode'" in msg
        or ("episode" in msg.lower() and "NoneType" in msg)
        or "KeyError" in msg
    )


def _provider_error_message(console, provider_name):
    console.print()
    console.print(
        f"[bold red]🚨 {provider_name} is returning broken responses.[/]\n"
        "[yellow]   This is an upstream provider issue, not a bb-dl bug.[/]\n"
        "[dim]   The provider's server is returning bad data — nothing fixable locally.[/]"
    )
    console.print()


def _get_streams_with_fallback(anime, ep, lang, sub_dub, console):
    """
    Try to get streams for `ep` from the anime's provider.
    If it fails with a known provider error, try the other provider.
    Returns (streams, anime_used) or (None, None).
    """
    # Try primary provider first
    try:
        streams = anime.get_videos(ep, lang)
        if streams:
            return streams, anime
    except Exception as e:
        if _is_provider_error(e):
            _provider_error_message(console, anime.provider.NAME)
        else:
            console.print(f"[red]❌ Stream fetch error: {e}[/]")
            _api_upgrade_hint(console)
            return None, None

    # Try fallback providers
    for fallback_name in FALLBACK_PROVIDERS:
        if fallback_name == anime.provider.NAME:
            continue
        console.print(f"[cyan]🔄 Trying fallback: {fallback_name}...[/]")
        try:
            fb_anime, _ = _search_with_fallback(
                anime.name, sub_dub, console, preferred_provider=fallback_name
            )
            if fb_anime is None:
                console.print(f"[yellow]   ⚠️  No match on {fallback_name}[/]")
                continue

            from anipy_api.provider import LanguageTypeEnum
            fb_lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB
            fb_eps  = fb_anime.get_episodes(fb_lang)
            fb_ep   = next((e for e in fb_eps if float(e) == float(ep)), None)

            if fb_ep is None:
                console.print(f"[yellow]   ⚠️  Episode not found on {fallback_name}[/]")
                continue

            streams = fb_anime.get_videos(fb_ep, fb_lang)
            if streams:
                console.print(f"[green]   ✅ Got streams from {fallback_name}[/]")
                return streams, fb_anime

        except Exception as fb_e:
            console.print(f"[yellow]   ⚠️  {fallback_name} also failed: {fb_e}[/]")

    console.print("[red]❌ All providers failed. Try again later.[/]")
    return None, None


def _try_download_stream(stream, out_file, console):
    """Try to download a stream. Returns result Path on success, None on 403."""
    from anipy_api.download import Downloader
    from rich.progress import (
        Progress, BarColumn, DownloadColumn,
        TransferSpeedColumn, TimeRemainingColumn, TextColumn,
    )

    is_hls = "m3u8" in stream.url
    if is_hls and not shutil.which("ffmpeg"):
        console.print(
            "[yellow]⚠️  HLS stream requires ffmpeg.\n"
            "   Install it: sudo pacman -S ffmpeg[/]"
        )
        return None

    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30, style="cyan", complete_style="green"),
        "[progress.percentage]{task.percentage:>5.1f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Downloading", total=100)

        def progress_cb(pct):
            progress.update(task, completed=float(pct))

        try:
            downloader = Downloader(progress_callback=progress_cb)
            result_path = downloader.download(stream, out_file, container=".mp4")
            progress.update(task, completed=100)
            return result_path
        except KeyboardInterrupt:
            progress.stop()
            raise
        except Exception as e:
            err = str(e).lower()
            if "403" in err or "forbidden" in err:
                return None
            raise


def download_episodes(anime, episodes_str, quality, sub_dub, download_folder, console):
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

    ep_numbers  = _parse_episode_range(episodes_str)
    preferred_q = _quality_to_int(quality)
    success_count = 0

    for num in ep_numbers:
        ep = next((e for e in available_eps if float(e) == float(num)), None)
        if ep is None:
            console.print(f"[yellow]⚠️  Episode {num} not found, skipping.[/]")
            console.print(f"[dim]   Available: {[str(e) for e in available_eps[:15]]}[/]")
            continue

        console.print(f"\n[cyan]⬇️  Fetching streams for episode {ep}...[/]")
        streams, used_anime = _get_streams_with_fallback(anime, ep, lang, sub_dub, console)

        if not streams:
            continue

        streams.sort(key=lambda s: abs(s.resolution - preferred_q))

        safe_name = used_anime.name.replace("/", "-").replace("\\", "-")
        out_file  = Path(download_folder) / f"{safe_name} - E{str(ep).zfill(2)}"

        downloaded = False
        for attempt, stream in enumerate(streams, 1):
            stream_type = "HLS" if "m3u8" in stream.url else "Direct"
            console.print(
                f"[dim]   Trying stream {attempt}/{len(streams)}: "
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
                    console.print("[yellow]   ⚠️  Stream blocked (403), trying next...[/]")
            except Exception as e:
                console.print(f"[red]   ❌ Stream error: {e}[/]")

        if not downloaded:
            console.print(f"[red]❌ All streams failed for episode {ep}.[/]")

    return success_count > 0


def stream_episode(anime, episode_str, quality, sub_dub, console, player="mpv"):
    from anipy_api.provider import LanguageTypeEnum

    lang = LanguageTypeEnum.DUB if sub_dub == "dub" else LanguageTypeEnum.SUB

    try:
        available_eps = anime.get_episodes(lang)
    except Exception as e:
        console.print(f"[red]❌ Could not fetch episode list: {e}[/]")
        _api_upgrade_hint(console)
        return False

    ep_num = float(episode_str.strip())
    ep     = next((e for e in available_eps if float(e) == ep_num), None)

    if ep is None:
        console.print(f"[red]❌ Episode {episode_str} not found.[/]")
        console.print(f"[dim]   Available: {[str(e) for e in available_eps[:15]]}[/]")
        return False

    preferred_q = _quality_to_int(quality)
    console.print(f"\n[cyan]🔗 Fetching streams for episode {ep}...[/]")

    streams, stream_anime = _get_streams_with_fallback(anime, ep, lang, sub_dub, console)
    if not streams:
        return False

    streams.sort(key=lambda s: abs(s.resolution - preferred_q))

    if not shutil.which(player):
        install_pkg = "vlc" if player == "vlc" else "mpv"
        console.print(f"[red]❌ {player} not found. Install it: sudo pacman -S {install_pkg}[/]")
        console.print(f"[yellow]   Direct URL: {streams[0].url}[/]")
        return False

    referrer   = getattr(streams[0], "referrer", None) or "https://allanime.day"
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    for attempt, stream in enumerate(streams, 1):
        stream_type = "HLS" if "m3u8" in stream.url else "Direct"
        console.print(
            f"[dim]   Trying stream {attempt}/{len(streams)}: "
            f"{stream.resolution}p {stream_type}[/]"
        )
        console.print(f"\n[bold green]▶️  Opening in mpv...[/]\n")

        if player == "vlc":
            player_cmd = [
                "vlc", stream.url,
                f"--http-referrer={referrer}",
                f"--http-user-agent={user_agent}",
            ]
        else:
            player_cmd = [
                "mpv", stream.url,
                "--no-ytdl",
                f"--title={stream_anime.name} - Episode {ep}",
                f"--referrer={referrer}",
                f"--user-agent={user_agent}",
            ]
        if stream.subtitle:
            player_cmd.append(f"--sub-file={stream.subtitle}")

        result = subprocess.run(player_cmd)
        if result.returncode != 2:
            return True

        console.print("[yellow]⚠️  Stream failed (blocked?), trying next...[/]")

    console.print("[red]❌ All streams failed. Provider may be down.[/]")
    return False


# ─────────────────────────────────────────────
#  Discover (Jikan API)
# ─────────────────────────────────────────────

def _jikan_get(url, console):
    """Fetch from Jikan API with error handling. Returns parsed JSON or None."""
    import requests
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        console.print(f"[red]❌ Could not reach Jikan API: {e}[/]")
        return None


def _pick_from_anime_list(items, console, title):
    """Show a Rich table of anime and let the user pick one. Returns title string or None."""
    from rich.table import Table
    import questionary

    if not items:
        console.print("[yellow]⚠️  No results found.[/]")
        return None

    table = Table(title=title, border_style="yellow",
                  header_style="bold magenta", show_lines=True)
    table.add_column("#",      style="dim",       width=4,  justify="right")
    table.add_column("Title",  style="bold white")
    table.add_column("Score",  style="yellow",    width=7,  justify="center")
    table.add_column("Eps",    style="cyan",       width=5,  justify="center")
    table.add_column("Genres", style="dim",        width=25)

    for i, a in enumerate(items, 1):
        score  = str(a.get("score") or "?")
        eps    = str(a.get("episodes") or "?")
        genres = ", ".join(g["name"] for g in a.get("genres", [])[:3]) or "?"
        table.add_row(str(i), a["title"], score, eps, genres)

    console.print(table)

    choices = [a["title"] for a in items]
    choices.append("← Back")

    pick = questionary.select(
        "Pick an anime to search for:",
        choices=choices,
        style=questionary.Style([
            ("selected", "fg:yellow bold"),
            ("pointer",  "fg:yellow bold"),
        ]),
    ).ask()

    if pick is None or pick == "← Back":
        return None
    return pick


def _fetch_top_airing(console):
    console.print("[dim]⏳ Fetching top airing anime...[/]", end="\r")
    data = _jikan_get("https://api.jikan.moe/v4/top/anime?filter=airing&limit=10", console)
    console.print(" " * 45, end="\r")
    if not data:
        return None
    return _pick_from_anime_list(data.get("data", []), console, "🔥 Top Airing This Week")


def _fetch_current_season(console):
    console.print("[dim]⏳ Fetching current season...[/]", end="\r")
    data = _jikan_get("https://api.jikan.moe/v4/seasons/now?limit=20", console)
    console.print(" " * 45, end="\r")
    if not data:
        return None
    return _pick_from_anime_list(data.get("data", []), console, "📺 Currently Airing This Season")


def _fetch_weekly_schedule(console):
    import questionary
    from datetime import datetime

    days  = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = datetime.now().strftime("%A").lower()

    day_pick = questionary.select(
        "Which day?",
        choices=[
            d.capitalize() + (" (today)" if d == today else "")
            for d in days
        ] + ["← Back"],
        style=questionary.Style([
            ("selected", "fg:cyan bold"),
            ("pointer",  "fg:cyan bold"),
        ]),
    ).ask()

    if day_pick is None or "Back" in day_pick:
        return None

    day_key = day_pick.split()[0].lower()
    console.print(f"[dim]⏳ Fetching {day_key.capitalize()}'s schedule...[/]", end="\r")
    data = _jikan_get(
        f"https://api.jikan.moe/v4/schedules?filter={day_key}&limit=20", console
    )
    console.print(" " * 45, end="\r")
    if not data:
        return None
    return _pick_from_anime_list(
        data.get("data", []), console, f"📅 {day_key.capitalize()}'s Schedule"
    )


def discover_menu(console):
    import questionary
    while True:
        console.print()
        choice = questionary.select(
            "🌟  Discover — what would you like to browse?",
            choices=[
                "🔥  Top airing this week",
                "📺  Currently airing this season",
                "📅  This week's schedule",
                "← Back",
            ],
            style=questionary.Style([
                ("selected", "fg:yellow bold"),
                ("pointer",  "fg:yellow bold"),
            ]),
        ).ask()

        if choice is None or "Back" in choice:
            return None

        if "Top airing" in choice:
            title = _fetch_top_airing(console)
        elif "Currently airing" in choice:
            title = _fetch_current_season(console)
        elif "schedule" in choice:
            title = _fetch_weekly_schedule(console)
        else:
            return None

        if title:
            return title


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

    banner = Text()
    banner.append("🎌  bb-dl", style="bold magenta")
    banner.append("   Anime Downloader & Streamer  ", style="dim white")
    banner.append("[AllAnime · AnimeKai]", style="dim cyan")
    console.print(Panel(banner, border_style="magenta", padding=(0, 2)))
    console.print()

    show_history(console)

    try:
        while True:
            action = questionary.select(
                "What do you want to do?",
                choices=[
                    "⬇️   Download anime",
                    "▶️   Stream anime",
                    "🌟   Discover anime",
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

                ok = download_episodes(anime, episodes, quality, sub_dub, download_folder, console)
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

                console.print(f"\n[bold green]▶️  Streaming {anime.name} episode {episode}...[/]\n")
                ok = stream_episode(anime, episode, quality, sub_dub, console,
                                    player=config.get("player", "mpv"))
                if ok:
                    save_history(
                        anime.name, episode, quality, sub_dub, "stream",
                        identifier=anime.identifier,
                        provider_name=anime.provider.NAME,
                    )

            # ── Discover ─────────────────────────
            elif "Discover" in action:
                discovered_title = discover_menu(console)
                if not discovered_title:
                    continue

                sub_dub = questionary.select("Sub or Dub?",
                    choices=["sub", "dub"],
                    default=config["default_sub_dub"]).ask() or config["default_sub_dub"]

                anime = search_and_pick(discovered_title, sub_dub, console)
                if not anime:
                    continue

                mode = questionary.select(
                    "Download or Stream?",
                    choices=["⬇️   Download", "▶️   Stream"],
                    style=questionary.Style([
                        ("selected", "fg:magenta bold"),
                        ("pointer",  "fg:magenta bold"),
                    ]),
                ).ask()

                if mode and "Download" in mode:
                    episodes = questionary.text("Episode or range (e.g. 1 or 1-12):").ask()
                    if not episodes:
                        continue
                    quality = questionary.select("Quality?",
                        choices=["360p", "480p", "720p", "1080p"],
                        default=config["default_quality"]).ask() or config["default_quality"]
                    download_folder = get_download_folder(anime.name, config)
                    console.print(f"[dim]📁 Saving to: {download_folder}[/]")
                    ok = download_episodes(anime, episodes, quality, sub_dub, download_folder, console)
                    if ok:
                        save_history(anime.name, episodes, quality, sub_dub, "download",
                            identifier=anime.identifier, provider_name=anime.provider.NAME)
                        console.print(f"\n[green]✅ Saved to history![/]")
                elif mode and "Stream" in mode:
                    episode = questionary.text("Episode number:").ask()
                    if not episode:
                        continue
                    quality = questionary.select("Quality?",
                        choices=["360p", "480p", "720p", "1080p"],
                        default=config["default_quality"]).ask() or config["default_quality"]
                    console.print(f"\n[bold green]▶️  Streaming {anime.name} episode {episode}...[/]\n")
                    ok = stream_episode(anime, episode, quality, sub_dub, console,
                                        player=config.get("player", "mpv"))
                    if ok:
                        save_history(anime.name, episode, quality, sub_dub, "stream",
                            identifier=anime.identifier, provider_name=anime.provider.NAME)

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

                sub_dub       = entry["sub_dub"]
                quality       = entry["quality"]
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
                    console.print(f"\n[cyan]🔁 Redownloading: {entry['title']} episode {last_ep}[/]")
                else:
                    console.print(f"\n[cyan]▶️  Continuing: {entry['title']} from episode {next_ep}[/]")
                    episodes = questionary.text("Episode or range:",
                        default=str(next_ep)).ask()
                    if not episodes:
                        continue

                try:
                    from anipy_api.provider import get_provider, LanguageTypeEnum
                    from anipy_api.anime import Anime

                    provider = get_provider(provider_name)
                    results  = list(provider.get_search(entry["title"]))
                    match    = next((r for r in results if r.identifier == identifier), None)
                    if match is None and results:
                        match = results[0]
                    if match is None:
                        console.print("[red]❌ Could not find anime. Try downloading fresh.[/]")
                        continue

                    anime = Anime.from_search_result(provider, match)
                except Exception as e:
                    console.print(f"[red]❌ Error restoring anime: {e}[/]")
                    continue

                download_folder = get_download_folder(anime.name, config)
                ok = download_episodes(anime, episodes, quality, sub_dub, download_folder, console)
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

    except KeyboardInterrupt:
        console.print("\n\n[bold magenta]👋  Interrupted. Goodbye![/]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋  Interrupted. Goodbye!\n")
