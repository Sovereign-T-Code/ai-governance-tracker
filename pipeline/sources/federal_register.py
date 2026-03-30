"""
Federal Register API source collector.

Free API, no key required.
Docs: https://www.federalregister.gov/developers/documentation/api/v1
"""

import time
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

API_BASE = "https://www.federalregister.gov/api/v1"
SOURCE_NAME = "Federal Register"
JURISDICTION = "United States — Federal"
JURISDICTION_CODE = "US-FED"

# Search terms for AI-related documents
SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "automated decision",
    "algorithmic",
    "facial recognition",
    "deepfake",
    "autonomous system",
]

# Map document types to normalized statuses
DOC_TYPE_STATUS = {
    "Rule": "In Force",
    "Proposed Rule": "Proposed",
    "Notice": "In Progress",
    "Presidential Document": "In Force",
}

REQUEST_DELAY = 0.5  # Federal Register is generous with rate limits


def fetch():
    """
    Fetch AI-related documents from the Federal Register API.

    Returns a list of entry dicts, or empty list on failure.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AIGovernanceTracker/1.0 (academic research)",
        })

        all_docs = {}

        for term in SEARCH_TERMS:
            logger.info(f"Searching Federal Register for: {term}")
            time.sleep(REQUEST_DELAY)

            params = {
                "conditions[term]": term,
                "conditions[publication_date][gte]": "2023-01-01",
                "per_page": 50,
                "order": "newest",
                "fields[]": [
                    "title", "document_number", "type", "abstract",
                    "html_url", "publication_date", "action",
                ],
            }

            try:
                response = session.get(
                    f"{API_BASE}/documents.json",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Federal Register request failed for '{term}': {e}")
                continue

            results = data.get("results", [])
            logger.info(f"  Found {len(results)} documents for: {term}")

            for doc in results:
                doc_num = doc.get("document_number", "")
                if not doc_num or doc_num in all_docs:
                    continue

                doc_type = doc.get("type", "Notice")
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                pub_date = doc.get("publication_date", "")

                abstract = doc.get("abstract", "") or ""
                if len(abstract) > 1000:
                    abstract = abstract[:997] + "..."

                all_docs[doc_num] = {
                    "id": f"fed-register-{doc_num}",
                    "title": doc.get("title", "No title"),
                    "jurisdiction": JURISDICTION,
                    "jurisdiction_code": JURISDICTION_CODE,
                    "source_url": doc.get("html_url", ""),
                    "source_name": SOURCE_NAME,
                    "type": "legislation",
                    "status": DOC_TYPE_STATUS.get(doc_type, "In Progress"),
                    "domains": [],  # filled by classify.py
                    "date_introduced": pub_date,
                    "date_last_action": pub_date,
                    "last_action_summary": doc.get("action", "") or f"Published as {doc_type}",
                    "summary": abstract or doc.get("title", ""),
                    "date_first_seen": now,
                    "date_last_updated": now,
                }

        entries = list(all_docs.values())
        logger.info(f"Federal Register: collected {len(entries)} AI-related documents")
        return entries

    except Exception as e:
        logger.error(f"Federal Register source failed: {e}")
        return []
