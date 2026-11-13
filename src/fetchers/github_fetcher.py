"""Fetcher for trending and high-velocity open-source repositories from GitHub Search API."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..config import GithubConfig
from ..models import RadarItem
from .base import BaseFetcher

logger = logging.getLogger("cortex_radar.github")


class GithubFetcher(BaseFetcher):
    """Fetches high-velocity and trending open-source AI and developer tool repositories."""

    GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

    def __init__(self, config: Optional[GithubConfig] = None):
        cfg = config or GithubConfig()
        super().__init__(
            name="GithubFetcher",
            timeout=cfg.timeout_seconds,
            max_retries=cfg.max_retries,
            backoff_factor=cfg.backoff_factor,
        )
        self.config = cfg

        # Support GITHUB_TOKEN or GH_TOKEN from environment for 5,000 req/hr rate limits
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
            logger.info("[GithubFetcher] Authenticated with GITHUB_TOKEN.")
        else:
            logger.info("[GithubFetcher] Running unauthenticated (standard rate limits apply).")

    def fetch(self, offline: bool = False) -> List[RadarItem]:
        """Query GitHub API for trending repositories or return offline fixtures."""
        if offline or not self.config.enabled:
            logger.info("[GithubFetcher] Offline mode active or source disabled. Loading local fixtures.")
            return self._get_offline_fixtures()

        all_items: Dict[str, RadarItem] = {}
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.config.query_window_days)).strftime("%Y-%m-%d")

        # Query across popular topics and star filters
        # e.g., "topic:llm pushed:>2026-11-06 stars:>25"
        selected_topics = self.config.topics[:4]
        for topic in selected_topics:
            query_str = f"topic:{topic} pushed:>{cutoff_date} stars:>{self.config.min_stars}"
            params: Dict[str, Any] = {
                "q": query_str,
                "sort": "stars",
                "order": "desc",
                "per_page": min(self.config.max_results, 30),
            }

            try:
                resp = self.request_with_retry(self.GITHUB_SEARCH_URL, params=params)
                data = resp.json()
                parsed = self.parse_response(data)
                for item in parsed:
                    if item.id not in all_items:
                        all_items[item.id] = item
            except Exception as e:
                logger.warning(f"[GithubFetcher] Search for topic '{topic}' encountered error: {e}")

        # If live search yielded results, return them
        if all_items:
            logger.info(f"[GithubFetcher] Successfully fetched {len(all_items)} unique repositories.")
            return list(all_items.values())

        logger.info("[GithubFetcher] No results or rate-limited. Falling back to offline fixtures.")
        return self._get_offline_fixtures()

    def parse_response(self, data: Dict[str, Any]) -> List[RadarItem]:
        """Convert GitHub search API response items into RadarItem instances."""
        items: List[RadarItem] = []
        raw_repos = data.get("items", [])

        for repo in raw_repos:
            try:
                full_name = repo.get("full_name", "")
                if not full_name:
                    continue

                item_id = f"github:{full_name}"
                html_url = repo.get("html_url", f"https://github.com/{full_name}")
                description = (repo.get("description") or "No description provided.").strip()
                stars = repo.get("stargazers_count", 0)
                forks = repo.get("forks_count", 0)
                language = repo.get("language") or "Other"
                topics = repo.get("topics", [])
                owner = (repo.get("owner") or {}).get("login", "")
                created_at = (repo.get("created_at") or "")[:10]
                pushed_at = (repo.get("pushed_at") or "")[:10]
                license_name = (repo.get("license") or {}).get("spdx_id", "")

                item = RadarItem(
                    id=item_id,
                    source="github",
                    title=full_name,
                    url=html_url,
                    authors_or_owner=owner,
                    summary=description,
                    tl_dr="",  # Synthesized by summarizer
                    primary_category="developer_tools",
                    category_badge="⚡ Dev Tools & Infra",
                    tags=topics[:5],
                    stars=stars,
                    forks=forks,
                    language=language,
                    published_date=created_at or pushed_at,
                    discovered_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    score=0.0,
                    metadata={
                        "pushed_at": pushed_at,
                        "open_issues": repo.get("open_issues_count", 0),
                        "license": license_name,
                        "topics": topics,
                    },
                )
                items.append(item)
            except Exception as err:
                logger.warning(f"[GithubFetcher] Skipped malformed repository: {err}")

        return items

    def _get_offline_fixtures(self) -> List[RadarItem]:
        """High-value realistic sample fixtures for testing and air-gapped environments."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [
            RadarItem(
                id="github:vllm-project/vllm",
                source="github",
                title="vllm-project/vllm",
                url="https://github.com/vllm-project/vllm",
                authors_or_owner="vllm-project",
                summary="A high-throughput and memory-efficient LLM serving engine featuring PagedAttention, speculative decoding, and chunked prefill.",
                tl_dr="Industry standard inference engine with PagedAttention and near-optimal GPU memory throughput.",
                primary_category="dev_tools_infra",
                category_badge="⚡ Dev Tools & Infra",
                tags=["llm", "inference", "paged-attention", "gpu", "cuda"],
                stars=42150,
                forks=6280,
                language="Python",
                published_date=today,
                discovered_date=today,
                score=9.9,
                metadata={"topics": ["llm", "inference", "cuda"], "license": "Apache-2.0"},
            ),
            RadarItem(
                id="github:browser-use/browser-use",
                source="github",
                title="browser-use/browser-use",
                url="https://github.com/browser-use/browser-use",
                authors_or_owner="browser-use",
                summary="Make websites accessible to AI agents. Open-source agentic browser automation framework connecting vision models to live web sessions.",
                tl_dr="Autonomous agent controller enabling vision LLMs to interact with live websites, fill forms, and execute complex workflows.",
                primary_category="agentic_systems",
                category_badge="🤖 Agents & Systems",
                tags=["agent", "browser-automation", "playwright", "vision-agent"],
                stars=34500,
                forks=3820,
                language="Python",
                published_date=today,
                discovered_date=today,
                score=9.7,
                metadata={"topics": ["agent", "browser", "automation"], "license": "MIT"},
            ),
            RadarItem(
                id="github:meta-llama/llama-stack",
                source="github",
                title="meta-llama/llama-stack",
                url="https://github.com/meta-llama/llama-stack",
                authors_or_owner="meta-llama",
                summary="Standardized, composable interfaces for building agentic AI applications with Llama models, memory providers, and tool runtimes.",
                tl_dr="Turnkey enterprise stack for orchestrating Llama reasoning, memory banks, safety guardrails, and tool evaluation.",
                primary_category="llm_reasoning",
                category_badge="🧠 LLMs & Reasoning",
                tags=["llama", "agentic", "memory", "safety", "standard"],
                stars=8900,
                forks=940,
                language="Python",
                published_date=today,
                discovered_date=today,
                score=9.3,
                metadata={"topics": ["llama", "agent", "rag"], "license": "MIT"},
            ),
        ]
