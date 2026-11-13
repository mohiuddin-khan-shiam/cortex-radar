"""Deduplication and state management for CortexRadar datasets."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from ..models import RadarItem

logger = logging.getLogger("cortex_radar.deduplicator")


class Deduplicator:
    """Manages existing master records and deduplicates incoming feed items."""

    def __init__(self, master_json_path: str | Path):
        self.master_json_path = Path(master_json_path)
        self.existing_items: Dict[str, RadarItem] = self._load_existing()

    def _load_existing(self) -> Dict[str, RadarItem]:
        """Load existing records from master dataset file if present."""
        if not self.master_json_path.exists():
            return {}

        try:
            with open(self.master_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    items = {}
                    for entry in data:
                        if isinstance(entry, dict) and "id" in entry:
                            items[str(entry["id"])] = RadarItem.from_dict(entry)
                    logger.info(f"[Deduplicator] Loaded {len(items)} existing records from {self.master_json_path}")
                    return items
        except Exception as e:
            logger.warning(f"[Deduplicator] Could not parse {self.master_json_path}: {e}")

        return {}

    def deduplicate(
        self, incoming: List[RadarItem]
    ) -> Tuple[List[RadarItem], List[RadarItem], List[RadarItem]]:
        """
        Deduplicates incoming items against master dataset.

        Returns:
            Tuple of (new_discoveries, updated_existing, all_merged_items)
        """
        new_items: List[RadarItem] = []
        updated_items: List[RadarItem] = []
        seen_incoming_ids = set()

        # Deduplicate incoming items among themselves first
        unique_incoming: List[RadarItem] = []
        for item in incoming:
            if item.id not in seen_incoming_ids:
                seen_incoming_ids.add(item.id)
                unique_incoming.append(item)

        master_map = dict(self.existing_items)

        for item in unique_incoming:
            if item.id in master_map:
                existing = master_map[item.id]
                # Update dynamic fields (stars, forks, score, recent summary)
                if item.stars is not None:
                    existing.stars = item.stars
                if item.forks is not None:
                    existing.forks = item.forks
                if item.score > 0:
                    existing.score = item.score
                if item.tl_dr:
                    existing.tl_dr = item.tl_dr
                existing.metadata.update(item.metadata)
                updated_items.append(existing)
            else:
                master_map[item.id] = item
                new_items.append(item)

        # Merge and return all items sorted by score descending
        all_merged = list(master_map.values())
        all_merged.sort(key=lambda x: x.score, reverse=True)

        logger.info(
            f"[Deduplicator] Ingestion stats: {len(new_items)} new discoveries, "
            f"{len(updated_items)} updated metrics, {len(all_merged)} total in master database."
        )

        return new_items, updated_items, all_merged
