from rich.console import Console

def show_help_menu():
    """Displays a clean, standard developer CLI help guide."""
    console = Console()
    
    # Title
    console.print("[bold cyan]ragchat[/bold cyan] - Universal Documentation & Workspace Chatbot\n")
    console.print("[bold white]USAGE:[/bold white]")
    console.print("  ragchat <command> [arguments]\n")
    
    console.print("[bold white]CORE COMMANDS:[/bold white]")
    console.print("  [bold green]-g <profile> <time>[/bold green]         Sync and list emails from a Google profile (zero LLM cost)")
    console.print("  [bold green]-m <profile> <time>[/bold green]         Sync and list emails from a Microsoft profile (zero LLM cost)")
    console.print("  [bold green]link <service> <profile>[/bold green]   Link a new account profile (google, microsoft, telegram, discord)")
    console.print("  [bold green]chat <collection>[/bold green]          Start interactive chat with an ingested collection")
    console.print("  [bold green]sync[/bold green]                        Run full sync daemon on connected channels")
    console.print("  [bold green]help[/bold green]                        Show this help usage menu\n")
    
    console.print("[bold white]TIME WINDOW FORMATS:[/bold white]")
    console.print("  Provide values like [cyan]10h[/cyan], [cyan]2d[/cyan], [cyan]1w[/cyan], [cyan]3m[/cyan], [cyan]1y[/cyan] where:")
    console.print("  [bold yellow]h[/bold yellow] : Hours    [bold yellow]d[/bold yellow] : Days    [bold yellow]w[/bold yellow] : Weeks    [bold yellow]m[/bold yellow] : Months (30 days)    [bold yellow]y[/bold yellow] : Years (365 days)\n")
    
    console.print("[bold white]EXAMPLES:[/bold white]")
    console.print("  ragchat -g dev 10h                # List dev Gmail emails from last 10 hours")
    console.print("  ragchat link google dev           # Authenticate and link a new Google account named 'dev'")
    console.print("  ragchat link telegram personal    # Connect a Telegram account named 'personal'")
    console.print("  ragchat chat work_docs            # Start chatting with the work_docs collection")
    console.print("  ragchat                           # Launch the interactive text menu\n")

def handle_cli_commands():
    """Handles structured non-interactive CLI commands by routing them to core.cli_handlers."""
    import sys
    from core.cli_handlers import (
        handle_rename_profile_cli,
        handle_sync_cli,
        handle_link_cli,
        handle_drive_cli,
        handle_onedrive_cli,
        handle_sheet_cli,
        handle_gmail_cli,
        handle_outlook_cli,
        handle_telegram_cli,
        handle_discord_cli
    )
    
    args = sys.argv[1:]
    if not args:
        return False
        
    cmd = args[0]
    
    if cmd in ['-h', '--help', 'help']:
        show_help_menu()
        sys.exit(0)

    # Command mapping dictionary
    commands = {
        'rename-profile': handle_rename_profile_cli,
        'sync': handle_sync_cli,
        'link': handle_link_cli,
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
