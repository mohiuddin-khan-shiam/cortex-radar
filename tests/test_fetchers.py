"""Unit tests for arXiv and GitHub fetchers."""

from __future__ import annotations

import pytest
from src.config import ArxivConfig, GithubConfig
from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.fetchers.github_fetcher import GithubFetcher


SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.99999v1</id>
    <updated>2026-11-12T12:00:00Z</updated>
    <published>2026-11-12T12:00:00Z</published>
    <title>Scaling Test-Time Compute via Autonomous Monte Carlo Tree Search</title>
    <summary>We present a novel search algorithm that dynamically allocates inference compute.</summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <arxiv:primary_category term="cs.AI"/>
    <category term="cs.AI"/>
    <category term="cs.LG"/>
    <link title="pdf" href="https://arxiv.org/pdf/2501.99999.pdf" type="application/pdf"/>
  </entry>
</feed>
"""

SAMPLE_GITHUB_JSON = {
    "total_count": 1,
    "items": [
        {
            "full_name": "example-org/fast-agent",
            "html_url": "https://github.com/example-org/fast-agent",
            "description": "High-throughput asynchronous LLM agent orchestration framework.",
            "stargazers_count": 1540,
            "forks_count": 180,
            "language": "Python",
            "topics": ["agent", "llm", "async"],
            "created_at": "2026-11-01T10:00:00Z",
            "pushed_at": "2026-11-12T15:00:00Z",
            "open_issues_count": 12,
            "license": {"spdx_id": "MIT"},
            "owner": {"login": "example-org"},
        }
    ],
}


def test_arxiv_parse_feed():
    """Verify arXiv XML parsing extracts metadata and identifiers accurately."""
    fetcher = ArxivFetcher(ArxivConfig())
    items = fetcher.parse_feed(SAMPLE_ARXIV_XML)

    assert len(items) == 1
    item = items[0]
    assert item.id == "arxiv:2501.99999"
    assert item.source == "arxiv"
    assert "Scaling Test-Time Compute" in item.title
    assert "Alice Smith, Bob Jones" in item.authors_or_owner
    assert item.primary_category == "cs.AI"
    assert "cs.LG" in item.tags
    assert item.metadata.get("pdf_url") == "https://arxiv.org/pdf/2501.99999.pdf"


def test_arxiv_parse_empty_feed():
    """Verify parser handles empty or malformed feeds gracefully."""
    fetcher = ArxivFetcher(ArxivConfig())
    assert fetcher.parse_feed("") == []
    assert fetcher.parse_feed("<feed></feed>") == []


def test_arxiv_offline_fallback():
    """Verify offline fallback returns valid structured fixtures."""
    fetcher = ArxivFetcher(ArxivConfig())
    items = fetcher.fetch(offline=True)
    assert len(items) > 0
    for item in items:
        assert item.source == "arxiv"
        assert item.id.startswith("arxiv:")
        assert item.title
        assert item.url


def test_github_parse_response():
    """Verify GitHub Search JSON parsing extracts repository details."""
    fetcher = GithubFetcher(GithubConfig())
    items = fetcher.parse_response(SAMPLE_GITHUB_JSON)

    assert len(items) == 1
    item = items[0]
    assert item.id == "github:example-org/fast-agent"
    assert item.source == "github"
    assert item.title == "example-org/fast-agent"
    assert item.stars == 1540
    assert item.forks == 180
    assert item.language == "Python"
    assert "agent" in item.tags
    assert item.metadata.get("license") == "MIT"


def test_github_offline_fallback():
    """Verify GitHub offline fallback returns valid structured fixtures."""
    fetcher = GithubFetcher(GithubConfig())
    items = fetcher.fetch(offline=True)
    assert len(items) > 0
    for item in items:
        assert item.source == "github"
        assert item.id.startswith("github:")
        assert item.stars is not None
        assert item.stars > 0
