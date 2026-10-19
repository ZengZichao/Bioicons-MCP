# Bioicons MCP Server

> ⚠️ **Third-Party / Unofficial Implementation**
>
> This is an **independent, community-developed** MCP server and is **not** the official MCP server for bioicons.com.
> This project is not affiliated with, endorsed by, or sponsored by bioicons.com or its creator.
> The official bioicons.com website can be found at [https://bioicons.com](https://bioicons.com).

> **Version 0.1.0**
>
> A [Model Context Protocol](https://modelcontextprotocol.io/) server for [bioicons.com](https://bioicons.com/) — a free library of 2800+ high quality science illustrations.

[中文文档 (Chinese README)](./README_CN.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Installation](#installation)
5. [Client Configuration](#client-configuration)
6. [Tools Reference](#tools-reference)
7. [Prompts](#prompts)
8. [Transport Modes](#transport-modes)
9. [Project Structure](#project-structure)
10. [Development](#development)
11. [Licensing](#licensing)
12. [FAQ](#faq)

---

## Overview

**Bioicons MCP Server** bridges [bioicons.com](https://bioicons.com/) — a curated library of open-source SVG illustrations for the life sciences — and any AI client that supports the Model Context Protocol (MCP), such as Claude Desktop, Cursor, or Cline.

With this server, your AI assistant can:

- 🔍 **Search** the entire bioicons.com icon library (2800+ icons)
- 📋 **Inspect** icon metadata (name, category, license, author)
- 📥 **Download** SVG files to your local filesystem
- 🏷️ **Understand** licensing and attribution requirements for each icon

> **What is bioicons.com?**
>
> Created by Simon Duerr, bioicons.com is an open platform providing high-quality vector illustrations for scientific figures. All icons are available as SVG files under permissive licenses (CC0, CC BY, CC BY-SA, MIT, BSD) and can be used in Inkscape, Adobe Illustrator, Microsoft Office, and more.

---

## Features

| Feature | Description |
|---------|-------------|
| ✅ Full-text search | Search icons by keyword; multiple tokens are AND-matched |
| ✅ Category filtering | Filter by 37 bio-science categories |
| ✅ License filtering | Filter by CC0 / CC BY / CC BY-SA / MIT / BSD |
| ✅ SVG retrieval | Fetch raw SVG source of any icon |
| ✅ Local download | Save SVG files to a specified directory |
| ✅ Rich metadata | Full icon info including license URL and attribution requirements |
| ✅ Bilingual | Category descriptions in English and Chinese |
| ✅ stdio transport | For Claude Desktop, Cursor, and other local clients |
| ✅ SSE transport | For remote / web-based clients |
| ✅ In-memory cache | Metadata cached for 1 hour to minimise network requests |
| ✅ Prompt template | Built-in "find science icons" prompt |

---

## Quick Start

### Prerequisites

- **Python ≥ 3.10**
- Network access to `https://bioicons.com`
- An MCP-compatible client (recommended: [Claude Desktop](https://claude.ai/download) or [Cursor](https://cursor.com))

### 60-Second Setup

```bash
# 1. Enter the project directory
cd Bioicons-MCP

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the package (editable mode)
pip install -e .

# 5. Verify installation
bioicons-mcp --help
```

Expected output:

```
usage: bioicons-mcp [-h] [--transport {stdio,sse}] [--host HOST] [--port PORT]

MCP server for bioicons.com — high quality science illustrations.
```

---

## Installation

### Option A: From source (recommended)

```bash
git clone <your-repo-url> Bioicons-MCP
cd Bioicons-MCP
pip install -e .
```

### Option B: Run directly without installing

```bash
cd Bioicons-MCP
pip install -r requirements.txt
python -m bioicons_mcp --transport stdio
```

---

## Client Configuration

### Claude Desktop

Edit the Claude Desktop config file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bioicons": {
      "command": "python",
      "args": ["-m", "bioicons_mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

> **Tip:** If you're using a virtual environment, replace `"python"` with the full path to the Python executable, e.g. `"C:\\Bioicons-MCP\\.venv\\Scripts\\python.exe"`.

### Cursor

Navigate to `Settings → MCP` and add:

```json
{
  "mcpServers": {
    "bioicons": {
      "command": "python",
      "args": ["-m", "bioicons_mcp"]
    }
  }
}
```

### Cline (VS Code)

In `.cline/mcp_settings.json`:

```json
{
  "mcpServers": {
    "bioicons": {
      "command": "python",
      "args": ["-m", "bioicons_mcp"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### SSE Mode (Remote Deployment)

Start the SSE server:

```bash
bioicons-mcp --transport sse --host 0.0.0.0 --port 8080
```

Then configure your client with the SSE URL:

```
http://<server-ip>:8080/sse
```

---

## Tools Reference

The server exposes **5 tools** that AI clients can call automatically.

### 1. `list_categories` — List All Categories

Lists every bioicons.com category with icon counts and descriptions.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | `string` (`"en"` / `"zh"`) | No | `"en"` | Language for descriptions |

**Example:**

```
list_categories(language="en")
```

**Sample output:**

```
# bioicons.com Icon Categories
Total icons: 2829

- **All_icons** (2829 icons): All available icons on bioicons.com
- **Amino-Acids** (31 icons): Amino acid illustrations
- **Animals** (384 icons): Animal and model organism illustrations
- **Chemistry** (92 icons): Chemistry illustrations
...
```

### 2. `search_icons` — Search Icons

Search the icon library by keyword, with optional category and license filters.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `string` | ✅ | — | Search keywords (space-separated, all must match) |
| `category` | `string` | No | `"All_icons"` | Category filter |
| `license` | `string` | No | `""` | License filter |
| `limit` | `integer` | No | `50` | Max results (cap: 500) |

**Example:**

```
search_icons(query="alanine", category="Amino-Acids", limit=10)
```

**License slugs:**

| Slug | Full name | Attribution required |
|------|-----------|---------------------|
| `cc-0` | CC0 (Public Domain) | No |
| `cc-by-3.0` | CC BY 3.0 | Yes |
| `cc-by-4.0` | CC BY 4.0 | Yes |
| `cc-by-sa-3.0` | CC BY-SA 3.0 | Yes |
| `cc-by-sa-4.0` | CC BY-SA 4.0 | Yes |
| `mit` | MIT | Yes |
| `bsd` | BSD 3-Clause | Yes |

### 3. `get_icon` — Get SVG Content

Fetch the raw SVG source of a specific icon.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | ✅ | Icon name (without `.svg`) |
| `category` | `string` | No | Category slug for exact matching |
| `license` | `string` | No | License slug for exact matching |
| `author` | `string` | No | Author slug for exact matching |

> If only `name` is provided, the first matching icon is returned.

**Example:**

```
get_icon(name="alanine")
```

### 4. `download_icon` — Download SVG to Disk

Save an icon's SVG file to the local filesystem.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `string` | ✅ | — | Icon name |
| `save_dir` | `string` | No | `"."` | Save directory (auto-created) |
| `filename` | `string` | No | icon name | Custom filename |
| `category` | `string` | No | `""` | Category slug |
| `license` | `string` | No | `""` | License slug |
| `author` | `string` | No | `""` | Author slug |

**Example:**

```
download_icon(name="PyTorch", save_dir="./icons", filename="pytorch.svg")
```

The tool will also display an attribution reminder if the icon's license requires it.

### 5. `get_icon_info` — Get Icon Metadata

Return detailed metadata for a specific icon, including license name, URL, and attribution requirements.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | ✅ | Icon name |
| `category` | `string` | No | Category slug |
| `license` | `string` | No | License slug |
| `author` | `string` | No | Author slug |

**Sample JSON output:**

```json
{
  "name": "alanine",
  "category": "Amino-Acids",
  "license": {
    "slug": "cc-0",
    "name": "CC0 (Public Domain)",
    "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "requires_attribution": "no"
  },
  "author": "B--Gideon-Bergheim",
  "svg_url": "https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg"
}
```

---

## Prompts

The server includes one reusable prompt template:

### `find_science_icons`

Find science illustrations based on a natural-language description.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `description` | `string` | ✅ | Natural-language description of the desired icon |
| `category` | `string` | No | Optional category to narrow the search |

**Example usage:**

> "Find me an icon of a DNA double helix"

The AI will automatically call `search_icons` with the keyword "DNA" and suggest the most relevant icons.

---

## Transport Modes

### stdio (default)

For local MCP clients (Claude Desktop, Cursor, etc.):

```bash
bioicons-mcp                       # default stdio
bioicons-mcp --transport stdio     # explicit
```

### SSE

For remote deployment or web-based clients:

```bash
bioicons-mcp --transport sse --host 0.0.0.0 --port 8080
```

SSE endpoints:

- Connection URL: `http://<host>:<port>/sse`
- Message endpoint: `http://<host>:<port>/messages/`

---

## Project Structure

```
Bioicons-MCP/
├── src/
│   └── bioicons_mcp/
│       ├── __init__.py        # Package init, version
│       ├── __main__.py        # Enable: python -m bioicons_mcp
│       ├── server.py          # MCP Server core (tools, prompts, transport)
│       ├── client.py          # Async bioicons.com API client (with cache)
│       ├── models.py          # IconInfo data model
│       ├── constants.py       # Constants: URLs, licenses, category descriptions
│       └── py.typed           # PEP 561 type marker
├── tests/
│   └── test_server.py         # Unit tests (no network required)
├── pyproject.toml              # Project metadata & build config
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Development dependencies
├── LICENSE                     # MIT License
├── README.md                   # English documentation (this file)
├── README_CN.md                # Chinese documentation
└── examples/
    ├── claude_desktop_config.json   # Claude Desktop config example
    ├── cursor_mcp_config.json       # Cursor config example
    └── cline_mcp_settings.json      # Cline config example
```

---

## Development

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### Linting & Type Checking

```bash
ruff check src/ tests/
mypy src/
```

### Architecture

```
┌─────────────────┐     MCP (stdio/SSE)     ┌──────────────────┐
│  MCP Client      │ ◄───────────────────► │  bioicons-mcp     │
│  (Claude, etc.)  │                         │  Server           │
└─────────────────┘                         └────────┬──────────┘
                                                     │
                                                     │ Async HTTP
                                                     ▼
                                            ┌──────────────────┐
                                            │  bioicons.com    │
                                            │  (GitHub Pages)  │
                                            │                  │
                                            │  icons.json      │
                                            │  categories.json │
                                            │  authors.json    │
                                            │  */icon.svg      │
                                            └──────────────────┘
```

**Key design decisions:**

1. **`BioiconsClient`** communicates with bioicons.com via `httpx.AsyncClient`, fetching JSON metadata in parallel and caching it for 1 hour.
2. **`IconInfo`** is an immutable dataclass (`frozen=True, slots=True`) with a `matches_query` method that mirrors the bioicons.com website's search logic.
3. **`constants.py`** centralises all static information for easy maintenance when the upstream site changes.
4. **SVG URL construction** follows bioicons.com's deterministic path: `/icons/{license}/{category}/{author}/{name}.svg`.

---

## Licensing

### This MCP Server

The server code is licensed under the **MIT License**. See [LICENSE](./LICENSE).

### Icons on bioicons.com

Icons accessed through this server are hosted by bioicons.com and each has its own license. **Always check and respect the license of each icon you download.**

| License | Attribution required | Notes |
|---------|---------------------|-------|
| CC0 | No | Public domain, free to use |
| CC BY 3.0/4.0 | Yes | Attribute the author |
| CC BY-SA 3.0/4.0 | Yes | Attribute + share-alike |
| MIT | Yes | Retain copyright notice |
| BSD | Yes | Retain copyright notice |

**Attribution example:**

> alanine icon by B--Gideon-Bergheim is licensed under CC0 (https://creativecommons.org/publicdomain/zero/1.0/)

---

## FAQ

### Q1: I get `ModuleNotFoundError: No module named 'mcp'`

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Q2: Search returns no results

- Verify network access to `https://bioicons.com`
- The search is case-insensitive but requires all whitespace-separated tokens to appear in the icon name
- Try broader keywords (e.g. "DNA" instead of "dna_replication_fork")

### Q3: Tools don't appear in Claude Desktop

- Restart Claude Desktop
- Check the JSON syntax of your config file
- Verify the Python path is correct (use an absolute path)

### Q4: Can I use this offline?

bioicons.com is a static website and metadata must be fetched online. Offline mode is not currently supported, but you could manually download `icons.json` and modify `client.py` to read from a local file.

### Q5: Which Python versions are supported?

Python 3.10 and above.

---

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](./CONTRIBUTING.md) before submitting a pull request.

To report a security vulnerability, see our [Security Policy](./SECURITY.md).

---

---

## Disclaimer

This project is a **third-party, unofficial** MCP server implementation for bioicons.com. It is **not** created, maintained, or endorsed by bioicons.com or its creator Simon Duerr. The official bioicons.com website is independently operated at [https://bioicons.com](https://bioicons.com).

This project simply provides an MCP adapter that interfaces with the publicly accessible data on bioicons.com. All icons accessed through this server remain the property of their respective authors and are subject to their individual licenses.

---

*This project is an independent, third-party community MCP adapter and is not officially affiliated with or endorsed by bioicons.com.*
