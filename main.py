#!/usr/bin/env python3
"""CortexRadar: Autonomous Daily AI, ML & Dev Tools Intelligence Radar.

Usage:
    python main.py
    python main.py --dry-run
    python main.py --offline
    python main.py --config custom_config.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import __version__
from src.config import load_config
from src.pipeline import RadarPipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI command line flags."""
    parser = argparse.ArgumentParser(
        description="CortexRadar: Autonomous AI, Machine Learning & Dev Tools Radar",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to custom config.yaml configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline and log results without writing files to disk",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode using pre-built fixtures (no network queries)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"CortexRadar v{__version__}",
        help="Print version information and exit",
    )
    return parser.parse_args()


def main() -> int:
    """Main execution entrypoint."""
    args = parse_args()

    print("=" * 70)
    print(f"📡 CortexRadar v{__version__} - Autonomous Daily Intelligence Engine")
    print("=" * 70)

    try:
        cfg = load_config(args.config)
        pipeline = RadarPipeline(config=cfg)
        result = pipeline.run(offline=args.offline, dry_run=args.dry_run)

        print("\n" + "=" * 70)
        print("✅ Pipeline execution completed successfully!")
        print(f"📅 Date:              {result.date_str}")
        print(f"📥 Total Ingested:    {result.total_fetched} items")
        print(f"✨ New Discoveries:   {result.new_discoveries}")
        print(f"🔄 Updated Metrics:   {result.updated_records}")
        print(f"📊 Master Database:   {result.master_count} total records")
        if result.archive_path:
            print(f"📁 Daily Archive:     {result.archive_path}")
        print("=" * 70 + "\n")
        return 0
    except KeyboardInterrupt:
        print("\n[INFO] Pipeline cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Pipeline encountered an unhandled exception: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
