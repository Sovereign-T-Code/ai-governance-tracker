"""
EUR-Lex REST API source collector.

Uses the EUR-Lex search API to find AI-related EU legislation.
No API key required.
"""

import time
import logging
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCE_NAME = "EUR-Lex"
JURISDICTION = "European Union"
JURISDICTION_CODE = "EU"

SEARCH_URL = "https://eur-lex.europa.eu/search.html"

# Search terms
SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "algorithmic",
    "automated decision",
    "AI Act",
]

# Status keywords found in EUR-Lex document metadata
STATUS_MAP = {
    "in force": "In Force",
    "entered into force": "In Force",
    "adopted": "Passed/Adopted",
    "published": "Passed/Adopted",
    "proposal": "Proposed",
    "pending": "In Progress",
    "repealed": "Withdrawn/Defeated",
    "no longer in force": "Withdrawn/Defeated",
}

REQUEST_DELAY = 2.0  # be polite to EUR-Lex


def _parse_status(status_text):
    """Map EUR-Lex status text to normalized status."""
    if not status_text:
        return "Proposed"
    lower = status_text.lower()
    for key, val in STATUS_MAP.items():
        if key in lower:
            return val
    return "Proposed"


def fetch():
    """
    Fetch AI-related EU legislation from EUR-Lex.

    Uses the EUR-Lex HTML search page and parses results.
    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
            "Accept-Language": "en",
        })

        all_docs = {}

        for term in SEARCH_TERMS:
            logger.info(f"Searching EUR-Lex for: {term}")
            time.sleep(REQUEST_DELAY)

            params = {
                "text": term,
                "scope": "EURLEX",
                "type": "quick",
                "lang": "en",
                "page": 1,
            }

            try:
                response = session.get(SEARCH_URL, params=params, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.warning(f"EUR-Lex request failed for '{term}': {e}")
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Parse search results
            results = soup.select("div.SearchResult")
            if not results:
                # Try alternative selector
                results = soup.select("div.EurlexContent div.SearchResultList div")

            logger.info(f"  Found {len(results)} results for: {term}")

            for result in results:
                try:
                    # Extract title and link
                    title_el = result.select_one("a.title, h2 a, .SearchResult_Title a")
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://eur-lex.europa.eu{link}"

                    # Extract CELEX number from URL or text
                    celex = ""
                    if "celex" in link.lower():
                        parts = link.split("/")
                        for i, p in enumerate(parts):
                            if p.lower() == "celex" and i + 1 < len(parts):
                                celex = parts[i + 1].split("?")[0]
                                break
                    if not celex:
                        celex = link.split("/")[-1].split("?")[0] if link else title[:30]

                    doc_id = f"eurlex-{celex}" if celex else f"eurlex-{hash(title) % 100000}"

                    if doc_id in all_docs:
                        continue

                    # Extract summary/description
                    desc_el = result.select_one(".SearchResult_Summary, .EurlexSummary, p")
                    summary = desc_el.get_text(strip=True)[:500] if desc_el else title

                    # Extract date
                    date_el = result.select_one(".SearchResult_Date, .date, time")
                    date_text = date_el.get_text(strip=True) if date_el else ""
                    # Try to parse date
                    pub_date = ""
                    if date_text:
                        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d %B %Y"]:
                            try:
                                pub_date = datetime.strptime(date_text, fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue

                    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                    all_docs[doc_id] = {
                        "id": doc_id,
                        "title": title,
                        "jurisdiction": JURISDICTION,
                        "jurisdiction_code": JURISDICTION_CODE,
                        "source_url": link,
                        "source_name": SOURCE_NAME,
                        "type": "legislation",
                        "status": "Proposed",  # default; updated by classify
                        "domains": [],
                        "date_introduced": pub_date,
                        "date_last_action": pub_date,
                        "last_action_summary": "",
                        "summary": summary,
                        "date_first_seen": now,
                        "date_last_updated": now,
                    }
                except Exception as e:
                    logger.debug(f"Failed to parse EUR-Lex result: {e}")
                    continue

        entries = list(all_docs.values())
        logger.info(f"EUR-Lex: collected {len(entries)} AI-related documents")
        return entries

    except Exception as e:
        logger.error(f"EUR-Lex source failed: {e}")
        return []
