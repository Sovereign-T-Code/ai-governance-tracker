"""
Google News RSS source collector.

Fetches AI governance news articles via Google News RSS feeds.
Completely free, no API key, no rate limits.
Uses feedparser (already a pipeline dependency).
"""

import time
import logging
import hashlib
import requests
import feedparser
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SOURCE_NAME = "Google News"
REQUEST_DELAY = 1.0

# Google News RSS search URL template
# URL-encode the query and append it
NEWS_RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"

# Search queries for AI governance news
SEARCH_QUERIES = [
    "AI regulation legislation",
    "artificial intelligence governance policy",
    "AI Act enforcement",
    "algorithmic accountability law",
    "AI safety regulation",
    "Canada AI regulation",
    "EU AI Act",
]

# Max articles per query
MAX_PER_QUERY = 15


def _make_id(link):
    """Generate a deterministic ID from the article URL."""
    return f"news-{hashlib.md5(link.encode()).hexdigest()[:12]}"


def _guess_jurisdiction(title, summary):
    """Try to guess jurisdiction from article text."""
    text = f"{title} {summary}".lower()

    if any(w in text for w in ["canada", "canadian", "ottawa", "trudeau", "pipeda"]):
        return "Canada — Federal", "CA-FED"
    if any(w in text for w in ["ontario"]):
        return "Canada — Ontario", "CA-ON"
    if any(w in text for w in ["eu ", "european", "brussels", "ai act", "eur-lex"]):
        return "European Union", "EU"
    if any(w in text for w in ["congress", "senate", "house", "biden", "trump", "white house", "federal register"]):
        return "United States — Federal", "US-FED"

    return "International", "INTL"


def fetch():
    """
    Fetch AI governance news from Google News RSS.

    Returns a list of entry dicts with type="news".
    Returns an empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
        })

        all_articles = {}

        for query in SEARCH_QUERIES:
            logger.info(f"Fetching Google News RSS for: {query}")
            time.sleep(REQUEST_DELAY)

            encoded_query = requests.utils.quote(query)
            feed_url = NEWS_RSS_BASE.format(query=encoded_query)

            try:
                response = session.get(feed_url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"News RSS returned {response.status_code} for: {query}")
                    continue

                feed = feedparser.parse(response.text)
            except Exception as e:
                logger.warning(f"News RSS request failed for '{query}': {e}")
                continue

            count = 0
            for item in feed.entries:
                if count >= MAX_PER_QUERY:
                    break

                title = item.get("title", "")
                link = item.get("link", "")
                summary = item.get("summary", "") or item.get("description", "")

                if not title or not link:
                    continue

                doc_id = _make_id(link)
                if doc_id in all_articles:
                    continue

                # Parse published date
                pub_date = ""
                if hasattr(item, "published_parsed") and item.published_parsed:
                    try:
                        pub_date = datetime(*item.published_parsed[:6]).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        pass

                jurisdiction, jurisdiction_code = _guess_jurisdiction(title, summary)
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Clean summary (remove HTML and entities)
                import re
                clean_summary = re.sub(r"<[^>]+>", "", summary).strip()
                clean_summary = clean_summary.replace("&nbsp;", " ").replace("&amp;", "&")
                if len(clean_summary) > 500:
                    clean_summary = clean_summary[:497] + "..."

                all_articles[doc_id] = {
                    "id": doc_id,
                    "title": title,
                    "jurisdiction": jurisdiction,
                    "jurisdiction_code": jurisdiction_code,
                    "source_url": link,
                    "source_name": SOURCE_NAME,
                    "type": "news",
                    "status": "",  # news articles don't have legislative status
                    "domains": [],
                    "date_introduced": pub_date,
                    "date_last_action": pub_date,
                    "last_action_summary": "",
                    "summary": clean_summary or title,
                    "date_first_seen": now,
                    "date_last_updated": now,
                }
                count += 1

        entries = list(all_articles.values())
        logger.info(f"News RSS: collected {len(entries)} AI governance articles")
        return entries

    except Exception as e:
        logger.error(f"News RSS source failed: {e}")
        return []
