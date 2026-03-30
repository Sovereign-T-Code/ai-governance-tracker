"""
Canada Gazette source collector.

Checks for RSS feeds first (more stable), falls back to HTML scraping.
Looks for AI-related regulatory proposals in Part I and Part II.

LAST_VERIFIED_DATE: 2026-03-29
"""

import time
import logging
import hashlib
import requests
import feedparser
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SOURCE_NAME = "Canada Gazette"
JURISDICTION = "Canada — Federal"
JURISDICTION_CODE = "CA-FED"

# RSS feeds for Canada Gazette
RSS_FEEDS = [
    "https://gazette.gc.ca/rp-pr/p1/index-eng.rss",
    "https://gazette.gc.ca/rp-pr/p2/index-eng.rss",
    "https://www.gazette.gc.ca/rss/gazette-eng.xml",
]

# Fallback search URL
SEARCH_URL = "https://gazette.gc.ca/rp-pr/publications-eng.html"

# AI keywords for filtering
AI_TERMS = [
    "artificial intelligence", "intelligence artificielle",
    "machine learning", "automated decision", "décision automatisée",
    "algorithmic", "algorithmique", "facial recognition",
    "reconnaissance faciale", "biometric", "biométrique",
    "autonomous", "autonome",
]

REQUEST_DELAY = 2.0


def _is_ai_related(text):
    """Check if text contains AI-related terms."""
    lower = text.lower()
    return any(term in lower for term in AI_TERMS)


def _make_id(title, link):
    """Generate a deterministic ID from title and link."""
    raw = f"{title}-{link}"
    short_hash = hashlib.md5(raw.encode()).hexdigest()[:10]
    return f"gazette-{short_hash}"


def _fetch_rss(session):
    """Try to fetch entries from Canada Gazette RSS feeds."""
    entries = {}

    for feed_url in RSS_FEEDS:
        logger.info(f"Trying Canada Gazette RSS: {feed_url}")
        time.sleep(REQUEST_DELAY)

        try:
            response = session.get(feed_url, timeout=30)
            if response.status_code != 200:
                logger.debug(f"RSS feed returned {response.status_code}: {feed_url}")
                continue

            feed = feedparser.parse(response.text)

            for item in feed.entries:
                title = item.get("title", "")
                summary = item.get("summary", "") or item.get("description", "")
                link = item.get("link", "")
                text = f"{title} {summary}"

                if not _is_ai_related(text):
                    continue

                doc_id = _make_id(title, link)
                if doc_id in entries:
                    continue

                # Parse published date
                pub_date = ""
                if hasattr(item, "published_parsed") and item.published_parsed:
                    pub_date = datetime(*item.published_parsed[:6]).strftime("%Y-%m-%d")

                now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                entries[doc_id] = {
                    "id": doc_id,
                    "title": title,
                    "jurisdiction": JURISDICTION,
                    "jurisdiction_code": JURISDICTION_CODE,
                    "source_url": link,
                    "source_name": SOURCE_NAME,
                    "type": "legislation",
                    "status": "Proposed",  # Gazette items are typically proposals
                    "domains": [],
                    "date_introduced": pub_date,
                    "date_last_action": pub_date,
                    "last_action_summary": "Published in Canada Gazette",
                    "summary": summary[:500] if summary else title,
                    "date_first_seen": now,
                    "date_last_updated": now,
                }

        except Exception as e:
            logger.debug(f"RSS feed failed: {feed_url} — {e}")
            continue

    return entries


def fetch():
    """
    Fetch AI-related entries from the Canada Gazette.

    Tries RSS feeds first (more stable), returns whatever is found.
    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
            "Accept-Language": "en-CA,en;q=0.9",
        })

        all_entries = _fetch_rss(session)

        entries = list(all_entries.values())
        logger.info(f"Canada Gazette: collected {len(entries)} AI-related entries")
        return entries

    except Exception as e:
        logger.error(f"Canada Gazette source failed: {e}")
        return []
