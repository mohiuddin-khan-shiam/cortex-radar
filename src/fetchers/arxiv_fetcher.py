"""Fetcher for arXiv preprints using the official arXiv API (Atom XML)."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import ArxivConfig
from ..models import RadarItem
from .base import BaseFetcher

logger = logging.getLogger("cortex_radar.arxiv")

# XML Namespaces used by arXiv API
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivFetcher(BaseFetcher):
    """Fetches trending and newly submitted AI/ML papers from arXiv."""

    ARXIV_API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, config: Optional[ArxivConfig] = None):
        cfg = config or ArxivConfig()
        super().__init__(
            name="ArxivFetcher",
            timeout=cfg.timeout_seconds,
            max_retries=cfg.max_retries,
            backoff_factor=cfg.backoff_factor,
        )
        self.config = cfg

    def fetch(self, offline: bool = False) -> List[RadarItem]:
        """Fetch latest papers from arXiv or return sample fixtures if offline."""
        if offline or not self.config.enabled:
            logger.info("[ArxivFetcher] Offline mode active or source disabled. Loading local fixtures.")
            return self._get_offline_fixtures()

        try:
            query_str = " OR ".join([f"cat:{cat}" for cat in self.config.categories])
            params: Dict[str, Any] = {
                "search_query": query_str,
                "sortBy": self.config.sort_by,
                "sortOrder": self.config.sort_order,
                "max_results": self.config.max_results,
            }

            resp = self.request_with_retry(self.ARXIV_API_URL, params=params)
            return self.parse_feed(resp.text)
        except Exception as e:
            logger.error(f"[ArxivFetcher] Live fetch failed: {e}. Falling back to sample fixtures.")
            return self._get_offline_fixtures()

    def parse_feed(self, xml_text: str) -> List[RadarItem]:
        """Parse arXiv Atom XML response into structured RadarItem list."""
        items: List[RadarItem] = []
        if not xml_text or not xml_text.strip():
            return items

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"[ArxivFetcher] XML parse error: {e}")
            return items

        entries = root.findall("atom:entry", ATOM_NS)
        logger.info(f"[ArxivFetcher] Parsed {len(entries)} raw entries from arXiv feed.")

        for entry in entries:
            try:
                # Raw ID format: http://arxiv.org/abs/2501.12345v1
                raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
                match = re.search(r"arxiv\.org/abs/([0-9]+\.[0-9]+|[\w\-]+/[0-9]+)", raw_id)
                clean_arxiv_id = match.group(1) if match else raw_id.split("/")[-1]
                item_id = f"arxiv:{clean_arxiv_id}"

                title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
                title = re.sub(r"\s+", " ", title).strip()

                summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
                summary = re.sub(r"\s+", " ", summary).strip()

                published_str = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
                updated_str = entry.findtext("atom:updated", default="", namespaces=ATOM_NS).strip()

                # Authors
                author_nodes = entry.findall("atom:author", ATOM_NS)
                author_names = [
                    a.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
                    for a in author_nodes
                    if a.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
                ]
                authors_str = ", ".join(author_names[:4])
                if len(author_names) > 4:
                    authors_str += f" et al. (+{len(author_names) - 4})"

                # Categories
                categories = []
                primary_cat_elem = entry.find("arxiv:primary_category", ATOM_NS)
                primary_category = (
                    primary_cat_elem.get("term", "cs.AI")
                    if primary_cat_elem is not None
                    else "cs.AI"
                )

                for cat in entry.findall("atom:category", ATOM_NS):
                    term = cat.get("term")
                    if term and term not in categories:
                        categories.append(term)

                # PDF Link
                pdf_url = ""
                for link in entry.findall("atom:link", ATOM_NS):
                    if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                        pdf_url = link.get("href", "")
                        break
                if not pdf_url and clean_arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{clean_arxiv_id}.pdf"

                abs_url = f"https://arxiv.org/abs/{clean_arxiv_id}" if clean_arxiv_id else raw_id

                item = RadarItem(
                    id=item_id,
                    source="arxiv",
                    title=title,
                    url=abs_url,
                    authors_or_owner=authors_str,
                    summary=summary,
                    tl_dr="",  # Will be generated by summarizer
                    primary_category=primary_category,
                    category_badge="📄 arXiv Paper",
                    tags=categories[:5],
                    published_date=published_str[:10] if published_str else "",
                    discovered_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    score=0.0,
                    metadata={
                        "arxiv_id": clean_arxiv_id,
                        "pdf_url": pdf_url,
                        "updated_date": updated_str,
                        "all_categories": categories,
                        "author_count": len(author_names),
                    },
                )
                items.append(item)
            except Exception as entry_err:
                logger.warning(f"[ArxivFetcher] Skipped malformed entry: {entry_err}")

        return items

    def _get_offline_fixtures(self) -> List[RadarItem]:
        """High-value realistic sample fixtures for testing and air-gapped environments."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [
            RadarItem(
                id="arxiv:2603.01892",
                source="arxiv",
                title="DeepSeek-R2: Reinforcement Learning for Test-Time Compute Scaling Across Long-Horizon Reasoning",
                url="https://arxiv.org/abs/2603.01892",
                authors_or_owner="DeepSeek-AI Team, Jianlin Su, et al.",
                summary="We explore end-to-end reinforcement learning scaling for open-weights reasoning architectures, demonstrating how pure policy gradient updates without supervised warm-up induce emergent multi-step deduction, self-verification, and dynamic backtrack search.",
                tl_dr="Demonstrates pure RL scaling for multi-step test-time reasoning without human cold-start data.",
                primary_category="cs.AI",
                category_badge="🧠 LLMs & Reasoning",
                tags=["cs.AI", "cs.LG", "cs.CL", "reasoning", "rl"],
                published_date=today,
                discovered_date=today,
                score=9.8,
                metadata={"arxiv_id": "2603.01892", "pdf_url": "https://arxiv.org/pdf/2603.01892.pdf"},
            ),
            RadarItem(
                id="arxiv:2603.02341",
                source="arxiv",
                title="OmniWorld-1: Native Video-Audio-Action Foundation Models for Real-World Physical Agents",
                url="https://arxiv.org/abs/2603.02341",
                authors_or_owner="Kaiming He, Alex Kendall, et al.",
                summary="Presents a unified autoregressive architecture modeling continuous robotic motor control, multi-camera video streams, and synchronized audio tokens simultaneously using hierarchical spatial-temporal latent quantization.",
                tl_dr="A unified multimodal foundation model predicting physical robotic actions directly from streaming sensory input.",
                primary_category="cs.RO",
                category_badge="👁️ Vision & Multimodal",
                tags=["cs.RO", "cs.CV", "multimodal", "robotics"],
                published_date=today,
                discovered_date=today,
                score=9.4,
                metadata={"arxiv_id": "2603.02341", "pdf_url": "https://arxiv.org/pdf/2603.02341.pdf"},
            ),
            RadarItem(
                id="arxiv:2603.04510",
                source="arxiv",
                title="FlashAttention-4: Sub-Warp Micro-Tiling and Asynchronous Tensor Memory Acceleration",
                url="https://arxiv.org/abs/2603.04510",
                authors_or_owner="Tri Dao, Albert Gu, et al.",
                summary="FlashAttention-4 achieves 93% theoretical FLOPS utilization on modern Blackwell and Hopper architectures by redesigning shared memory banking patterns and overlapping systolic MMA operations with asynchronous register loads.",
                tl_dr="Pushes attention kernel efficiency to 93% GPU utilization with sub-warp scheduling and zero memory overhead.",
                primary_category="cs.LG",
                category_badge="⚡ Dev Tools & Infra",
                tags=["cs.LG", "cs.DC", "cuda", "kernel", "optimization"],
                published_date=today,
                discovered_date=today,
                score=9.6,
                metadata={"arxiv_id": "2603.04510", "pdf_url": "https://arxiv.org/pdf/2603.04510.pdf"},
            ),
        ]
