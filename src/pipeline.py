"""CortexRadar Master Pipeline: Orchestrates ingestion, processing, and generation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import RadarAppConfig, load_config
from .fetchers import ArxivFetcher, GithubFetcher
from .generators import ArchiveBuilder, ReadmeBuilder, SiteBuilder
from .models import RadarItem
from .processors import Categorizer, Deduplicator, Summarizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cortex_radar.pipeline")


class PipelineResult:
    """Carries output statistics from a pipeline run."""

    def __init__(
        self,
        date_str: str,
        total_fetched: int,
        new_discoveries: int,
        updated_records: int,
        master_count: int,
        archive_path: Optional[Path],
    ):
        self.date_str = date_str
        self.total_fetched = total_fetched
        self.new_discoveries = new_discoveries
        self.updated_records = updated_records
        self.master_count = master_count
        self.archive_path = archive_path


class RadarPipeline:
    """End-to-end autonomous intelligence pipeline for CortexRadar."""

    def __init__(self, config: Optional[RadarAppConfig] = None):
        self.config = config or load_config()

        # Initialize components
        self.arxiv_fetcher = ArxivFetcher(self.config.arxiv)
        self.github_fetcher = GithubFetcher(self.config.github)
        self.deduplicator = Deduplicator(self.config.output.master_json)
        self.categorizer = Categorizer(self.config.categories)
        self.summarizer = Summarizer()
        self.readme_builder = ReadmeBuilder(self.config)
        self.archive_builder = ArchiveBuilder(self.config)
        self.site_builder = SiteBuilder(self.config)

    def run(self, offline: bool = False, dry_run: bool = False) -> PipelineResult:
        """Execute the full radar ingestion and generation workflow."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info(f"=== Starting CortexRadar Pipeline [{today}] (offline={offline}, dry_run={dry_run}) ===")

        # Step 1: Fetch raw feeds
        raw_items: List[RadarItem] = []

        if self.config.arxiv.enabled:
            logger.info("Fetching arXiv AI/ML preprints...")
            arxiv_items = self.arxiv_fetcher.fetch(offline=offline)
            raw_items.extend(arxiv_items)

        if self.config.github.enabled:
            logger.info("Fetching trending GitHub repositories...")
            github_items = self.github_fetcher.fetch(offline=offline)
            raw_items.extend(github_items)

        logger.info(f"Total raw items gathered from sources: {len(raw_items)}")

        # Step 2: Categorization & Scoring
        logger.info("Classifying taxonomy categories and computing impact scores...")
        categorized_items = self.categorizer.process_items(raw_items)

        # Step 3: Summarization & TL;DR Synthesis
        logger.info("Normalizing text and synthesizing executive summaries...")
        processed_items = self.summarizer.process_items(categorized_items)

        # Step 4: Deduplication & State Merging
        logger.info("Deduplicating items against master dataset...")
        new_items, updated_items, all_master_items = self.deduplicator.deduplicate(processed_items)

        archive_file: Optional[Path] = None

        if not dry_run:
            # Step 5: Save Datasets
            logger.info("Writing master JSON, CSV, and GitHub Pages data mirrors...")
            self.archive_builder.save_master_datasets(all_master_items)

            # Step 6: Generate Daily Archival Markdown
            logger.info(f"Generating daily digest archive for {today}...")
            # Balance highlights between papers and repositories
            papers = [i for i in processed_items if i.source == "arxiv"]
            repos = [i for i in processed_items if i.source == "github"]
            papers.sort(key=lambda x: x.score, reverse=True)
            repos.sort(key=lambda x: x.score, reverse=True)

            archive_items = papers[:15] + repos[:15]
            archive_file = self.archive_builder.build_daily_archive(archive_items, today)

            # Step 7: Update Main README.md (Balanced Top 10: 5 papers + 5 repos, sorted by score)
            logger.info("Injecting top discoveries table into README.md...")
            readme_items = papers[:5] + repos[:5]
            readme_items.sort(key=lambda x: x.score, reverse=True)
            self.readme_builder.update_readme(readme_items, today)

            # Step 8: Build / Refresh Web Dashboard Assets
            logger.info("Building static dashboard files (docs/)...")
            self.site_builder.build_site()
        else:
            logger.info("[Dry Run] Skipped writing files to disk.")

        logger.info(
            f"=== CortexRadar Pipeline Finished. {len(new_items)} new discoveries, "
            f"{len(all_master_items)} total cataloged. ==="
        )

        return PipelineResult(
            date_str=today,
            total_fetched=len(raw_items),
            new_discoveries=len(new_items),
            updated_records=len(updated_items),
            master_count=len(all_master_items),
            archive_path=archive_file,
        )
