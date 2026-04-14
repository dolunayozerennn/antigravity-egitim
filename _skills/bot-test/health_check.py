#!/usr/bin/env python3
"""
Bot Health Check — Telegram Bot Canlılık Kontrolü
==================================================
Tüm Telegram bot'ların (YouTube, eCom, Shorts, Supplement) durumunu kontrol eder.

Kontroller:
  1. Telegram Bot API getMe → token geçerli mi, bot adı doğru mu
  2. Railway deployment status → son deploy başarılı mı
  3. Railway deployment logs → FATAL hata pattern'i var mı

Kullanım:
  python3 health_check.py              # Tüm kontroller
  python3 health_check.py --telegram   # Sadece Telegram API
  python3 health_check.py --railway    # Sadece Railway kontrol
  python3 health_check.py --json       # JSON çıktı
  python3 health_check.py --quick      # Sadece Telegram (env yükleme dahil, hızlı)

Çıkış Kodu:
  0 = Tüm botlar sağlıklı
  1 = En az bir bot'ta sorun var
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# master.env'den token oku
MASTER_ENV = Path(__file__).resolve().parents[2] / "_knowledge" / "credentials" / "master.env"


def _load_env():
    """master.env dosyasından environment variable'ları yükle."""
    if not MASTER_ENV.exists():
        print(f"⚠️  master.env bulunamadı: {MASTER_ENV}")
        return
    for line in MASTER_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()

# ══════════════════════════════════════════
# 📌 BOT TANIMLARI
# ══════════════════════════════════════════

BOTS = [
    {
        "name": "YouTube Otomasyonu",
        "emoji": "📺",
        "token_env": "TELEGRAM_YOUTUBE_BOT_TOKEN",
        "railway_project_id": "87e24335-52c9-460f-8b2e-0f481f5501bd",
        "railway_service_id": "d17abb9e-3ef1-4f50-98c1-f4290bb2f090",
        "railway_env_id": "30bb2f27-0297-4148-88f0-d28f2ac58a6c",
        "type": "worker",
    },
    {
        "name": "eCom Reklam Otomasyonu",
        "emoji": "🛒",
        "token_env": "TELEGRAM_ECOM_BOT_TOKEN",
        "railway_project_id": "8797307d-7b80-41cb-add0-976c09eaeed4",
        "railway_service_id": "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a",
        "railway_env_id": "b8353ac5-0ec4-4785-8d72-7aae17f18e56",
        "type": "worker",
    },
    {
        "name": "Shorts Demo Botu",
        "emoji": "🎬",
        "token_env": "TELEGRAM_SHORTS_BOT_TOKEN",
        "railway_project_id": "01bf8d6e-9eb4-4a42-aaa0-0103e6e56033",
        "railway_service_id": "151725ce-0416-41dd-9b94-768353c919b5",
        "railway_env_id": "64704cfe-b15e-4cb0-9256-e89575da34c4",
        "type": "worker",
    },
    {
        "name": "Supplement Analyzer",
        "emoji": "💊",
        "token_env": "TELEGRAM_SUPPLEMENT_BOT_TOKEN",
        "railway_project_id": "35acfbc5-f058-45f9-ba76-373b47e66b07",
        "railway_service_id": "0a3f240f-6fea-4176-b480-a2cdb99e4a93",
        "railway_env_id": "6f09ea79-49b6-4414-b820-6c83d5bd31cb",
        "type": "worker",
    },
]

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN", "")
RAILWAY_GQL_URL = "https://backboard.railway.com/graphql/v2"

# Fatal hata pattern'leri
FATAL_PATTERNS = [
    "AttributeError", "ImportError", "SyntaxError", "ModuleNotFoundError",
    "Traceback (most recent call last)", "CRASHED", "EnvironmentError",
    "RuntimeError", "TypeError: ", "NameError: ",
]


# ══════════════════════════════════════════
# 🔍 TELEGRAM API KONTROLÜ
# ══════════════════════════════════════════

