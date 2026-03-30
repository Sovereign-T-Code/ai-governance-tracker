"""
LEGISinfo (Canadian Parliament) source collector.

Scrapes parl.ca/legisinfo for AI-related federal bills.
This is a fragile scraper — CSS selectors may change with site redesigns.

LAST_VERIFIED_DATE: 2026-03-29
"""

import time
import logging
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCE_NAME = "LEGISinfo"
JURISDICTION = "Canada — Federal"
JURISDICTION_CODE = "CA-FED"

# LEGISinfo search URL
# The search supports keyword queries via the 'Text' parameter
SEARCH_URL = "https://www.parl.ca/legisinfo/en/bills"

# CSS selectors — update these if the site redesigns
SELECTORS = {
    "bill_row": "table tbody tr, .BillList .BillItem, .bill-item",
    "bill_link": "a[href*='bill']",
    "bill_title": "td:nth-child(2), .BillTitle, .bill-title",
    "bill_status": "td:nth-child(3), .BillStatus, .bill-status",
    "bill_number": "td:nth-child(1), .BillNumber, .bill-number",
}

# AI-related search terms
SEARCH_TERMS = [
    "artificial intelligence",
    "intelligence artificielle",
    "automated decision",
    "décision automatisée",
    "algorithmic",
    "facial recognition",
    "reconnaissance faciale",
    "machine learning",
]

REQUEST_DELAY = 2.0  # be polite to government servers

# Status mapping for Canadian federal bills
STATUS_MAP = {
    "first reading": "Proposed",
    "première lecture": "Proposed",
    "second reading": "In Progress",
    "deuxième lecture": "In Progress",
    "committee": "In Progress",
    "comité": "In Progress",
    "report stage": "In Progress",
    "étape du rapport": "In Progress",
    "third reading": "In Progress",
    "troisième lecture": "In Progress",
    "royal assent": "Passed/Adopted",
    "sanction royale": "Passed/Adopted",
    "defeated": "Withdrawn/Defeated",
    "withdrawn": "Withdrawn/Defeated",
    "retiré": "Withdrawn/Defeated",
}


def _normalize_status(status_text):
    """Map LEGISinfo status text to normalized status."""
    if not status_text:
        return "Proposed"
    lower = status_text.lower().strip()
    for key, val in STATUS_MAP.items():
        if key in lower:
            return val
    return "Proposed"


def fetch():
    """
    Fetch AI-related Canadian federal bills from LEGISinfo.

    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
            "Accept-Language": "en-CA,en;q=0.9,fr-CA;q=0.8",
        })

        all_bills = {}

        for term in SEARCH_TERMS:
            logger.info(f"Searching LEGISinfo for: {term}")
            time.sleep(REQUEST_DELAY)

            try:
                response = session.get(
                    SEARCH_URL,
                    params={"Text": term},
                    timeout=30,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.warning(f"LEGISinfo request failed for '{term}': {e}")
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Try to find bill listings using various selectors
            rows = []
            for selector in SELECTORS["bill_row"].split(", "):
                rows = soup.select(selector)
                if rows:
                    break

            logger.info(f"  Found {len(rows)} results for: {term}")

            for row in rows:
                try:
                    # Find the link to the bill
                    link_el = row.select_one("a[href]")
                    if not link_el:
                        continue

                    title = link_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://www.parl.ca{href}"

                    # Try to extract bill number from the text or URL
                    bill_text = row.get_text(" ", strip=True)
                    bill_number = ""
                    for part in bill_text.split():
                        if part.startswith(("C-", "S-", "c-", "s-")):
                            bill_number = part.upper()
                            break

                    # Extract status if available
                    status_text = ""
                    for selector in SELECTORS["bill_status"].split(", "):
                        status_el = row.select_one(selector)
                        if status_el:
                            status_text = status_el.get_text(strip=True)
                            break

                    # Build ID
                    bill_id = bill_number or title[:30].replace(" ", "-").lower()
                    doc_id = f"legisinfo-{bill_id}"

                    if doc_id in all_bills:
                        continue

                    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                    all_bills[doc_id] = {
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
                    logger.debug(f"Failed to parse LEGISinfo row: {e}")
                    continue

        entries = list(all_bills.values())
        logger.info(f"LEGISinfo: collected {len(entries)} bills")
        return entries

    except Exception as e:
        logger.error(f"LEGISinfo source failed: {e}")
        return []
