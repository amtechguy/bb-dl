#!/usr/bin/env python3

import subprocess
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

CONFIG_DIR = os.path.expanduser("~/.config/bb-ani")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
WATCHLIST_FILE = os.path.join(CONFIG_DIR, "watchlist.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def check_dependencies():
    missing = []
    for pkg in ["requests", "rich", "questionary"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print(f"📦 Installing: {', '.join(missing)} ...")
        subprocess.run([sys.executable, "-m", "pip", "install", *missing, "--break-system-packages"], check=True)
    
    result = subprocess.run(["which", "ani-cli"], capture_output=True)
    if result.returncode != 0:
        print("📦 Installing ani-cli...")
        subprocess.run(["yay", "-S", "ani-cli", "--noconfirm"], check=True)

check_dependencies()

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import questionary
from rich import print as rprint

console = Console()

# Ensure config dir exists
os.makedirs(CONFIG_DIR, exist_ok=True)

def load_json(filepath, default_val):
    if not os.path.exists(filepath):
        return default_val
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return default_val

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def load_history():
    # Fallback to old history file if it exists and new one doesn't
    old_history = os.path.expanduser("~/.bb-dl/history.json")
    old_v2_history = os.path.expanduser("~/.config/bb-dl/history.json")
    if not os.path.exists(HISTORY_FILE):
        if os.path.exists(old_v2_history):
            return load_json(old_v2_history, [])
        elif os.path.exists(old_history):
            return load_json(old_history, [])
    return load_json(HISTORY_FILE, [])

def save_history(title, episodes, quality, sub_dub, type_action="download"):
    history = load_history()
    history = [e for e in history if e["title"] != title]
    
    history.insert(0, {
        "title": title,
        "episodes": episodes,
        "quality": quality,
        "sub_dub": sub_dub,
        "type": type_action,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_json(HISTORY_FILE, history)

def load_watchlist():
    return load_json(WATCHLIST_FILE, [])

def save_watchlist(anime_data):
    watchlist = load_watchlist()
    if not any(e["title"] == anime_data["title"] for e in watchlist):
        watchlist.insert(0, anime_data)
        save_json(WATCHLIST_FILE, watchlist)
        console.print(f"[green]⭐ Added '{anime_data['title']}' to your Watchlist![/green]")
    else:
        console.print(f"[yellow]⭐ '{anime_data['title']}' is already in your Watchlist.[/yellow]")

def get_config():
    default_config = {"library_dirs": ["~/Videos/Anime"]}
    config = load_json(CONFIG_FILE, default_config)
    if "library_dirs" not in config:
        config["library_dirs"] = default_config["library_dirs"]
    return config

def clean_html(raw_html):
    if not raw_html: return "No description available."
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.replace("&quot;", '"').replace("&#039;", "'").replace("&amp;", "&").strip()

def format_episodes(anime):
    status = anime.get("status")
    total_eps = anime.get("episodes")
    next_airing = anime.get("nextAiringEpisode")
    
    if status == "RELEASING" and next_airing:
        current_ep = next_airing.get("episode", 1) - 1
        if total_eps:
            return f"{current_ep}/{total_eps}"
        return str(current_ep)
    return str(total_eps) if total_eps else "?"

def parse_kitsu_anime(anime):
    attrs = anime.get("attributes", {})
    titles = attrs.get("titles", {}) if attrs.get("titles") else {}
    title = attrs.get("canonicalTitle") or titles.get("en") or titles.get("en_jp") or "Unknown"
    
    eps = attrs.get("episodeCount")
    episodes = str(eps) if eps else "?"
    if attrs.get("status") == "current" and attrs.get("nextRelease"):
        episodes = f"?/{episodes}" if eps else "?"
        
    start_date = attrs.get("startDate")
    year = start_date.split("-")[0] if start_date else "?"
    
    score = attrs.get("averageRating")
    if score:
        try: score = round(float(score))
        except: score = "N/A"
    else: score = "N/A"
    
    return {
        "title": title,
        "episodes": episodes,
        "year": year,
        "score": score,
        "description": attrs.get("synopsis") or attrs.get("description"),
        "genres": [],
        "status": attrs.get("status") or "UNKNOWN"
    }

def search_anime(query):
    with console.status(f"[cyan]Searching for '{query}'..."):
        try:
            url = "https://graphql.anilist.co"
            graphql_query = '''
            query ($search: String) {
              Page(page: 1, perPage: 15) {
                media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
                  title { romaji english }
                  episodes
                  seasonYear
                  averageScore
                  description(asHtml: false)
                  genres
                  status
                  nextAiringEpisode { episode }
                }
              }
            }
            '''
            response = requests.post(
                url,
                json={"query": graphql_query, "variables": {"search": query}},
                timeout=10
            )
            data = response.json()
            data_block = data.get("data")
            if not data_block:
                errors = data.get("errors", [])
                err_msg = errors[0].get("message") if errors else "API returned empty data"
                raise Exception(err_msg)
                
            results = []
            for anime in data_block.get("Page", {}).get("media", []):
                title = anime.get("title", {}).get("english") or anime.get("title", {}).get("romaji")
                results.append({
                    "title": title,
                    "episodes": format_episodes(anime),
                    "year": anime.get("seasonYear") or "?",
                    "score": anime.get("averageScore") or "N/A",
                    "description": anime.get("description"),
                    "genres": anime.get("genres") or [],
                    "status": anime.get("status") or "UNKNOWN"
                })
            return results
        except Exception as e:
            console.print(f"[yellow]AniList failed ({e}), falling back to Kitsu...[/yellow]")
            try:
                kitsu_url = f"https://kitsu.io/api/edge/anime?filter[text]={query}&page[limit]=15"
                resp = requests.get(kitsu_url, timeout=10).json()
                results = []
                for anime in resp.get("data", []):
                    results.append(parse_kitsu_anime(anime))
                return results
            except Exception as e2:
                console.print(f"[red]Error searching (both APIs failed): {e2}[/red]")
                return []

# ─────────────────────────────────────────────
#  Genre browser (AniList API — same as search)
# ─────────────────────────────────────────────

def _anilist_post(query, variables=None):
    """POST to AniList GraphQL. Returns response data dict or None."""
    try:
        resp = requests.post(
            "https://graphql.anilist.co",
            json={"query": query, "variables": variables or {}},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise Exception(result["errors"][0].get("message", "GraphQL error"))
        return result.get("data")
    except Exception as e:
        console.print(f"[red]❌ AniList error: {e}[/red]")
        return None


# AniList's full genre list — no API call needed, it's a fixed set.
ANILIST_GENRES = sorted([
    "Action", "Adventure", "Comedy", "Drama", "Ecchi", "Fantasy",
    "Horror", "Mahou Shoujo", "Mecha", "Music", "Mystery", "Psychological",
    "Romance", "Sci-Fi", "Slice of Life", "Sports", "Supernatural", "Thriller",
])

SORT_OPTIONS = {
    "⭐  Score (highest rated)": "SCORE_DESC",
    "🔥  Popularity":            "POPULARITY_DESC",
    "📅  Newest first":          "START_DATE_DESC",
    "🔀  No sort (full catalog)": "ID",
}


def browse_by_genre():
    """Let the user pick a genre, then page through the full AniList catalog."""

    # ── Genre pick ───────────────────────────────────────────
    genre_choices = [questionary.Choice(g, g) for g in ANILIST_GENRES]
    genre_choices.append(questionary.Choice("❌ Back", "cancel"))

    chosen_genre = questionary.select(
        "🎭  Pick a genre:",
        choices=genre_choices,
        style=questionary.Style([("highlighted", "fg:green bold")]),
    ).ask()

    if not chosen_genre or chosen_genre == "cancel":
        return

    # ── Sort pick ────────────────────────────────────────────
    sort_label = questionary.select(
        f"Sort '{chosen_genre}' by:",
        choices=list(SORT_OPTIONS.keys()) + ["❌  Back"],
        style=questionary.Style([("highlighted", "fg:green bold")]),
    ).ask()

    if not sort_label or sort_label == "❌  Back":
        return

    sort_value = SORT_OPTIONS[sort_label]

    # ── Paginated catalog loop ───────────────────────────────
    PAGE_SIZE = 25
    page      = 1
    last_page = None
    total_items = "?"

    GQL = """
    query ($genre: String, $page: Int, $perPage: Int, $sort: [MediaSort]) {
      Page(page: $page, perPage: $perPage) {
        pageInfo { total currentPage lastPage hasNextPage }
        media(type: ANIME, genre: $genre, sort: $sort) {
          title { english romaji }
          episodes
          seasonYear
          averageScore
          genres
          status
          description(asHtml: false)
          nextAiringEpisode { episode }
        }
      }
    }
    """

    while True:
        page_label = f"{page}/{last_page}" if last_page else str(page)
        with console.status(f"[cyan]Loading page {page_label} of {chosen_genre}..."):
            data = _anilist_post(GQL, {
                "genre":   chosen_genre,
                "page":    page,
                "perPage": PAGE_SIZE,
                "sort":    [sort_value],
            })

        if not data:
            input("\nPress Enter to return to menu...")
            return

        page_info = data["Page"]["pageInfo"]
        items_raw = data["Page"]["media"]

        if last_page is None:
            last_page   = page_info.get("lastPage", 1)
            total_items = page_info.get("total", "?")

        if not items_raw:
            console.print("[yellow]⚠️  No results on this page.[/yellow]")
            input("\nPress Enter to return to menu...")
            return

        # Normalise into bb-ani's internal shape right away
        items = []
        for a in items_raw:
            title = (a.get("title") or {}).get("english") or (a.get("title") or {}).get("romaji") or "Unknown"
            items.append({
                "title":       title,
                "episodes":    format_episodes(a),
                "year":        str(a.get("seasonYear") or "?"),
                "score":       a.get("averageScore") or "N/A",
                "description": a.get("description") or "",
                "genres":      a.get("genres") or [],
                "status":      a.get("status") or "UNKNOWN",
            })

        # ── Draw table ───────────────────────────────────────
        offset = (page - 1) * PAGE_SIZE
        table = Table(
            title=f"\n🎭 {chosen_genre}  —  Page {page}/{last_page}  ({total_items} total)",
            style="green", show_header=True, header_style="bold magenta",
        )
        table.add_column("#",      style="dim",      width=5)
        table.add_column("Title",  style="bold white")
        table.add_column("Year",   justify="center", style="magenta", width=6)
        table.add_column("Eps",    justify="center", style="green",   width=5)
        table.add_column("Score",  justify="center", style="yellow",  width=7)
        table.add_column("Genres", style="dim",      width=30)

        for i, a in enumerate(items, 1):
            g_list = ", ".join(a["genres"][:3]) or "?"
            score  = f"{a['score']}/100" if str(a["score"]).isdigit() else str(a["score"])
            table.add_row(str(offset + i), a["title"], a["year"], a["episodes"], score, g_list)

        console.print(table)
        console.print()

        # ── Picker ───────────────────────────────────────────
        anime_choices = [questionary.Choice(a["title"], a) for a in items]

        if page > 1:
            anime_choices.append(questionary.Choice("⬅️   Previous page", "prev"))
        if page < last_page:
            anime_choices.append(questionary.Choice("➡️   Next page",     "next"))
        anime_choices.append(questionary.Choice("🔢  Jump to page",        "jump"))
        anime_choices.append(questionary.Choice("❌  Back to genres",      "back"))

        pick = questionary.select(
            f"Pick an anime  (page {page}/{last_page}):",
            choices=anime_choices,
            style=questionary.Style([("highlighted", "fg:green bold")]),
        ).ask()

        if not pick or pick == "back":
            return
        elif pick == "prev":
            page -= 1
        elif pick == "next":
            page += 1
        elif pick == "jump":
            jump = questionary.text(
                f"Go to page (1–{last_page}):",
                validate=lambda v: (v.isdigit() and 1 <= int(v) <= last_page)
                                   or f"Enter a number between 1 and {last_page}",
            ).ask()
            if jump:
                page = int(jump)
        else:
            handle_anime_action(pick)
            return


def discover_anime():
    with console.status("[cyan]Fetching latest anime trends..."):
        try:
            url = "https://graphql.anilist.co"
            graphql_query = '''
            query {
              trending: Page(page: 1, perPage: 15) {
                media(type: ANIME, sort: TRENDING_DESC) { title { english romaji } episodes seasonYear averageScore description(asHtml: false) genres status nextAiringEpisode { episode } }
              }
              popular: Page(page: 1, perPage: 15) {
                media(type: ANIME, sort: POPULARITY_DESC) { title { english romaji } episodes seasonYear averageScore description(asHtml: false) genres status nextAiringEpisode { episode } }
              }
              new: Page(page: 1, perPage: 15) {
                media(type: ANIME, status: RELEASING, sort: START_DATE_DESC) { title { english romaji } episodes seasonYear averageScore description(asHtml: false) genres status nextAiringEpisode { episode } }
              }
            }
            '''
            response = requests.post(url, json={"query": graphql_query}, timeout=10)
            data = response.json()
            data_block = data.get("data")
            if not data_block:
                errors = data.get("errors", [])
                err_msg = errors[0].get("message") if errors else "API returned empty data"
                raise Exception(err_msg)
                
            parsed = {"trending": [], "popular": [], "new": []}
            for cat in ["trending", "popular", "new"]:
                for anime in data_block.get(cat, {}).get("media", []):
                    title = anime.get("title", {}).get("english") or anime.get("title", {}).get("romaji")
                    parsed[cat].append({
                        "title": title,
                        "episodes": format_episodes(anime),
                        "year": anime.get("seasonYear") or "?",
                        "score": anime.get("averageScore") or "N/A",
                        "description": anime.get("description"),
                        "genres": anime.get("genres") or [],
                        "status": anime.get("status") or "UNKNOWN"
                    })
            return parsed
        except Exception as e:
            console.print(f"[yellow]AniList failed ({e}), falling back to Kitsu...[/yellow]")
            try:
                trending = requests.get("https://kitsu.io/api/edge/trending/anime?limit=15", timeout=10).json().get("data", [])
                popular = requests.get("https://kitsu.io/api/edge/anime?sort=-userCount&page[limit]=15", timeout=10).json().get("data", [])
                new = requests.get("https://kitsu.io/api/edge/anime?filter[status]=current&sort=-startDate&page[limit]=15", timeout=10).json().get("data", [])
                
                return {
                    "trending": [parse_kitsu_anime(a) for a in trending],
                    "popular": [parse_kitsu_anime(a) for a in popular],
                    "new": [parse_kitsu_anime(a) for a in new]
                }
            except Exception as e2:
                console.print(f"[red]Error fetching discover lists (both APIs failed): {e2}[/red]")
                return None

def display_anime_table(title, results):
    table = Table(title=f"\n[bold]{title}[/bold]", style="cyan", show_header=True, header_style="bold blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="bold white")
    table.add_column("Year", justify="center", style="magenta")
    table.add_column("Eps", justify="center", style="green")
    table.add_column("Score", justify="center", style="yellow")
    
    for idx, r in enumerate(results):
        score_str = f"{r['score']}/100" if str(r['score']).isdigit() else str(r['score'])
        table.add_row(
            str(idx + 1),
            r["title"],
            str(r["year"]),
            str(r["episodes"]),
            score_str
        )
    console.print(table)
    console.print()

def display_anime_info(anime):
    console.clear()
    desc = clean_html(anime.get('description'))
    if len(desc) > 800:
        desc = desc[:797] + "..."
        
    genres = ", ".join(anime.get('genres', []))
    status = str(anime.get('status', 'UNKNOWN')).replace("_", " ").title()
    score = f"{anime.get('score', 'N/A')}/100" if str(anime.get('score')).isdigit() else str(anime.get('score'))
    
    info_text = f"[bold cyan]Status:[/bold cyan] {status}\n"
    info_text += f"[bold magenta]Genres:[/bold magenta] {genres}\n"
    info_text += f"[bold yellow]Score:[/bold yellow] {score} | [bold green]Episodes:[/bold green] {anime.get('episodes', '?')}\n\n"
    info_text += f"[italic]{desc}[/italic]"
    
    panel = Panel(
        info_text,
        title=f"[bold white]{anime['title']}[/bold white]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)
    console.print()

def get_download_folder(anime_title):
    safe_title = "".join([c for c in anime_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    folder = os.path.expanduser(f"~/Videos/Anime/{safe_title}")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def simplify_title(title):
    """Strip verbose English subtitles that ani-cli's source won't have."""
    import re
    title = re.sub(r'\s*[-\u2013]\s*Starting Life in Another World[-\u2013]?', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*(Season|Part)\s+\d+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(\d{4}\)', '', title)
    return title.strip()

def run_ani_cli(title, episodes, quality, sub_dub, action_type):
    ani_cli_path = os.path.expanduser("~/.local/bin/ani-cli")
    if not os.path.exists(ani_cli_path):
        ani_cli_path = "ani-cli"

    # Let user confirm/edit the search term so ani-cli finds the right show
    suggested = simplify_title(title)
    console.print(f"\n[cyan]ani-cli will search for:[/cyan] [yellow]{suggested}[/yellow]")
    search_term = questionary.text(
        "Edit search term if needed (or press Enter to confirm):",
        default=suggested
    ).ask()
    if not search_term:
        search_term = suggested

    command = [ani_cli_path, "-q", quality]
    if sub_dub == "dub":
        command.append("--dub")
    if action_type == "download":
        command.append("-d")

    command.extend(["-e", str(episodes)])
    command.append(search_term)

    console.print(f"\n[cyan]\U0001f680 Launching ani-cli...[/cyan]")

    if action_type == "download":
        download_folder = get_download_folder(title)
        os.chdir(download_folder)
        console.print(f"[green]\U0001f4c1 Saving to: {download_folder}[/green]")

    try:
        subprocess.call(command)
        save_history(title, episodes, quality, sub_dub, action_type)
        console.print("\n[green]\u2705 Operation completed![/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]\u26a0\ufe0f Interrupted by user.[/yellow]")

def update_backend():
    ani_cli_path = os.path.expanduser("~/.local/bin/ani-cli")
    if not os.path.exists(ani_cli_path):
        console.print("[yellow]Local ani-cli not found. Falling back to system ani-cli...[/yellow]")
        ani_cli_path = "ani-cli"
        
    console.print("[cyan]🔄 Updating ani-cli backend...[/cyan]")
    try:
        subprocess.run([ani_cli_path, "-U"], check=True)
        console.print("[green]✅ Backend updated successfully![/green]")
    except subprocess.CalledProcessError:
        console.print("[red]❌ Failed to update backend. You may need to run this with sudo manually if using system ani-cli.[/red]")
    except FileNotFoundError:
        console.print("[red]❌ ani-cli not found.[/red]")
    input("\nPress Enter to return to menu...")

def browse_local_library():
    config = get_config()
    library_dirs = [os.path.expanduser(d) for d in config.get("library_dirs", [])]
    
    video_files = []
    valid_exts = {".mp4", ".mkv", ".avi", ".webm"}
    
    with console.status("[cyan]Scanning library directories...[/cyan]"):
        for d in library_dirs:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    for file in files:
                        if os.path.splitext(file)[1].lower() in valid_exts:
                            video_files.append(os.path.join(root, file))
                            
    if not video_files:
        console.print("[yellow]No video files found in your configured library directories.[/yellow]")
        console.print(f"Checked: {', '.join(library_dirs)}")
        input("\nPress Enter to return to menu...")
        return
        
    video_choices = []
    video_files.sort()
    for vf in video_files:
        display_name = os.path.basename(vf)
        for d in library_dirs:
            if vf.startswith(d):
                display_name = os.path.relpath(vf, d)
                break
        video_choices.append(questionary.Choice(display_name, vf))
        
    video_choices.append(questionary.Choice("❌ Cancel", "cancel"))
    
    selected_video = questionary.select(
        "Select a video to play:",
        choices=video_choices,
        use_indicator=True,
    ).ask()
    
    if not selected_video or selected_video == "cancel":
        return
        
    console.print(f"[cyan]▶️ Playing {os.path.basename(selected_video)}...[/cyan]")
    try:
        if subprocess.run(["which", "mpv"], capture_output=True).returncode == 0:
            subprocess.run(["mpv", selected_video])
        else:
            subprocess.run(["xdg-open", selected_video])
    except Exception as e:
        console.print(f"[red]Error playing video: {e}[/red]")
        input("\nPress Enter to return to menu...")

def handle_anime_action(anime_data):
    display_anime_info(anime_data)
    
    while True:
        action = questionary.select(
            f"What do you want to do with {anime_data['title']}?",
            choices=[
                questionary.Choice("▶️ Stream", "stream"),
                questionary.Choice("⬇️ Download", "download"),
                questionary.Choice("⭐ Add to Watchlist", "watchlist"),
                questionary.Choice("❌ Cancel", "cancel")
            ]
        ).ask()
        
        if not action or action == "cancel": return
        
        if action == "watchlist":
            save_watchlist(anime_data)
            input("\nPress Enter to continue...")
            break
            
        episodes = questionary.text("Enter episode number (or range like 1-12):").ask()
        if not episodes: continue
        
        sub_dub = questionary.select("Sub or Dub?", choices=["sub", "dub"]).ask()
        quality = questionary.select("Quality?", choices=["best", "1080p", "720p", "480p", "360p"], default="1080p").ask()
        
        run_ani_cli(anime_data['title'], episodes, quality, sub_dub, action)
        input("\nPress Enter to return to menu...")
        break

def main_menu():
    while True:
        console.clear()
        console.print(Panel.fit("[bold blue]🎌 bb-ani v2.0[/bold blue] - Anime Downloader & Streamer", border_style="blue"))
        
        choices = [
            questionary.Choice("🌟 Discover (Trending, Popular, New)", "discover"),
            questionary.Choice("🎭 Browse by Genre",                   "genre"),
            questionary.Choice("🔍 Search & Stream/Download",          "search"),
            questionary.Choice("📜 History & Continue Watching",       "history"),
            questionary.Choice("📖 View Watchlist",                    "watchlist"),
            questionary.Choice("📁 Local Library",                     "library"),
            questionary.Choice("🔄 Update ani-cli scraper",            "update"),
            questionary.Choice("❌ Exit",                              "exit")
        ]
        
        action = questionary.select(
            "What would you like to do?",
            choices=choices,
            style=questionary.Style([("highlighted", "fg:cyan bold")])
        ).ask()
        
        if not action or action == "exit":
            console.print("[blue]👋 Goodbye![/blue]")
            break
            
        if action == "genre":
            browse_by_genre()

        elif action == "discover":
            data = discover_anime()
            if not data:
                input("Press Enter to continue...")
                continue
                
            discover_type = questionary.select(
                "Which list would you like to view?",
                choices=[
                    questionary.Choice("🔥 Trending Anime", "trending"),
                    questionary.Choice("⭐ Popular Anime", "popular"),
                    questionary.Choice("🆕 New / Releasing Anime", "new"),
                    questionary.Choice("❌ Cancel", "cancel")
                ]
            ).ask()
            
            if not discover_type or discover_type == "cancel": continue
            
            parsed_results = data.get(discover_type, [])
            
            display_anime_table(f"Discover: {discover_type.title()} Anime", parsed_results)
            
            anime_choices = []
            for r in parsed_results:
                anime_choices.append(questionary.Choice(r['title'], r))
            anime_choices.append(questionary.Choice("❌ Cancel", "cancel"))
            
            selected_anime = questionary.select(
                "Select Anime:",
                choices=anime_choices
            ).ask()
            
            if not selected_anime or selected_anime == "cancel": continue
            handle_anime_action(selected_anime)
            
        elif action == "search":
            query = questionary.text("Enter anime name to search:").ask()
            if not query: continue
            
            results = search_anime(query)
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                input("Press Enter to continue...")
                continue
                
            display_anime_table(f"Search Results for '{query}'", results)
            
            anime_choices = []
            for r in results:
                anime_choices.append(questionary.Choice(r['title'], r))
            anime_choices.append(questionary.Choice("❌ Cancel", "cancel"))
            
            selected_anime = questionary.select(
                "Select Anime:",
                choices=anime_choices
            ).ask()
            
            if not selected_anime or selected_anime == "cancel": continue
            handle_anime_action(selected_anime)
            
        elif action == "history":
            history = load_history()
            if not history:
                console.print("[yellow]No history found.[/yellow]")
                input("Press Enter to continue...")
                continue
                
            hist_choices = []
            for e in history[:20]:
                icon = "▶️" if e.get("type") == "stream" else "⬇️"
                label = f"{icon} {e['title']} | Ep: {e['episodes']} | {e['sub_dub']} | {e['quality']} | {e['date']}"
                hist_choices.append(questionary.Choice(label, e))
            hist_choices.append(questionary.Choice("❌ Back to menu", "cancel"))
            
            selected_entry = questionary.select(
                "Select from history:",
                choices=hist_choices
            ).ask()
            
            if not selected_entry or selected_entry == "cancel": continue
            
            last_ep = selected_entry["episodes"]
            try:
                if "-" in str(last_ep):
                    next_ep = int(last_ep.split("-")[-1]) + 1
                else:
                    next_ep = int(last_ep) + 1
            except:
                next_ep = 1
                
            action_type = selected_entry.get("type", "stream")
            
            resume_action = questionary.select(
                f"What do you want to do with {selected_entry['title']}?",
                choices=[
                    questionary.Choice(f"⏭️ Continue to next episode (Ep {next_ep})", "next"),
                    questionary.Choice(f"🔄 Re-watch/download episode {last_ep}", "redo"),
                    questionary.Choice(f"✏️ Choose different episode", "custom"),
                    questionary.Choice("❌ Cancel", "cancel")
                ]
            ).ask()
            
            if not resume_action or resume_action == "cancel": continue
            
            if resume_action == "next":
                episodes = str(next_ep)
            elif resume_action == "redo":
                episodes = str(last_ep)
            else:
                episodes = questionary.text("Enter episode number (or range):").ask()
                
            if not episodes: continue
                
            run_ani_cli(selected_entry['title'], episodes, selected_entry['quality'], selected_entry['sub_dub'], action_type)
            input("\nPress Enter to return to menu...")
            
        elif action == "watchlist":
            watchlist = load_watchlist()
            if not watchlist:
                console.print("[yellow]Your Watchlist is empty.[/yellow]")
                input("Press Enter to continue...")
                continue
                
            wl_choices = []
            for w in watchlist:
                wl_choices.append(questionary.Choice(w['title'], w))
            wl_choices.append(questionary.Choice("❌ Back to menu", "cancel"))
            
            selected_anime = questionary.select(
                "Select from Watchlist:",
                choices=wl_choices
            ).ask()
            
            if not selected_anime or selected_anime == "cancel": continue
            handle_anime_action(selected_anime)
            
        elif action == "library":
            browse_local_library()
            
        elif action == "update":
            update_backend()

if __name__ == "__main__":
    main_menu()