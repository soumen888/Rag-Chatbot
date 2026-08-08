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

    def process_telegram_messages(self, messages):
        """
        Groups and chunks raw Telegram messages into context-rich chunks.
        Includes channel title, date, sender, and direct message link.
        """
        all_chunks = []
        if not messages:
            return all_chunks

        # Group short consecutive messages to preserve context
        grouped_blocks = []
        current_block = []
        current_len = 0

        for msg in messages:
            msg_str = f"[{msg['date_str']}] {msg['sender']}: {msg['text']}"
            if current_len + len(msg_str) > self.chunk_size and current_block:
                grouped_blocks.append(current_block)
                current_block = [msg]
                current_len = len(msg_str)
            else:
                current_block.append(msg)
                current_len += len(msg_str)

        if current_block:
            grouped_blocks.append(current_block)

        for i, block in enumerate(grouped_blocks):
            first_msg = block[0]
            combined_text = "\n".join([f"[{m['date_str']}] {m['sender']}: {m['text']}" for m in block])
            
            metadata = {
                "source": first_msg["link"],
                "title": f"Telegram ({first_msg['channel_title']})",
                "peer_id": first_msg["peer_id"],
                "channel_title": first_msg["channel_title"],
                "timestamp": first_msg["timestamp"],
                "chunk_index": i
            }

            prepended_text = (
                f"Channel: {first_msg['channel_title']} (Peer ID: {first_msg['peer_id']})\n"
                f"Source Link: {first_msg['link']}\n"
                f"Date: {first_msg['date_str']}\n\n"
                f"{combined_text}"
            )

            all_chunks.append({
                "text": prepended_text,
                "metadata": metadata
            })

        return all_chunks

    def process_discord_messages(self, messages):
        """
        Groups and chunks raw Discord messages into context-rich chunks.
        Includes server name, channel name, sender details, and direct jump link.
        """
        all_chunks = []
        if not messages:
            return all_chunks

        # Group consecutive messages to preserve context
        grouped_blocks = []
        current_block = []
        current_len = 0

        for msg in messages:
            msg_str = f"[{msg['date_str']}] {msg['sender']} ({msg['username']}): {msg['text']}"
            if current_len + len(msg_str) > self.chunk_size and current_block:
                grouped_blocks.append(current_block)
                current_block = [msg]
                current_len = len(msg_str)
            else:
                current_block.append(msg)
                current_len += len(msg_str)

        if current_block:
            grouped_blocks.append(current_block)

        for i, block in enumerate(grouped_blocks):
            first_msg = block[0]
            combined_text = "\n".join([f"[{m['date_str']}] {m['sender']} ({m['username']}): {m['text']}" for m in block])
            
            metadata = {
                "source": first_msg["link"],
                "title": f"Discord ({first_msg['server_name']} -> #{first_msg['channel_title']})",
                "channel_id": first_msg["channel_id"],
                "channel_title": first_msg["channel_title"],
                "server_name": first_msg["server_name"],
                "timestamp": first_msg["timestamp"],
                "chunk_index": i
            }

            prepended_text = (
                f"Server: {first_msg['server_name']}\n"
                f"Channel: #{first_msg['channel_title']} (ID: {first_msg['channel_id']})\n"
                f"Source Link: {first_msg['link']}\n"
                f"Date: {first_msg['date_str']}\n\n"
                f"{combined_text}"
            )

            all_chunks.append({
                "text": prepended_text,
                "metadata": metadata
            })

        return all_chunks
