import os
from core.menus.chat import format_col_display

def handle_collections_menu(db):
    while True:
        print("\n--- COLLECTIONS MENU ---")
        print("1. List all indexed collections")
        print("2. Delete an indexed collection")
        print("3. Back to main menu")
        
        sub = input("\nSelect option (1-3): ").strip()
        if sub == "3" or sub.lower() in ["back", "b"]:
            break
        
        if sub == "1":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed collections found.")
            else:
                print("\nIndexed collections:")
                for col in collections:
                    print(f"- {format_col_display(col)}")
                    
        elif sub == "2":
            collections = db.list_collections()
            if not collections:
                print("[!] No indexed collections found.")
                continue
                
            print("\nAvailable indexed collections:")
            print("0. Back to main menu")
            for idx, col in enumerate(collections):
                print(f"{idx + 1}. {format_col_display(col)}")
                
            sel = input(f"Select a collection to delete (0-{len(collections)}): ").strip()
            if sel == "0" or sel.lower() in ["back", "b"]:
                continue
            if not sel.isdigit() or int(sel) < 1 or int(sel) > len(collections):
                print("[!] Invalid selection.")
                continue
                
            col_to_delete = collections[int(sel) - 1]
            confirm = input(f"Are you sure you want to delete '{format_col_display(col_to_delete)}'? (y/n): ").strip().lower()
            if confirm == 'y':
                db.delete_collection(col_to_delete)
                cache_file = os.path.join("./.crawl_cache", f"{col_to_delete}.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass
