#!/usr/bin/env python3

import subprocess
import sys
import os
import json
from datetime import datetime

HISTORY_FILE = os.path.expanduser("~/.bb-dl/history.json")

def check_dependencies():
    print("🔍 Checking dependencies...")
    try:
        import requests
    except ImportError:
        print("📦 Installing requests...")
        subprocess.run(["pip", "install", "requests", "--break-system-packages"], check=True)
    result = subprocess.run(["which", "ani-cli"], capture_output=True)
    if result.returncode != 0:
        print("📦 Installing ani-cli...")
        subprocess.run(["yay", "-S", "ani-cli", "--noconfirm"], check=True)
    print("✅ All dependencies ready!\n")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(title, episodes, quality, sub_dub, type="download"):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = load_history()
    for entry in history:
        if entry["title"] == title:
            entry["episodes"] = episodes
            entry["quality"] = quality
            entry["sub_dub"] = sub_dub
            entry["type"] = type
            entry["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    else:
        history.append({
            "title": title,
            "episodes": episodes,
            "quality": quality,
            "sub_dub": sub_dub,
            "type": type,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def show_history():
    history = load_history()
    if not history:
        print("📭 No history yet.\n")
        return
    print("📜 History:\n")
    for i, entry in enumerate(history, 1):
        icon = "▶️" if entry.get("type") == "stream" else "⬇️"
        print(f"{i}. {icon} {entry['title']} | Episodes: {entry['episodes']} | {entry['sub_dub'].upper()} | {entry['quality']} | {entry['date']}")
    print()

def search_anime(query):
    import requests
    print(f"\n🔍 Searching for: {query}")
    
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
            timeout=10
        )
        data = response.json()
        media = data["data"]["Page"]["media"]
        
        if media:
            results = []
            for anime in media:
                title = anime["title"]["english"] or anime["title"]["romaji"]
                episodes = anime.get("episodes", "?")
                year = anime.get("seasonYear", "?")
                results.append({"title": title, "episodes": episodes, "year": year})
            return results
    except Exception:
        print("⚠️ AniList failed, trying backup...")
    
    # Fall back to Jikan
    try:
        response = requests.get(
            f"https://api.jikan.moe/v4/anime?q={query}&limit=10",
            timeout=10
        )
        data = response.json()
        if "data" not in data:
            print("❌ Both search sources failed. Please try again.")
            return []
        results = []
        for anime in data["data"]:
            title = anime["titles"][0]["title"]
            episodes = anime.get("episodes", "?")
            year = anime.get("year", "?")
            results.append({"title": title, "episodes": episodes, "year": year})
        return results
    except Exception:
        print("❌ Both search sources failed. Please try again.")
        return []

def pick_anime(results):
    print(f"\n📋 Search results:\n")
    for i, anime in enumerate(results, 1):
        print(f"{i}. {anime['title']} | Episodes: {anime['episodes']} | Year: {anime['year']}")
    try:
        choice = int(input("\nEnter number of your choice (0 to cancel): "))
        if choice == 0:
            return None
        return results[choice - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return None

def get_download_folder(anime_title):
    folder = os.path.expanduser(f"~/Videos/{anime_title}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Created folder: {folder}")
    else:
        print(f"✅ Saving to: {folder}")
    return folder

def main():
    print("🎌 Welcome to bb-dl!")
    print("====================\n")

    check_dependencies()
    show_history()

    print("What do you want to do?")
    print("1. Download new anime")
    print("2. Stream anime")
    print("3. Continue from history")
    print("4. Exit")

    action = input("\nEnter choice (1/2/3/4): ").strip()

    if action == "4":
        print("👋 Goodbye!")
        return

    elif action == "1":
        query = input("\nEnter anime name: ").strip()
        results = search_anime(query)
        if not results:
            print("❌ No results found.")
            return
        selected = pick_anime(results)
        if not selected:
            return
        sub_dub = input("Sub or Dub? (sub/dub): ").strip().lower()
        episodes = input("Episode or range (e.g. 1 or 1-12): ").strip()
        quality = input("Quality? (360p/480p/720p/1080p) [default 720p]: ").strip().lower()
        if not quality:
            quality = "720p"
        download_folder = get_download_folder(selected['title'])
        command = ["ani-cli", "-d", selected['title'], "-e", episodes, "-q", quality]
        if sub_dub == "dub":
            command.append("--dub")
        print(f"\n⬇️ Starting download...")
        os.chdir(download_folder)
        subprocess.run(command)
        save_history(selected['title'], episodes, quality, sub_dub, "download")
        print(f"\n✅ Saved to history!")

    elif action == "2":
        query = input("\nEnter anime name: ").strip()
        results = search_anime(query)
        if not results:
            print("❌ No results found.")
            return
        selected = pick_anime(results)
        if not selected:
            return
        sub_dub = input("Sub or Dub? (sub/dub): ").strip().lower()
        episode = input("Episode number: ").strip()
        quality = input("Quality? (360p/480p/720p/1080p) [default 720p]: ").strip().lower()
        if not quality:
            quality = "720p"
        command = ["ani-cli", selected['title'], "-e", episode, "-q", quality]
        if sub_dub == "dub":
            command.append("--dub")
        print(f"\n▶️ Streaming {selected['title']} episode {episode}...")
        subprocess.run(command)
        pass

    elif action == "3":
        history = load_history()
        if not history:
            print("❌ No history yet. Download something first!")
            return
        pick = int(input("Enter number from history to continue: ").strip())
        entry = history[pick - 1]
        last_ep = entry["episodes"]
        try:
            if "-" in str(last_ep):
                next_ep = int(last_ep.split("-")[-1]) + 1
            else:
                next_ep = int(last_ep) + 1
        except (ValueError, TypeError):
            next_ep = 1
            print("⚠️ Could not determine last episode, starting from 1")
            
        sub_dub = entry["sub_dub"]
        quality = entry["quality"]

        print(f"\n1. Continue from next episode (episode {next_ep})")
        print(f"2. Redownload last episode (episode {last_ep})")
        
        resume_choice = input("\nEnter choice (1/2): ").strip()
        
        if resume_choice == "2":
            episodes = str(last_ep)
            print(f"\n✅ Redownloading: {entry['title']} episode {last_ep}")
        else:
            print(f"\n✅ Continuing: {entry['title']} from episode {next_ep}")
            episodes = input(f"Episode or range (e.g. {next_ep} or {next_ep}-{next_ep+11}): ").strip()
        download_folder = get_download_folder(entry["title"])
        command = ["ani-cli", "-d", entry["title"], "-e", episodes, "-q", quality]
        if sub_dub == "dub":
            command.append("--dub")
        print(f"\n⬇️ Starting download...")
        os.chdir(download_folder)
        subprocess.run(command)
        save_history(entry["title"], episodes, quality, sub_dub, "download")
        print(f"\n✅ History updated!")

if __name__ == "__main__":
    main()
