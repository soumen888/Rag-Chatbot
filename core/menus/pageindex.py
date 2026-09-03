import os
from rich.console import Console
from rich.markdown import Markdown

try:
    from ragchat_core.core.pageindex_client import index_document, query_document, list_indexed_documents
except ImportError:
    from core.pageindex_client import index_document, query_document, list_indexed_documents

def handle_pageindex_menu(cfg):
    """Interactive menu for reasoning-based RAG using PageIndex on large PDFs/Books."""
    console = Console()
    
    while True:
        print("\n--- LARGE DOCUMENT RAG (PAGEINDEX) ---")
        print("1. Index a New Local PDF Document")
        print("2. Chat with an Indexed Document")
        print("3. List Indexed Documents")
        print("4. Back to Main Menu")

        choice = input("\nSelect option (1-4): ").strip()
        if choice == "4" or choice.lower() in ["back", "b"]:
            break

        if choice == "1":
            pdf_path = input("Enter absolute path to the local PDF file: ").strip("'\" ")
            if not pdf_path:
                print("[!] File path cannot be empty.")
                continue
            if not os.path.exists(pdf_path):
                print(f"[!] File not found: {pdf_path}")
                continue

            with console.status("[bold cyan]Generating Table-of-Contents Tree & Indexing...", spinner="dots"):
                try:
                    doc_id = index_document(pdf_path)
                    console.print(f"\n[bold green][+] Document indexed successfully![/bold green]")
                    console.print(f"[bold green][+] Document ID: {doc_id}[/bold green]\n")
                except Exception as e:
                    console.print(f"\n[bold red][!] Indexing failed: {e}[/bold red]\n")

        elif choice == "2":
            try:
                docs = list_indexed_documents()
            except Exception as e:
                print(f"[!] Failed to list documents: {e}")
                continue

            if not docs:
                print("[-] No indexed documents found. Please index a PDF first.")
                continue

            print("\nAvailable PageIndex Documents:")
            for idx, doc in enumerate(docs):
                print(f"{idx + 1}. {doc}")
            print("0. Back")

            sel = input(f"Select a document to chat (0-{len(docs)}): ").strip()
            if sel == "0" or not sel.isdigit() or int(sel) < 1 or int(sel) > len(docs):
                continue

            selected_doc_id = docs[int(sel) - 1]
            print(f"\n[+] Started Reasoning-based Chat with: {selected_doc_id}")
            print("Type 'exit' or 'back' to return.\n")

            while True:
                user_query = input("You: ").strip()
                if not user_query:
                    continue
                if user_query.lower() in ["exit", "back"]:
                    break

                with console.status("[bold green]Reasoning and searching document tree...", spinner="dots"):
                    try:
                        answer = query_document(selected_doc_id, user_query)
                    except Exception as e:
                        answer = f"Error during query: {e}"

                console.print("\n[bold cyan]Bot:[/bold cyan]")
                console.print(Markdown(answer))
                print()

        elif choice == "3":
            print("\nRetrieving indexed documents...")
            try:
                docs = list_indexed_documents()
                if not docs:
                    print("[-] No documents indexed yet.")
                else:
                    print("\nIndexed PageIndex Documents:")
                    for doc in docs:
                        print(f"  - {doc}")
            except Exception as e:
                print(f"[!] Failed to retrieve documents: {e}")
