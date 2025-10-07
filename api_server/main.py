# main.py (with enhanced coloring)
import os
import subprocess
import shlex
import shutil
from functools import lru_cache
from typing import Generator, List, AsyncGenerator
import sys
import asyncio
import random

# --- Standard Library Replacements for Typer ---

# Expanded color palette for a cleaner interface
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "end": "\033[0m",
}

def cprint(text: str, color: str = ""):
    """Prints text in a specified color."""
    if color in COLORS:
        print(f"{COLORS[color]}{text}{COLORS['end']}")
    else:
        print(text)

# --- Original Application Logic ---
from dotenv import load_dotenv
load_dotenv()

from config import MODEL_NAME, MPV_PATH, YT_DLP_PATH
from agent import create_agent_executor
from tools import ALL_TOOLS

# Global agent executor (cached)
agent_executor = create_agent_executor()

# --- Fast-path: Play music / video via YouTube (Unchanged) ---
def fast_play_music(full_query: str) -> None:
    """Handles 'play [song]' or 'listen to [music]' queries."""
    print(f"⚡ Fast-path detected! Searching and playing: {full_query}")
    try:
        # Assuming youtube_search_tool is imported and works as intended
        from tools import youtube_search_tool
        result = youtube_search_tool.run(full_query)
        if "Found YouTube URL:" in result:
            url = result.split("Found YouTube URL:")[1].strip()
            print(f"Found URL: {url}. Proposing playback...")
            confirmation = input("Do you want to play this video? [y/N]: ").strip().lower()
            if confirmation in ['y', 'yes']:
                command = f"{MPV_PATH} '{url}'"
                print(f"Playing: {command}")
                subprocess.Popen(command, shell=True)
                cprint("\n✅ Playback started.", color="green")
            else:
                cprint("Playback cancelled.", color="yellow")
        else:
            cprint(f"❌ Could not find a YouTube video for '{full_query}'.", color="red")
    except Exception as e:
        cprint(f"❌ Error during playback: {e}", color="red")



# main.py (updated function)

async def process_prompt_with_events(full_prompt: str) -> None:
    """
    Handles routing and executes the agent using astream_events() 
    for real-time streaming with a clean, colored interface.
    """
    print(f"🤖 DEBUG: Processing prompt: '{full_prompt}'")
    
    play_keywords = ["play", "listen", "song", "music", "video", "watch"]
    if any(kw.lower() in full_prompt.lower() for kw in play_keywords):
        print("🎵 DEBUG: Detected music/video query, using fast path")
        fast_play_music(full_prompt)
        return

    try:
        final_answer = ""
        cprint("\n🤖 AI Response:", color="cyan")
        
        iteration_count = 0
        async for event in agent_executor.astream_events(
            {"input": full_prompt},
            version="v1",
        ):
            iteration_count += 1
            kind = event["event"]
            
            print(f"🔄 DEBUG: Event {iteration_count} - {kind}")
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    sys.stdout.write(content)
                    sys.stdout.flush()
                    final_answer += content
            
            elif kind == "on_tool_start":
                tool_name = event['name']
                tool_input = event['data'].get('input', '')
                print(f"🛠️ DEBUG: Tool START - {tool_name} with input: {tool_input}")
                
                sys.stdout.flush() 
                if tool_name != 'dad_joke_tool':
                    cprint(f"\n\n🛠️ Calling Tool: {tool_name}", color="yellow")
            
            elif kind == "on_tool_end":
                tool_name = event['name']
                output = event['data'].get('output', '')
                print(f"🛠️ DEBUG: Tool END - {tool_name} with output length: {len(output)}")
                
                if tool_name != 'dad_joke_tool':
                    if output and len(output) < 200:
                        cprint(f"🔍 Tool Result: {output}", color="magenta")
                    else:
                        cprint(f"🔍 Tool Result: [Output too long to display]", color="magenta")

            elif kind == "on_chain_end":
                chain_name = event["name"]
                print(f"⛓️ DEBUG: Chain END - {chain_name}")
                if chain_name == "AgentExecutor":
                    if not final_answer:
                        final_answer = event['data'].get('output')['output']
                        sys.stdout.write(final_answer)
                        sys.stdout.flush()
                        print(f"📝 DEBUG: Final answer set from chain end: {len(final_answer)} chars")

            elif kind == "on_chain_start":
                chain_name = event["name"]
                print(f"⛓️ DEBUG: Chain START - {chain_name}")

        print(f"✅ DEBUG: Processing complete. Total events: {iteration_count}")

    except Exception as e:
        cprint(f"\n❌ An error occurred: {e}", color="red")
        import traceback
        traceback.print_exc()

async def run_command(prompt_list: List[str]) -> None:
    """Handles the 'run' command logic."""
    if not prompt_list:
        cprint("Error: The 'run' command requires a prompt.", color="red")
        return
    full_prompt = " ".join(prompt_list)
    await process_prompt_with_events(full_prompt)

async def chat_command() -> None:
    """Handles the 'chat' command logic (REPL)."""
    cprint("Entering chat mode. Type 'exit' or 'quit' to end.", color="yellow")
    while True:
        prompt_text = f"\n\n{COLORS['green']}> {COLORS['end']}"
        try:
            prompt = input(prompt_text)
            if prompt.lower() in ["exit", "quit"]:
                cprint("Exiting chat.", color="yellow")
                break
            final_prompt = prompt
            joke_keywords = ["dad joke", "new joke", "another joke", "joke"]
            await process_prompt_with_events(prompt)
        except (KeyboardInterrupt, EOFError):
            cprint("\nExiting chat.", color="yellow")
            break


async def main():
    """Main async function to parse args and dispatch commands."""
    args = sys.argv[1:]
    if not args:
        print("Cluj-AI: A local-first, AI-powered terminal assistant.")
        print("\nUsage:")
        print("  python main.py run <prompt...>")
        print("  python main.py chat")
        return

    command = args[0]
    if command == "run":
        await run_command(args[1:])
    elif command == "chat":
        await chat_command()
    else:
        cprint(f"Error: Unknown command '{command}'", color="red")

# === MAIN ENTRY POINT ===
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This is handled in chat_command, but is a good failsafe
        print("\nExiting.")
