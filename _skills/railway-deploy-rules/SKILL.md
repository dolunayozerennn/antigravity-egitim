---
name: railway-deploy-rules
description: Official best practices and operational rules for deploying and managing services on Railway. Covers configuration as code, startup delays, health checks, and API integration.
license: MIT
metadata:
  author: antigravity
  version: "1.0.0"
  organization: Antigravity
  date: April 2026
  abstract: Defines the standard operating procedures for integrating and deploying projects to Railway within the Antigravity ecosystem. Focuses on robust deployment patterns to prevent crash loops, strict environment variable management, and using the Railway GraphQL API for automated CI/CD processes.
---

# Railway Deploy Rules (AI Best Practices)

Railway is the primary deployment platform for Antigravity production services. To ensure maximum uptime and prevent deployment failures, strictly adhere to the following rules when creating, modifying, or deploying Railway projects.

## 1. Startup & Boot Sequence (Critical)

A common issue in automated deployments is rapid boot-looping or hitting external API rate limits immediately upon startup (e.g., all workers fetching from Notion simultaneously).
- **Rule:** Implement a stagger or startup delay mechanism where applicable.
- **Action:** Utilize a `STARTUP_DELAY_SECONDS` environment variable to pause script execution briefly at boot (e.g., `time.sleep(int(os.getenv("STARTUP_DELAY_SECONDS", 0)))`). This allows external APIs to settle and prevents stampedes.

## 2. Configuration as Code

- **Rule:** Prefer defining infrastructure and build commands in code rather than clicking through the Railway UI.
- **Action:** Use a `railway.toml` file or a `Procfile` at the root of the project to explicitly define the `[build]` and `[deploy]` phases.
  - *Example:* `startCommand = "python src/main.py"`
- **Why:** Ensures that any Agent checking out the repository knows exactly how the project is built and run, making migrations and rollbacks deterministic.

## 3. Environment Variable Management

- **Rule:** Never hardcode secrets. Ever.
- **Action:** All credentials (`NOTION_TOKEN`, `API_KEY`, `DATABASE_URL`) MUST be read from environment variables using `os.getenv()`.
- **Pre-flight Check:** Production scripts should "fail-fast" at boot if critical environment variables are missing. Do not wait for a function call deep in the code to throw an error.
  - *Example:* `if not os.getenv("NOTION_TOKEN"): raise ValueError("NOTION_TOKEN missing")`

## 4. API & CLI Integration

- **Rule:** When the Agent needs to interact with Railway (e.g., to trigger a redeploy, check status, or inject variables), use the Railway GraphQL API.
- **Authentication:** Use `curl` commands authenticated with the `RAILWAY_TOKEN` (retrieved from `_knowledge/credentials/master.env`).
- **Forbidden Action:** Do not use browser subagents to navigate the Railway dashboard.

## 5. Health Checks & Observability

- **Rule:** Services should expose their status if they are web servers.
- **Action:** If deploying an API (FastAPI, Flask), always include a `/health` endpoint that returns a 200 OK. Railway uses this to determine if the deployment was successful.
- **Logging:** Use standard output (`stdout`) and standard error (`stderr`) for all logging. Railway automatically captures these. Avoid writing log files to the local disk, as Railway's ephemeral filesystem will wipe them upon restart.

## 6. Pre-Deploy Safety (The /canli-yayina-al Workflow)

- **Rule:** Never push broken code to the `main` branch, as it triggers automatic Railway deployments.
- **Action:** Always run syntax checks, import verifications, and basic smoke tests locally before pushing to GitHub. If the code breaks locally, DO NOT push.
