"""Constants and metadata for the Bioicons MCP server.

This module centralises every piece of *static* information about bioicons.com
that the server needs at runtime: the base URL, the JSON metadata endpoints, the
list of supported licences / categories, and the licence display names.

Keeping these values in one place makes it trivial to update them if the upstream
bioicons.com website changes its URL scheme or adds new categories.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Upstream URLs
# ---------------------------------------------------------------------------

#: Root URL of the bioicons.com website.
BIOICONS_BASE_URL: Final[str] = "https://bioicons.com"

#: Endpoint that returns the full icon metadata as a JSON array.
ICONS_JSON_URL: Final[str] = f"{BIOICONS_BASE_URL}/icons/icons.json"

#: Endpoint that returns the category list as a JSON array.
CATEGORIES_JSON_URL: Final[str] = f"{BIOICONS_BASE_URL}/icons/categories.json"

#: Endpoint that returns the author list as a JSON array.
AUTHORS_JSON_URL: Final[str] = f"{BIOICONS_BASE_URL}/icons/authors.json"

# ---------------------------------------------------------------------------
# SVG download URL template
# ---------------------------------------------------------------------------
#
# The SVG file for every icon follows a deterministic path on bioicons.com:
#
#   /icons/{license}/{category}/{author}/{icon_name}.svg
#
# For example, the "alanine" amino-acid icon by B--Gideon-Bergheim under CC-0 is
# available at:
#
#   https://bioicons.com/icons/cc-0/Amino-Acids/B--Gideon-Bergheim/alanine.svg
#
# The *icon metadata* stores ``license`` in a lower-case slug form (``cc-0``,
# ``cc-by-sa`` …) which is exactly what appears in the URL path.

#: Format string for building a direct SVG download URL.
SVG_URL_TEMPLATE: Final[str] = (
    f"{BIOICONS_BASE_URL}/icons/{{license}}/{{category}}/{{author}}/{{name}}.svg"
)

# ---------------------------------------------------------------------------
# Server identity
# ---------------------------------------------------------------------------

SERVER_NAME: Final[str] = "bioicons-mcp"
SERVER_VERSION: Final[str] = "0.1.0"

# ---------------------------------------------------------------------------
# Licence metadata
# ---------------------------------------------------------------------------
#
# The ``license`` field in icons.json uses a lower-case slug.  We map each slug
# to a human-readable display name and a URL pointing to the full licence text
# so that the MCP tools can return rich attribution information.

LICENSE_INFO: Final[dict[str, dict[str, str]]] = {
    "cc-0": {
        "name": "CC0 (Public Domain)",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "requires_attribution": "no",
    },
    "cc-by-3.0": {
        "name": "CC BY 3.0",
        "url": "https://creativecommons.org/licenses/by/3.0/",
        "requires_attribution": "yes",
    },
    "cc-by-4.0": {
        "name": "CC BY 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
        "requires_attribution": "yes",
    },
    "cc-by-sa-3.0": {
        "name": "CC BY-SA 3.0",
        "url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "requires_attribution": "yes",
    },
    "cc-by-sa-4.0": {
        "name": "CC BY-SA 4.0",
        "url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "requires_attribution": "yes",
    },
    "mit": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
        "requires_attribution": "yes",
    },
    "bsd": {
        "name": "BSD 3-Clause",
        "url": "https://opensource.org/licenses/BSD-3-Clause",
        "requires_attribution": "yes",
    },
}

# ---------------------------------------------------------------------------
# Human-readable category descriptions (English)
# ---------------------------------------------------------------------------

CATEGORY_DESCRIPTIONS_EN: Final[dict[str, str]] = {
    "All_icons": "All available icons on bioicons.com",
    "Procedures": "Laboratory and scientific procedures",
    "Blood_Immunology": "Blood cells and immunology illustrations",
    "Viruses": "Virus structure and morphology illustrations",
    "Parasites": "Parasite illustrations",
    "Scientific_graphs": "Scientific graphs and charts",
    "Receptors_channels": "Cell receptors and ion channels",
    "Microbiology": "Microbiology illustrations",
    "Animals": "Animal and model organism illustrations",
    "Imaging": "Imaging and microscopy illustrations",
    "People-Other": "People and other illustrations",
    "General_items": "General laboratory items",
    "Neuroscience": "Neuroscience illustrations",
    "Lab_apparatus": "Laboratory apparatus and equipment",
    "Plants_Algae": "Plants and algae illustrations",
    "Tissues": "Tissue and histology illustrations",
    "Epigenetics": "Epigenetics illustrations",
    "Extracellular_matrix": "Extracellular matrix illustrations",
    "Human_physiology": "Human physiology illustrations",
    "Nucleic_acids": "Nucleic acid illustrations (DNA, RNA)",
    "Cell_types": "Cell type illustrations",
    "Machine_Learning": "Machine learning framework logos",
    "Cell_culture": "Cell culture illustrations",
    "Oncology": "Oncology and cancer illustrations",
    "Chemistry": "Chemistry illustrations",
    "Chemo-_and_Bioinformatics": "Chemoinformatics and bioinformatics illustrations",
    "Genomics": "Genomics illustrations",
    "Molecular_modelling": "Molecular modelling illustrations",
    "Nanotechnology": "Nanotechnology illustrations",
    "Intracellular_components": "Intracellular component illustrations",
    "Peptides": "Peptide illustrations",
    "Molecular_Biology": "Molecular biology illustrations",
    "Genetics": "Genetics illustrations",
    "Cell_lines": "Cell line illustrations",
    "Safety_symbols": "Laboratory safety symbols",
    "Cell_membrane": "Cell membrane illustrations",
    "Computer_hardware": "Computer hardware illustrations",
    "Amino-Acids": "Amino acid illustrations",
}

# ---------------------------------------------------------------------------
# Human-readable category descriptions (Chinese)
# ---------------------------------------------------------------------------

CATEGORY_DESCRIPTIONS_ZH: Final[dict[str, str]] = {
    "All_icons": "bioicons.com 上的全部图标",
    "Procedures": "实验室与科学操作流程",
    "Blood_Immunology": "血液细胞与免疫学插图",
    "Viruses": "病毒结构与形态插图",
    "Parasites": "寄生虫插图",
    "Scientific_graphs": "科学图表",
    "Receptors_channels": "细胞受体与离子通道",
    "Microbiology": "微生物学插图",
    "Animals": "动物与模式生物插图",
    "Imaging": "成像与显微镜插图",
    "People-Other": "人物及其他插图",
    "General_items": "实验室通用物品",
    "Neuroscience": "神经科学插图",
    "Lab_apparatus": "实验室仪器与设备",
    "Plants_Algae": "植物与藻类插图",
    "Tissues": "组织学与切片插图",
    "Epigenetics": "表观遗传学插图",
    "Extracellular_matrix": "细胞外基质插图",
    "Human_physiology": "人体生理学插图",
    "Nucleic_acids": "核酸插图（DNA、RNA）",
    "Cell_types": "细胞类型插图",
    "Machine_Learning": "机器学习框架徽标",
    "Cell_culture": "细胞培养插图",
    "Oncology": "肿瘤学插图",
    "Chemistry": "化学插图",
    "Chemo-_and_Bioinformatics": "化学信息学与生物信息学插图",
    "Genomics": "基因组学插图",
    "Molecular_modelling": "分子建模插图",
    "Nanotechnology": "纳米技术插图",
    "Intracellular_components": "细胞内组分插图",
    "Peptides": "多肽插图",
    "Molecular_Biology": "分子生物学插图",
    "Genetics": "遗传学插图",
    "Cell_lines": "细胞系插图",
    "Safety_symbols": "实验室安全符号",
    "Cell_membrane": "细胞膜插图",
    "Computer_hardware": "计算机硬件插图",
    "Amino-Acids": "氨基酸插图",
}

# ---------------------------------------------------------------------------
# HTTP settings
# ---------------------------------------------------------------------------

#: Default timeout for HTTP requests (seconds).
HTTP_TIMEOUT: Final[float] = 30.0

#: Maximum number of icons returned by ``search_icons`` when no explicit limit
#: is provided.
DEFAULT_SEARCH_LIMIT: Final[int] = 50

#: Hard ceiling for the number of icons returned in a single search to avoid
#: overloading the MCP client.
MAX_SEARCH_LIMIT: Final[int] = 500
