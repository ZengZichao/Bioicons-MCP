"""Asynchronous client for fetching icon metadata from bioicons.com.

The client downloads the three JSON metadata files published by bioicons.com
(``icons.json``, ``categories.json``, ``authors.json``), parses them into typed
models and caches the result for the lifetime of the process.

Because bioicons.com is a static GitHub-Pages site the metadata changes
infrequently, so an in-memory cache with a configurable TTL is sufficient.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .constants import (
    AUTHORS_JSON_URL,
    CATEGORIES_JSON_URL,
    HTTP_TIMEOUT,
    ICONS_JSON_URL,
    SVG_URL_TEMPLATE,
)
from .models import IconInfo


class BioiconsClient:
    """Thin async wrapper around the bioicons.com JSON metadata endpoints.

    Parameters
    ----------
    client:
        An optional pre-configured :class:`httpx.AsyncClient`.  When ``None``
        a new client is created lazily on the first request.
    cache_ttl:
        Time-to-live for the in-memory metadata cache, in seconds.  The
        default of 1 hour strikes a good balance between freshness and
        politeness towards the upstream server.
    """

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        cache_ttl: float = 3600.0,
    ) -> None:
        self._client: httpx.AsyncClient | None = client
        self._owns_client = client is None
        self._cache_ttl = cache_ttl

        # Cache state ----------------------------------------------------
        self._icons: list[IconInfo] | None = None
        self._categories: list[str] | None = None
        self._authors: list[str] | None = None
        self._icons_by_name: dict[str, list[IconInfo]] | None = None
        self._icons_by_category: dict[str, list[IconInfo]] | None = None
        self._icons_by_license: dict[str, list[IconInfo]] | None = None
        self._cache_time: float = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        """Return the underlying HTTP client, creating it on demand."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(HTTP_TIMEOUT),
                follow_redirects=True,
                headers={"User-Agent": "bioicons-mcp/0.1.0"},
            )
            self._owns_client = True
        return self._client

    async def close(self) -> None:
        """Close the HTTP client if this instance owns it."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> BioiconsClient:
        await self._get_client()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------
    def _is_cache_valid(self) -> bool:
        """Return ``True`` when the cached metadata is still fresh."""
        return (
            self._icons is not None
            and self._categories is not None
            and (time.monotonic() - self._cache_time) < self._cache_ttl
        )

    def invalidate_cache(self) -> None:
        """Force the next metadata access to re-download from bioicons.com."""
        self._icons = None
        self._categories = None
        self._authors = None
        self._icons_by_name = None
        self._icons_by_category = None
        self._icons_by_license = None

    async def _ensure_loaded(self) -> None:
        """Download and parse metadata if the cache is stale."""
        if self._is_cache_valid():
            return

        client = await self._get_client()

        # Fetch all three JSON files in parallel for speed.
        import asyncio

        icons_resp, cat_resp, author_resp = await asyncio.gather(
            client.get(ICONS_JSON_URL),
            client.get(CATEGORIES_JSON_URL),
            client.get(AUTHORS_JSON_URL),
        )

        icons_resp.raise_for_status()
        cat_resp.raise_for_status()
        # authors.json is optional — tolerate failure.
        if author_resp.is_success:
            self._authors = author_resp.json()
        else:
            self._authors = []

        raw_icons: list[dict[str, Any]] = icons_resp.json()
        self._icons = [IconInfo.from_raw(item) for item in raw_icons]
        self._categories = cat_resp.json()

        # Build lookup indices ------------------------------------------
        by_name: dict[str, list[IconInfo]] = {}
        by_cat: dict[str, list[IconInfo]] = {}
        by_lic: dict[str, list[IconInfo]] = {}
        for icon in self._icons:
            by_name.setdefault(icon.name.lower(), []).append(icon)
            by_cat.setdefault(icon.category, []).append(icon)
            by_lic.setdefault(icon.license, []).append(icon)

        self._icons_by_name = by_name
        self._icons_by_category = by_cat
        self._icons_by_license = by_lic
        self._cache_time = time.monotonic()

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------
    async def get_categories(self) -> list[str]:
        """Return the list of bioicons.com category slugs."""
        await self._ensure_loaded()
        assert self._categories is not None
        return list(self._categories)

    async def get_all_icons(self) -> list[IconInfo]:
        """Return the full list of icons."""
        await self._ensure_loaded()
        assert self._icons is not None
        return list(self._icons)

    async def get_icons_by_category(self, category: str) -> list[IconInfo]:
        """Return every icon that belongs to *category*."""
        await self._ensure_loaded()
        assert self._icons_by_category is not None
        if category == "All_icons":
            assert self._icons is not None
            return list(self._icons)
        return list(self._icons_by_category.get(category, []))

    async def get_icons_by_license(self, license_slug: str) -> list[IconInfo]:
        """Return every icon published under *license_slug*."""
        await self._ensure_loaded()
        assert self._icons_by_license is not None
        return list(self._icons_by_license.get(license_slug, []))

    async def get_authors(self) -> list[str]:
        """Return the list of author slugs."""
        await self._ensure_loaded()
        assert self._authors is not None
        return list(self._authors)

    async def search_icons(
        self,
        query: str,
        *,
        category: str | None = None,
        license_slug: str | None = None,
        limit: int | None = None,
    ) -> list[IconInfo]:
        """Search icons by name, optionally filtered by category and licence.

        Parameters
        ----------
        query:
            Free-text search string.  The search is case-insensitive and
            every whitespace-separated token must be present in the icon name.
        category:
            Optional category slug filter.  ``"All_icons"`` or ``None``
            means no category filter.
        license_slug:
            Optional licence slug filter.
        limit:
            Maximum number of results to return.
        """
        await self._ensure_loaded()
        assert self._icons is not None

        # Start from a filtered slice.
        if category and category != "All_icons":
            assert self._icons_by_category is not None
            pool = self._icons_by_category.get(category, [])
        else:
            pool = self._icons

        if license_slug:
            pool = [icon for icon in pool if icon.license == license_slug]

        results = [icon for icon in pool if icon.matches_query(query)]

        if limit is not None and limit > 0:
            results = results[:limit]
        return results

    async def find_icon(self, name: str) -> list[IconInfo]:
        """Return all icons whose name matches *name* (case-insensitive)."""
        await self._ensure_loaded()
        assert self._icons_by_name is not None
        key = name.lower()
        # Try exact key first, then fall back to substring search.
        if key in self._icons_by_name:
            return list(self._icons_by_name[key])
        return [
            icon for icon in (self._icons or []) if key in icon.name.lower()
        ]

    # ------------------------------------------------------------------
    # SVG download
    # ------------------------------------------------------------------
    @staticmethod
    def build_svg_url(icon: IconInfo) -> str:
        """Return the direct download URL for an icon's SVG file."""
        return SVG_URL_TEMPLATE.format(
            license=icon.license,
            category=icon.category,
            author=icon.author,
            name=icon.name,
        )

    async def fetch_svg(self, icon: IconInfo) -> str:
        """Download the SVG content for *icon* and return it as text."""
        client = await self._get_client()
        url = self.build_svg_url(icon)
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
