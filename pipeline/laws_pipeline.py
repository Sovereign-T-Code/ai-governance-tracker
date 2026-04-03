"""
Laws pipeline — separate from the main entries pipeline.

Loads data/laws.json, fetches status patches from laws_canada.py,
applies allowed updates, and saves the result.

Rules:
- manually_curated=True entries: only auto-update allowed fields
  (status, date_last_action, date_last_amended, last_action_summary)
- manually_curated=False entries: any field may be patched
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

LAWS_PATH = Path(__file__).parent.parent / "data" / "laws.json"

# Fields that may be auto-updated even on manually curated entries
ALLOWED_AUTO_UPDATE = {"status", "date_last_action", "date_last_amended", "last_action_summary"}


def load_laws() -> list[dict]:
    if not LAWS_PATH.exists():
        logger.warning("laws.json not found — starting with empty list")
        return []
    with open(LAWS_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_laws(laws: list[dict]) -> None:
    LAWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LAWS_PATH, "w", encoding="utf-8") as f:
        json.dump(laws, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(laws)} laws to {LAWS_PATH}")


def apply_patches(laws: list[dict], patches: list[dict]) -> tuple[list[dict], int]:
    """
    Apply patches to matching law records. Returns (updated_laws, change_count).

    Each patch must contain "id" plus the fields to update.
    """
    index = {law["id"]: law for law in laws}
    change_count = 0

    for patch in patches:
        law_id = patch.get("id")
        if not law_id:
            logger.warning(f"Patch missing 'id': {patch}")
            continue

        if law_id not in index:
            logger.info(f"Patch targets unknown law id '{law_id}' — skipping")
            continue

        law = index[law_id]
        is_curated = law.get("manually_curated", False)
        changed = False

        for field, value in patch.items():
            if field == "id":
                continue
            if is_curated and field not in ALLOWED_AUTO_UPDATE:
                logger.debug(
                    f"Skipping auto-update of '{field}' on curated law '{law_id}'"
                )
                continue
            if law.get(field) != value:
                logger.info(
                    f"Updating law '{law_id}': {field} = {value!r} (was {law.get(field)!r})"
                )
                law[field] = value
                changed = True

        if changed:
            law["date_last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            change_count += 1

    return list(index.values()), change_count


def run_laws_pipeline() -> int:
    """
    Run the full laws pipeline. Returns number of law records changed.
    """
    from pipeline.sources.laws_canada import fetch as fetch_canada_patches

    laws = load_laws()
    if not laws:
        logger.info("No laws to update")
        return 0

    patches = []
    try:
        canada_patches = fetch_canada_patches()
        logger.info(f"laws_canada: {len(canada_patches)} patches fetched")
        patches.extend(canada_patches)
    except Exception as e:
        logger.error(f"laws_canada fetch failed: {e}")

    if not patches:
        logger.info("No patches to apply")
        return 0

    updated_laws, change_count = apply_patches(laws, patches)

    if change_count > 0:
        save_laws(updated_laws)

    return change_count
