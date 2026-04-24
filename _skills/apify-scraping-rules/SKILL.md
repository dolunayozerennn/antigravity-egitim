---
name: apify-scraping-rules
description: Official best practices for using Apify for web scraping and automation. Emphasizes finding and utilizing existing Actors from the Apify Store over writing custom scraping scripts, and details the robust creation of new Actors using Crawlee.
license: MIT
metadata:
  author: antigravity
  version: "1.0.0"
  organization: Antigravity
  date: April 2026
  abstract: Defines the standard operating procedures for web scraping and data extraction in the Antigravity ecosystem using Apify. Mandates the use of pre-built Apify Store Actors (e.g., Google Maps Email Extractor, Instagram Profile Scraper) to bypass anti-bot systems automatically. When custom scraping is required, defines the rules for Actor development using CheerioCrawler vs PlaywrightCrawler, proxy usage, and Apify SDK storage mechanisms.
---

# Apify Scraping Rules (AI Best Practices)

Web scraping is a core component of Antigravity projects like `Web_Site_Satis_Otomasyonu` and `Ceren`. Because modern websites aggressively block automated traffic, raw Python/Node scraping scripts (e.g., raw BeautifulSoup or Selenium) are heavily discouraged. Always use Apify.

## 1. Actor Discovery & Selection (Critical)

**Rule: DO NOT reinvent the wheel.** The Apify Store contains over 4,500 production-ready scraping tools (Actors) that handle proxies, CAPTCHAs, and browser fingerprinting out of the box.

- **Action:** When tasked with extracting data from a major platform, ALWAYS search the Apify Store first.
- **Examples:**
  - **Google Maps:** Use `Google Maps Email Extractor` (`WnMxbsRLNbPeYL6ge`) or `Google Maps Scraper` (`Compass`).
  - **Instagram:** Use `Instagram Profile Scraper` (`dSCLg0C3YEZ83HzYX`) or `Instagram Scraper` (`apify/instagram-scraper`).
  - **LinkedIn:** Search for specialized LinkedIn lead generation actors.
- **Integration:** Call these actors via the Apify API (`apify-client` in Python) using the `APIFY_API_TOKEN` stored in `master.env`.

## 2. API & SDK Integration

When calling existing Actors from Python code:
- **Rule:** Use the official `apify-client` library.
- **Pattern:** Always run the actor, wait for it to finish, and stream the results from the default dataset.
  ```python
  from apify_client import ApifyClient
  client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
  
  # Start the actor and wait for it to finish
  run = client.actor("actor_id").call(run_input={"search": "query"})
  
  # Fetch results
  for item in client.dataset(run["defaultDatasetId"]).iterate_items():
      print(item)
  ```

## 3. Custom Actor Development (If Store Actor Doesn't Exist)

If you must build a custom scraper because the target is a niche website, build it as an Apify Actor using Crawlee (Node.js/TypeScript) or the Apify Python SDK.

- **Crawlee Selection:** 
  - ALWAYS default to `CheerioCrawler` (or `BeautifulSoup` in Python) for static HTML pages. It is 10x faster and cheaper.
  - ONLY use `PlaywrightCrawler` if the website heavily relies on Client-Side Rendering (React/Vue) or requires complex interactions (login, clicking).
- **Anti-Blocking:** Always enable Apify Proxy (`proxyConfiguration`). Never scrape from the raw server IP.
- **Data Storage:** Do not save data to local files (`.csv` or `.json` on disk). Use Apify's `Dataset` for tabular data (pushData) and `KeyValueStore` for files/images.
- **Logging:** Use the official logger (e.g., `import { log } from 'apify';`) to ensure sensitive data is censored and logs are formatted correctly in the Apify Console.

## 4. Local Testing & Deployment

- **Local Run:** Before deploying, always test the actor locally using `apify run`. Ensure the input schema (`INPUT_SCHEMA.json`) works correctly.
- **Deployment:** Use `apify push` to deploy the actor to the cloud.

## 5. Cost Estimation & Rate Limiting

- **Rule:** Be mindful of Compute Units (CUs). Playwright is much more expensive than Cheerio. When running large loops over Apify API, ensure you don't exhaust the monthly credit limit.
- **Batching:** Pass multiple URLs or search terms in a single Actor run rather than triggering the Actor 100 separate times via the API. Each run has a boot-up cost.
