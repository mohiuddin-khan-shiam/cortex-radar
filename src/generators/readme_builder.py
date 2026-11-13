"""Injects the latest daily discoveries into the repository's main README.md."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import OutputConfig, RadarAppConfig
from ..models import RadarItem

logger = logging.getLogger("cortex_radar.readme_builder")

START_MARKER = "<!-- START_DAILY_UPDATE -->"
END_MARKER = "<!-- END_DAILY_UPDATE -->"


class ReadmeBuilder:
    """Updates README.md between dynamic comment anchors."""

    def __init__(self, config: Optional[RadarAppConfig] = None, readme_path: str = "README.md"):
        self.readme_path = Path(readme_path)
        self.config = config or RadarAppConfig()

    def update_readme(self, top_items: List[RadarItem], date_str: Optional[str] = None) -> bool:
        """Inject top discoveries into README.md between comment markers."""
        if not self.readme_path.exists():
            logger.error(f"[ReadmeBuilder] README file not found at {self.readme_path}")
            return False

        today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        limit = self.config.output.readme_top_count
        selected = top_items[:limit]

        block_content = self.generate_markdown_block(selected, today)

        try:
            with open(self.readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            pattern = re.compile(
                f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
                re.DOTALL,
            )

            if pattern.search(content):
                new_content = pattern.sub(
                    f"{START_MARKER}\n{block_content}\n{END_MARKER}",
                    content,
                )
            else:
                logger.warning(
                    f"[ReadmeBuilder] Markers not found in {self.readme_path}. Appending to the end."
                )
                new_content = f"{content}\n\n{START_MARKER}\n{block_content}\n{END_MARKER}\n"

            with open(self.readme_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(
                f"[ReadmeBuilder] Successfully injected {len(selected)} items into {self.readme_path} for {today}."
            )
            return True

        except Exception as e:
            logger.error(f"[ReadmeBuilder] Failed to update README: {e}")
            return False

    def generate_markdown_block(self, items: List[RadarItem], date_str: str) -> str:
        """Render the Markdown table and badges for the README injection zone."""
        lines = [
            f"> 📡 **Latest Daily Radar Digest:** `{date_str}` | "
            f"[🌐 Open Interactive Web Dashboard]({self.config.dashboard_url}) | "
            f"[📁 Browse Archives](archives/)\n",
            "| # | Type | Discovery / Project | Category | Signal / Stars | Key Contribution (TL;DR) |",
            "| :---: | :---: | :--- | :--- | :---: | :--- |",
        ]

        for idx, item in enumerate(items, start=1):
            source_icon = "📄 Paper" if item.source == "arxiv" else "⭐ Repo"
            clean_title = item.clean_title_for_table()
            # Truncate title if extremely long
            if len(clean_title) > 65:
                display_title = f"[{clean_title[:62]}...]({item.url})"
            else:
                display_title = f"[{clean_title}]({item.url})"

            # Stars or Impact
            if item.source == "github" and item.stars is not None:
                if item.stars >= 1000:
                    star_str = f"⭐ {item.stars / 1000:.1f}k"
                else:
                    star_str = f"⭐ {item.stars}"
            else:
                star_str = f"⚡ {item.score:.1f}"

            badge = item.category_badge
            clean_tldr = item.clean_text_for_table(item.tl_dr or item.summary)
            if len(clean_tldr) > 130:
                clean_tldr = clean_tldr[:127] + "..."

            lines.append(
                f"| **{idx:02d}** | `{source_icon}` | **{display_title}** | {badge} | `{star_str}` | {clean_tldr} |"
            )

        lines.append("")
        lines.append(
            f"*Updated automatically every 24 hours at 02:00 UTC via [GitHub Actions](.github/workflows/daily_update.yml).*"
        )
        return "\n".join(lines)
