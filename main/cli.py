import os
import sys
import subprocess
from rich.console import Console

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
            handle_discord_cli
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
            handle_discord_cli
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
        'discord': handle_discord_cli
    }

    if cmd in commands:
        commands[cmd](args)
        sys.exit(0)

    return False