def check_telegram_bot(bot: dict) -> dict:
    """Telegram Bot API getMe ile bot'un canlılığını kontrol eder."""
    import urllib.request
    import urllib.error

    token = os.environ.get(bot["token_env"], "")
    result = {
        "name": bot["name"],
        "emoji": bot["emoji"],
        "type": bot.get("type", "worker"),
        "telegram_ok": False,
        "telegram_detail": "",
        "bot_username": "",
    }

    if not token:
        result["telegram_detail"] = f"Token bulunamadı: {bot['token_env']}"
        return result

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("ok"):
                bot_info = data["result"]
                result["telegram_ok"] = True
                result["bot_username"] = f"@{bot_info.get('username', '?')}"
                result["telegram_detail"] = (
                    f"Bot aktif: {result['bot_username']} "
                    f"(ID: {bot_info.get('id')})"
                )
            else:
                result["telegram_detail"] = f"API yanıtı OK değil: {data}"
    except urllib.error.HTTPError as e:
        result["telegram_detail"] = f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        result["telegram_detail"] = f"Bağlantı hatası: {e}"

    return result


# ══════════════════════════════════════════
# 🚂 RAILWAY KONTROLÜ
# ══════════════════════════════════════════

def _railway_gql(query: str, variables: dict = None) -> dict:
    """Railway GraphQL API sorgusu."""
    import urllib.request

    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        RAILWAY_GQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {RAILWAY_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def check_railway_deployment(bot: dict) -> dict:
    """Railway'den son deployment durumunu kontrol eder."""
    result = {
        "railway_ok": False,
        "railway_detail": "",
        "railway_status": "",
        "deploy_date": "",
        "fatal_errors": [],
    }

    if not RAILWAY_TOKEN:
        result["railway_detail"] = "RAILWAY_TOKEN bulunamadı"
        return result

    # Son deployment'ı al
    query = """
    query ($serviceId: String!, $environmentId: String!) {
        deployments(
            input: {
                serviceId: $serviceId
                environmentId: $environmentId
            }
            first: 1
        ) {
            edges {
                node {
                    id
                    status
                    createdAt
                }
            }
        }
    }
    """
    try:
        resp = _railway_gql(query, {
            "serviceId": bot["railway_service_id"],
            "environmentId": bot["railway_env_id"],
        })

        edges = resp.get("data", {}).get("deployments", {}).get("edges", [])
        if not edges:
            result["railway_detail"] = "Deployment bulunamadı"
            return result

        deploy = edges[0]["node"]
        status = deploy["status"]
        deploy_id = deploy["id"]
        created = deploy["createdAt"]

        result["railway_status"] = status
        result["deploy_date"] = created[:10]  # YYYY-MM-DD

        if status in ("SUCCESS", "DEPLOYING"):
            result["railway_ok"] = True
            result["railway_detail"] = f"Deploy OK: {status} ({created[:16]})"
        else:
            result["railway_detail"] = f"Deploy SORUNLU: {status} ({created[:16]})"

        # Son logları kontrol et (fatal pattern)
        log_query = """
        query ($deploymentId: String!) {
            deploymentLogs(deploymentId: $deploymentId, limit: 100) {
                ... on DeploymentLog {
                    message
                    timestamp
                    severity
                }
            }
        }
        """
        try:
            log_resp = _railway_gql(log_query, {"deploymentId": deploy_id})
            logs = log_resp.get("data", {}).get("deploymentLogs", [])
            if isinstance(logs, list):
                for log_entry in logs:
                    msg = log_entry.get("message", "") if isinstance(log_entry, dict) else str(log_entry)
                    for pattern in FATAL_PATTERNS:
                        if pattern in msg:
                            result["fatal_errors"].append(msg[:200])
                            break

                if result["fatal_errors"]:
                    result["railway_ok"] = False
                    result["railway_detail"] += f" | ⚠️ {len(result['fatal_errors'])} fatal hata tespit edildi"
        except Exception as e:
            # Log sorgusu başarısız — deployment durumu yeterli
            result["railway_detail"] += f" | Log sorgusu başarısız: {e}"

    except Exception as e:
        result["railway_detail"] = f"Railway API hatası: {e}"

    return result


# ══════════════════════════════════════════
# 📋 RAPOR
# ══════════════════════════════════════════

def run_all_checks(telegram_only=False, railway_only=False) -> list:
    """Tüm kontrolleri çalıştır ve sonuçları döndür."""
    results = []

    for bot in BOTS:
        t_start = time.time()
        bot_result = {"name": bot["name"], "emoji": bot["emoji"], "type": bot.get("type", "worker")}

        if not railway_only:
            tg = check_telegram_bot(bot)
            bot_result.update(tg)

        if not telegram_only:
            rw = check_railway_deployment(bot)
            bot_result.update(rw)

        bot_result["check_duration"] = round(time.time() - t_start, 1)
        results.append(bot_result)

    return results


def print_report(results: list, total_duration: float = 0) -> bool:
    """Konsola rapor yazdır."""
    print(f"\n{'='*60}")
    print(f"🧪 BOT HEALTH CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if total_duration > 0:
        print(f"⏱️  Toplam süre: {total_duration:.1f} saniye")
    print(f"{'='*60}")

    all_ok = True
    has_warning = False
    total_checks = 0
    passed_checks = 0

    for r in results:
        deploy_info = f" — Deploy: {r.get('deploy_date', '?')}" if r.get("deploy_date") else ""
        timing = f" ({r.get('check_duration', 0):.1f}s)" if r.get("check_duration") else ""
        print(f"\n{r['emoji']} {r['name']}{deploy_info}")
        print(f"{'─'*40}")

        # Telegram (KRİTİK — başarısız olursa all_ok = False)
        if "telegram_ok" in r:
            total_checks += 1
            icon = "✅" if r["telegram_ok"] else "❌"
            print(f"  {icon} Telegram: {r['telegram_detail']}")
            if r["telegram_ok"]:
                passed_checks += 1
            else:
                all_ok = False

        # Railway (BİLGİLENDİRME — API erişilemezse uyarı verir ama all_ok bozmaz)
        if "railway_ok" in r:
            total_checks += 1
            is_api_error = "API hatası" in r.get("railway_detail", "") or "bulunamadı" in r.get("railway_detail", "")
            if is_api_error:
                print(f"  ⚠️  Railway:  {r['railway_detail']} (API erişilemedi — Telegram kontrolü yeterli)")
                has_warning = True
                passed_checks += 1  # API erişilemezse geçti say (Telegram yeterli)
            else:
                icon = "✅" if r["railway_ok"] else "❌"
                print(f"  {icon} Railway:  {r['railway_detail']}")
                if r["railway_ok"]:
                    passed_checks += 1
                else:
                    all_ok = False

            # Fatal errors
            if r.get("fatal_errors"):
                print(f"  🔴 Fatal hatalar ({len(r['fatal_errors'])}):")
                for i, err in enumerate(r["fatal_errors"][:5]):
                    print(f"     {i+1}. {err[:120]}")

        print(f"  ⏱️  Kontrol süresi: {timing}")

    print(f"\n{'='*60}")
    print(f"📊 Kontrol: {passed_checks}/{total_checks} geçti")

    if all_ok and not has_warning:
        print(f"✅ TÜM BOTLAR SAĞLIKLI")
    elif all_ok and has_warning:
        print(f"✅ BOTLAR AKTİF (Railway API erişilemedi — Telegram kontrolü yeterli)")
    else:
        failed_bots = []
        for r in results:
            tg_fail = "telegram_ok" in r and not r["telegram_ok"]
            rw_fail = "railway_ok" in r and not r["railway_ok"] and "API hatası" not in r.get("railway_detail", "") and "bulunamadı" not in r.get("railway_detail", "")
            if tg_fail or rw_fail:
                failed_bots.append(r["name"])
        print(f"❌ DİKKAT: SORUN TESPİT EDİLDİ → {', '.join(failed_bots)}")
    print(f"{'='*60}\n")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Bot Health Check")
    parser.add_argument("--telegram", action="store_true", help="Sadece Telegram API kontrolü")
    parser.add_argument("--railway", action="store_true", help="Sadece Railway kontrolü")
    parser.add_argument("--json", action="store_true", help="JSON çıktı")
    parser.add_argument("--quick", action="store_true", help="Hızlı kontrol (sadece Telegram)")
    args = parser.parse_args()

    # --quick = --telegram
    if args.quick:
        args.telegram = True

    t_total_start = time.time()

    results = run_all_checks(
        telegram_only=args.telegram,
        railway_only=args.railway,
    )

    total_duration = time.time() - t_total_start

    if args.json:
        # JSON modda fatal_errors listesini kısalt
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(total_duration, 1),
            "bots": [],
        }
        for r in results:
            bot_data = {k: v for k, v in r.items() if k != "fatal_errors"}
            if "fatal_errors" in r:
                bot_data["fatal_error_count"] = len(r["fatal_errors"])
                bot_data["fatal_errors"] = r["fatal_errors"][:3]
            output["bots"].append(bot_data)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        all_ok = all(
            r.get("telegram_ok", True) and r.get("railway_ok", True)
            for r in results
        )
    else:
        all_ok = print_report(results, total_duration)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
