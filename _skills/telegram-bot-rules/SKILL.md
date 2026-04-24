---
name: telegram-bot-rules
description: Official best practices and operational rules for Telegram bots within Antigravity projects. Solves common concurrency issues, specifically the getUpdates conflict, and establishes notification standards.
license: MIT
metadata:
  author: antigravity
  version: "1.0.0"
  organization: Antigravity
  date: April 2026
  abstract: Defines the standard operating procedures for integrating and running Telegram bots. Addresses the critical "Conflict: terminated by other getUpdates request" error by mandating environment separation. Sets rules for choosing the right framework (python-telegram-bot v20+) and preventing alarm fatigue by restricting Telegram notifications to P1 incidents.
---

# Telegram Bot Rules (AI Best Practices)

Telegram is frequently used across Antigravity projects for system alerts, human-in-the-loop approvals, and monitoring (e.g., `eCom_Reklam_Otomasyonu`, `Ceren` projects). Strictly adhere to the following rules to ensure stable, conflict-free bot operations.

## 1. The Single-Instance Rule (Conflict Resolution)

**The Problem:** The error `Conflict: terminated by other getUpdates request` occurs when two scripts try to run the same bot using `polling()` simultaneously (e.g., your local machine and the Railway production server).
**The Rules:**
- **Local Development:** When testing a bot locally, you MUST ensure the production instance on Railway is either paused, or you must use a separate `TELEGRAM_DEV_TOKEN`.
- **Production Architecture:** For high-availability projects, prefer **Webhooks** over `getUpdates` polling. If polling must be used (due to Railway lacking a static IP or complex webhook setup), strictly enforce a single worker instance in `railway.toml`. Never run multiple replicas of a polling bot.

## 2. Framework Selection

- **Rule:** Always use **`python-telegram-bot` (version 20+)** because it natively supports `asyncio`.
- **Action:** Avoid using `pyTelegramBotAPI` (`telebot`) or older versions of `python-telegram-bot` as they are synchronous and will block the event loop, causing performance bottlenecks in concurrent Antigravity nodes.
- **Pattern:** All handlers must be `async def`, and network calls must use `await`.

## 3. Alarm Fatigue & Notification Tiers

- **Rule:** Do NOT use Telegram as a dump for standard `INFO` or `DEBUG` logs.
- **Action:** 
  - **P1 (Critical):** Fatal crashes, database disconnections, or failed payments. **Send to Telegram.**
  - **P2 (Warning):** Temporary rate limits or minor retryable errors. **Log to file/Supabase only.** Do not send a Telegram message.
  - **P3 (Info):** "Script started" or "Job finished successfully." **Send a single summary message at the end of a long process.** Do not send a message for every step.

## 4. Robust Error Handling

Telegram API can timeout or become unreachable temporarily.
- **Rule:** Bots must not crash due to transient Telegram API errors.
- **Action:** Catch specific exceptions like `telegram.error.TimedOut`, `telegram.error.NetworkError`, and `telegram.error.RetryAfter`. Implement exponential backoff for `RetryAfter`.

## 5. Security & Tokens

- **Rule:** Never hardcode the `TELEGRAM_TOKEN` or `TELEGRAM_CHAT_ID`.
- **Action:** Retrieve them strictly via `os.getenv()`. Fail fast on boot if these variables are missing, unless Telegram notifications are strictly marked as an optional feature in the specific project's configuration.
