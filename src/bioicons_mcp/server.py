"""MCP server implementation for bioicons.com.

This module wires together the :class:`~bioicons_mcp.client.BioiconsClient`
and the Model Context Protocol SDK, exposing five tools:

* ``list_categories`` — enumerate bioicons.com categories.
* ``search_icons``    — full-text search over the icon library.
* ``get_icon``        — fetch the SVG content of a single icon.
* ``download_icon``   — save an icon's SVG file to the local filesystem.
* ``get_icon_info``   — return detailed metadata for a specific icon.

The server supports two transport modes:

* **stdio** (default) — used by Claude Desktop, Cursor and most local MCP
  clients.
* **SSE** — suitable for remote / browser-based clients.

Run ``python -m bioicons_mcp.server`` to start the server in stdio mode, or
pass ``--transport sse --port 8080`` for SSE mode.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from mcp.server import NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    GetPromptRequestParams,
    GetPromptResult,
    ListPromptsResult,
    ListToolsResult,
    PaginatedRequestParams,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from .client import BioiconsClient
from .constants import (
    CATEGORY_DESCRIPTIONS_EN,
    CATEGORY_DESCRIPTIONS_ZH,
    DEFAULT_SEARCH_LIMIT,
    LICENSE_INFO,
    MAX_SEARCH_LIMIT,
    SERVER_NAME,
    SERVER_VERSION,
)
from .models import IconInfo

# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------


def create_server() -> tuple[Server, BioiconsClient]:
    """Create and wire up the MCP ``Server`` instance.

    Returns a tuple of ``(server, client)`` so callers can manage the client
    lifecycle (e.g. close it on shutdown).
    """
    client = BioiconsClient()

    # ------------------------------------------------------------------
    # Handler implementations
    # ------------------------------------------------------------------
    #
    # In MCP SDK 2.x, handlers are registered via constructor parameters
    # (``on_list_tools``, ``on_call_tool``, etc.) rather than decorators.
    # Each handler receives a :class:`ServerRequestContext` as its first
    # argument — we don't need the context for stateless tools, so we
    # ignore it (``_ctx``).

    async def handle_list_tools(
        _ctx: Any, _params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        """Return the static list of tools offered by this server."""
        return ListToolsResult(
            tools=[
                Tool(
                    name="list_categories",
                    description=(
                        "List all icon categories available on bioicons.com, "
                        "each with the number of icons and descriptions in both "
                        "English and Chinese."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "enum": ["en", "zh"],
                                "default": "en",
                                "description": (
                                    "Language for category descriptions: "
                                    "'en' for English, 'zh' for Chinese."
                                ),
                            }
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="search_icons",
                    description=(
                        "Search the bioicons.com icon library by keyword. "
                        "Returns matching icons with name, category, license, "
                        "author and a direct SVG download URL. "
                        "Optionally filter by category and/or license."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "Search keywords. The search is "
                                    "case-insensitive and every "
                                    "whitespace-separated token must appear "
                                    "in the icon name."
                                ),
                            },
                            "category": {
                                "type": "string",
                                "default": "All_icons",
                                "description": (
                                    "Filter by category slug "
                                    "(e.g. 'Amino-Acids', 'Chemistry'). "
                                    "Use 'All_icons' (default) to search all "
                                    "categories."
                                ),
                            },
                            "license": {
                                "type": "string",
                                "default": "",
                                "description": (
                                    "Filter by license slug "
                                    "(e.g. 'cc-0', 'mit', 'bsd', "
                                    "'cc-by-4.0', 'cc-by-sa-4.0'). "
                                    "Empty string means no license filter."
                                ),
                            },
                            "limit": {
                                "type": "integer",
                                "default": DEFAULT_SEARCH_LIMIT,
                                "minimum": 1,
                                "maximum": MAX_SEARCH_LIMIT,
                                "description": (
                                    f"Maximum number of results to return "
                                    f"(default {DEFAULT_SEARCH_LIMIT}, max "
                                    f"{MAX_SEARCH_LIMIT})."
                                ),
                            },
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_icon",
                    description=(
                        "Fetch the SVG content of a specific icon from "
                        "bioicons.com. Provide either the exact icon name or "
                        "all four identifying fields (name, category, "
                        "license, author). The SVG source is returned as text."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": (
                                    "Icon name (without .svg extension)."
                                ),
                            },
                            "category": {
                                "type": "string",
                                "default": "",
                                "description": (
                                    "Category slug. If omitted, the first "
                                    "icon matching *name* is used."
                                ),
                            },
                            "license": {
                                "type": "string",
                                "default": "",
                                "description": (
                                    "License slug. If omitted, the first "
                                    "icon matching *name* is used."
                                ),
                            },
                            "author": {
                                "type": "string",
                                "default": "",
                                "description": (
                                    "Author slug. If omitted, the first "
                                    "icon matching *name* is used."
                                ),
                            },
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="download_icon",
                    description=(
                        "Download an icon's SVG file from bioicons.com and "
                        "save it to the local filesystem. Returns the saved "
                        "file path."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Icon name (without .svg).",
                            },
                            "category": {
                                "type": "string",
                                "default": "",
                                "description": "Category slug (optional).",
                            },
                            "license": {
                                "type": "string",
                                "default": "",
                                "description": "License slug (optional).",
                            },
                            "author": {
                                "type": "string",
                                "default": "",
                                "description": "Author slug (optional).",
                            },
                            "save_dir": {
                                "type": "string",
                                "default": ".",
                                "description": (
                                    "Directory where the SVG file should be "
                                    "saved. Created if it does not exist. "
                                    "Defaults to the current working directory."
                                ),
                            },
                            "filename": {
                                "type": "string",
                                "default": "",
                                "description": (
                                    "Custom file name (with or without .svg). "
                                    "Defaults to the icon name."
                                ),
                            },
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_icon_info",
                    description=(
                        "Return detailed metadata for a specific icon: "
                        "name, category, license (with full name and URL), "
                        "author, SVG download URL, and attribution "
                        "requirements."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Icon name (without .svg).",
                            },
                            "category": {
                                "type": "string",
                                "default": "",
                                "description": "Category slug (optional).",
                            },
                            "license": {
                                "type": "string",
                                "default": "",
                                "description": "License slug (optional).",
                            },
                            "author": {
                                "type": "string",
                                "default": "",
                                "description": "Author slug (optional).",
                            },
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                ),
            ]
        )

    async def handle_call_tool(
        _ctx: Any, params: CallToolRequestParams
    ) -> CallToolResult:
        """Route a tool invocation to the appropriate handler."""
        name = params.name
        arguments: dict[str, Any] = dict(params.arguments or {})

        try:
            if name == "list_categories":
                content = await _tool_list_categories(client, arguments)
            elif name == "search_icons":
                content = await _tool_search_icons(client, arguments)
            elif name == "get_icon":
                content = await _tool_get_icon(client, arguments)
            elif name == "download_icon":
                content = await _tool_download_icon(client, arguments)
            elif name == "get_icon_info":
                content = await _tool_get_icon_info(client, arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    is_error=True,
                )
            return CallToolResult(content=[content], is_error=False)
        except Exception as exc:  # noqa: BLE001
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error executing tool '{name}': {exc}",
                    )
                ],
                is_error=True,
            )

    async def handle_list_prompts(
        _ctx: Any, _params: PaginatedRequestParams | None
    ) -> ListPromptsResult:
        """Expose a reusable prompt for finding science icons."""
        return ListPromptsResult(
            prompts=[
                Prompt(
                    name="find_science_icons",
                    description=(
                        "Find and describe science icons from bioicons.com "
                        "based on a natural-language description of what the "
                        "user is looking for."
                    ),
                    arguments=[
                        PromptArgument(
                            name="description",
                            description=(
                                "Natural-language description of the desired icon, "
                                "e.g. 'DNA double helix' or 'laboratory beaker'."
                            ),
                            required=True,
                        ),
                        PromptArgument(
                            name="category",
                            description=(
                                "Optional category to narrow the search."
                            ),
                            required=False,
                        ),
                    ],
                )
            ]
        )

    async def handle_get_prompt(
        _ctx: Any, params: GetPromptRequestParams
    ) -> GetPromptResult:
        """Return the rendered prompt messages."""
        if params.name != "find_science_icons":
            raise ValueError(f"Unknown prompt: {params.name}")

        arguments = params.arguments or {}
        desc = arguments.get("description", "")
        category = arguments.get("category", "All_icons")

        category_clause = (
            f" within the '{category}' category" if category != "All_icons" else ""
        )

        return GetPromptResult(
            description=f"Search bioicons.com for: {desc}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            f'I need a science illustration matching this '
                            f'description: "{desc}".\n\n'
                            f"Please search bioicons.com{category_clause} "
                            f"and suggest the most relevant icons. "
                            "For each suggestion, include the icon name, "
                            "category, license, author, the SVG download URL, "
                            "and whether attribution is required."
                        ),
                    ),
                )
            ],
        )

    # ------------------------------------------------------------------
    # Build the Server with handler parameters
    # ------------------------------------------------------------------
    server = Server(
        SERVER_NAME,
        version=SERVER_VERSION,
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
        on_list_prompts=handle_list_prompts,
        on_get_prompt=handle_get_prompt,
    )

    return server, client


# ---------------------------------------------------------------------------
# Tool implementations (return TextContent)
# ---------------------------------------------------------------------------


async def _tool_list_categories(
    client: BioiconsClient, args: dict[str, Any]
) -> TextContent:
    """Implement the ``list_categories`` tool."""
    language = args.get("language", "en")
    desc_map = (
        CATEGORY_DESCRIPTIONS_ZH if language == "zh" else CATEGORY_DESCRIPTIONS_EN
    )

    categories = await client.get_categories()
    all_icons = await client.get_all_icons()

    # Count icons per category.
    counts: dict[str, int] = {}
    for icon in all_icons:
        counts[icon.category] = counts.get(icon.category, 0) + 1

    lines: list[str] = []
    header = (
        "bioicons.com 图标分类列表"
        if language == "zh"
        else "bioicons.com Icon Categories"
    )
    lines.append(f"# {header}")
    lines.append(f"Total icons: {len(all_icons)}\n")

    for cat in categories:
        if cat == "All_icons":
            count = len(all_icons)
        else:
            count = counts.get(cat, 0)
        description = desc_map.get(cat, "")
        lines.append(f"- **{cat}** ({count} icons): {description}")

    return TextContent(type="text", text="\n".join(lines))


async def _tool_search_icons(
    client: BioiconsClient, args: dict[str, Any]
) -> TextContent:
    """Implement the ``search_icons`` tool."""
    query = args.get("query", "")
    category = args.get("category", "All_icons") or "All_icons"
    license_slug = args.get("license", "") or ""
    limit = args.get("limit", DEFAULT_SEARCH_LIMIT)

    icons = await client.search_icons(
        query,
        category=category if category else None,
        license_slug=license_slug if license_slug else None,
        limit=limit,
    )

    if not icons:
        msg = (
            f"No icons found for query '{query}'"
            + (f" in category '{category}'" if category != "All_icons" else "")
            + (f" with license '{license_slug}'" if license_slug else "")
            + "."
        )
        return TextContent(type="text", text=msg)

    lines: list[str] = []
    lines.append(f"# Search results for '{query}' ({len(icons)} icons found)")
    lines.append("")
    for i, icon in enumerate(icons, 1):
        url = client.build_svg_url(icon)
        lic_display = LICENSE_INFO.get(icon.license, {}).get("name", icon.license)
        lines.append(
            f"{i}. **{icon.name}**\n"
            f"   - Category: {icon.category}\n"
            f"   - License: {lic_display} (`{icon.license}`)\n"
            f"   - Author: {icon.author}\n"
            f"   - SVG URL: {url}"
        )

    return TextContent(type="text", text="\n".join(lines))


async def _resolve_icon(
    client: BioiconsClient, args: dict[str, Any]
) -> IconInfo:
    """Resolve a single :class:`IconInfo` from tool arguments.

    If ``category``, ``license`` and ``author`` are all provided, we look for
    an exact match.  Otherwise we fall back to the first icon whose name
    matches.
    """
    name = args["name"]
    category = args.get("category", "")
    license_slug = args.get("license", "")
    author = args.get("author", "")

    if category and license_slug and author:
        # Exact match.
        all_icons = await client.get_all_icons()
        for icon in all_icons:
            if (
                icon.name == name
                and icon.category == category
                and icon.license == license_slug
                and icon.author == author
            ):
                return icon

    # Fallback: first icon with matching name.
    matches = await client.find_icon(name)
    if not matches:
        raise ValueError(
            f"Icon '{name}' not found on bioicons.com. "
            "Use search_icons to discover available icons."
        )
    return matches[0]


async def _tool_get_icon(
    client: BioiconsClient, args: dict[str, Any]
) -> TextContent:
    """Implement the ``get_icon`` tool — return raw SVG text."""
    icon = await _resolve_icon(client, args)
    svg_content = await client.fetch_svg(icon)
    url = client.build_svg_url(icon)

    text = (
        f"# Icon: {icon.name}\n"
        f"Category: {icon.category}\n"
        f"License: {icon.license}\n"
        f"Author: {icon.author}\n"
        f"Source URL: {url}\n"
        f"\n## SVG Content\n\n```svg\n{svg_content}\n```"
    )
    return TextContent(type="text", text=text)


async def _tool_download_icon(
    client: BioiconsClient, args: dict[str, Any]
) -> TextContent:
    """Implement the ``download_icon`` tool — save SVG to disk."""
    icon = await _resolve_icon(client, args)
    svg_content = await client.fetch_svg(icon)

    save_dir = Path(args.get("save_dir", ".")).expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = args.get("filename", "") or icon.name
    # Security: sanitise the filename to prevent path traversal.
    # Strip any path separators and leading directory components so that
    # only the bare file name remains.
    filename = Path(filename).name
    if not filename:
        filename = icon.name
    if not filename.endswith(".svg"):
        filename += ".svg"

    file_path = save_dir / filename
    # Guard against symlinks or other tricks that could escape save_dir.
    if not file_path.resolve().is_relative_to(save_dir):
        raise ValueError(
            f"Resolved file path '{file_path}' is outside the save directory "
            f"'{save_dir}'. Refusing to write for security reasons."
        )
    file_path.write_text(svg_content, encoding="utf-8")

    url = client.build_svg_url(icon)
    lic_display = LICENSE_INFO.get(icon.license, {}).get("name", icon.license)

    text = (
        f"# Icon downloaded successfully\n\n"
        f"- **Name**: {icon.name}\n"
        f"- **Category**: {icon.category}\n"
        f"- **License**: {lic_display} (`{icon.license}`)\n"
        f"- **Author**: {icon.author}\n"
        f"- **Source URL**: {url}\n"
        f"- **Saved to**: `{file_path}`\n"
        f"- **File size**: {file_path.stat().st_size} bytes\n"
    )

    # Add attribution reminder if the licence requires it.
    lic_info = LICENSE_INFO.get(icon.license)
    if lic_info and lic_info.get("requires_attribution") == "yes":
        text += (
            f"\n> ⚠️ **Attribution required**: This icon is licensed under "
            f"{lic_info['name']}. You must attribute the author "
            f"({icon.author}) and link to {lic_info['url']}.\n"
            f"> Example: \"{icon.name} icon by {icon.author} is licensed "
            f"under {lic_info['name']} ({lic_info['url']})\"\n"
        )

    return TextContent(type="text", text=text)


async def _tool_get_icon_info(
    client: BioiconsClient, args: dict[str, Any]
) -> TextContent:
    """Implement the ``get_icon_info`` tool — return rich metadata."""
    icon = await _resolve_icon(client, args)
    url = client.build_svg_url(icon)
    lic_info = LICENSE_INFO.get(icon.license, {})
    lic_name = lic_info.get("name", icon.license)
    lic_url = lic_info.get("url", "")
    requires_attr = lic_info.get("requires_attribution", "unknown")

    info: dict[str, Any] = {
        "name": icon.name,
        "category": icon.category,
        "license": {
            "slug": icon.license,
            "name": lic_name,
            "url": lic_url,
            "requires_attribution": requires_attr,
        },
        "author": icon.author,
        "svg_url": url,
        "bioicons_page": "https://bioicons.com/",
    }

    # Pretty-print as a readable summary plus raw JSON.
    lines: list[str] = [
        f"# Icon Info: {icon.name}",
        "",
        f"- **Name**: {icon.name}",
        f"- **Category**: {icon.category}",
        f"- **License**: {lic_name} (`{icon.license}`)",
    ]
    if lic_url:
        lines.append(f"- **License URL**: {lic_url}")
    lines.extend([
        f"- **Author**: {icon.author}",
        f"- **SVG download URL**: {url}",
        f"- **Attribution required**: {requires_attr}",
    ])
    lines.append("")
    lines.append("## Raw JSON")
    lines.append("```json")
    lines.append(json.dumps(info, indent=2, ensure_ascii=False))
    lines.append("```")

    return TextContent(type="text", text="\n".join(lines))


# ---------------------------------------------------------------------------
# Transport runners
# ---------------------------------------------------------------------------


async def run_stdio() -> None:
    """Run the MCP server using the stdio transport (default)."""
    server, client = create_server()
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(
                    NotificationOptions(
                        tools_changed=True,
                        prompts_changed=True,
                    )
                ),
            )
    finally:
        await client.close()


def create_sse_app() -> Starlette:
    """Create a Starlette ASGI app that serves the MCP server over SSE."""
    server, client = create_server()
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request: Any) -> None:
        async with sse_transport.connect_sse(
            request.scope, request.receive, request.send
        ) as streams:
            read_stream, write_stream = streams
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(
                    NotificationOptions(
                        tools_changed=True,
                        prompts_changed=True,
                    )
                ),
            )

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> Any:
        yield
        await client.close()

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ],
        lifespan=lifespan,
    )
    return app


async def run_sse(host: str, port: int) -> None:
    """Run the MCP server using the SSE transport."""
    app = create_sse_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    uv_server = uvicorn.Server(config)
    await uv_server.serve()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point: parse arguments and start the server."""
    parser = argparse.ArgumentParser(
        prog="bioicons-mcp",
        description="MCP server for bioicons.com — high quality science illustrations.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind when using SSE transport (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on when using SSE transport (default: 8080).",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio())
    else:
        asyncio.run(run_sse(args.host, args.port))


if __name__ == "__main__":
    main()
