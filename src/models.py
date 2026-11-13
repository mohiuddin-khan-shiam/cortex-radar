"""Data models for CortexRadar items, classifications, and daily summaries."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RadarItem:
    """Represents a discovered paper, repository, or tool."""

    id: str  # Unique identifier, e.g. "arxiv:2401.12345" or "github:user/repo"
    source: str  # "arxiv" or "github"
    title: str
    url: str
    authors_or_owner: str
    summary: str
    tl_dr: str = ""
    primary_category: str = "general_ai"
    category_badge: str = "🤖 General AI"
    tags: List[str] = field(default_factory=list)
    stars: Optional[int] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    published_date: str = ""  # ISO 8601 or YYYY-MM-DD
    discovered_date: str = ""  # Date CortexRadar ingested it (YYYY-MM-DD)
    score: float = 0.0  # Computed impact / velocity score
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the radar item into a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RadarItem:
        """Instantiate a RadarItem from a dictionary with backward-compatible defaults."""
        return cls(
            id=str(data.get("id", "")),
            source=str(data.get("source", "unknown")),
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            authors_or_owner=str(data.get("authors_or_owner", "")),
            summary=str(data.get("summary", "")),
            tl_dr=str(data.get("tl_dr", "")),
            primary_category=str(data.get("primary_category", "general_ai")),
            category_badge=str(data.get("category_badge", "🤖 General AI")),
            tags=list(data.get("tags", [])),
            stars=data.get("stars"),
            forks=data.get("forks"),
            language=data.get("language"),
            published_date=str(data.get("published_date", "")),
            discovered_date=str(data.get("discovered_date", "")),
            score=float(data.get("score", 0.0)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_csv_row(self) -> Dict[str, Any]:
        """Format item for tabular master CSV export."""
        return {
            "id": self.id,
            "source": self.source,
            "title": self.clean_title_for_table(),
            "url": self.url,
            "authors_or_owner": self.authors_or_owner,
            "primary_category": self.primary_category,
            "category_badge": self.category_badge,
            "tags": ";".join(self.tags),
            "stars": self.stars if self.stars is not None else "",
            "forks": self.forks if self.forks is not None else "",
            "language": self.language or "",
            "published_date": self.published_date,
            "discovered_date": self.discovered_date,
            "score": round(self.score, 2),
            "tl_dr": self.clean_text_for_table(self.tl_dr),
        }

    def clean_title_for_table(self) -> str:
        """Sanitize title for Markdown/CSV tables (strip linebreaks and pipes)."""
        clean = re.sub(r"\s+", " ", self.title).strip()
        return clean.replace("|", "/")

    @staticmethod
    def clean_text_for_table(text: str) -> str:
        """Sanitize text block for table cells."""
        clean = re.sub(r"\s+", " ", text).strip()
        return clean.replace("|", "/")
