---
name: notion-api-rules
description: Official best practices and operational rules for interacting with Notion. Covers dual-mode execution (MCP for local agent tasks, API/SDK for production code), search-before-create paradigms, pagination, and deterministic ID management.
license: MIT
metadata:
  author: antigravity
  version: "1.0.0"
  organization: Antigravity
  date: April 2026
  abstract: Defines the standard operating procedures for integrating with Notion within the Antigravity ecosystem. Emphasizes the distinction between local agent actions via Notion MCP and production implementation. Mandates strict idempotency (search before create), secure credential management, and robust error handling for API limits.
---

# Notion API Rules (AI Best Practices)

Notion is a core data layer for many Antigravity projects (e.g., Web_Site_Satis_Otomasyonu). Because Notion rate limits can be strict and data duplication is a common issue, strictly adhere to the following rules when writing production code or performing local tasks.

## 1. Dual-Mode Execution (Local vs. Production)

Antigravity operates in two modes regarding Notion:
- **Local Agent Mode (MCP):** When you (the AI) need to interact with Notion directly during development (e.g., to read a database, check existing data, or create a quick test page), **use the `notion-mcp-server` tools**. Do NOT write custom Python scripts just to read data locally if an MCP tool exists.
- **Production Mode (Code):** When writing code that will run in production (e.g., on Railway), use the official Notion SDK (`notion-client` for Python) or raw API requests. Rely on the project's specific `notion_helper.py` or `notion_service.py` if it exists.

## 2. Idempotency: Search BEFORE Create (Critical)

Never blindly create pages or database items.
- **Rule:** Before creating a new entry (e.g., a new lead in CRM, a new invoice), query the database (`mcp_notion-mcp-server_API-query-data-source` or API equivalent) using a unique identifier (like Email, Domain, or ID).
- **Action:** If the record exists, **Update** it. If it does not exist, **Create** it.
- **Why:** Prevents massive duplication in CRM databases if a script is run multiple times.

## 3. Deterministic ID Management

- **Rule:** Never guess or hardcode Database IDs or Page IDs in the middle of business logic.
- **Action:** All Notion IDs (Database IDs, Parent Page IDs) MUST be defined in configuration files (e.g., `config.py` or `.env`).
- **MCP Usage:** If you need to find a Database ID locally, use `mcp_notion-mcp-server_API-post-search` to search by title, retrieve the ID, and then add it to the project's config.

## 4. Security & Credentials

- **Token Name:** The Notion API token is ALWAYS referenced as `NOTION_TOKEN` in environment variables.
- **Rule:** NEVER hardcode the `NOTION_TOKEN` in scripts or print it in logs.
- **Access:** When running production code, ensure the `NOTION_TOKEN` has been explicitly shared with the target Notion Database (via the "Connections" menu in Notion).

## 5. Rate Limiting & Pagination

- **Rate Limits:** Notion API limits are typically 3 requests per second. When writing production loops, implement a slight delay or use exponential backoff to handle `429 Too Many Requests` errors.
- **Pagination:** Always respect the `has_more` and `next_cursor` fields when retrieving database items or block children. Never assume a single query will return all results.

## 6. Dangerous Operations

- **Rule:** DO NOT perform bulk deletes or massive destructive updates on Notion databases without explicit user confirmation.
- **Action:** If a user requests a cleanup, simulate the action first (count the items to be deleted), present the number, and wait for a "Proceed" command.
