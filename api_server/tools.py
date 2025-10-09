import subprocess
import os
import shutil
import shlex # Used for safe command construction
from functools import lru_cache
import hashlib
from pathlib import Path
# import yt_dlp # Use the yt-dlp library directly for robust searching
from langchain.agents import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
import asyncio 

from config import MPV_PATH # Only mpv path is needed now
import requests

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Dict, Callable

# Cache configuration - add this at the top of your tools.py
CACHE_DIR = Path.home() / ".cache" / "cluj-ai" / "search"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DURATION = timedelta(hours=1)
debug = True  # Make sure debug is defined

def normalize_query(query: str) -> str:
    """Normalize query for better cache matching."""
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)
    return query

def get_cache_key(query: str) -> str:
    """Generate a cache key from normalized query."""
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode()).hexdigest()

def get_cache_file(query: str) -> Path:
    """Get the cache file path for a query."""
    cache_key = get_cache_key(query)
    return CACHE_DIR / f"{cache_key}.json"

def get_cached_result(query: str) -> str | None:
    """Get cached result if available and valid."""
    cache_file = get_cache_file(query)
    if cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text())
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time < CACHE_DURATION:
                if debug:
                    print(f"🔍 Cache HIT for: '{query}'")
                return cache_data['result']
        except Exception as e:
            if debug:
                print(f"🔍 Cache read error: {e}")
    return None

# Pre-defined tool routing - bypasses agent decision making
TOOL_ROUTING_RULES = {
    # Search patterns
    r'(who|what|when|where|why|how).*\?': 'search_tool',
    r'(news|current|latest|recent|update|happened)': 'search_tool',
    r'(president|prime minister|ceo|leader)': 'search_tool',
    r'(capital|population|weather|temperature)': 'search_tool',
    r'search for|look up|find.*about': 'search_tool',
    
    # Weather patterns
    r'weather|temperature|forecast|raining|snowing': 'weather_tool',
    
    # Joke patterns  
    r'joke|funny|humor|dad joke': 'dad_joke_tool',
    
    # Command patterns
    r'run |execute |command |terminal |shell ': 'terminal_tool',
}

def route_to_tool_directly(query: str) -> str | None:
    """Fast tool routing without agent decision making."""
    query_lower = query.lower().strip()
    
    for pattern, tool_name in TOOL_ROUTING_RULES.items():
        if re.search(pattern, query_lower):
            return tool_name
    
    return None

# @tool
# def search_tool(query: str) -> str:
#     """Search the web with caching. FAST VERSION."""
#     # Ultra-fast cache check
#     cache_file = get_cache_file(query)
#     if cache_file.exists():
#         try:
#             cache_data = json.loads(cache_file.read_text())
#             cached_time = datetime.fromisoformat(cache_data['timestamp'])
#             if datetime.now() - cached_time < CACHE_DURATION:
#                 return cache_data['result']
#         except:
#             pass  # If cache read fails, continue to normal search
    
#     # If we get here, do the actual search
#     try:
#         # Try multiple SearXNG instances
#         instances = [
#             "https://search.rhscz.eu/search",
#             "https://priv.au/search", 
#             "https://searx.perennialte.ch/search"
#         ]
        
#         for instance in instances:
#             try:
#                 response = requests.get(
#                     instance,
#                     params={'q': query, 'format': 'json', 'language': 'en'},


@tool
def search_tool(query: str) -> str:
    """Search the web with caching. FAST VERSION."""
    # Ultra-fast cache check
    cache_file = get_cache_file(query)
    if cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text())
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time < CACHE_DURATION:
                return cache_data['result']
        except:
            pass  # If cache read fails, continue to normal search
    
    # If we get here, do the actual search
    try:
        # Use Startpage (more reliable than SearXNG instances)
        response = requests.get(
            "https://www.startpage.com/sp/search",
            params={
                'query': query,
                'language': 'english',
                'lui': 'english'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            },
            timeout=10
        )
        
        # Parse the HTML response from Startpage
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract search results
        results = []
        
        # Startpage result selectors (may need adjustment)
        result_blocks = soup.select('.w-gl__result, .result, .search-result')
        
        for block in result_blocks[:5]:  # Get top 5 results
            title_elem = block.select_one('h3, .title, .result-title')
            url_elem = block.select_one('a, .result-url')
            desc_elem = block.select_one('.desc, .result-description, .snippet')
            
            title = title_elem.get_text().strip() if title_elem else "No Title"
            url = url_elem.get('href', '') if url_elem else "No URL"
            description = desc_elem.get_text().strip() if desc_elem else "No description"
            
            if title != "No Title":  # Only add valid results
                results.append({
                    'title': title,
                    'url': url,
                    'description': description[:150]  # Limit description length
                })
        
        if not results:
            result_text = "No results found."
        else:
            output = ["--- SEARCH RESULTS ---"]
            for i, result in enumerate(results):
                output.append(f"{i+1}. {result['title']}\n   URL: {result['url']}\n   Description: {result['description']}")
            result_text = "\n".join(output) + "\n--- END ---"
        
        # Cache the result
        save_to_cache_fast(query, result_text)
        return result_text
        
    except Exception as e:
        error_text = f"Search error: {e}"
        # Still cache errors to avoid retrying too frequently
        save_to_cache_fast(query, error_text)
        return error_text
    
def save_to_cache_fast(query: str, result: str):
    """Fast cache saving without pretty printing."""
    cache_file = get_cache_file(query)
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'result': result
    }
    cache_file.write_text(json.dumps(cache_data))  # No indent for speed


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
    """Get weather information using wttr.in."""
    if (debug):
        print(f"🌤️ DEBUG: Weather tool called with location: '{location}'")
    
    try:
        location = location.strip()
        if not location:
            return "Error: No location provided."
            
        if (debug):
            print(f"🌤️ DEBUG: Making weather request for: {location}")
        
        # Use requests instead of curl
        url = f"http://wttr.in/{location}"
        params = {
            'format': '%l: %c %t %w %h',  # Location: Condition Temperature Wind Humidity
        }
        
        if (debug):
            print(f"🌤️ DEBUG: Request URL: {url}")
        
        response = requests.get(url, params=params, timeout=10)
        if (debug):
            print(f"🌤️ DEBUG: Response status: {response.status_code}")
        
        if response.status_code == 200:
            weather_data = response.text.strip()
            if (debug):
                print(f"🌤️ DEBUG: Raw weather data: '{weather_data}'")
            
            if weather_data and "unknown location" not in weather_data.lower():
                return weather_data
            else:
                return f"Could not find weather for: {location}"
        else:
            return f"Weather service error: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        if (debug):
            print("🌤️ DEBUG: Weather request timed out")
        return "Error: Weather service timed out."
    except requests.exceptions.ConnectionError:
        if (debug):
            print("🌤️ DEBUG: Cannot connect to weather service")
        return "Error: Cannot connect to weather service. Check network connectivity."
    except Exception as e:
        if (debug):
            print(f"🌤️ DEBUG: Weather tool exception: {e}")
        return f"Error fetching weather: {e}"

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
    terminal_tool,
    weather_tool,
    dad_joke_tool,
]


