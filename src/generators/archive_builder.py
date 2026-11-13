"""Generates daily archival Markdown digests and maintains structured JSON/CSV datasets."""

from __future__ import annotations

import csv
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import RadarAppConfig
from ..models import RadarItem

logger = logging.getLogger("cortex_radar.archive_builder")


class ArchiveBuilder:
    """Creates daily markdown snapshots and updates master JSON and CSV databases."""

    def __init__(self, config: Optional[RadarAppConfig] = None):
        self.config = config or RadarAppConfig()
        self.archive_dir = Path(self.config.output.archive_dir)
        self.data_dir = Path(self.config.output.data_dir)
        self.docs_data_dir = Path(self.config.output.docs_dir) / "data"

        # Ensure directories exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.docs_data_dir.mkdir(parents=True, exist_ok=True)

    def build_daily_archive(self, items: List[RadarItem], date_str: Optional[str] = None) -> Path:
        """Create structured daily digest under archives/YYYY/MM/YYYY-MM-DD.md."""
        today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        year, month = today.split("-")[0], today.split("-")[1]
        target_dir = self.archive_dir / year / month
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{today}.md"

        papers = [item for item in items if item.source == "arxiv"]
        repos = [item for item in items if item.source == "github"]

        lines = [
            f"# 📡 CortexRadar Daily Digest: {today}",
            "",
            f"> Daily automated intelligence report tracking top AI/ML research breakthroughs and trending developer tools. Ingested at 02:00 UTC.",
            "",
            "## 📊 Executive Overview",
            f"- **Total Discoveries Tracked Today:** `{len(items)}`",
            f"- **ArXiv AI Preprints:** `{len(papers)}`",
            f"- **Trending Open-Source Repositories:** `{len(repos)}`",
            f"- **Web Dashboard:** [Live Interactive App]({self.config.dashboard_url})",
            "",
            "---",
            "",
            "## 🔬 Breakthrough Research Papers (arXiv)",
            "",
        ]

        if not papers:
            lines.append("*No new research papers met threshold criteria today.*")
        else:
            for p in papers:
                pdf_link = p.metadata.get("pdf_url")
                links = f"[arXiv Page]({p.url})"
                if pdf_link:
                    links += f" | [Direct PDF]({pdf_link})"

                lines.extend(
                    [
                        f"### [{p.title}]({p.url})",
                        f"- **Category:** {p.category_badge} (`{p.primary_category}`)",
                        f"- **Authors:** {p.authors_or_owner}",
                        f"- **Signal Score:** `{p.score:.1f}/10.0`",
                        f"- **Links:** {links}",
                        "",
                        f"**TL;DR:** {p.tl_dr}",
                        "",
                        "<details>",
                        "<summary><b>Abstract & Metadata</b></summary>",
                        "",
                        f"{p.summary}",
                        "",
                        f"*Tags:* `{'`, `'.join(p.tags)}`",
                        "</details>",
                        "",
                    ]
                )

        lines.extend(
            [
                "---",
                "",
                "## 🚀 Explosive Open-Source Repositories (GitHub)",
                "",
            ]
        )

        if not repos:
            lines.append("*No new open-source repositories met threshold criteria today.*")
        else:
            for r in repos:
                star_str = f"{r.stars:,}" if r.stars is not None else "N/A"
                fork_str = f"{r.forks:,}" if r.forks is not None else "N/A"
                license_str = r.metadata.get("license") or "Not specified"

                lines.extend(
                    [
                        f"### [{r.title}]({r.url})",
                        f"- **Category:** {r.category_badge}",
                        f"- **Language:** `{r.language or 'Other'}` | **License:** `{license_str}`",
                        f"- **Stars:** `⭐ {star_str}` | **Forks:** `🍴 {fork_str}` | **Signal Score:** `{r.score:.1f}/10.0`",
                        "",
                        f"**TL;DR:** {r.tl_dr}",
                        "",
                        "<details>",
                        "<summary><b>Description & Topics</b></summary>",
                        "",
                        f"{r.summary}",
                        "",
                        f"*Topics:* `{'`, `'.join(r.tags)}`",
                        "</details>",
                        "",
                    ]
                )

        lines.extend(
            [
                "---",
                "",
                "## 💾 Datasets & Raw Ingestion",
                "- Complete Master JSON: [`data/master_dataset.json`](../../data/master_dataset.json)",
                "- Tabular Master CSV: [`data/master_dataset.csv`](../../data/master_dataset.csv)",
                "",
                f"Generated by [{self.config.name}]({self.config.repo_url}) automation pipeline.",
            ]
        )

        with open(target_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"[ArchiveBuilder] Created daily archive at {target_file}")
        return target_file

    def save_master_datasets(self, all_items: List[RadarItem]) -> None:
        """Update master JSON and CSV files and synchronize to docs for GitHub Pages."""
        json_path = Path(self.config.output.master_json)
        csv_path = Path(self.config.output.master_csv)
        docs_json_path = Path(self.config.output.docs_json)

        # 1. Save Master JSON
        json_data = [item.to_dict() for item in all_items]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.info(f"[ArchiveBuilder] Saved {len(all_items)} records to {json_path}")

        # 2. Save Master CSV
        if all_items:
            fieldnames = list(all_items[0].to_csv_row().keys())
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in all_items:
                    writer.writerow(item.to_csv_row())
            logger.info(f"[ArchiveBuilder] Saved {len(all_items)} records to {csv_path}")

        # 3. Synchronize to docs/data/master_dataset.json for static site
        docs_json_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(json_path, docs_json_path)
        logger.info(f"[ArchiveBuilder] Synchronized dataset to {docs_json_path}")
