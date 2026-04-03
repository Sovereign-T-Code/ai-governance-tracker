"""
laws_canada.py — Fetches status patches for known Canadian AI laws.

Returns a list of patch dicts, each containing:
  - "id": the law ID from laws.json
  - any fields that have changed (status, date_last_amended, etc.)

This source is conservative: if any check fails it is silently skipped
so it never causes the pipeline to crash.
"""

import logging
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get(url: str, **kwargs) -> requests.Response:
    return requests.get(url, timeout=REQUEST_TIMEOUT, **kwargs)


# ---------------------------------------------------------------------------
# 1. TBS Directive on Automated Decision-Making
#    Check the "Date modified" field on the TBS policy page.
# ---------------------------------------------------------------------------

TBS_DIRECTIVE_ID = "ca-fed-tbs-directive-automated-decision-2019"
TBS_DIRECTIVE_URL = "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32592"


def _check_tbs_directive() -> dict | None:
    try:
        resp = _get(TBS_DIRECTIVE_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # TBS pages include a "Date modified" meta tag or visible field
        date_modified = None

        # Try meta tag first
        meta = soup.find("meta", {"name": "dcterms.modified"})
        if meta and meta.get("content"):
            date_modified = meta["content"][:10]

        # Fallback: look for visible "Date modified" text
        if not date_modified:
            for tag in soup.find_all(string=re.compile(r"Date modified", re.I)):
                parent = tag.parent
                sibling = parent.find_next_sibling()
                if sibling:
                    text = sibling.get_text(strip=True)
                    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                    if m:
                        date_modified = m.group(1)
                        break

        if date_modified:
            return {
                "id": TBS_DIRECTIVE_ID,
                "date_last_amended": date_modified,
                "date_last_action": date_modified,
            }

    except Exception as e:
        logger.warning(f"TBS directive check failed: {e}")

    return None


# ---------------------------------------------------------------------------
# 2. AIDA / Bill C-27 — check LEGISinfo for re-introduction
#    Searches by title "Artificial Intelligence and Data Act"
# ---------------------------------------------------------------------------

AIDA_ID = "ca-fed-aida-c27-2022"
LEGISINFO_SEARCH_URL = "https://www.parl.ca/LegisInfo/en/search"


def _check_aida() -> dict | None:
    try:
        params = {
            "q": "Artificial Intelligence and Data Act",
            "type": "Bill",
            "parlSession": "current",
        }
        resp = _get(LEGISINFO_SEARCH_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for a result containing the bill title
        results = soup.find_all(class_=re.compile(r"bill|result", re.I))
        for result in results:
            text = result.get_text(" ", strip=True)
            if "artificial intelligence and data act" in text.lower():
                # Found a re-introduction — extract status
                status_map = {
                    "royal assent": "Passed/Adopted",
                    "in force": "In Force",
                    "third reading": "In Progress",
                    "second reading": "In Progress",
                    "first reading": "Proposed",
                    "withdrawn": "Withdrawn/Defeated",
                    "defeated": "Withdrawn/Defeated",
                }
                detected_status = None
                for keyword, mapped in status_map.items():
                    if keyword in text.lower():
                        detected_status = mapped
                        break

                patch = {"id": AIDA_ID, "date_last_action": TODAY}
                if detected_status:
                    patch["status"] = detected_status
                    patch["last_action_summary"] = (
                        f"Bill detected in current Parliament session (status: {detected_status})"
                    )
                return patch

    except Exception as e:
        logger.warning(f"AIDA/LEGISinfo check failed: {e}")

    return None


# ---------------------------------------------------------------------------
# 3. Quebec Law 25 — check Légis Québec for amendment dates
# ---------------------------------------------------------------------------

QC_LAW25_ID = "ca-qc-law25-2021"
QC_LAW25_URL = "https://www.legisquebec.gouv.qc.ca/en/document/cs/P-39.1"


def _check_qc_law25() -> dict | None:
    try:
        resp = _get(QC_LAW25_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Légis Québec pages show "Last amendment" or "Dernière modification"
        date_modified = None
        for tag in soup.find_all(string=re.compile(r"last amendment|dernière modification", re.I)):
            parent = tag.parent
            text = parent.get_text(" ", strip=True) + " "
            # Check next sibling too
            sibling = parent.find_next_sibling()
            if sibling:
                text += sibling.get_text(strip=True)
            m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            if m:
                date_modified = m.group(1)
                break

        if date_modified:
            return {
                "id": QC_LAW25_ID,
                "date_last_amended": date_modified,
                "date_last_action": date_modified,
            }

    except Exception as e:
        logger.warning(f"Quebec Law 25 check failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch() -> list[dict]:
    """
    Run all Canadian law checks. Returns list of patch dicts.
    Each patch has "id" plus any fields that have been updated.
    """
    patches = []

    patch = _check_tbs_directive()
    if patch:
        logger.info(f"TBS directive patch: {patch}")
        patches.append(patch)

    patch = _check_aida()
    if patch:
        logger.info(f"AIDA patch: {patch}")
        patches.append(patch)

    patch = _check_qc_law25()
    if patch:
        logger.info(f"Quebec Law 25 patch: {patch}")
        patches.append(patch)

    return patches
