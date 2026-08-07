import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import sys

class DocCrawler:
    def __init__(self, base_url, max_pages=50, max_depth=3, delay=0.5):
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.visited = {} # Crawled pages in this session (url: {html, title})
        self.already_crawled_urls = {} # URL -> Title from previous sessions
        self.queue = [(self.base_url, 0)]  # (url, depth)
        
        parsed = urlparse(base_url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme
        self.base_path = parsed.path

    def is_valid_url(self, url):
        parsed = urlparse(url)
        # Stay on the same domain
        if parsed.netloc != self.domain:
            return False
        # Avoid non-http/https links
        if parsed.scheme not in ["http", "https"]:
            return False
        # Avoid files/media links
        path = parsed.path.lower()
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz", ".xml", ".json"]:
            if path.endswith(ext):
                return False
        return True

    def load_state(self, filepath):
        import json
        import os
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.already_crawled_urls = data.get("already_crawled_urls", {})
                    self.queue = [tuple(item) for item in data.get("queue", [])]
                    # If queue was empty, reset to base URL
                    if not self.queue and self.base_url not in self.already_crawled_urls:
                        self.queue = [(self.base_url, 0)]
                print(f"[+] Loaded crawl state: {len(self.already_crawled_urls)} pages already crawled, {len(self.queue)} links in queue.")
                return True
            except Exception as e:
                print(f"[!] Error loading state: {e}")
        return False

    def save_state(self, filepath):
        import json
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Combine already crawled with current session crawled
        combined_crawled = self.already_crawled_urls.copy()
        for url, data in self.visited.items():
            combined_crawled[url] = data["title"]
            
        data = {
            "already_crawled_urls": combined_crawled,
            "queue": self.queue
        }
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[+] Saved crawl state of {len(combined_crawled)} pages to {filepath}")
        except Exception as e:
            print(f"[!] Error saving state: {e}")

    def scroll_to_bottom(self, page, max_scrolls=5, scroll_delay=800):
        try:
            last_height = page.evaluate("document.body.scrollHeight")
            for _ in range(max_scrolls):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(scroll_delay)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception:
            pass

    def detect_js_required(self, url):
        print(f"[*] Checking if JavaScript rendering is required for {url}...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                # Fallback to Playwright if page has access blocks
                return True
                
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return False
                
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()
            text = soup.get_text().strip()
            
            # If text content is very short, it's likely a React/SPA template requiring client-side JS
            if len(text) < 1500:
                print("[+] Page body is short/empty; JavaScript rendering (Playwright) will be used.")
                return True
            print("[+] Rich static HTML detected; running fast parser (requests) to crawl.")
            return False
        except Exception as e:
            print(f"[!] Detection failed ({e}). Defaulting to Playwright.")
            return True

    def process_page_html(self, url, html, depth):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else url
        
        self.visited[url] = {
            "html": html,
            "title": title
        }
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)
            full_url_parsed = urlparse(full_url)
            full_url_clean = f"{full_url_parsed.scheme}://{full_url_parsed.netloc}{full_url_parsed.path}"
            
            if self.is_valid_url(full_url_clean) and full_url_clean not in self.visited and full_url_clean not in self.already_crawled_urls:
                if (full_url_clean, depth + 1) not in self.queue:
                    self.queue.append((full_url_clean, depth + 1))

    def crawl(self):
        print(f"[*] Starting crawl from: {self.base_url}")
        self.visited = {}
        pages_crawled_this_session = 0
        
        # Auto-detect if JavaScript is required based on base URL
        use_playwright = self.detect_js_required(self.base_url)
        
        if use_playwright:
            from playwright.sync_api import sync_playwright
            try:
                with sync_playwright() as p:
                    print("[*] Launching headless browser...")
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = context.new_page()
                    
                    while self.queue and pages_crawled_this_session < self.max_pages:
                        url, depth = self.queue.pop(0)
                        parsed_url = urlparse(url)
                        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        
                        if normalized_url in self.visited or normalized_url in self.already_crawled_urls:
                            continue
                        if depth > self.max_depth:
                            continue

                        print(f"[+] Crawling ({pages_crawled_this_session+1}/{self.max_pages}) [Playwright]: {normalized_url}")
                        pages_crawled_this_session += 1
                        
                        try:
                            page.goto(normalized_url, timeout=20000)
                            try:
                                page.wait_for_load_state("networkidle", timeout=3000)
                            except Exception:
                                pass
                                
                            self.scroll_to_bottom(page)
                            html = page.content()
                            time.sleep(self.delay)
                            
                            self.process_page_html(normalized_url, html, depth)
                        except Exception as e:
                            print(f"[!] Error crawling {normalized_url}: {e}")
                    browser.close()
            except Exception as e:
                print(f"[!] Playwright browser error: {e}")
                print("[*] Fallback: running requests crawler...")
                use_playwright = False
                
        if not use_playwright:
            while self.queue and pages_crawled_this_session < self.max_pages:
                url, depth = self.queue.pop(0)
                parsed_url = urlparse(url)
                normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                
                if normalized_url in self.visited or normalized_url in self.already_crawled_urls:
                    continue
                if depth > self.max_depth:
                    continue

                print(f"[+] Crawling ({pages_crawled_this_session+1}/{self.max_pages}) [Requests]: {normalized_url}")
                pages_crawled_this_session += 1
                
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    response = requests.get(normalized_url, headers=headers, timeout=10)
                    time.sleep(self.delay)
                    
                    if response.status_code != 200:
                        print(f"[!] Failed to fetch {normalized_url}: HTTP {response.status_code}")
                        continue
                        
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        continue
                        
                    self.process_page_html(normalized_url, response.text, depth)
                except Exception as e:
                    print(f"[!] Error crawling {normalized_url}: {e}")
                    
        print(f"[*] Crawling finished. Successfully retrieved {len(self.visited)} new pages.")
        return self.visited

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 crawler.py <url>")
        sys.exit(1)
    crawler = DocCrawler(sys.argv[1], max_pages=5)
    results = crawler.crawl()
    for url, data in results.items():
        print(f"- {data['title']}: {url}")
