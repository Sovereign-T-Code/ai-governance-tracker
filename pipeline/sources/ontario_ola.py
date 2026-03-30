"""
Ontario Legislative Assembly (OLA) source collector.

Scrapes the Ontario bills page for AI-related provincial legislation.
This is a fragile scraper — CSS selectors may need updates.

LAST_VERIFIED_DATE: 2026-03-29
"""

import time
import logging
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCE_NAME = "Ontario Legislative Assembly"
JURISDICTION = "Canada — Ontario"
JURISDICTION_CODE = "CA-ON"

# OLA bills page
BILLS_URL = "https://www.ola.org/en/legislative-business/bills"

# AI keywords for filtering
AI_TERMS = [
    "artificial intelligence", "intelligence artificielle",
    "machine learning", "automated decision", "algorithmic",
    "facial recognition", "biometric", "autonomous",
    "data protection", "digital", "technology",
]

REQUEST_DELAY = 2.0

STATUS_MAP = {
    "first reading": "Proposed",
    "second reading": "In Progress",
    "committee": "In Progress",
    "third reading": "In Progress",
    "royal assent": "Passed/Adopted",
    "proclaimed": "In Force",
    "withdrawn": "Withdrawn/Defeated",
}


def _normalize_status(status_text):
    if not status_text:
        return "Proposed"
    lower = status_text.lower().strip()
    for key, val in STATUS_MAP.items():
        if key in lower:
            return val
    return "Proposed"


def _is_ai_related(text):
    lower = text.lower()
    return any(term in lower for term in AI_TERMS)


def fetch():
    """
    Fetch AI-related Ontario bills from OLA.

    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
            "Accept-Language": "en-CA,en;q=0.9",
        })

        logger.info("Fetching Ontario Legislative Assembly bills page...")
        time.sleep(REQUEST_DELAY)

        try:
            response = session.get(BILLS_URL, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning(f"OLA request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "lxml")

        # Try various selectors for bill listings
        rows = (
            soup.select("table tbody tr") or
            soup.select(".view-content .views-row") or
            soup.select(".bill-listing li") or
            soup.select("article")
        )

        logger.info(f"Found {len(rows)} bill rows on OLA page")

        entries = {}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for row in rows:
            try:
                link_el = row.select_one("a[href]")
                if not link_el:
                    continue

                title = link_el.get_text(strip=True)
                href = link_el.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.ola.org{href}"

                # Get full row text for AI relevance check
                row_text = row.get_text(" ", strip=True)

                if not _is_ai_related(f"{title} {row_text}"):
                    continue

                # Try to extract bill number
                bill_number = ""
                for part in row_text.split():
                    if part.isdigit() and len(part) <= 4:
                        bill_number = part
                        break

                # Try to extract status
                status_text = ""
                status_el = row.select_one("td:last-child, .field-status, .bill-status")
                if status_el:
                    status_text = status_el.get_text(strip=True)

                doc_id = f"ontario-bill-{bill_number}" if bill_number else f"ontario-{hash(title) % 100000}"

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
                    "status": _normalize_status(status_text),
                    "domains": [],
                    "date_introduced": "",
                    "date_last_action": "",
                    "last_action_summary": status_text,
                    "summary": title,
                    "date_first_seen": now,
                    "date_last_updated": now,
                }
            except Exception as e:
                logger.debug(f"Failed to parse OLA row: {e}")
                continue

        result = list(entries.values())
        logger.info(f"Ontario OLA: collected {len(result)} AI-related bills")
        return result

    except Exception as e:
        logger.error(f"Ontario OLA source failed: {e}")
        return []
