"""
Congress.gov API source collector.

Uses the summaries endpoint to find AI-related bills by searching
summary text and titles for AI keywords. This is more effective than
the bills endpoint, which doesn't support text search.

Requires a CONGRESS_GOV_API_KEY environment variable.
Get a free key at: https://api.congress.gov/sign-up/
"""

import os
import re
import time
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

API_BASE = "https://api.congress.gov/v3"
SOURCE_NAME = "Congress.gov"
JURISDICTION = "United States — Federal"
JURISDICTION_CODE = "US-FED"

# Keywords to search for in bill summaries and titles
AI_TERMS = [
    "artificial intelligence",
    "machine learning",
    "algorithmic",
    "automated decision",
    "facial recognition",
    "deepfake",
    "autonomous system",
    "neural network",
    "large language model",
    "foundation model",
    "predictive analytics",
    "generative ai",
    "deep learning",
    "computer vision",
    "robotic",
    "biometric",
]

# Map Congress.gov action descriptions to normalized statuses
STATUS_MAP = {
    "introduced": "Proposed",
    "referred to": "Proposed",
    "reported by committee": "In Progress",
    "passed house": "In Progress",
    "passed senate": "In Progress",
    "resolving differences": "In Progress",
    "to president": "In Progress",
    "became law": "In Force",
    "became public law": "In Force",
    "signed by president": "Passed/Adopted",
    "vetoed": "Withdrawn/Defeated",
    "failed": "Withdrawn/Defeated",
}

# Rate limiting
REQUEST_DELAY = 1.1  # seconds between requests
MAX_RETRIES = 3
BACKOFF_BASE = 2

# How far back to search (summaries endpoint requires date range)
SEARCH_START_DATE = "2023-01-01T00:00:00Z"
MAX_SUMMARIES = 5000  # safety cap


def _get_api_key():
    """Get API key from environment variable."""
    key = os.environ.get("CONGRESS_GOV_API_KEY")
    if not key:
        raise ValueError(
            "CONGRESS_GOV_API_KEY environment variable not set. "
            "Get a free key at https://api.congress.gov/sign-up/"
        )
    return key


def _make_request(session, url, params):
    """Make an API request with rate limiting and exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(REQUEST_DELAY)
            response = session.get(url, params=params, timeout=60)

            if response.status_code == 429:
                wait_time = BACKOFF_BASE ** (attempt + 1)
                logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** (attempt + 1))
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** (attempt + 1))

    return None


def _normalize_status(action_desc):
    """Map a Congress.gov action description to a normalized status."""
    if not action_desc:
        return "Proposed"
    action_lower = action_desc.lower()
    for key, status in STATUS_MAP.items():
        if key in action_lower:
            return status
    return "Proposed"


def _bill_type_path(bill_type):
    """Convert bill type code to the URL path segment used on congress.gov."""
    type_map = {
        "hr": "house-bill",
        "s": "senate-bill",
        "hjres": "house-joint-resolution",
        "sjres": "senate-joint-resolution",
        "hconres": "house-concurrent-resolution",
        "sconres": "senate-concurrent-resolution",
        "hres": "house-resolution",
        "sres": "senate-resolution",
    }
    return type_map.get(bill_type.lower(), "house-bill")


def _strip_html(text):
    """Remove HTML tags from summary text."""
    return re.sub(r"<[^>]+>", "", text)


def _is_ai_related(title, summary_html):
    """Check if a bill's title or summary mentions AI-related terms."""
    text = (title + " " + _strip_html(summary_html)).lower()
    return any(term in text for term in AI_TERMS)


def _build_entry(bill_info, summary_record):
    """Build an entry dict from a summary record and its bill info."""
    bill_type = bill_info.get("type", "HR").lower()
    bill_number = bill_info.get("number", "0")
    congress = bill_info.get("congress", "")
    title = bill_info.get("title", "No title")

    entry_id = f"congress-gov-{bill_type}{bill_number}-{congress}"

    # Build human-readable URL
    ordinal = _ordinal(congress)
    source_url = (
        f"https://www.congress.gov/bill/{ordinal}-congress/"
        f"{_bill_type_path(bill_type)}/{bill_number}"
    )

    # Clean summary text
    raw_summary = summary_record.get("text", "")
    clean_summary = _strip_html(raw_summary).strip()
    # Truncate very long summaries
    if len(clean_summary) > 1000:
        clean_summary = clean_summary[:997] + "..."

    action_desc = summary_record.get("actionDesc", "")
    action_date = summary_record.get("actionDate", "")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "id": entry_id,
        "title": title,
        "jurisdiction": JURISDICTION,
        "jurisdiction_code": JURISDICTION_CODE,
        "source_url": source_url,
        "source_name": SOURCE_NAME,
        "type": "legislation",
        "status": _normalize_status(action_desc),
        "domains": [],  # filled in by classify.py
        "date_introduced": action_date,  # best date we have from the summary
        "date_last_action": action_date,
        "last_action_summary": action_desc,
        "summary": clean_summary,
        "date_first_seen": now,
        "date_last_updated": now,
    }


def _ordinal(n):
    """Convert a congress number to ordinal string (e.g., 119 -> '119th')."""
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    suffix = "th" if 11 <= (n % 100) <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fetch():
    """
    Fetch AI-related bills from Congress.gov via the summaries endpoint.

    Strategy: paginate through recent bill summaries and keyword-filter
    for AI-related content. The summaries endpoint provides full text,
    making it much better for discovery than the bills endpoint.

    Returns a list of entry dicts, or an empty list on failure.
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        logger.error(str(e))
        return []

    session = requests.Session()
    session.headers.update({
        "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
        "Accept": "application/json",
    })

    # Track unique bills (a bill may appear in multiple summary versions)
    bills_found = {}
    offset = 0
    limit = 250  # max page size
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    while offset < MAX_SUMMARIES:
        logger.info(f"Fetching summaries (offset={offset})...")

        data = _make_request(session, f"{API_BASE}/summaries", {
            "api_key": api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "sort": "updateDate+desc",
            "fromDateTime": SEARCH_START_DATE,
            "toDateTime": now_iso,
        })

        if not data:
            logger.warning(f"No response at offset {offset}, stopping pagination")
            break

        summaries = data.get("summaries", [])
        if not summaries:
            break

        for record in summaries:
            bill_info = record.get("bill", {})
            title = bill_info.get("title", "")
            summary_text = record.get("text", "")

            if _is_ai_related(title, summary_text):
                # Use congress-type-number as dedup key
                bill_key = f"{bill_info.get('congress')}-{bill_info.get('type')}-{bill_info.get('number')}"
                if bill_key not in bills_found:
                    entry = _build_entry(bill_info, record)
                    if entry:
                        bills_found[bill_key] = entry

        # Check if there are more pages
        if not data.get("pagination", {}).get("next"):
            break
        offset += limit

    entries = list(bills_found.values())
    logger.info(f"Congress.gov: collected {len(entries)} AI-related bills from summaries")
    return entries
