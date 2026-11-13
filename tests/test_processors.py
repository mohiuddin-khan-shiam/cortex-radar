"""Unit tests for processors: Deduplicator, Categorizer, and Summarizer."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from src.config import CategoryRule
from src.models import RadarItem
from src.processors.categorizer import Categorizer
from src.processors.deduplicator import Deduplicator
from src.processors.summarizer import Summarizer


@pytest.fixture
def sample_categories():
    return [
        CategoryRule(
            id="llm_reasoning",
            name="LLMs & Reasoning",
            badge="🧠 LLMs & Reasoning",
            keywords=["llm", "reasoning", "transformer", "chain of thought"],
        ),
        CategoryRule(
            id="dev_tools_infra",
            name="Developer Tools & Infra",
            badge="⚡ Dev Tools & Infra",
            keywords=["inference", "compiler", "cuda", "vllm", "kernel"],
        ),
    ]


def test_categorizer_matching(sample_categories):
    categorizer = Categorizer(sample_categories)

    item1 = RadarItem(
        id="arxiv:test1",
        source="arxiv",
        title="Chain of Thought Reasoning in Large Language Models",
        url="https://arxiv.org/abs/test1",
        authors_or_owner="Researcher A",
        summary="We study reasoning abilities in modern transformer architectures.",
        tags=["cs.AI"],
    )

    categorizer.classify_item(item1)
    categorizer.compute_score(item1)

    assert item1.primary_category == "llm_reasoning"
    assert "🧠" in item1.category_badge
    assert 6.0 <= item1.score <= 10.0


def test_categorizer_github_scoring(sample_categories):
    categorizer = Categorizer(sample_categories)

    item = RadarItem(
        id="github:org/repo",
        source="github",
        title="org/repo",
        url="https://github.com/org/repo",
        authors_or_owner="org",
        summary="Fast GPU inference engine and kernel accelerator.",
        stars=10000,
        forks=1200,
        language="Python",
        tags=["inference", "cuda"],
    )

    categorizer.classify_item(item)
    categorizer.compute_score(item)

    assert item.primary_category == "dev_tools_infra"
    assert item.score >= 8.5


def test_summarizer_extract_tldr():
    summarizer = Summarizer()

    item = RadarItem(
        id="arxiv:test2",
        source="arxiv",
        title="Advanced Neural Search",
        url="https://arxiv.org/abs/test2",
        authors_or_owner="Author B",
        summary="In recent years search has evolved. We introduce a fast vector index that reduces memory by 75%. Experiments confirm state-of-the-art results.",
        tags=[],
    )

    summarizer.summarize_item(item)
    assert "We introduce a fast vector index that reduces memory by 75%." in item.tl_dr


def test_deduplicator(tmp_path):
    master_file = tmp_path / "master.json"

    # Seed existing database
    existing = [
        {
            "id": "github:old/repo",
            "source": "github",
            "title": "old/repo",
            "url": "https://github.com/old/repo",
            "authors_or_owner": "old",
            "summary": "Existing repo",
            "stars": 100,
            "forks": 10,
            "score": 6.0,
            "discovered_date": "2026-11-01",
        }
    ]
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(existing, f)

    dedup = Deduplicator(master_file)

    incoming = [
        # Updated repo with new star count
        RadarItem(
            id="github:old/repo",
            source="github",
            title="old/repo",
            url="https://github.com/old/repo",
            authors_or_owner="old",
            summary="Existing repo updated",
            stars=150,
            forks=15,
            score=6.3,
        ),
        # Brand new repo
        RadarItem(
            id="github:new/repo",
            source="github",
            title="new/repo",
            url="https://github.com/new/repo",
            authors_or_owner="new",
            summary="New brand discovery",
            stars=500,
            forks=50,
            score=7.5,
        ),
    ]

    new_items, updated_items, all_items = dedup.deduplicate(incoming)

    assert len(new_items) == 1
    assert new_items[0].id == "github:new/repo"

    assert len(updated_items) == 1
    assert updated_items[0].stars == 150

    assert len(all_items) == 2
