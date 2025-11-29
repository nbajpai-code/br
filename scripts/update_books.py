import feedparser
import os
import datetime
import re

import requests

def update_feed(feed_url, file_path, title_filter=None):
    print(f"Checking feed: {feed_url}")
    
    # Headers to mimic a browser and avoid 403s
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }

    try:
        # Fetch content first
        response = requests.get(feed_url, headers=headers, timeout=10)
        if response.status_code == 403:
            print(f"  Warning: Access forbidden (403) for {feed_url}. Anti-bot protection active.")
            return
        elif response.status_code == 404:
            print(f"  Warning: Feed not found (404) for {feed_url}.")
            return
        response.raise_for_status()

        # Parse content
        feed = feedparser.parse(response.content)
        if feed.bozo:
            print(f"  Warning: Feed parsing error: {feed.bozo_exception}")


        new_entries = []
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            # Optional filter (e.g., for Gates Notes to find book posts)
            if title_filter and not title_filter(title, entry):
                continue

            # Clean up title if needed
            title = title.strip()
            
            new_entries.append(f"*   [{title}]({link})")

        if not new_entries:
            print("  No entries found.")
            return

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read existing content
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
        else:
            content = f"# {feed.feed.get('title', 'Book List')}\n\n"

        added_count = 0
        today = datetime.date.today().isoformat()
        updates = []

        for item in new_entries:
            # Check if link is already in content (simple duplicate check)
            # We extract the link from the markdown: ](link)
            link_match = re.search(r'\((http.*?)\)', item)
            if link_match:
                link_url = link_match.group(1)
                if link_url in content:
                    continue
            
            updates.append(item)
            added_count += 1

        if updates:
            with open(file_path, 'a') as f:
                f.write(f"\n\n## Updates ({today})\n")
                for update in updates:
                    f.write(f"{update}\n")
            print(f"  Added {added_count} new items to {os.path.basename(file_path)}.")
        else:
            print(f"  No new items to add for {os.path.basename(file_path)}.")

    except Exception as e:
        print(f"  Error updating feed: {e}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Bill Gates
    gates_feed = "http://www.gatesnotes.com/rss"
    gates_file = os.path.join(base_dir, "luminaries/bill_gates.md")
    # Filter for Gates: Look for "book" or "reading" in title, or just take recent posts as he often reviews books.
    # Let's be broader for now to capture his essays which often contain recs.
    update_feed(gates_feed, gates_file)

    # 2. NYT Book Review
    nyt_feed = "https://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/section/books/review/rss.xml"
    nyt_file = os.path.join(base_dir, "platforms/nyt_book_review.md")
    update_feed(nyt_feed, nyt_file)

    # 3. NPR Books
    npr_feed = "https://feeds.npr.org/1032/rss.xml"
    npr_file = os.path.join(base_dir, "platforms/npr_books.md")
    update_feed(npr_feed, npr_file)

if __name__ == "__main__":
    main()
