import os
from urllib.parse import urlparse
from website import DocCrawler
from core.chunker import DocChunker

def handle_website_menu(db):
    while True:
        print("\n--- WEBSITE MENU ---")
        print("1. Crawl & Index a new documentation site")
        print("2. Back to main menu")
        
        sub = input("\nSelect option (1-2): ").strip()
        if sub == "2" or sub.lower() in ["back", "b"]:
            break
        if sub != "1":
            continue

        url = input("Enter documentation base URL (or type 'back' to cancel): ").strip()
        if not url or url.lower() in ["back", "b"]:
            continue
            
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print("[!] Invalid URL scheme or domain.")
            continue
            
        collection_name = parsed.netloc
        safe_col_name = db.sanitize_collection_name(collection_name)
        
        cache_dir = "./.crawl_cache"
        cache_file = os.path.join(cache_dir, f"{safe_col_name}.json")
        
        resume = False
        if os.path.exists(cache_file):
            print(f"\n[!] Found previous crawl state for '{safe_col_name}'.")
            print("1. Resume crawling (crawl new pages, append to database)")
            print("2. Start fresh (delete existing collection & cache, crawl from scratch)")
            print("3. Back to main menu")
            sub_choice = input("Select option (1-3, default 1): ").strip()
            if sub_choice == "3" or sub_choice.lower() in ["back", "b"]:
                continue
            elif sub_choice == "2":
                print(f"[*] Deleting existing collection and cache for '{safe_col_name}'...")
                db.delete_collection(collection_name)
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass
            else:
                resume = True
        
        max_pages_input = input("Max pages to crawl this session (default 50): ").strip()
        max_pages = int(max_pages_input) if max_pages_input.isdigit() else 50
        
        crawler = DocCrawler(base_url=url, max_pages=max_pages)
        if resume:
            crawler.load_state(cache_file)
            
        pages = crawler.crawl()
        
        if not pages:
            print("[!] No new pages crawled this session.")
            if resume:
                crawler.save_state(cache_file)
            continue
            
        print("[*] Parsing and chunking HTML content...")
        chunker = DocChunker()
        chunks = chunker.process_pages(pages)
        print(f"[+] Created {len(chunks)} chunks from {len(pages)} new pages.")
        
        db.add_chunks(collection_name, chunks)
        crawler.save_state(cache_file)
        print(f"[+] Collection '{safe_col_name}' is ready to chat!")
