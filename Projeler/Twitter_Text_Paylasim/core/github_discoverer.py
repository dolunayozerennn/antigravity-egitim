"""GitHub Repo Discoverer.

Stratejisi:
  1. Çoklu topic search (ai-agents, llm, automation, langchain, mcp...)
  2. Filtre: son 90 gün içinde push, en az 50 yıldız, README var
  3. Skor üretimi tweet_writer'a bırakılır — buraya sadece sıralama düşer
  4. Notion dedup ile son 30 günde işlenmiş repo atlanır

Çıktı: List of repo_data dicts, en yüksek puanlıdan başlayarak
"""

from datetime import datetime, timezone, timedelta

import requests

from ops_logger import get_ops_logger
from config import settings

ops = get_ops_logger("Twitter_Text_Paylasim", "GithubDiscoverer")

GH_API = "https://api.github.com"

# AI/agent/automation odaklı topicler — birincil hedef kitle
PRIMARY_TOPICS = [
    "ai-agents", "llm-agents", "agentic-ai", "ai-automation",
    "langchain", "langgraph", "mcp", "n8n", "autogen", "crewai",
]

# Daha geniş AI alanı — sayı az çıkarsa fallback
SECONDARY_TOPICS = [
    "llm", "rag", "openai", "anthropic-claude", "ai-tools",
]


class GithubDiscoverer:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _search_by_topic(self, topic: str, min_stars: int = 50,
                        days_back: int = 90, per_page: int = 10) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).date().isoformat()
        q = f"topic:{topic} pushed:>{cutoff} stars:>={min_stars}"
        params = {"q": q, "sort": "stars", "order": "desc", "per_page": per_page}
        try:
            r = requests.get(f"{GH_API}/search/repositories",
                            headers=self.headers, params=params, timeout=20)
            r.raise_for_status()
            return r.json().get("items", [])
        except Exception as e:
            ops.warning(f"Topic search hatası ({topic}): {e}")
            return []

    def _fetch_readme(self, full_name: str) -> str:
        """README'nin ilk 4000 karakterini döner."""
        try:
            r = requests.get(f"{GH_API}/repos/{full_name}/readme",
                            headers={**self.headers, "Accept": "application/vnd.github.raw"},
                            timeout=20)
            if r.status_code == 200:
                return r.text[:4000]
            return ""
        except Exception as e:
            ops.warning(f"README fetch hatası ({full_name}): {e}")
            return ""

    def discover_candidates(self, max_candidates: int = 8) -> list[dict]:
        """Aday repo listesi döner, deduplicate edilmiş."""
        seen = set()
        candidates = []

        # Primary topic'leri dolaş, her topic'ten en iyi 5
        for topic in PRIMARY_TOPICS:
            for item in self._search_by_topic(topic, per_page=5):
                full_name = item.get("full_name", "")
                if full_name and full_name not in seen:
                    seen.add(full_name)
                    candidates.append(self._normalize(item))
            if len(candidates) >= max_candidates * 2:
                break

        # Yetersizse secondary'lere bak
        if len(candidates) < max_candidates:
            for topic in SECONDARY_TOPICS:
                for item in self._search_by_topic(topic, per_page=3, min_stars=200):
                    full_name = item.get("full_name", "")
                    if full_name and full_name not in seen:
                        seen.add(full_name)
                        candidates.append(self._normalize(item))
                if len(candidates) >= max_candidates * 2:
                    break

        # Star'a göre sırala, en iyi N'i README ile zenginleştir
        candidates.sort(key=lambda c: c.get("stars", 0), reverse=True)
        top = candidates[:max_candidates]

        for c in top:
            c["readme_excerpt"] = self._fetch_readme(c["full_name"])

        ops.info(f"GitHub keşif: {len(top)} aday repo (toplam {len(candidates)} bulundu)")
        return top

    def _normalize(self, item: dict) -> dict:
        return {
            "full_name": item.get("full_name", ""),
            "url": item.get("html_url", ""),
            "description": item.get("description") or "",
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language") or "",
            "pushed_at": item.get("pushed_at", ""),
        }
