"""Typed data models for icon metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IconInfo:
    """A single icon entry as returned by the bioicons.com metadata endpoint.

    Attributes
    ----------
    name:
        The icon file name *without* the ``.svg`` extension, e.g. ``"alanine"``.
    category:
        The bioicons.com category slug, e.g. ``"Amino-Acids"``.
    license:
        The licence slug in lower case, e.g. ``"cc-0"``, ``"mit"``, ``"bsd"``.
    author:
        The author slug used in the URL path, e.g. ``"B--Gideon-Bergheim"``.
    """

    name: str
    category: str
    license: str
    author: str

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> IconInfo:
        """Build an :class:`IconInfo` from a raw JSON object.

        Missing fields default to an empty string so that a slightly
        malformed entry never crashes the whole server.
        """
        return cls(
            name=str(raw.get("name", "")),
            category=str(raw.get("category", "")),
            license=str(raw.get("license", "")),
            author=str(raw.get("author", "")),
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, str]:
        """Return a plain ``dict`` suitable for JSON serialisation."""
        return asdict(self)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def matches_query(self, query: str) -> bool:
        """Return ``True`` when *query* appears in the icon name (case-insensitive).

        The query is split on whitespace and **every** token must be present —
        this mirrors the search behaviour of the bioicons.com website.
        """
        if not query.strip():
            return True
        name_lower = self.name.lower()
        return all(token in name_lower for token in query.lower().split())
