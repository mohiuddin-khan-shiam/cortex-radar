# Contributing to CortexRadar

Thank you for your interest in contributing to **CortexRadar**! We are committed to building an open, transparent, and developer-friendly radar for the global AI and open-source community.

Whether you're fixing a bug, adding a new data source, improving the frontend dashboard, or refining the categorization algorithms, your help is welcome!

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Local Development Setup](#local-development-setup)
- [Adding a New Data Source](#adding-a-new-data-source)
- [Customizing Categories & Keywords](#customizing-categories--keywords)
- [Running Tests](#running-tests)
- [Commit & Pull Request Conventions](#commit--pull-request-conventions)

---

## Code of Conduct

This project adheres to the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---

## How to Contribute

1. **Check Existing Issues**: Before creating a new PR, check if an issue or discussion already exists.
2. **Open an Issue**: For major architecture changes or new fetchers, open an issue first to discuss your proposal.
3. **Fork & Branch**: Create a feature branch with a descriptive name (e.g., `feat/huggingface-papers-fetcher` or `fix/arxiv-rate-limit`).
4. **Submit a Pull Request**: Provide a clear summary of changes and reference any related issues.

---

## Local Development Setup

### 1. Prerequisites
- Python 3.10+
- `git`
- (Optional) A `GITHUB_TOKEN` in your environment to test GitHub API with higher rate limits (5,000 requests/hr vs. 60).

### 2. Setup Environment
```bash
# Clone your fork
git clone https://github.com/<your-username>/cortex-radar.git
cd cortex-radar

# Create virtual environment
python -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate
# Or on Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements.txt
```

### 3. Run the Pipeline Locally
```bash
# Run standard daily update pipeline
python main.py

# Run in dry-run mode (fetches and processes without writing files)
python main.py --dry-run

# Run in offline mode using mock fixtures (useful for air-gapped development)
python main.py --offline
```

---

## Adding a New Data Source

To add a new data source (e.g. HuggingFace Daily Papers, Papers With Code, PyPI Trending):

1. Create a new fetcher module in `src/fetchers/<source>_fetcher.py`.
2. Inherit from or follow the pattern of `BaseFetcher` (returning `List[RadarItem]`).
3. Add configuration schema in `config.yaml` under `sources.<source>`.
4. Register the fetcher in `src/pipeline.py`.
5. Add unit tests in `tests/test_fetchers.py`.

---

## Customizing Categories & Keywords

All taxonomy categories and matching keywords live inside `config.yaml`.
You can adjust keyword lists, add new categories, or change threshold parameters without touching any Python code.

---

## Running Tests

We maintain high unit test coverage with `pytest`:

```bash
pytest
```

To run with verbose output:
```bash
pytest -v --tb=short
```

---

## Commit & Pull Request Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` A new feature or capability (e.g., `feat(fetcher): add HuggingFace papers support`)
- `fix:` A bug fix (e.g., `fix(arxiv): handle 503 retry backoff with jitter`)
- `docs:` Documentation updates
- `style:` Code style / formatting changes (no functional impact)
- `refactor:` Code refactoring that neither fixes a bug nor adds a feature
- `test:` Adding or updating unit tests
- `chore:` Maintenance tasks, dependency updates, CI workflows

Thank you for helping keep CortexRadar sharp and useful for everyone!
