import subprocess
import os
import shutil
import shlex # Used for safe command construction
from functools import lru_cache
import hashlib
from pathlib import Path

import yt_dlp # Use the yt-dlp library directly for robust searching
from langchain.agents import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
import asyncio 

from config import MPV_PATH # Only mpv path is needed now
import requests

# --- Tools (as LangChain tools) ---
# These are now properly defined, with correct signatures

# @tool
# def search_tool(query: str) -> str:
#     """Search the web with Google Serper."""
#     print(f"🔍 Web search: {query}")
#     try:
#         from langchain_community.utilities import GoogleSerperAPIWrapper
#         wrapper = GoogleSerperAPIWrapper()
#         result = wrapper.run(query)
#         if not result:
#             return "No results found."
#         return f"--- SEARCH RESULTS ---\n{result}\n--- END ---"
#     except Exception as e:
#         return f"Error during search: {e}"

@tool
def search_tool(query: str) -> str:
    """Search the web with a local SearXNG instance."""
    print(f"🔍 Local search: {query}")
    try:
        # Define the URL for your local SearXNG instance's search endpoint
        searxng_url = "http://localhost:3000/search"

        # Set the parameters for the search query
        params = {
            'q': query,
            'format': 'json',  # We need the JSON format
            'language': 'en'
        }

        # Make the HTTP GET request
        response = requests.get(searxng_url, params=params, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()
        results = data.get("results", [])

        if not results:
            return "No results found."

        # Format the top 5 results into a clean string
        output = ["--- SEARCH RESULTS ---"]
        for i, result in enumerate(results[:5]): # Get the top 5 results
            title = result.get('title', 'No Title')
            url = result.get('url', '#')
            content = result.get('content', 'No content available.').replace('\n', ' ')
            output.append(f"{i+1}. {title}\n   URL: {url}\n   Snippet: {content}")

        return "\n".join(output) + "\n--- END ---"

    except requests.exceptions.RequestException as e:
        return f"Error connecting to SearXNG instance: {e}"
    except Exception as e:
        return f"An unexpected error occurred during search: {e}"


# Create a cache directory for downloaded videos
CACHE_DIR = Path.home() / ".cache" / "cluj-ai" / "youtube"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

@tool
def youtube_search_tool(query: str) -> str:
    """Search YouTube for a video, download it, and play from local cache."""
    print(f"🎬 YouTube search and download: '{query}'")
    
    try:
        # Generate a cache key from the query
        cache_key = hashlib.md5(query.lower().encode()).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}.mp4"
        
        # Check if we already have this video cached
        if cache_file.exists():
            print(f"📦 Found cached video: {cache_file}")
            # Play the cached video
            subprocess.Popen(
                [MPV_PATH, str(cache_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"Playing cached video for: {query}"
        
        # If not cached, search and download
        ydl_opts = {
            'format': 'best[height<=720]',  # Limit to 720p for reasonable file sizes
            'outtmpl': str(cache_file).replace('.mp4', '.%(ext)s'),
            'noplaylist': True,
            'default_search': 'ytsearch',
            'quiet': False,
        }
        
        print(f"⬇️ Downloading video for: {query}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            
            if info.get('entries'):
                # Get the first search result
                video_info = info['entries'][0]
                title = video_info.get('title', 'Unknown title')
                url = video_info.get('webpage_url', 'Unknown URL')
                
                # Find the actual downloaded file
                downloaded_files = list(CACHE_DIR.glob(f"{cache_key}.*"))
                if downloaded_files:
                    actual_file = downloaded_files[0]
                    # Rename to .mp4 for consistency
                    if actual_file.suffix != '.mp4':
                        mp4_file = actual_file.with_suffix('.mp4')
                        actual_file.rename(mp4_file)
                        actual_file = mp4_file
                    
                    print(f"🎬 Playing downloaded video: {title}")
                    subprocess.Popen(
                        [MPV_PATH, str(actual_file)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return f"Downloaded and playing: {title}"
                else:
                    return "❌ Video downloaded but file not found in cache"
            else:
                return "❌ No video found for the search query"
                
    except Exception as e:
        return f"❌ Error in YouTube download: {e}"


@tool
def terminal_tool(command: str) -> str:
    """Execute shell command. Safe input and confirmation required."""
    cleaned_command = command.strip()
    parts = cleaned_command.split()
    if parts and parts[0] == "mpv":
        cmd = f"{MPV_PATH} {' '.join(parts[1:])}"
    else:
        cmd = cleaned_command

    print(f"\033[93mProposed command: `\033[1m{cmd}\033[0m\033[93m`\033[0m")
    confirmation = input("Execute? [y/N]: ").strip().lower()
    if confirmation not in ['y', 'yes']:
        return "Command cancelled by user."

    if not shutil.which(parts[0] if parts else ""):
        return f"Error: Command '{parts[0]}' not found in PATH."

    try:
        if parts[0] in ['mpv', 'xdg-open']:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Started '{parts[0]}' in background."
        else:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return f"✅ Output:\n{result.stdout}\n❌ Errors:\n{result.stderr}"
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def weather_tool(location: str) -> str:
    """Get weather information."""
    cmd = f"curl -s --max-time 5 'wttr.in/{shlex.quote(location)}?format=3'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


@tool
def dad_joke_tool(query: str = "") -> str:
    """Get a random dad joke."""
    print("😄 Fetching dad joke...")
    try:
        import random
        random_param = random.randint(1, 100000)
        cmd = f'curl -s -H "Accept: text/plain" -H "User-Agent: Cluj-AI Assistant" "https://icanhazdadjoke.com/?_{random_param}"'
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True, timeout=10
        )
        joke_text = result.stdout.strip()
        if not joke_text:
            return "Could not fetch a joke at this time."
        # Return ONLY the joke - no formatting
        return joke_text
    except Exception as e:
        return f"Error fetching joke: {e}"


@tool
def ascii_art_tool(art_name: str) -> str:
    """Fetch ASCII art from reliable sources."""
    art_name = art_name.strip().lower()
    
    # Use asciiart.club which is more reliable
    cmd = f"curl -s --max-time 10 'https://asciiart.club/api/search?q={shlex.quote(art_name)}'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        
        if output and len(output) > 10:
            return output
        else:
            # Fallback to static ASCII art
            return get_static_ascii_art(art_name)
            
    except Exception:
        return get_static_ascii_art(art_name)


# --- All available tools for the agent ---
ALL_TOOLS = [
    search_tool,
    youtube_search_tool,
    terminal_tool,
    weather_tool,
    dad_joke_tool,
]


