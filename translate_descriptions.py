#!/usr/bin/env python3
"""
translate_descriptions.py

Batch-translates English descriptions in existing YAML game files to Japanese
using Gemini 2.0 Flash, adding a `description_ja` field to each file.

Usage:
    python translate_descriptions.py              # process all files in game_data/
    python translate_descriptions.py --force      # re-translate even if description_ja exists
    python translate_descriptions.py --limit 10   # process only the first 10 files
    python translate_descriptions.py --dry-run    # show what would be translated, no writes
"""

import argparse
import os
import sys
import time
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

GAME_DATA_DIR = Path("game_data")


def parse_args():
    parser = argparse.ArgumentParser(description="Batch translate board game descriptions to Japanese")
    parser.add_argument("--force",   action="store_true", help="Re-translate even if description_ja already exists")
    parser.add_argument("--limit",   type=int, default=0, help="Max number of files to process (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated without writing files")
    parser.add_argument("--delay",   type=float, default=0.5, help="Seconds to wait between API calls (default: 0.5)")
    return parser.parse_args()


def load_yaml(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load {path.name}: {e}")
        return None


def save_yaml(path: Path, data: dict) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save {path.name}: {e}")
        return False


def main():
    args = parse_args()

    # Import translator (will fail clearly if google-genai is not installed)
    try:
        from src.api.gemini_translator import translate_description
    except ImportError as e:
        logger.error(f"Cannot import gemini_translator: {e}")
        logger.error("Run: pip install google-genai")
        sys.exit(1)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.error("GEMINI_API_KEY is not set in .env")
        sys.exit(1)

    # Collect YAML files
    yaml_files = sorted(GAME_DATA_DIR.glob("*.yaml"))
    if not yaml_files:
        logger.error(f"No YAML files found in {GAME_DATA_DIR}/")
        sys.exit(1)

    if args.limit > 0:
        yaml_files = yaml_files[: args.limit]

    logger.info(f"Found {len(yaml_files)} file(s) to process")

    translated = 0
    skipped    = 0
    failed     = 0

    for i, path in enumerate(yaml_files, 1):
        data = load_yaml(path)
        if data is None:
            failed += 1
            continue

        description = data.get("description", "")
        if not description:
            logger.info(f"[{i}/{len(yaml_files)}] {path.name}: no description — skip")
            skipped += 1
            continue

        if not args.force and data.get("description_ja"):
            logger.info(f"[{i}/{len(yaml_files)}] {path.name}: description_ja already exists — skip")
            skipped += 1
            continue

        if args.dry_run:
            logger.info(f"[{i}/{len(yaml_files)}] {path.name}: would translate ({len(description)} chars)")
            translated += 1
            continue

        logger.info(f"[{i}/{len(yaml_files)}] {path.name}: translating ({len(description)} chars) ...")
        try:
            result = translate_description(description)
        except Exception as e:
            logger.warning(f"  → translation error: {e}")
            failed += 1
            continue

        if not result:
            logger.warning(f"  → translation returned empty (description may already be Japanese)")
            skipped += 1
            continue

        # Insert description_ja immediately after description
        ordered = {}
        for k, v in data.items():
            ordered[k] = v
            if k == 'description':
                ordered['description_ja'] = result
        if 'description_ja' not in ordered:
            ordered['description_ja'] = result
        if save_yaml(path, ordered):
            logger.info(f"  → saved ({len(result)} chars)")
            translated += 1
        else:
            failed += 1

        # Polite delay between API calls
        if i < len(yaml_files):
            time.sleep(args.delay)

    logger.info(
        f"\nDone. Translated: {translated} | Skipped: {skipped} | Failed: {failed}"
    )


if __name__ == "__main__":
    main()
