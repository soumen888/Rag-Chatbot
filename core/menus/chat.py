from rich.console import Console
from rich.markdown import Markdown

def format_col_display(col_name):
    """Formats a ChromaDB collection name for display in menus."""
    if col_name == "telegram_all":
        return "Telegram: All Channels (telegram_all)"
    elif col_name.startswith("tg_"):
        raw_name = col_name[3:].replace("_", " ").title()
        return f"Telegram: {raw_name} ({col_name})"
    elif col_name.startswith("ds_"):
        raw_name = col_name[3:].replace("_", " ").title()
        return f"Discord: {raw_name} ({col_name})"
    else:
        return f"Docs: {col_name}"

def handle_chat_menu(db, chatbot):
    from main.stats import print_system_stats
    from core.menus.settings import init_llm_provider_wrapper
    
    collections = db.list_collections()
    if not collections:
        print("[!] No indexed collections found. Please index a website or Telegram/Discord channel first.")
        return chatbot
        
    print("\nAvailable indexed collections:")
    print("0. Back to main menu")
    for idx, col in enumerate(collections):
        print(f"{idx + 1}. {format_col_display(col)}")
        
    sel = input(f"Select a collection to chat (0-{len(collections)}): ").strip()
    if sel == "0" or sel.lower() in ["back", "b"]:
        return chatbot
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
        print("[!] Invalid selection.")
        return chatbot
        
    selected_collection = collections[int(sel) - 1]
    print(f"\n[+] Started chat session with '{format_col_display(selected_collection)}'")
    print("Type 'exit' or 'back' to return to the main menu.\n")
    
    if not chatbot:
        chatbot = init_llm_provider_wrapper()
    if not chatbot:
        print("[!] Cannot start chat without a configured LLM provider.")
        return chatbot
            
    console = Console()
    while True:
        user_query = input("You: ").strip()
        if not user_query:
            continue
        if user_query.lower() in ["exit", "back", "b"]:
            break
            
        with console.status("[bold cyan]Searching knowledge base...", spinner="dots"):
            results = db.query(selected_collection, user_query, n_results=10)
        
        if not results:
            console.print("[yellow]Bot: No relevant context found in database.[/yellow]")
            continue
            
        with console.status("[bold green]Formulating answer...", spinner="dots"):
            answer = chatbot.generate_answer(user_query, results)
            
        console.print("\n[bold cyan]Bot:[/bold cyan]")
        console.print(Markdown(answer))
        print()
        console.print(f"[dim][SYSTEM] {print_system_stats()}[/dim]")
        print()

    return chatbot
