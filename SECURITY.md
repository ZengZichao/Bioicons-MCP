# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅ Active support  |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please:

1. Email the maintainers directly (if a security contact is listed in the repository).
2. Or open a **private** [GitHub Security Advisory](https://github.com/bioicons-mcp/bioicons-mcp/security/advisories/new).

Please include:

- A description of the vulnerability
- Steps to reproduce
- The potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and strive to provide a fix or mitigation within 7 days.

## Security Measures

This project implements the following security measures:

- **Path traversal protection**: The `download_icon` tool sanitises filenames to prevent directory traversal attacks.
- **Input validation**: All tool inputs are validated against JSON schemas.
- **No arbitrary code execution**: The server only fetches static SVG files and JSON metadata from bioicons.com.
- **Read-only filesystem access**: The server only writes SVG files to user-specified directories.

## Scope

This security policy covers the MCP server code only. Icons accessed through bioicons.com are subject to their respective licenses and are outside the scope of this policy.
