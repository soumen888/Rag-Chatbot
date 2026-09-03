import os
import sys
import subprocess
import threading
import urllib.request
import json
import atexit
from rich.console import Console

import time

CURRENT_VERSION = "1.1.6"
LATEST_VERSION_FOUND = None

def fetch_latest_release_worker():
    global LATEST_VERSION_FOUND
    config_dir = os.path.expanduser("~/.config/ragchat")
    state_file = os.path.join(config_dir, "update_state.json")
    os.makedirs(config_dir, exist_ok=True)

    now = time.time()
    last_check = 0.0
    cached_version = None

    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
                last_check = state.get("last_check", 0.0)
                cached_version = state.get("latest_version")
        except Exception:
            pass

    # If checked less than 24 hours (86400 seconds) ago, use cached value
    if now - last_check < 86400.0 and cached_version is not None:
        LATEST_VERSION_FOUND = cached_version
        return

    try:
        url = "https://api.github.com/repos/soumen888/Rag-Chatbot/releases/latest"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "RAGChat-Client"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            tag_name = data.get("tag_name", "").strip().lstrip("v")
            if tag_name:
                LATEST_VERSION_FOUND = tag_name
                # Cache the successful result
                with open(state_file, "w") as f:
                    json.dump({"last_check": now, "latest_version": tag_name}, f)
    except Exception:
        # If API check failed, fall back to cached version if present to prevent errors
        if cached_version:
            LATEST_VERSION_FOUND = cached_version

def print_update_notification():
    if LATEST_VERSION_FOUND:
        # Check if the latest version is greater than current version
        try:
            curr_parts = [int(x) for x in CURRENT_VERSION.split(".")]
            latest_parts = [int(x) for x in LATEST_VERSION_FOUND.split(".")]
            if latest_parts > curr_parts:
                console = Console()
                console.print("\n[bold cyan]========================================================================[/bold cyan]")
                console.print(f"[bold green][*] A new RAGChat version is available: v{LATEST_VERSION_FOUND} (Installed: v{CURRENT_VERSION})[/bold green]")
                console.print("[bold yellow][*] Run `ragchat update` or view release notes at:[/bold yellow]")
                console.print("    [cyan]https://github.com/soumen888/Rag-Chatbot/releases[/cyan]")
                console.print("    [cyan]https://ragchat-auth.vercel.app[/cyan]")
                console.print("[bold cyan]========================================================================[/bold cyan]\n")
        except Exception:
            pass

# Register termination update check alert
atexit.register(print_update_notification)

# Start background check thread immediately when cli.py is loaded
check_thread = threading.Thread(target=fetch_latest_release_worker, daemon=True)
check_thread.start()

def handle_update():
    """Handles auto-updating RAGChat across macOS, Linux, and Windows."""
    console = Console()
    console.print("[bold cyan][*] Checking for RAGChat updates...[/bold cyan]")

    # Standard curl / git installation update

    install_dir = os.path.expanduser("~/.ragchat")
    if os.path.exists(os.path.join(install_dir, ".git")):
        try:
            console.print("[*] Pulling latest code changes from GitHub...")
            subprocess.run(["git", "-C", install_dir, "pull", "--quiet"], check=True)
            
            venv_pip = os.path.join(install_dir, "venv", "bin", "pip")
            if not os.path.exists(venv_pip):
                venv_pip = os.path.join(install_dir, "venv", "Scripts", "pip.exe")

            if os.path.exists(venv_pip):
                console.print("[*] Updating dependencies & core binaries...")
                subprocess.run([venv_pip, "install", "-r", os.path.join(install_dir, "requirements.txt"), "--quiet"], check=False)
                
                # Parse the updated WHEEL_URL from macos.sh so pip can locate the binary
                wheel_url = None
                macos_sh_path = os.path.join(install_dir, "install", "macos.sh")
                if os.path.exists(macos_sh_path):
                    try:
                        with open(macos_sh_path, "r") as f:
                            for line in f:
                                if line.strip().startswith("WHEEL_URL="):
                                    wheel_url = line.split("WHEEL_URL=")[1].strip().strip('"').strip("'")
                                    break
                    except Exception:
                        pass
                
                if wheel_url:
                    subprocess.run([venv_pip, "install", "--upgrade", wheel_url, "--quiet"], check=False)
                else:
                    subprocess.run([venv_pip, "install", "--upgrade", "ragchat_core", "--quiet"], check=False)

            console.print("\n[bold green][+] RAGChat updated successfully to the latest version![/bold green]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red][!] Update failed: {e}[/bold red]")
            console.print("Run the installer script to perform a fresh update:")
            console.print("  [cyan]curl -fsSL https://raw.githubusercontent.com/soumen888/Rag-Chatbot/main/install/macos.sh | bash[/cyan]")
            sys.exit(1)
    else:
        console.print("[bold yellow][!] Standalone git directory not found.[/bold yellow]")
        console.print("To update, run the installer:")
        console.print("  [cyan]curl -fsSL https://raw.githubusercontent.com/soumen888/Rag-Chatbot/main/install/macos.sh | bash[/cyan]")
        sys.exit(0)

