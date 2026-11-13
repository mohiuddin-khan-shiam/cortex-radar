"""Base fetcher interface and resilient networking utilities."""

from __future__ import annotations

import abc
import logging
import random
import time
from typing import Any, Dict, List, Optional
import requests

from ..models import RadarItem

logger = logging.getLogger("cortex_radar.fetcher")


class BaseFetcher(abc.ABC):
    """Abstract base class for all data ingestion fetchers."""

    def __init__(self, name: str, timeout: int = 25, max_retries: int = 3, backoff_factor: float = 2.0):
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "CortexRadar/1.0 (+https://github.com/cortexradar/cortex-radar)",
                "Accept": "*/*",
            }
        )

    @abc.abstractmethod
    def fetch(self, offline: bool = False) -> List[RadarItem]:
        """Fetch items from the source. When offline=True, return fallback mock records."""
        raise NotImplementedError

    def request_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Execute HTTP GET with exponential backoff and jitter."""
        attempt = 0
        last_exception: Optional[Exception] = None

        req_headers = dict(self.session.headers)
        if headers:
            req_headers.update(headers)

        while attempt < self.max_retries:
            attempt += 1
            try:
                logger.info(f"[{self.name}] GET {url} (Attempt {attempt}/{self.max_retries})")
                response = self.session.get(url, params=params, headers=req_headers, timeout=self.timeout)

                # ArXiv or GitHub rate limit / transient errors: 429, 500, 502, 503, 504
                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        f"[{self.name}] Received HTTP {response.status_code}. Retrying..."
                    )
                    retry_after = response.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else (self.backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(sleep_time)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"[{self.name}] Request failed: {e}. Attempt {attempt}/{self.max_retries}")
                if attempt < self.max_retries:
                    sleep_time = (self.backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(sleep_time)

        if last_exception:
            raise last_exception
        raise RuntimeError(f"[{self.name}] Failed to fetch {url} after {self.max_retries} retries.")
