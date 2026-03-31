"""
AI Governance Tracker — Historical Bulk Import

One-time script to backfill entries.json with AI-related legislation
from before the tracker was first set up. Uses the same source collectors
as the daily pipeline, but with an earlier start date.

Sources with date-range support: Congress.gov, Federal Register
Sources without date-range support: EUR-Lex, LEGISinfo, OLA, Canada Gazette, TBS
(these are covered by the daily pipeline going forward)

Usage:
    python pipeline/historical_import.py [--from-date YYYY-MM-DD]

Example:
    python pipeline/historical_import.py --from-date 2020-01-01
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is on the path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.sources import congress_gov, federal_register
from pipeline.classify import is_ai_relevant, classify_entry
from pipeline.main import load_existing_entries, deduplicate, save_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("historical_import")

DEFAULT_FROM_DATE = "2020-01-01"


def filter_and_classify(entries):
    """Filter for AI relevance and classify each entry."""
    classified = []
    for entry in entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        entry_type = entry.get("type", "legislation")
        if entry_type == "news" or is_ai_relevant(title, summary):
            classify_entry(entry)
            classified.append(entry)
    return classified


def main():
    parser = argparse.ArgumentParser(
        description="Backfill the AI governance tracker with historical legislation data."
    )
    parser.add_argument(
        "--from-date",
        default=DEFAULT_FROM_DATE,
        metavar="YYYY-MM-DD",
        help=f"Start date for historical search (default: {DEFAULT_FROM_DATE})",
    )
    args = parser.parse_args()
    from_date = args.from_date

    logger.info("=" * 60)
    logger.info("AI Governance Tracker — Historical Import")
    logger.info(f"Fetching entries from {from_date} onward")
    logger.info("=" * 60)

    # Load what's already in entries.json
    existing = load_existing_entries()
    logger.info(f"Loaded {len(existing)} existing entries")

    all_fetched = []

    # Congress.gov — full pagination with extended date range
    logger.info("Fetching historical Congress.gov bills...")
    congress_entries = congress_gov.fetch(from_date=f"{from_date}T00:00:00Z")
    logger.info(f"  Congress.gov: {len(congress_entries)} entries fetched")
    all_fetched.extend(congress_entries)

    # Federal Register — extended date range
    logger.info("Fetching historical Federal Register documents...")
    fed_entries = federal_register.fetch(from_date=from_date)
    logger.info(f"  Federal Register: {len(fed_entries)} entries fetched")
    all_fetched.extend(fed_entries)

    # Filter for AI relevance and classify domains
    classified = filter_and_classify(all_fetched)
    logger.info(f"Classified {len(classified)} AI-relevant entries")

    # Merge into existing data
    merged, truly_new = deduplicate(existing, classified)
    updated_count = len(classified) - len(truly_new)

    logger.info(f"Results:")
    logger.info(f"  {len(truly_new)} new entries added")
    logger.info(f"  {updated_count} existing entries updated")
    logger.info(f"  {len(merged)} total entries after import")

    # Save — build a minimal sources_status for the meta file
    now_iso = datetime.now(timezone.utc).isoformat()
    sources_status = {
        "congress_gov": {
            "status": "ok",
            "last_run": now_iso,
            "entries_found": len(congress_entries),
        },
        "federal_register": {
            "status": "ok",
            "last_run": now_iso,
            "entries_found": len(fed_entries),
        },
    }
    save_data(merged, sources_status)
    logger.info("Historical import complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
