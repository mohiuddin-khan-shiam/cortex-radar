"""Configuration loader and schema validator for CortexRadar."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ArxivConfig:
    enabled: bool = True
    max_results: int = 35
    query_window_days: int = 3
    categories: List[str] = field(default_factory=lambda: ["cs.AI", "cs.LG", "cs.CL", "cs.CV"])
    sort_by: str = "submittedDate"
    sort_order: str = "descending"
    timeout_seconds: int = 25
    max_retries: int = 3
    backoff_factor: float = 2.0


@dataclass
class GithubConfig:
    enabled: bool = True
    max_results: int = 35
    min_stars: int = 25
    query_window_days: int = 7
    topics: List[str] = field(
        default_factory=lambda: [
            "llm",
            "machine-learning",
            "deep-learning",
            "generative-ai",
            "developer-tools",
        ]
    )
    languages: List[str] = field(
        default_factory=lambda: ["Python", "Rust", "TypeScript", "Go", "C++"]
    )
    timeout_seconds: int = 25
    max_retries: int = 3
    backoff_factor: float = 2.0


@dataclass
class CategoryRule:
    id: str
    name: str
    badge: str
    color: str = "#6366f1"
    keywords: List[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    readme_top_count: int = 10
    daily_digest_top_count: int = 25
    archive_dir: str = "archives"
    data_dir: str = "data"
    docs_dir: str = "docs"
    master_json: str = "data/master_dataset.json"
    master_csv: str = "data/master_dataset.csv"
    docs_json: str = "docs/data/master_dataset.json"


@dataclass
class RadarAppConfig:
    name: str = "CortexRadar"
    version: str = "1.0.0"
    tagline: str = "Autonomous AI Research & Open-Source Developer Tools Radar"
    timezone: str = "UTC"
    repo_url: str = "https://github.com/cortexradar/cortex-radar"
    dashboard_url: str = "https://cortexradar.github.io/cortex-radar/"
    arxiv: ArxivConfig = field(default_factory=ArxivConfig)
    github: GithubConfig = field(default_factory=GithubConfig)
    categories: List[CategoryRule] = field(default_factory=list)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(config_path: Optional[str | Path] = None) -> RadarAppConfig:
    """Load configuration from YAML file or return robust defaults if absent."""
    if config_path is None:
        # Default search paths
        candidates = [
            Path("config.yaml"),
            Path("config.yml"),
            Path(__file__).parent.parent / "config.yaml",
        ]
        target = next((c for c in candidates if c.exists()), None)
    else:
        target = Path(config_path)

    raw_data: Dict[str, Any] = {}
    if target and target.is_file():
        try:
            with open(target, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
                if isinstance(parsed, dict):
                    raw_data = parsed
        except Exception as e:
            print(f"[WARN] Failed to parse {target}: {e}. Falling back to default config.")

    # Radar block
    radar_raw = raw_data.get("radar", {})
    name = str(radar_raw.get("name", "CortexRadar"))
    version = str(radar_raw.get("version", "1.0.0"))
    tagline = str(radar_raw.get("tagline", "Autonomous AI Research & Open-Source Developer Tools Radar"))
    timezone = str(radar_raw.get("timezone", "UTC"))
    repo_url = str(radar_raw.get("repo_url", "https://github.com/cortexradar/cortex-radar"))
    dashboard_url = str(radar_raw.get("dashboard_url", "https://cortexradar.github.io/cortex-radar/"))

    # Sources block
    sources = raw_data.get("sources", {})
    ar_raw = sources.get("arxiv", {})
    arxiv_cfg = ArxivConfig(
        enabled=bool(ar_raw.get("enabled", True)),
        max_results=int(ar_raw.get("max_results", 35)),
        query_window_days=int(ar_raw.get("query_window_days", 3)),
        categories=list(ar_raw.get("categories", ["cs.AI", "cs.LG", "cs.CL", "cs.CV"])),
        sort_by=str(ar_raw.get("sort_by", "submittedDate")),
        sort_order=str(ar_raw.get("sort_order", "descending")),
        timeout_seconds=int(ar_raw.get("timeout_seconds", 25)),
        max_retries=int(ar_raw.get("max_retries", 3)),
        backoff_factor=float(ar_raw.get("backoff_factor", 2.0)),
    )

    gh_raw = sources.get("github", {})
    github_cfg = GithubConfig(
        enabled=bool(gh_raw.get("enabled", True)),
        max_results=int(gh_raw.get("max_results", 35)),
        min_stars=int(gh_raw.get("min_stars", 25)),
        query_window_days=int(gh_raw.get("query_window_days", 7)),
        topics=list(gh_raw.get("topics", ["llm", "machine-learning", "deep-learning", "generative-ai"])),
        languages=list(gh_raw.get("languages", ["Python", "Rust", "TypeScript", "Go"])),
        timeout_seconds=int(gh_raw.get("timeout_seconds", 25)),
        max_retries=int(gh_raw.get("max_retries", 3)),
        backoff_factor=float(gh_raw.get("backoff_factor", 2.0)),
    )

    # Categories block
    cat_rules: List[CategoryRule] = []
    for c in raw_data.get("categories", []):
        cat_rules.append(
            CategoryRule(
                id=str(c.get("id", "")),
                name=str(c.get("name", "")),
                badge=str(c.get("badge", "")),
                color=str(c.get("color", "#6366f1")),
                keywords=[k.lower() for k in c.get("keywords", [])],
            )
        )

    # Output block
    out_raw = raw_data.get("output", {})
    out_cfg = OutputConfig(
        readme_top_count=int(out_raw.get("readme_top_count", 10)),
        daily_digest_top_count=int(out_raw.get("daily_digest_top_count", 25)),
        archive_dir=str(out_raw.get("archive_dir", "archives")),
        data_dir=str(out_raw.get("data_dir", "data")),
        docs_dir=str(out_raw.get("docs_dir", "docs")),
        master_json=str(out_raw.get("master_json", "data/master_dataset.json")),
        master_csv=str(out_raw.get("master_csv", "data/master_dataset.csv")),
        docs_json=str(out_raw.get("docs_json", "docs/data/master_dataset.json")),
    )

    return RadarAppConfig(
        name=name,
        version=version,
        tagline=tagline,
        timezone=timezone,
        repo_url=repo_url,
        dashboard_url=dashboard_url,
        arxiv=arxiv_cfg,
        github=github_cfg,
        categories=cat_rules,
        output=out_cfg,
    )
