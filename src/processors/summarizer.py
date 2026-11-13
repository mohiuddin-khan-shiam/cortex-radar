"""Text normalization and executive summary (TL;DR) synthesizer for CortexRadar."""

from __future__ import annotations

import logging
import re
from typing import List

from ..models import RadarItem

logger = logging.getLogger("cortex_radar.summarizer")


class Summarizer:
    """Cleans raw abstracts/descriptions and extracts executive TL;DR punchlines."""

    CONTRIBUTION_PATTERNS = [
        re.compile(r"(we introduce[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(we propose[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(we present[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(in this work[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(this paper presents[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(this paper proposes[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(we show that[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
        re.compile(r"(we demonstrate[^\.\!\?]+[\.\!\?])", re.IGNORECASE),
    ]

    def process_items(self, items: List[RadarItem]) -> List[RadarItem]:
        """Synthesize TL;DR and sanitize text for each item."""
        for item in items:
            self.summarize_item(item)
        return items

    def summarize_item(self, item: RadarItem) -> None:
        """Create a punchy TL;DR if not already provided or if placeholder."""
        # Sanitize summary first
        clean_summary = self.clean_text(item.summary)
        item.summary = clean_summary

        if item.tl_dr and len(item.tl_dr.strip()) > 10:
            item.tl_dr = self.clean_text(item.tl_dr)
            return

        if item.source == "github":
            # For GitHub repos, the description is already concise
            desc = clean_summary
            if desc.endswith("."):
                item.tl_dr = desc
            else:
                item.tl_dr = f"{desc}." if desc else "Trending open-source repository."
        else:
            # For arXiv, locate the key contribution sentence or extract the first two sentences
            item.tl_dr = self._extract_arxiv_tldr(clean_summary)

    def _extract_arxiv_tldr(self, text: str) -> str:
        """Find the core contribution claim in an academic abstract."""
        if not text:
            return "Breakthrough AI research preprint."

        # Search for key contribution phrases
        for pattern in self.CONTRIBUTION_PATTERNS:
            match = pattern.search(text)
            if match:
                sentence = match.group(1).strip()
                if 25 < len(sentence) < 180:
                    return sentence

        # Fallback to the first 1-2 sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) >= 2 and len(sentences[0]) < 80:
            combined = f"{sentences[0]} {sentences[1]}"
            return combined[:180] + ("..." if len(combined) > 180 else "")
        elif sentences:
            first = sentences[0]
            return first[:160] + ("..." if len(first) > 160 else "")

        return "Breakthrough AI research preprint."

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove redundant whitespace, citations, and markdown breaks."""
        if not text:
            return ""
        # Remove LaTeX math artifacts like $...$ if messy, or normalize
        cleaned = re.sub(r"\s+", " ", text).strip()
        # Remove citation brackets like [1], [2, 3]
        cleaned = re.sub(r"\[\d+(?:,\s*\d+)*\]", "", cleaned)
        return cleaned
