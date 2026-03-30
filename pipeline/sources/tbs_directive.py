"""
Treasury Board of Canada Secretariat (TBS) directive collector.

Targeted scrape for the Directive on Automated Decision-Making
and related AI policy documents. This typically returns only 1-3 entries.

LAST_VERIFIED_DATE: 2026-03-29
"""

import time
import logging
import hashlib
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCE_NAME = "TBS Canada"
JURISDICTION = "Canada — Federal"
JURISDICTION_CODE = "CA-FED"

# Known TBS AI policy pages
KNOWN_PAGES = [
    {
        "url": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32592",
        "title": "Directive on Automated Decision-Making",
        "status": "In Force",
    },
    {
        "url": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32593",
        "title": "Algorithmic Impact Assessment Tool",
        "status": "In Force",
    },
]

# TBS policy search for additional AI-related directives
SEARCH_URL = "https://www.tbs-sct.canada.ca/pol/index-eng.aspx"

AI_TERMS = [
    "artificial intelligence", "automated decision", "algorithmic",
    "machine learning", "digital", "data",
]

REQUEST_DELAY = 2.0


def _is_ai_related(text):
    lower = text.lower()
    return any(term in lower for term in AI_TERMS)


def fetch():
    """
    Fetch TBS AI-related directives and policies.

    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
            "Accept-Language": "en-CA,en;q=0.9",
        })

        entries = {}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Add known pages first
        for page in KNOWN_PAGES:
            doc_id = f"tbs-{hashlib.md5(page['url'].encode()).hexdigest()[:10]}"
            entries[doc_id] = {
                "id": doc_id,
                "title": page["title"],
                "jurisdiction": JURISDICTION,
                "jurisdiction_code": JURISDICTION_CODE,
                "source_url": page["url"],
                "source_name": SOURCE_NAME,
                "type": "legislation",
                "status": page["status"],
                "domains": [],
                "date_introduced": "",
                "date_last_action": "",
                "last_action_summary": "Federal directive/policy",
                "summary": page["title"],
                "date_first_seen": now,
                "date_last_updated": now,
            }

        # Try to scrape the policy index for additional AI-related entries
        logger.info("Checking TBS policy index for AI-related directives...")
        time.sleep(REQUEST_DELAY)

        try:
            response = session.get(SEARCH_URL, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            links = soup.select("a[href*='doc-eng']")

            for link in links:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.tbs-sct.canada.ca{href}"

                if not _is_ai_related(title):
                    continue

                doc_id = f"tbs-{hashlib.md5(href.encode()).hexdigest()[:10]}"
                if doc_id in entries:
                    continue

                entries[doc_id] = {
                    "id": doc_id,
                    "title": title,
                    "jurisdiction": JURISDICTION,
                    "jurisdiction_code": JURISDICTION_CODE,
                    "source_url": href,
                    "source_name": SOURCE_NAME,
                    "type": "legislation",
                    "status": "In Force",
                    "domains": [],
                    "date_introduced": "",
                    "date_last_action": "",
                    "last_action_summary": "Federal directive/policy",
                    "summary": title,
                    "date_first_seen": now,
                    "date_last_updated": now,
                }
        except requests.exceptions.RequestException as e:
            logger.warning(f"TBS policy index request failed: {e}")

        result = list(entries.values())
        logger.info(f"TBS: collected {len(result)} AI-related directives")
        return result

    except Exception as e:
        logger.error(f"TBS source failed: {e}")
        return []
