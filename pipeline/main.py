"""
AI Governance Tracker — Pipeline Orchestrator

Runs all data source collectors, classifies entries, deduplicates against
existing data, and writes updated JSON files. Sends email notification
only when new entries are detected.

Usage:
    python pipeline/main.py

Environment variables:
    CONGRESS_GOV_API_KEY — required for Congress.gov source
    GMAIL_USER — optional, for email notifications
    GMAIL_APP_PASSWORD — optional, for email notifications
    NOTIFY_EMAIL — optional, for email notifications
    LOG_LEVEL — optional, default INFO
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.classify import is_ai_relevant, classify_entry
from pipeline.notify import send_notification

# Source modules — each exposes a fetch() -> list[dict] function.
# Add new sources here as they're built.
from pipeline.sources import congress_gov
from pipeline.sources import federal_register
from pipeline.sources import eurlex
from pipeline.sources import legisinfo
from pipeline.sources import canada_gazette
from pipeline.sources import ontario_ola
from pipeline.sources import tbs_directive

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
ENTRIES_FILE = DATA_DIR / "entries.json"
META_FILE = DATA_DIR / "meta.json"
NEW_COUNT_FILE = DATA_DIR / "new_count.txt"

# All source modules to run. Each must have a fetch() function.
SOURCES = {
    "congress_gov": congress_gov,
    "federal_register": federal_register,
    "eurlex": eurlex,
    "legisinfo": legisinfo,
    "canada_gazette": canada_gazette,
    "ontario_ola": ontario_ola,
    "tbs_directive": tbs_directive,
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


def load_existing_entries():
    """Load the current entries.json, or return an empty list."""
    if not ENTRIES_FILE.exists():
        return []
    try:
        with open(ENTRIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        logger.warning("entries.json is not a list, starting fresh")
        return []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read entries.json: {e}")
        return []


def deduplicate(existing, new_entries):
    """
    Merge new entries into existing, deduplicating by ID.

    If a duplicate is found:
    - Keep the entry with the newer date_last_action
    - Preserve the original date_first_seen

    Returns (merged_list, truly_new_entries).
    """
    existing_map = {e["id"]: e for e in existing}
    truly_new = []

    for entry in new_entries:
        entry_id = entry["id"]

        if entry_id in existing_map:
            old = existing_map[entry_id]
            # Update if the new entry has a more recent action
            old_date = old.get("date_last_action", "")
            new_date = entry.get("date_last_action", "")
            if new_date > old_date:
                entry["date_first_seen"] = old.get("date_first_seen", entry["date_first_seen"])
                existing_map[entry_id] = entry
        else:
            truly_new.append(entry)
            existing_map[entry_id] = entry

    return list(existing_map.values()), truly_new


def run_sources():
    """
    Run all source collectors and return their entries + status info.

    Each source runs in a try/except so one failure never kills the pipeline.
    """
    all_entries = []
    sources_status = {}

    for name, module in SOURCES.items():
        logger.info(f"Running source: {name}")
        try:
            entries = module.fetch()
            count = len(entries)
            logger.info(f"  {name}: fetched {count} entries")
            all_entries.extend(entries)
            sources_status[name] = {
                "status": "ok",
                "last_run": datetime.now(timezone.utc).isoformat(),
                "entries_found": count,
            }
        except Exception as e:
            logger.error(f"  {name} failed: {e}")
            sources_status[name] = {
                "status": "error",
                "last_run": datetime.now(timezone.utc).isoformat(),
                "entries_found": 0,
                "error": str(e),
            }

    return all_entries, sources_status


def filter_and_classify(entries):
    """Filter for AI relevance and run classification on each entry."""
    classified = []
    for entry in entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")

        if is_ai_relevant(title, summary):
            classify_entry(entry)
            classified.append(entry)

    logger.info(f"Classification: {len(classified)}/{len(entries)} entries are AI-relevant")
    return classified


def save_data(entries, sources_status):
    """Write entries.json and meta.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Sort entries by date_last_action descending (most recent first)
    entries.sort(key=lambda e: e.get("date_last_action", ""), reverse=True)

    with open(ENTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    meta = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(entries),
        "sources_status": sources_status,
    }
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(entries)} entries to {ENTRIES_FILE}")


def main():
    """Main pipeline entry point."""
    logger.info("=" * 60)
    logger.info("AI Governance Tracker — Pipeline Run")
    logger.info("=" * 60)

    # Load existing data
    existing = load_existing_entries()
    logger.info(f"Loaded {len(existing)} existing entries")

    # Run all sources
    raw_entries, sources_status = run_sources()

    # Filter for AI relevance and classify
    classified = filter_and_classify(raw_entries)

    # Deduplicate against existing
    merged, new_entries = deduplicate(existing, classified)
    new_count = len(new_entries)
    logger.info(f"New entries: {new_count}")

    # Save updated data
    save_data(merged, sources_status)

    # Write new count for GitHub Actions to check
    with open(NEW_COUNT_FILE, "w") as f:
        f.write(str(new_count))

    # Send notification if there are new entries
    if new_count > 0:
        logger.info(f"Sending notification for {new_count} new entries")
        send_notification(new_entries)
    else:
        logger.info("No new entries — skipping notification")

    # Run laws pipeline (separate from main entries pipeline)
    try:
        from pipeline.laws_pipeline import run_laws_pipeline
        laws_changes = run_laws_pipeline()
        if laws_changes > 0:
            logger.info(f"Laws pipeline: {laws_changes} law records updated")
        else:
            logger.info("Laws pipeline: no changes")
    except Exception as e:
        logger.error(f"Laws pipeline failed: {e}")

    logger.info("Pipeline run complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
