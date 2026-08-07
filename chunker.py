from bs4 import BeautifulSoup
import re

class DocChunker:
    def __init__(self, chunk_size=800, chunk_overlap=150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_html(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove non-content elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
            element.decompose()

        # Get plain text
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        chunks = [line for line in lines if line]
        clean_text = "\n".join(chunks)
        
        # Collapse multiple newlines/spaces
        clean_text = re.sub(r'\n+', '\n', clean_text)
        clean_text = re.sub(r' +', ' ', clean_text)
        
        return clean_text

    def chunk_text(self, text, metadata):
        chunks = []
        text_len = len(text)
        
        if text_len <= self.chunk_size:
            chunks.append({
                "text": text,
                "metadata": metadata
            })
            return chunks

        start = 0
        while start < text_len:
            end = start + self.chunk_size
            
            # If we are not at the end of the text, try to find a natural boundary (newline or space)
            if end < text_len:
                # Look for a newline in the last 150 chars of the chunk
                search_start = max(start, end - 150)
                boundary = text.rfind('\n', search_start, end)
                if boundary != -1 and boundary > start:
                    end = boundary + 1
                else:
                    # Fallback to space
                    boundary = text.rfind(' ', search_start, end)
                    if boundary != -1 and boundary > start:
                        end = boundary + 1
                        
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata.copy()
                })
                
            start = end - self.chunk_overlap
            if start >= text_len - self.chunk_overlap:
                break
                
        return chunks

    def process_pages(self, crawled_pages):
        all_chunks = []
        for url, data in crawled_pages.items():
            clean_txt = self.clean_html(data["html"])
            metadata = {
                "source": url,
                "title": data["title"]
            }
            page_chunks = self.chunk_text(clean_txt, metadata)
            
            # Add index to metadata and prepend context to the text body
            for i, chunk in enumerate(page_chunks):
                chunk["metadata"]["chunk_index"] = i
                chunk["text"] = f"Document Title: {data['title']}\nSource: {url}\n\n{chunk['text']}"
                
            all_chunks.extend(page_chunks)
            
        return all_chunks

if __name__ == "__main__":
    dummy_html = """
    <html>
      <head><title>Test Page</title></head>
      <body>
        <nav><a href="#">Home</a></nav>
        <div id="sidebar">Sidebar content</div>
        <div class="content">
          <h1>Main Header</h1>
          <p>This is the first paragraph of the test page. It contains some basic information that we want to retrieve.</p>
          <h2>Second Header</h2>
          <p>Here is another paragraph containing details about how RAG systems work. They retrieve documents and feed them to LLMs.</p>
        </div>
        <footer>Footer content</footer>
      </body>
    </html>
    """
    chunker = DocChunker(chunk_size=100, chunk_overlap=20)
    crawled = {"https://example.com/test": {"html": dummy_html, "title": "Test Page"}}
    chunks = chunker.process_pages(crawled)
    for i, c in enumerate(chunks):
        print(f"--- Chunk {i} ---")
        print(f"Meta: {c['metadata']}")
        print(f"Content:\n{c['text']}")
