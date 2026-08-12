import os
import sys
import psutil
from rich.console import Console

def get_dir_size(path):
    total = 0
    try:
        if os.path.exists(path):
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
    except Exception:
        pass
    return total

def print_system_stats():
    """Returns process CPU, RAM, and vector database size formatted string."""
    try:
        process = psutil.Process(os.getpid())
        process_mem = process.memory_info().rss / (1024 * 1024) # MB
        total_mem = psutil.virtual_memory().total / (1024 * 1024 * 1024) # GB
        mem_percent = psutil.virtual_memory().percent
        cpu_percent = process.cpu_percent(interval=None)
        db_size = get_dir_size("./ragchat_db") / (1024 * 1024) # MB
        
        return (
            f"RAM: {process_mem:.1f} MB (System: {total_mem:.1f} GB, {mem_percent}%) | "
            f"CPU: {cpu_percent:.1f}% | "
            f"DB Storage: {db_size:.2f} MB"
        )
    except Exception:
        return "System resource details unavailable"

def print_banner():
    # ANSI escape code to clear terminal screen and move cursor to top-left (0,0)
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

    stats_str = print_system_stats()
    
    console = Console()
    console.print("[bold cyan]========================================================================[/bold cyan]")
    console.print("[bold]                   Universal Documentation Chat (RAG)                  [/bold]")
    console.print(f"[dim]  {stats_str}  [/dim]")
    console.print("[bold cyan]========================================================================[/bold cyan]")
