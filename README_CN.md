# Bioicons MCP Server · 中文文档

> ⚠️ **第三方实现 / 非官方**
>
> 这是一个**社区独立开发**的 MCP 服务器，**并非** bioicons.com 的官方 MCP 服务器。
> 本项目与 bioicons.com 及其创建者无任何官方关联、认可或赞助关系。
> bioicons.com 官方网站地址：[https://bioicons.com](https://bioicons.com)

> **版本 0.1.0**
>
> 适配 [bioicons.com](https://bioicons.com/) 的 Model Context Protocol (MCP) 服务器

---

## 目录

1. [项目简介](#项目简介)
2. [功能特性](#功能特性)
3. [快速开始](#快速开始)
4. [安装方式](#安装方式)
5. [配置 MCP 客户端](#配置-mcp-客户端)
6. [工具详解](#工具详解)
7. [提示词（Prompts）](#提示词prompts)
8. [传输模式](#传输模式)
9. [项目结构](#项目结构)
10. [开发指南](#开发指南)
11. [许可证说明](#许可证说明)
12. [常见问题](#常见问题)

---

## 项目简介

**Bioicons MCP Server** 是一个基于 [Model Context Protocol](https://modelcontextprotocol.io/)（MCP，模型上下文协议）的服务器，它将 [bioicons.com](https://bioicons.com/) ——一个收录了 **2800+** 张高质量科学插图的免费图库——接入到各类支持 MCP 的 AI 客户端（如 Claude Desktop、Cursor、Cline 等）中。

借助本服务器，AI 助手能够：

- 🔍 **搜索** bioicons.com 上的全部图标
- 📋 **查看** 图标的元数据（名称、分类、许可证、作者）
- 📥 **下载** SVG 格式的图标文件到本地
- 🏷️ **了解** 每个图标的许可证与署名要求

> **什么是 bioicons.com？**
>
> bioicons.com 由 Simon Duerr 创建，是一个面向生命科学领域的开放插图库，所有图标均以 SVG 矢量格式提供，涵盖 CC0、CC BY、CC BY-SA、MIT、BSD 等宽松许可证，可直接用于 Inkscape、Adobe Illustrator 或 Microsoft Office 等软件中绘制科学论文插图。

---

## 功能特性

| 特性 | 说明 |
|------|------|
| ✅ 全文搜索 | 支持按关键词搜索图标，多关键词以空格分隔，全部匹配才返回 |
| ✅ 分类筛选 | 支持按 37 个生物科学分类筛选图标 |
| ✅ 许可证筛选 | 支持按 CC0 / CC BY / CC BY-SA / MIT / BSD 筛选 |
| ✅ SVG 获取 | 直接获取图标的 SVG 源码 |
| ✅ 本地下载 | 将 SVG 文件保存到指定目录 |
| ✅ 元数据查询 | 返回图标的完整信息，包括许可证链接与署名要求 |
| ✅ 双语支持 | 分类描述支持中文和英文 |
| ✅ stdio 传输 | 适用于 Claude Desktop、Cursor 等本地客户端 |
| ✅ SSE 传输 | 适用于远程 / Web 客户端 |
| ✅ 内存缓存 | 元数据缓存在内存中，减少网络请求 |
| ✅ 提示词模板 | 内置「查找科学图标」提示词模板 |

---

## 快速开始

### 环境要求

- **Python ≥ 3.10**
- 网络可访问 `https://bioicons.com`
- 一个支持 MCP 的客户端（推荐 [Claude Desktop](https://claude.ai/download) 或 [Cursor](https://cursor.com)）

### 一分钟上手

```bash
# 1. 克隆 / 进入项目目录
cd Bioicons-MCP

# 2. 安装依赖（推荐使用虚拟环境）
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# 3. 安装本包（开发模式）
pip install -e .

# 4. 验证安装
bioicons-mcp --help
```

看到如下输出即表示安装成功：

```
usage: bioicons-mcp [-h] [--transport {stdio,sse}] [--host HOST] [--port PORT]

MCP server for bioicons.com — high quality science illustrations.
```

---

## 安装方式

### 方式一：从源码安装（推荐）

```bash
git clone <你的仓库地址> Bioicons-MCP
cd Bioicons-MCP
pip install -e .
```

### 方式二：仅用 pip 安装依赖后直接运行

```bash
cd Bioicons-MCP
pip install -r requirements.txt
python -m bioicons_mcp --transport stdio
```

---

## 配置 MCP 客户端

### Claude Desktop

编辑 Claude Desktop 的配置文件：

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

添加以下内容：

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

> 如果使用了虚拟环境，请将 `python` 替换为虚拟环境中 Python 解释器的完整路径，例如 `C:\\Bioicons-MCP\\.venv\\Scripts\\python.exe`。

### Cursor

在 Cursor 的 `Settings → MCP` 中添加新的 MCP Server：

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

在 `.cline/mcp_settings.json` 中添加：

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

### SSE 模式（远程部署）

先启动 SSE 服务器：

```bash
bioicons-mcp --transport sse --host 0.0.0.0 --port 8080
```

然后在客户端配置中填写 SSE URL：

```
http://<服务器IP>:8080/sse
```

---

## 工具详解

本服务器提供 **5 个工具**，AI 客户端可自动调用。

### 1. `list_categories` — 列出所有分类

列出 bioicons.com 上的全部图标分类，每个分类附带图标数量与中英文描述。

**参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `language` | `string` (`"en"` / `"zh"`) | 否 | `"en"` | 描述语言 |

**示例调用：**

```
list_categories(language="zh")
```

**示例输出：**

```
# bioicons.com 图标分类列表
Total icons: 2829

- **All_icons** (2829 icons): bioicons.com 上的全部图标
- **Amino-Acids** (31 icons): 氨基酸插图
- **Animals** (384 icons): 动物与模式生物插图
- **Chemistry** (92 icons): 化学插图
...
```

### 2. `search_icons` — 搜索图标

按关键词搜索图标，支持分类和许可证筛选。

**参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | `string` | ✅ | — | 搜索关键词（空格分隔多关键词） |
| `category` | `string` | 否 | `"All_icons"` | 分类筛选 |
| `license` | `string` | 否 | `""` | 许可证筛选 |
| `limit` | `integer` | 否 | `50` | 最大返回数量（上限 500） |

**示例调用：**

```
search_icons(query="alanine", category="Amino-Acids", limit=10)
```

**示例输出：**

```
# Search results for 'alanine' (2 icons found)

1. **alanine**
   - Category: Amino-Acids
   - License: CC0 (Public Domain) (`cc-0`)
   - Author: B--Gideon-Bergheim
   - SVG URL: https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg

2. **alanine_chem**
   ...
```

**许可证取值参考：**

| 许可证 slug | 全称 | 是否需要署名 |
|-------------|------|-------------|
| `cc-0` | CC0 (公共领域) | 否 |
| `cc-by-3.0` | CC BY 3.0 | 是 |
| `cc-by-4.0` | CC BY 4.0 | 是 |
| `cc-by-sa-3.0` | CC BY-SA 3.0 | 是 |
| `cc-by-sa-4.0` | CC BY-SA 4.0 | 是 |
| `mit` | MIT | 是 |
| `bsd` | BSD 3-Clause | 是 |

### 3. `get_icon` — 获取图标 SVG 内容

获取指定图标的 SVG 源码。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `string` | ✅ | 图标名称（不含 `.svg` 后缀） |
| `category` | `string` | 否 | 分类 slug，用于精确定位 |
| `license` | `string` | 否 | 许可证 slug，用于精确定位 |
| `author` | `string` | 否 | 作者 slug，用于精确定位 |

> 如果只提供 `name`，将返回第一个名称匹配的图标。

**示例调用：**

```
get_icon(name="alanine")
```

**示例输出：**

```
# Icon: alanine
Category: Amino-Acids
License: cc-0
Author: B--Gideon-Bergheim
Source URL: https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg

## SVG Content

```svg
<svg xmlns="http://www.w3.org/2000/svg" ...>
  ...
</svg>
```
```

### 4. `download_icon` — 下载图标到本地

将图标的 SVG 文件下载保存到本地文件系统。

**参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | `string` | ✅ | — | 图标名称 |
| `save_dir` | `string` | 否 | `"."` | 保存目录（不存在会自动创建） |
| `filename` | `string` | 否 | 图标名 | 自定义文件名 |
| `category` | `string` | 否 | `""` | 分类 slug |
| `license` | `string` | 否 | `""` | 许可证 slug |
| `author` | `string` | 否 | `""` | 作者 slug |

**示例调用：**

```
download_icon(name="PyTorch", save_dir="./icons", filename="pytorch.svg")
```

**示例输出：**

```
# Icon downloaded successfully

- **Name**: PyTorch
- **Category**: Machine_Learning
- **License**: BSD 3-Clause (`bsd`)
- **Author**: Facebook
- **Source URL**: https://bioicons.com/icons/bsd/Machine_Learning/Facebook/PyTorch.svg
- **Saved to**: `/home/user/icons/pytorch.svg`
- **File size**: 1234 bytes

> ⚠️ **Attribution required**: This icon is licensed under BSD 3-Clause.
> You must attribute the author (Facebook) and link to
> https://opensource.org/licenses/BSD-3-Clause.
```

### 5. `get_icon_info` — 查看图标详情

返回图标的完整元数据，包括许可证全称、URL 和署名要求。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `string` | ✅ | 图标名称 |
| `category` | `string` | 否 | 分类 slug |
| `license` | `string` | 否 | 许可证 slug |
| `author` | `string` | 否 | 作者 slug |

**示例输出（JSON）：**

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
  "svg_url": "https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg",
  "bioicons_page": "https://bioicons.com/"
}
```

---

## 提示词（Prompts）

本服务器内置一个可复用的提示词模板：

### `find_science_icons`

根据自然语言描述查找科学插图。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `description` | `string` | ✅ | 对所需图标的自然语言描述 |
| `category` | `string` | 否 | 可选的分类限定 |

**使用示例：**

> "帮我找一个 DNA 双螺旋的图标"

AI 将自动调用 `search_icons` 工具，搜索 `DNA` 关键词，并返回最相关的图标建议。

---

## 传输模式

### stdio 模式（默认）

适用于本地运行的 MCP 客户端（Claude Desktop、Cursor 等）。

```bash
bioicons-mcp                       # 默认 stdio
bioicons-mcp --transport stdio     # 显式指定
```

### SSE 模式

适用于远程部署或 Web 客户端访问。

```bash
bioicons-mcp --transport sse --host 0.0.0.0 --port 8080
```

SSE 端点：

- 连接 URL: `http://<host>:<port>/sse`
- 消息端点: `http://<host>:<port>/messages/`

---

## 项目结构

```
Bioicons-MCP/
├── src/
│   └── bioicons_mcp/
│       ├── __init__.py        # 包初始化，版本号
│       ├── __main__.py        # 支持 python -m bioicons_mcp 运行
│       ├── server.py          # MCP Server 核心实现（工具、提示词、传输）
│       ├── client.py          # bioicons.com 异步 API 客户端（带缓存）
│       ├── models.py          # IconInfo 数据模型
│       ├── constants.py       # 常量：URL、许可证、分类描述
│       └── py.typed           # PEP 561 类型标记
├── tests/
│   └── test_server.py         # 单元测试（无需网络）
├── pyproject.toml              # 项目元数据与构建配置
├── requirements.txt            # 运行时依赖
├── requirements-dev.txt        # 开发依赖
├── LICENSE                     # MIT 许可证
├── README.md                   # 英文文档
├── README_CN.md                # 中文文档（本文件）
└── examples/
    ├── claude_desktop_config.json   # Claude Desktop 配置示例
    ├── cursor_mcp_config.json       # Cursor 配置示例
    └── cline_mcp_settings.json      # Cline 配置示例
```

---

## 开发指南

### 运行测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 代码风格检查

```bash
ruff check src/ tests/
mypy src/
```

### 架构说明

```
┌─────────────────┐     MCP (stdio/SSE)     ┌──────────────────┐
│  MCP 客户端      │ ◄───────────────────► │  bioicons-mcp     │
│  (Claude等)      │                         │  Server           │
└─────────────────┘                         └────────┬──────────┘
                                                     │
                                                     │ 异步 HTTP
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

**关键设计：**

1. **`BioiconsClient`** 负责与 bioicons.com 通信，使用 `httpx.AsyncClient` 异步下载 JSON 元数据，并缓存 1 小时。
2. **`IconInfo`** 是不可变的数据模型（`frozen=True, slots=True`），提供 `matches_query` 方法实现与 bioicons.com 网站一致的搜索逻辑。
3. **`constants.py`** 集中管理所有静态信息，便于上游网站变更时一键更新。
4. **SVG URL 构造** 遵循 bioicons.com 的路径规则：`/icons/{license}/{category}/{author}/{name}.svg`。

---

## 许可证说明

### 本项目代码

本项目（MCP Server 代码）采用 **MIT 许可证**，详见 [LICENSE](./LICENSE)。

### bioicons.com 上的图标

通过本服务器访问的图标由 bioicons.com 托管，各图标拥有独立的许可证。**使用任何图标前，请务必检查其许可证并遵守相应要求。**

| 许可证 | 是否需要署名 | 说明 |
|--------|-------------|------|
| CC0 | 否 | 公共领域，可自由使用 |
| CC BY 3.0/4.0 | 是 | 需署名作者 |
| CC BY-SA 3.0/4.0 | 是 | 需署名且衍生作品须以相同许可证发布 |
| MIT | 是 | 需保留版权声明 |
| BSD | 是 | 需保留版权声明 |

**署名示例：**

> alanine icon by B--Gideon-Bergheim is licensed under CC0 (https://creativecommons.org/publicdomain/zero/1.0/)

---

## 常见问题

### Q1: 启动时报错 `ModuleNotFoundError: No module named 'mcp'`

请确保已安装依赖：

```bash
pip install -r requirements.txt
```

### Q2: 搜索不到图标？

- 检查网络是否能访问 `https://bioicons.com`
- 图标名称区分大小写，但搜索本身不区分大小写
- 多关键词搜索时，所有关键词都必须出现在图标名称中

### Q3: Claude Desktop 中看不到工具？

- 重启 Claude Desktop
- 检查配置文件 JSON 语法是否正确
- 确认 Python 路径正确（推荐使用绝对路径）

### Q4: 如何在无网络环境下使用？

bioicons.com 是静态网站，元数据需要在线获取。目前不支持离线模式，但你可以手动下载 `icons.json` 并修改 `client.py` 从本地读取。

### Q5: 支持哪些 Python 版本？

Python 3.10 及以上版本。

---

## 贡献指南

欢迎提交 Pull Request！请先阅读 [贡献指南](./CONTRIBUTING.md)。

如需报告安全漏洞，请参阅 [安全政策](./SECURITY.md)。

---

---

## 免责声明

本项目是 bioicons.com 的**第三方、非官方** MCP 服务器实现。本项目**并非**由 bioicons.com 或其创建者 Simon Duerr 创建、维护或认可。bioicons.com 官方网站独立运营于 [https://bioicons.com](https://bioicons.com)。

本项目仅提供一个 MCP 适配器，用于与 bioicons.com 上公开可访问的数据进行交互。通过本服务器访问的所有图标仍归各自作者所有，并受其各自许可证的约束。

---

*本项目与 bioicons.com 无官方关联，仅为社区开发的第三方 MCP 适配器。*