def show_help_menu():
    """Displays a clean, standard developer CLI help guide."""
    console = Console()
    
    console.print("[bold cyan]ragchat[/bold cyan] - Universal Documentation & Workspace Chatbot\n")
    console.print("[bold]USAGE:[/bold]")
    console.print("  ragchat <command> [arguments]\n")
    
    console.print("[bold]CORE COMMANDS:[/bold]")
    console.print("  [bold green]-g <profile> <time>[/bold green]         Sync and list emails from a Google profile (zero LLM cost)")
    console.print("  [bold green]-m <profile> <time>[/bold green]         Sync and list emails from a Microsoft profile (zero LLM cost)")
    console.print("  [bold green]bind [google] [file][/bold green]      Bind custom Google OAuth Client JSON credentials")
    console.print("  [bold green]link <service> <profile>[/bold green]   Link a new account profile (google, microsoft, telegram, discord)")
    console.print("  [bold green]chat <collection>[/bold green]          Start interactive chat with an ingested collection")
    console.print("  [bold green]pageindex <action>[/bold green]          PageIndex RAG on long PDFs (actions: index, chat, list)")
    console.print("  [bold green]sync[/bold green]                        Run full sync daemon on connected channels")
    console.print("  [bold green]update[/bold green]                      Update RAGChat to the latest version")
    console.print("  [bold green]help[/bold green]                        Show this help usage menu\n")
    
    console.print("[bold]TIME WINDOW FORMATS:[/bold]")
    console.print("  Provide values like [cyan]10h[/cyan], [cyan]2d[/cyan], [cyan]1w[/cyan], [cyan]3m[/cyan], [cyan]1y[/cyan] where:")
    console.print("  [bold yellow]h[/bold yellow] : Hours    [bold yellow]d[/bold yellow] : Days    [bold yellow]w[/bold yellow] : Weeks    [bold yellow]m[/bold yellow] : Months (30 days)    [bold yellow]y[/bold yellow] : Years (365 days)\n")
    
    console.print("[bold]EXAMPLES:[/bold]")
    console.print("  ragchat bind google ~/Downloads/client_secret.json # Bind custom Google OAuth JSON")
    console.print("  ragchat -g dev 10h                # List dev Gmail emails from last 10 hours")
    console.print("  ragchat link google dev           # Authenticate and link a new Google account named 'dev'")
    console.print("  ragchat update                    # Update RAGChat to the latest release")
    console.print("  ragchat                           # Launch the interactive text menu\n")

def handle_cli_commands():
    """Handles structured non-interactive CLI commands by routing them to core.cli_handlers."""
    args = sys.argv[1:]
    if not args:
        return False
        
    cmd = args[0]
    
    if cmd in ['-h', '--help', 'help']:
        show_help_menu()
        sys.exit(0)

    if cmd in ['update', '--update']:
        handle_update()

    try:
        from core.cli_handlers import (
            handle_rename_profile_cli,
            handle_list_profiles_cli,
            handle_sync_cli,
            handle_link_cli,
            handle_bind_cli,
            handle_drive_cli,
            handle_onedrive_cli,
            handle_sheet_cli,
            handle_gmail_cli,
            handle_outlook_cli,
            handle_telegram_cli,
            handle_discord_cli,
            handle_pageindex_cli
        )
    except ImportError:
        from ragchat_core.core.cli_handlers import (
            handle_rename_profile_cli,
            handle_list_profiles_cli,
            handle_sync_cli,
            handle_link_cli,
            handle_bind_cli,
            handle_drive_cli,
            handle_onedrive_cli,
            handle_sheet_cli,
            handle_gmail_cli,
            handle_outlook_cli,
            handle_telegram_cli,
            handle_discord_cli,
            handle_pageindex_cli
        )

    commands = {
        'rename-profile': handle_rename_profile_cli,
        'profiles': handle_list_profiles_cli,
        'sync': handle_sync_cli,
        'link': handle_link_cli,
        'bind': handle_bind_cli,
        'drive': handle_drive_cli,
        'onedrive': handle_onedrive_cli,
        'sheet': handle_sheet_cli,
        '-g': handle_gmail_cli,
        '-m': handle_outlook_cli,
        'telegram': handle_telegram_cli,
        'discord': handle_discord_cli,
        'pageindex': handle_pageindex_cli
    }

    if cmd in commands:
        commands[cmd](args)
        sys.exit(0)

    # If there are CLI arguments but none of them matched, it's an invalid command
    console = Console()
    console.print(f"[bold red][!] Unrecognized command: '{cmd}'[/bold red]")
    console.print("[yellow]Type [cyan]ragchat --help[/cyan] to get the list of commands.[/yellow]\n")
    sys.exit(1)
