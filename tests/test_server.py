"""Unit tests for the Bioicons MCP server.

These tests do **not** make real HTTP requests.  Instead they patch the
:class:`~bioicons_mcp.client.BioiconsClient` with in-memory data so the test
suite is fast and deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from bioicons_mcp.client import BioiconsClient
from bioicons_mcp.constants import SVG_URL_TEMPLATE
from bioicons_mcp.models import IconInfo
from bioicons_mcp.server import (
    _tool_download_icon,
    _tool_get_icon,
    _tool_get_icon_info,
    _tool_list_categories,
    _tool_search_icons,
    create_server,
)

# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------

SAMPLE_ICONS: list[dict[str, str]] = [
    {"name": "alanine", "category": "Amino-Acids", "license": "cc-0", "author": "B--Gideon-Bergheim"},
    {"name": "alanine_chem", "category": "Amino-Acids", "license": "cc-0", "author": "B--Gideon-Bergheim"},
    {"name": "Mouse", "category": "Animals", "license": "cc-0", "author": "Ben-Murrell"},
    {"name": "PyTorch", "category": "Machine_Learning", "license": "bsd", "author": "Facebook"},
    {"name": "Jupyter", "category": "Machine_Learning", "license": "bsd", "author": "Jupyter"},
    {"name": "Tensorflow", "category": "Machine_Learning", "license": "bsd", "author": "Google"},
]

SAMPLE_CATEGORIES: list[str] = [
    "All_icons",
    "Amino-Acids",
    "Animals",
    "Machine_Learning",
]

SAMPLE_AUTHORS: list[str] = ["B--Gideon-Bergheim", "Ben-Murrell", "Facebook"]

FAKE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_icons() -> list[IconInfo]:
    return [IconInfo.from_raw(item) for item in SAMPLE_ICONS]


@pytest.fixture
def patched_client(mock_icons: list[IconInfo]) -> BioiconsClient:
    """Return a :class:`BioiconsClient` whose HTTP calls are stubbed."""
    client = BioiconsClient()
    # Inject data directly into the cache to avoid network access.
    client._icons = mock_icons  # type: ignore[attr-defined]
    client._categories = SAMPLE_CATEGORIES  # type: ignore[attr-defined]
    client._authors = SAMPLE_AUTHORS  # type: ignore[attr-defined]
    client._icons_by_name = {}  # type: ignore[attr-defined]
    client._icons_by_category = {}  # type: ignore[attr-defined]
    client._icons_by_license = {}  # type: ignore[attr-defined]
    for icon in mock_icons:
        client._icons_by_name.setdefault(icon.name.lower(), []).append(icon)  # type: ignore[attr-defined]
        client._icons_by_category.setdefault(icon.category, []).append(icon)  # type: ignore[attr-defined]
        client._icons_by_license.setdefault(icon.license, []).append(icon)  # type: ignore[attr-defined]
    client._cache_time = float("inf")  # type: ignore[attr-defined]  # never expire
    return client


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestIconInfo:
    def test_from_raw(self) -> None:
        raw = {"name": "alanine", "category": "Amino-Acids", "license": "cc-0", "author": "X"}
        icon = IconInfo.from_raw(raw)
        assert icon.name == "alanine"
        assert icon.category == "Amino-Acids"

    def test_from_raw_missing_fields(self) -> None:
        icon = IconInfo.from_raw({})
        assert icon.name == ""
        assert icon.license == ""

    def test_from_raw_extra_fields_ignored(self) -> None:
        raw = {"name": "x", "category": "y", "license": "mit", "author": "z", "extra": "ignored"}
        icon = IconInfo.from_raw(raw)
        assert icon.name == "x"

    def test_matches_query_single_token(self) -> None:
        icon = IconInfo("alanine_chem", "Amino-Acids", "cc-0", "X")
        assert icon.matches_query("alanine")
        assert not icon.matches_query("glycine")

    def test_matches_query_multiple_tokens(self) -> None:
        icon = IconInfo("alanine_chem", "Amino-Acids", "cc-0", "X")
        assert icon.matches_query("alanine chem")
        assert not icon.matches_query("alanine glycine")

    def test_matches_query_empty(self) -> None:
        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "X")
        assert icon.matches_query("")

    def test_matches_query_whitespace_only(self) -> None:
        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "X")
        assert icon.matches_query("   ")

    def test_matches_query_case_insensitive(self) -> None:
        icon = IconInfo("Alanine", "Amino-Acids", "cc-0", "X")
        assert icon.matches_query("ALANINE")
        assert icon.matches_query("AlAnInE")

    def test_to_dict(self) -> None:
        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "B--Gideon-Bergheim")
        d = icon.to_dict()
        assert d == {
            "name": "alanine",
            "category": "Amino-Acids",
            "license": "cc-0",
            "author": "B--Gideon-Bergheim",
        }

    def test_frozen(self) -> None:
        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "X")
        with pytest.raises((AttributeError, TypeError)):
            icon.name = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        icon1 = IconInfo("alanine", "Amino-Acids", "cc-0", "X")
        icon2 = IconInfo("alanine", "Amino-Acids", "cc-0", "X")
        icon3 = IconInfo("glycine", "Amino-Acids", "cc-0", "X")
        assert icon1 == icon2
        assert icon1 != icon3


# ---------------------------------------------------------------------------
# Client tests
# ---------------------------------------------------------------------------


class TestBioiconsClient:
    @pytest.mark.asyncio
    async def test_get_categories(self, patched_client: BioiconsClient) -> None:
        cats = await patched_client.get_categories()
        assert "Amino-Acids" in cats
        assert cats[0] == "All_icons"

    @pytest.mark.asyncio
    async def test_get_all_icons(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_all_icons()
        assert len(icons) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_get_all_icons_returns_copy(self, patched_client: BioiconsClient) -> None:
        icons1 = await patched_client.get_all_icons()
        icons2 = await patched_client.get_all_icons()
        assert icons1 == icons2
        assert icons1 is not icons2

    @pytest.mark.asyncio
    async def test_get_icons_by_category(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_icons_by_category("Amino-Acids")
        assert all(i.category == "Amino-Acids" for i in icons)
        assert len(icons) == 2

    @pytest.mark.asyncio
    async def test_get_icons_by_category_all(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_icons_by_category("All_icons")
        assert len(icons) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_get_icons_by_category_empty(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_icons_by_category("NonExistent")
        assert len(icons) == 0

    @pytest.mark.asyncio
    async def test_get_icons_by_license(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_icons_by_license("bsd")
        assert all(i.license == "bsd" for i in icons)
        assert len(icons) == 3

    @pytest.mark.asyncio
    async def test_get_icons_by_license_empty(self, patched_client: BioiconsClient) -> None:
        icons = await patched_client.get_icons_by_license("nonexistent")
        assert len(icons) == 0

    @pytest.mark.asyncio
    async def test_get_authors(self, patched_client: BioiconsClient) -> None:
        authors = await patched_client.get_authors()
        assert "B--Gideon-Bergheim" in authors
        assert len(authors) == len(SAMPLE_AUTHORS)

    @pytest.mark.asyncio
    async def test_search_icons_by_name(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("alanine")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_icons_case_insensitive(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("ALANINE")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_icons_empty_query(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("")
        assert len(results) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_search_icons_with_category_filter(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", category="Machine_Learning")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_icons_with_category_all_icons(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", category="All_icons")
        assert len(results) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_search_icons_with_license_filter(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", license_slug="bsd")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_icons_with_category_and_license(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons(
            "", category="Machine_Learning", license_slug="bsd"
        )
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_icons_with_limit(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_icons_limit_zero(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", limit=0)
        assert len(results) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_search_icons_limit_negative(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("", limit=-1)
        assert len(results) == len(SAMPLE_ICONS)

    @pytest.mark.asyncio
    async def test_search_icons_no_match(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("nonexistent_icon")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_icons_multiple_tokens(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.search_icons("alanine chem")
        assert len(results) == 1
        assert results[0].name == "alanine_chem"

    @pytest.mark.asyncio
    async def test_find_icon_exact(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.find_icon("PyTorch")
        assert len(results) == 1
        assert results[0].name == "PyTorch"

    @pytest.mark.asyncio
    async def test_find_icon_case_insensitive(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.find_icon("pytorch")
        assert len(results) == 1
        assert results[0].name == "PyTorch"

    @pytest.mark.asyncio
    async def test_find_icon_substring(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.find_icon("alan")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_icon_not_found(self, patched_client: BioiconsClient) -> None:
        results = await patched_client.find_icon("nonexistent")
        assert len(results) == 0

    def test_build_svg_url(self) -> None:
        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "B--Gideon-Bergheim")
        url = BioiconsClient.build_svg_url(icon)
        expected = SVG_URL_TEMPLATE.format(
            license="cc-0",
            category="Amino-Acids",
            author="B--Gideon-Bergheim",
            name="alanine",
        )
        assert url == expected
        assert "alanine.svg" in url

    def test_build_svg_url_special_chars(self) -> None:
        icon = IconInfo("my_icon", "Cell_types", "cc-by-4.0", "Author-Name")
        url = BioiconsClient.build_svg_url(icon)
        assert "cc-by-4.0" in url
        assert "Cell_types" in url
        assert "Author-Name" in url
        assert "my_icon.svg" in url

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, patched_client: BioiconsClient) -> None:
        # Cache should be valid initially.
        assert patched_client._is_cache_valid()
        patched_client.invalidate_cache()
        assert not patched_client._is_cache_valid()

    @pytest.mark.asyncio
    async def test_fetch_svg(self, patched_client: BioiconsClient) -> None:
        """Test fetch_svg with a mocked HTTP client."""
        from unittest.mock import MagicMock

        mock_http = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = FAKE_SVG
        mock_response.raise_for_status = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_response)

        patched_client._client = mock_http  # type: ignore[attr-defined]
        patched_client._owns_client = False  # type: ignore[attr-defined]

        icon = IconInfo("alanine", "Amino-Acids", "cc-0", "B--Gideon-Bergheim")
        svg = await patched_client.fetch_svg(icon)
        assert svg == FAKE_SVG
        mock_http.get.assert_called_once()


# ---------------------------------------------------------------------------
# Tool layer tests
# ---------------------------------------------------------------------------


class TestToolListCategories:
    @pytest.mark.asyncio
    async def test_list_categories_en(self, patched_client: BioiconsClient) -> None:
        result = await _tool_list_categories(patched_client, {"language": "en"})
        assert result.type == "text"
        assert "bioicons.com Icon Categories" in result.text
        assert "Total icons: 6" in result.text
        assert "Amino-Acids" in result.text
        assert "Amino acid illustrations" in result.text

    @pytest.mark.asyncio
    async def test_list_categories_zh(self, patched_client: BioiconsClient) -> None:
        result = await _tool_list_categories(patched_client, {"language": "zh"})
        assert result.type == "text"
        assert "bioicons.com 图标分类列表" in result.text
        assert "氨基酸插图" in result.text

    @pytest.mark.asyncio
    async def test_list_categories_default_language(self, patched_client: BioiconsClient) -> None:
        result = await _tool_list_categories(patched_client, {})
        assert "bioicons.com Icon Categories" in result.text

    @pytest.mark.asyncio
    async def test_list_categories_counts(self, patched_client: BioiconsClient) -> None:
        result = await _tool_list_categories(patched_client, {})
        assert "(2 icons)" in result.text  # Amino-Acids has 2
        assert "(3 icons)" in result.text  # Machine_Learning has 3
        assert "(6 icons)" in result.text  # All_icons has 6


class TestToolSearchIcons:
    @pytest.mark.asyncio
    async def test_search_with_results(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(patched_client, {"query": "alanine"})
        assert result.type == "text"
        assert "Search results for 'alanine'" in result.text
        assert "2 icons found" in result.text
        assert "alanine" in result.text

    @pytest.mark.asyncio
    async def test_search_no_results(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(patched_client, {"query": "nonexistent"})
        assert "No icons found" in result.text

    @pytest.mark.asyncio
    async def test_search_with_category(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(
            patched_client, {"query": "", "category": "Machine_Learning"}
        )
        assert "3 icons found" in result.text

    @pytest.mark.asyncio
    async def test_search_with_license(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(
            patched_client, {"query": "", "license": "bsd"}
        )
        assert "3 icons found" in result.text

    @pytest.mark.asyncio
    async def test_search_with_limit(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(
            patched_client, {"query": "", "limit": 2}
        )
        assert "2 icons found" in result.text

    @pytest.mark.asyncio
    async def test_search_result_contains_svg_url(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(patched_client, {"query": "PyTorch"})
        assert "https://bioicons.com/icons/" in result.text
        assert "PyTorch.svg" in result.text

    @pytest.mark.asyncio
    async def test_search_result_contains_license_name(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(patched_client, {"query": "PyTorch"})
        assert "BSD 3-Clause" in result.text

    @pytest.mark.asyncio
    async def test_search_empty_query_all_icons(self, patched_client: BioiconsClient) -> None:
        result = await _tool_search_icons(patched_client, {"query": ""})
        assert "6 icons found" in result.text


class TestToolGetIcon:
    @pytest.mark.asyncio
    async def test_get_icon_by_name(self, patched_client: BioiconsClient) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_get_icon(patched_client, {"name": "alanine"})
        assert result.type == "text"
        assert "# Icon: alanine" in result.text
        assert "Amino-Acids" in result.text
        assert "```svg" in result.text
        assert FAKE_SVG in result.text

    @pytest.mark.asyncio
    async def test_get_icon_not_found(self, patched_client: BioiconsClient) -> None:
        with pytest.raises(ValueError, match="not found"):
            await _tool_get_icon(patched_client, {"name": "nonexistent"})

    @pytest.mark.asyncio
    async def test_get_icon_exact_match(self, patched_client: BioiconsClient) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_get_icon(
                patched_client,
                {
                    "name": "PyTorch",
                    "category": "Machine_Learning",
                    "license": "bsd",
                    "author": "Facebook",
                },
            )
        assert "PyTorch" in result.text

    @pytest.mark.asyncio
    async def test_get_icon_exact_match_not_found_fallback(
        self, patched_client: BioiconsClient
    ) -> None:
        """If exact match fails, should fall back to name match."""
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_get_icon(
                patched_client,
                {
                    "name": "PyTorch",
                    "category": "WrongCategory",
                    "license": "wrong",
                    "author": "wrong",
                },
            )
        assert "PyTorch" in result.text


class TestToolDownloadIcon:
    @pytest.mark.asyncio
    async def test_download_icon_default(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(tmp_path)},
            )
        assert result.type == "text"
        assert "downloaded successfully" in result.text
        saved_file = tmp_path / "alanine.svg"
        assert saved_file.exists()
        assert saved_file.read_text(encoding="utf-8") == FAKE_SVG

    @pytest.mark.asyncio
    async def test_download_icon_custom_filename(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(tmp_path), "filename": "custom.svg"},
            )
        assert (tmp_path / "custom.svg").exists()

    @pytest.mark.asyncio
    async def test_download_icon_filename_without_svg_extension(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(tmp_path), "filename": "noext"},
            )
        assert (tmp_path / "noext.svg").exists()

    @pytest.mark.asyncio
    async def test_download_icon_creates_dir(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        nested = tmp_path / "a" / "b" / "c"
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(nested)},
            )
        assert (nested / "alanine.svg").exists()

    @pytest.mark.asyncio
    async def test_download_icon_attribution_reminder(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        """BSD license requires attribution."""
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_download_icon(
                patched_client,
                {"name": "PyTorch", "save_dir": str(tmp_path)},
            )
        assert "Attribution required" in result.text
        assert "BSD 3-Clause" in result.text

    @pytest.mark.asyncio
    async def test_download_icon_no_attribution_for_cc0(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        """CC0 does not require attribution."""
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(tmp_path)},
            )
        assert "Attribution required" not in result.text

    @pytest.mark.asyncio
    async def test_download_icon_file_size(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_download_icon(
                patched_client,
                {"name": "alanine", "save_dir": str(tmp_path)},
            )
        assert f"{len(FAKE_SVG)} bytes" in result.text

    @pytest.mark.asyncio
    async def test_download_icon_path_traversal_filename(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        """Security: filename with path separators must be sanitised."""
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            result = await _tool_download_icon(
                patched_client,
                {
                    "name": "alanine",
                    "save_dir": str(tmp_path),
                    "filename": "../../../etc/evil.svg",
                },
            )
        # The sanitised filename should be just "evil.svg" inside save_dir.
        assert (tmp_path / "evil.svg").exists()
        # No file should exist outside tmp_path.
        assert not (tmp_path.parent.parent.parent / "etc" / "evil.svg").exists()
        assert "evil.svg" in result.text

    @pytest.mark.asyncio
    async def test_download_icon_path_traversal_windows(
        self, patched_client: BioiconsClient, tmp_path: Path
    ) -> None:
        """Security: Windows-style path traversal in filename."""
        with patch.object(
            BioiconsClient, "fetch_svg", new=AsyncMock(return_value=FAKE_SVG)
        ):
            await _tool_download_icon(
                patched_client,
                {
                    "name": "alanine",
                    "save_dir": str(tmp_path),
                    "filename": "..\\..\\evil.svg",
                },
            )
        # After sanitisation, only the basename should remain.
        assert (tmp_path / "evil.svg").exists()


class TestToolGetIconInfo:
    @pytest.mark.asyncio
    async def test_get_icon_info_basic(self, patched_client: BioiconsClient) -> None:
        result = await _tool_get_icon_info(patched_client, {"name": "alanine"})
        assert result.type == "text"
        assert "# Icon Info: alanine" in result.text
        assert "Amino-Acids" in result.text
        assert "cc-0" in result.text
        assert "B--Gideon-Bergheim" in result.text

    @pytest.mark.asyncio
    async def test_get_icon_info_svg_url(self, patched_client: BioiconsClient) -> None:
        result = await _tool_get_icon_info(patched_client, {"name": "alanine"})
        assert "https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg" in result.text

    @pytest.mark.asyncio
    async def test_get_icon_info_license_details(self, patched_client: BioiconsClient) -> None:
        result = await _tool_get_icon_info(patched_client, {"name": "PyTorch"})
        assert "BSD 3-Clause" in result.text
        assert "https://opensource.org/licenses/BSD-3-Clause" in result.text
        assert "yes" in result.text  # requires_attribution

    @pytest.mark.asyncio
    async def test_get_icon_info_cc0_no_attribution(self, patched_client: BioiconsClient) -> None:
        result = await _tool_get_icon_info(patched_client, {"name": "alanine"})
        assert "CC0 (Public Domain)" in result.text
        assert "no" in result.text  # requires_attribution

    @pytest.mark.asyncio
    async def test_get_icon_info_json_output(self, patched_client: BioiconsClient) -> None:
        result = await _tool_get_icon_info(patched_client, {"name": "alanine"})
        assert "```json" in result.text
        # Extract the JSON block.
        json_start = result.text.index("```json\n") + len("```json\n")
        json_end = result.text.index("\n```", json_start)
        raw_json = result.text[json_start:json_end]
        data = json.loads(raw_json)
        assert data["name"] == "alanine"
        assert data["category"] == "Amino-Acids"
        assert data["license"]["slug"] == "cc-0"
        assert data["license"]["name"] == "CC0 (Public Domain)"
        assert data["author"] == "B--Gideon-Bergheim"

    @pytest.mark.asyncio
    async def test_get_icon_info_unknown_license(self, patched_client: BioiconsClient) -> None:
        """Icon with a license not in LICENSE_INFO should still work."""
        # Inject an icon with an unknown license.
        patched_client._icons.append(  # type: ignore[attr-defined]
            IconInfo("weird", "Amino-Acids", "unknown-license", "X")
        )
        patched_client._icons_by_name["weird"] = [  # type: ignore[attr-defined]
            IconInfo("weird", "Amino-Acids", "unknown-license", "X")
        ]
        result = await _tool_get_icon_info(patched_client, {"name": "weird"})
        assert "unknown-license" in result.text


# ---------------------------------------------------------------------------
# Server factory tests
# ---------------------------------------------------------------------------


class TestCreateServer:
    def test_create_server_returns_tuple(self) -> None:
        server, client = create_server()
        assert server is not None
        assert client is not None
        assert server.name == "bioicons-mcp"

    @pytest.mark.asyncio
    async def test_create_server_cleanup(self) -> None:
        server, client = create_server()
        await client.close()
