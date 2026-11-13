"""Unit tests for generators: ReadmeBuilder, ArchiveBuilder, and SiteBuilder."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from src.config import OutputConfig, RadarAppConfig
from src.generators.archive_builder import ArchiveBuilder
from src.generators.readme_builder import END_MARKER, START_MARKER, ReadmeBuilder
from src.generators.site_builder import SiteBuilder
from src.models import RadarItem


@pytest.fixture
def sample_items():
    return [
        RadarItem(
            id="arxiv:2603.01892",
            source="arxiv",
            title="DeepSeek-R2: Reinforcement Learning for Test-Time Compute",
            url="https://arxiv.org/abs/2603.01892",
            authors_or_owner="DeepSeek-AI",
            summary="We explore end-to-end RL scaling.",
            tl_dr="Demonstrates pure RL scaling for multi-step test-time reasoning.",
            primary_category="llm_reasoning",
            category_badge="🧠 LLMs & Reasoning",
            tags=["reasoning", "rl"],
            score=9.8,
            published_date="2026-11-13",
            discovered_date="2026-11-13",
        ),
        RadarItem(
            id="github:vllm-project/vllm",
            source="github",
            title="vllm-project/vllm",
            url="https://github.com/vllm-project/vllm",
            authors_or_owner="vllm-project",
            summary="A high-throughput LLM serving engine.",
            tl_dr="PagedAttention inference engine with near-optimal GPU memory throughput.",
            primary_category="dev_tools_infra",
            category_badge="⚡ Dev Tools & Infra",
            tags=["inference", "cuda"],
            stars=42000,
            forks=6000,
            language="Python",
            score=9.9,
            published_date="2026-11-13",
            discovered_date="2026-11-13",
        ),
    ]


def test_readme_builder_injection(tmp_path, sample_items):
    readme_path = tmp_path / "README.md"
    initial_text = f"""# Test Project

Intro paragraph here.

{START_MARKER}
Old content to be replaced.
{END_MARKER}

Footer paragraph that must be preserved.
"""
    readme_path.write_text(initial_text, encoding="utf-8")

    cfg = RadarAppConfig()
    builder = ReadmeBuilder(config=cfg, readme_path=str(readme_path))

    success = builder.update_readme(sample_items, date_str="2026-11-13")
    assert success is True

    result_text = readme_path.read_text(encoding="utf-8")

    # Assert old content was replaced
    assert "Old content to be replaced" not in result_text
    # Assert headers and footers are preserved
    assert "# Test Project" in result_text
    assert "Footer paragraph that must be preserved." in result_text
    # Assert table contents exist
    assert "DeepSeek-R2" in result_text
    assert "vllm-project/vllm" in result_text
    assert "2026-11-13" in result_text


def test_archive_builder(tmp_path, sample_items):
    cfg = RadarAppConfig(
        output=OutputConfig(
            archive_dir=str(tmp_path / "archives"),
            data_dir=str(tmp_path / "data"),
            docs_dir=str(tmp_path / "docs"),
            master_json=str(tmp_path / "data" / "master_dataset.json"),
            master_csv=str(tmp_path / "data" / "master_dataset.csv"),
            docs_json=str(tmp_path / "docs" / "data" / "master_dataset.json"),
        )
    )

    builder = ArchiveBuilder(config=cfg)

    # 1. Build daily archive
    archive_file = builder.build_daily_archive(sample_items, date_str="2026-11-13")
    assert archive_file.exists()
    content = archive_file.read_text(encoding="utf-8")
    assert "CortexRadar Daily Digest: 2026-11-13" in content
    assert "DeepSeek-R2" in content
    assert "vllm-project/vllm" in content

    # 2. Save master datasets
    builder.save_master_datasets(sample_items)
    json_path = Path(cfg.output.master_json)
    csv_path = Path(cfg.output.master_csv)
    docs_json_path = Path(cfg.output.docs_json)

    assert json_path.exists()
    assert csv_path.exists()
    assert docs_json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 2

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["id"] == "arxiv:2603.01892"


def test_site_builder(tmp_path):
    cfg = RadarAppConfig(
        output=OutputConfig(
            docs_dir=str(tmp_path / "docs"),
        )
    )
    builder = SiteBuilder(config=cfg)
    builder.build_site()

    docs = Path(cfg.output.docs_dir)
    assert (docs / "index.html").exists()
    assert (docs / "style.css").exists()
    assert (docs / "app.js").exists()

    html_content = (docs / "index.html").read_text(encoding="utf-8")
    assert "Cortex" in html_content
    assert "Radar" in html_content
