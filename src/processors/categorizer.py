"""Automatic category classification and impact scoring for CortexRadar."""

from __future__ import annotations

import logging
import math
import re
from typing import List, Optional

from ..config import CategoryRule
from ..models import RadarItem

logger = logging.getLogger("cortex_radar.categorizer")


class Categorizer:
    """Classifies items into taxonomy categories and calculates impact velocity scores."""

    def __init__(self, categories: List[CategoryRule]):
        self.categories = categories

    def process_items(self, items: List[RadarItem]) -> List[RadarItem]:
        """Categorize and score each item in place, then sort by impact score."""
        for item in items:
            self.classify_item(item)
            self.compute_score(item)

        items.sort(key=lambda x: x.score, reverse=True)
        return items

    def classify_item(self, item: RadarItem) -> None:
        """Assign best-matching category and badge based on keyword occurrences."""
        corpus = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()

        best_category: Optional[CategoryRule] = None
        highest_score = 0

        for cat in self.categories:
            score = 0
            for kw in cat.keywords:
                # Whole-word or phrase matching
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, corpus))
                if matches > 0:
                    score += matches * 2

            if score > highest_score:
                highest_score = score
                best_category = cat

        if best_category and highest_score > 0:
            item.primary_category = best_category.id
            item.category_badge = best_category.badge
        else:
            # Fallback by source type
            if item.source == "arxiv":
                item.primary_category = "llm_reasoning"
                item.category_badge = "🧠 LLMs & Reasoning"
            else:
                item.primary_category = "dev_tools_infra"
                item.category_badge = "⚡ Dev Tools & Infra"

    def compute_score(self, item: RadarItem) -> None:
        """
        Compute normalized impact score (1.0 - 10.0).

        For GitHub repos: based on star count, forks, and topic density.
        For arXiv papers: based on author breadth, domain significance, and keyword signals.
        """
        score = 5.0

        if item.source == "github":
            stars = item.stars or 0
            forks = item.forks or 0

            # Logarithmic star scaling (e.g. 100 stars -> ~6.8, 1000 stars -> ~7.7, 10000+ -> 9.0+)
            if stars > 0:
                score = 5.0 + (math.log10(max(stars, 1)) * 0.92)
            if forks > 0:
                score += min(0.8, math.log10(max(forks, 1)) * 0.2)
            if item.language in ("Python", "Rust", "C++", "TypeScript"):
                score += 0.3
            if len(item.tags) >= 3:
                score += 0.2
        else:
            # ArXiv paper scoring: calibrated to match high-signal repositories
            score = 7.2
            auth_count = item.metadata.get("author_count", 1)
            score += min(1.0, auth_count * 0.18)

            # High-signal modern breakthrough keywords
            high_signal = [
                "reasoning", "reinforcement learning", "scaling", "foundation",
                "agent", "attention", "kernel", "benchmark", "multimodal",
                "diffusion", "transformer", "distillation", "alignment", "efficiency"
            ]
            title_summary = f"{item.title} {item.summary}".lower()
            keyword_matches = sum(1 for term in high_signal if term in title_summary)
            score += min(1.6, keyword_matches * 0.35)

        # Clamp score between 1.0 and 9.9
        item.score = round(max(1.0, min(9.9, score)), 1)
