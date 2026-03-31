#!/usr/bin/env python3
"""
🏥 Antigravity Servis İzleyici — Railway Edition (v4)
=====================================================
Railway üzerinde çalışan bağımsız izleme servisi.
deploy-registry.md yerine gömülü config + env variable kullanır.

Kontrol kapsamı:
  • Railway servislerinin deployment durumu (SUCCESS/FAILED/CRASHED)
  • Son 24 saatlik deployment loglarını tarama
  • 🩺 Bilinen hataları otomatik düzeltme (self-healing)
  • 📧 Sorun tespit edildiğinde e-posta bildirimi

Kaldırılan (lokal) özellikler:
  ✘ LaunchAgent / cron kontrolü (artık gereksiz — Railway kendisi çalıştırıyor)
  ✘ Lokal klasör varlık kontrolü
  ✘ Eski plist tespiti
"""

import os
import re
import ssl
import sys
import json
import time
import logging
import smtplib
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ── SSL Context ───────────────────────────────────────────
def _create_ssl_context():
    """SSL context oluşturur."""
    ctx = ssl.create_default_context()
    try:
        urllib.request.urlopen("https://railway.app", timeout=5, context=ctx)
        return ctx
    except Exception:
        return ssl._create_unverified_context()

_ssl_ctx = _create_ssl_context()

# ── Sabitler ──────────────────────────────────────────────
RAILWAY_GQL_URL = "https://backboard.railway.app/graphql/v2"
ALERT_EMAIL = "EMAIL_ADRESI_BURAYA"
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"

# Alarm verilmeyecek durumlar
HEALTHY_STATUSES = {"SUCCESS", "SLEEPING", "BUILDING", "DEPLOYING", "INITIALIZING", "WAITING"}
TRANSIENT_STATUSES = {"BUILDING", "DEPLOYING", "INITIALIZING", "WAITING", "SLEEPING"}
ALERT_STATUSES = {"FAILED", "CRASHED", "REMOVED"}

# Log tarama pattern'ları
ERROR_PATTERNS = re.compile(
    r"(ERROR|Exception|Traceback|FAILED|CRITICAL|panic|fatal|killed|OOMKilled|segfault)",
    re.IGNORECASE,
)

# Yanlış pozitif (false positive) mesajlar — bunlar hata DEĞİL
FALSE_POSITIVE_PATTERNS = re.compile(
    r"("
    r"Score is exceptionally high"
    r"|Accepting this as the final image"
    r"|exceptionally high.*accepting"
    r"|Successfully"
    r"|Critique:.*Excellent"
    r"|Excellent execution"
    r"|Log verisi alınamadı"
    r")",
    re.IGNORECASE,
)

# Servis-izleyicinin kendi çıktılarını tekrar hata olarak algılamasını engelle
SELF_REFERENCE_PATTERN = re.compile(
    r"("
    r"→"
    r"|\]\s+→"
    r"|\]\s+\[\d{4}-\d{2}-\d{2}"
    r"|hata bulundu:"
    r"|hata tespit edildi"
    r"|hata:"
    r"|📋 Log taranıyor"
    r"|⚠️\s+Son 24 saatte"
    r"|📧 Alarm e-postası"
    r"|📧 Self-heal raporu"
    r"|🚨 API Hatası"
    r"|🚨 Sorunlu:"
    r"|🩺 OTOMATİK İYİLEŞTİRME"
    r"|🩺 İYİLEŞTİRME SONUCU"
    r"|❓.*Bilinmeyen hata"
    r"|❌ Düzeltilemedi"
    r"|✅ Düzeltildi"
    r"|📧 Manuel müdahale"
    r")",
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════
# ██  PROJE REGISTRY (Gömülü — env ile override edilebilir)
# ══════════════════════════════════════════════════════════

DEFAULT_PROJECTS = [
    {
        "name": "shorts-demo-bot",
        "platform": "railway",
        "project_id": "01bf8d6e-9eb4-4a42-aaa0-0103e6e56033",
        "service_id": "151725ce-0416-41dd-9b94-768353c919b5",
        "environment_id": "64704cfe-b15e-4cb0-9256-e89575da34c4",
        "github_repo": "GITHUB_USERNAME_BURAYA/shorts-demo-bot",
    },
    {
        "name": "marka-email-automation",
        "platform": "railway",
        "project_id": "0c1ff084-c7a2-4e46-8372-2fb9c58ec6e4",
        "service_id": "08224222-4d79-43ec-b649-1a8ac4c8c8ad",
        "environment_id": "6b719f66-e9a6-45d3-81b5-a566fabb829f",
        "github_repo": "GITHUB_USERNAME_BURAYA/marka-email-automation",
    },
    {
        "name": "tele-satis-crm",
        "platform": "railway",
        "project_id": "f23cb036-8434-497e-911b-5df08d6b49e6",
        "service_id": "faba9665-7499-4ab7-9e8a-d2a26050733f",
        "environment_id": "be2153d6-97b5-4b47-84f9-9bb679693b78",
        "github_repo": "GITHUB_USERNAME_BURAYA/tele-satis-crm",
    },
    {
        "name": "kullanici-reels-kapak",
        "platform": "railway",
        "project_id": "fed6db49-de57-4fbe-9988-528416f1b668",
        "service_id": "98fa5736-7e6f-454a-a648-22e47a92c28a",
        "environment_id": "f555d0bb-125e-4d15-838e-dbeb2936a721",
        "github_repo": "GITHUB_USERNAME_BURAYA/kullanici-reels-kapak",
    },
    {
        "name": "lead-notifier-bot",
        "platform": "railway",
        "project_id": "f23cb036-8434-497e-911b-5df08d6b49e6",
        "service_id": "4d0cfb99-8b2a-4585-86b3-44cc4967bc59",
        "environment_id": "be2153d6-97b5-4b47-84f9-9bb679693b78",
        "github_repo": "GITHUB_USERNAME_BURAYA/lead-notifier-bot",
    },
]


def load_projects() -> list:
    """
    Projeleri yükler.
    Önce PROJECTS_JSON env variable'ı kontrol eder (override için).
    Yoksa gömülü DEFAULT_PROJECTS kullanılır.
    """
    projects_json = os.environ.get("PROJECTS_JSON")
    if projects_json:
        try:
            return json.loads(projects_json)
        except json.JSONDecodeError:
            logging.warning("⚠️ PROJECTS_JSON parse edilemedi, varsayılan liste kullanılıyor.")
    return DEFAULT_PROJECTS


# ── Credentials ──────────────────────────────────────────
def load_credentials() -> dict:
    """Env variable'lardan token bilgilerini yükler."""
    return {
        "RAILWAY_TOKEN": os.environ.get("RAILWAY_TOKEN", ""),
        "SMTP_USER": os.environ.get("SMTP_USER", ""),
        "SMTP_APP_PASSWORD": os.environ.get("SMTP_APP_PASSWORD", ""),
    }


# ── Railway GraphQL ──────────────────────────────────────
def _gql_request(token: str, query: str, variables: dict) -> dict:
    """Railway GraphQL API'ye istek gönderir."""
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")

    req = urllib.request.Request(
        RAILWAY_GQL_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Antigravity-HealthCheck/4.0-Railway",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return {"errors": [{"message": f"HTTP {e.code}: {body[:200]}"}]}
    except urllib.error.URLError as e:
        return {"errors": [{"message": f"Bağlantı hatası: {e.reason}"}]}
    except Exception as e:
        return {"errors": [{"message": str(e)}]}


def query_railway(token: str, project_id: str, service_id: str, environment_id: str = None) -> dict:
    """Railway deployment durumunu sorgular."""
    if not environment_id:
        env_query = """
        query($projectId: String!) {
            project(id: $projectId) {
                environments { edges { node { id name } } }
            }
        }
        """
        env_result = _gql_request(token, env_query, {"projectId": project_id})
        if env_result and "data" in env_result:
            edges = env_result["data"]["project"]["environments"]["edges"]
            if edges:
                environment_id = edges[0]["node"]["id"]
            else:
                return {"error": "Environment bulunamadı"}

    query = """
    query($projectId: String!, $serviceId: String!, $environmentId: String!) {
        deployments(
            first: 1,
            input: {
                projectId: $projectId,
                serviceId: $serviceId,
                environmentId: $environmentId
            }
        ) {
            edges {
                node { id status createdAt staticUrl }
            }
        }
    }
    """
    variables = {
        "projectId": project_id,
        "serviceId": service_id,
        "environmentId": environment_id,
    }

    result = _gql_request(token, query, variables)
    if not result or "errors" in result:
        error_msg = result.get("errors", [{}])[0].get("message", "Bilinmeyen hata") if result else "API yanıt vermedi"
        return {"error": error_msg}

    edges = result.get("data", {}).get("deployments", {}).get("edges", [])
    if not edges:
        return {"status": "NO_DEPLOYMENTS", "message": "Hiç deployment bulunamadı"}

    node = edges[0]["node"]
    return {
        "status": node.get("status", "UNKNOWN"),
        "deployment_id": node.get("id"),
        "created_at": node.get("createdAt"),
        "url": node.get("staticUrl"),
        "environment_id": environment_id,
    }


def query_railway_deployment_logs(token: str, deployment_id: str, limit: int = 500) -> list:
    """Railway deployment loglarını çeker."""
    query = """
    query($deploymentId: String!, $limit: Int) {
        deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
            timestamp message severity
        }
    }
    """
    variables = {"deploymentId": deployment_id, "limit": limit}
    result = _gql_request(token, query, variables)

    if not result or "errors" in result:
        alt_query = """
        query($deploymentId: String!, $limit: Int) {
            deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
                ... on Log { timestamp message severity }
            }
        }
        """
        result = _gql_request(token, alt_query, variables)
        if not result or "errors" in result:
            return []

    logs = result.get("data", {}).get("deploymentLogs", [])
    return logs if isinstance(logs, list) else []


def analyze_logs_for_errors(logs: list, hours: int = 24) -> dict:
    """Log listesini analiz eder, son N saat içindeki hataları bulur."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    errors = []
    warnings = []

    for log_entry in logs:
        msg = ""
        ts = None
        severity = ""

        if isinstance(log_entry, dict):
            msg = log_entry.get("message", "")
            severity = log_entry.get("severity", "").upper()
            ts_str = log_entry.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    ts = None
        elif isinstance(log_entry, str):
            msg = log_entry
        else:
            continue

        if ts and ts < cutoff:
            continue

        if ERROR_PATTERNS.search(msg):
            if FALSE_POSITIVE_PATTERNS.search(msg):
                continue
            if SELF_REFERENCE_PATTERN.search(msg):
                continue
            if severity in ("ERROR", "CRITICAL", "FATAL"):
                errors.append(msg.strip()[:200])
            elif "warning" in msg.lower():
                warnings.append(msg.strip()[:200])
            else:
                errors.append(msg.strip()[:200])

    return {
        "error_count": len(errors),
        "errors": errors[-10:],
        "warning_count": len(warnings),
    }


# ── Zaman Yardımcısı ────────────────────────────────────
def format_time_ago(iso_time: str) -> str:
    """ISO zaman damgasını 'X saat/gün/dk önce' formatına çevirir."""
    try:
        deploy_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - deploy_time
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)} dk önce"
        elif hours < 24:
            return f"{hours} saat önce"
        else:
            return f"{hours // 24} gün önce"
    except Exception:
        return "—"


# ══════════════════════════════════════════════════════════
# ██  ANA KONTROL FONKSİYONLARI
# ══════════════════════════════════════════════════════════

def check_railway_projects(projects: list, token: str, deep_scan: bool = True) -> list:
    """Railway projelerini kontrol eder. deep_scan=True ise logları da tarar."""
    results = []
    railway_projects = [p for p in projects if p.get("platform") == "railway"]

    if not railway_projects:
        logging.info("  ℹ️  Railway projesi bulunamadı")
        return results

    for project in railway_projects:
        time.sleep(1)  # Rate limit
        name = project["name"]
        logging.info(f"  🔍 {name}")

        result_entry = {"name": name, "platform": "railway", "status": "UNKNOWN", "problems": []}

        deploy_result = query_railway(
            token=token,
            project_id=project.get("project_id", ""),
            service_id=project.get("service_id", ""),
            environment_id=project.get("environment_id"),
        )

        if "error" in deploy_result:
            result_entry["status"] = "API_ERROR"
            result_entry["problems"].append(deploy_result["error"])
            logging.error(f"     🚨 API Hatası: {deploy_result['error']}")
        else:
            status = deploy_result.get("status", "UNKNOWN")
            created_at = deploy_result.get("created_at", "")
            time_info = format_time_ago(created_at) if created_at else "—"
            result_entry["status"] = status
            result_entry["time_info"] = time_info

            if status in ALERT_STATUSES:
                result_entry["problems"].append(f"Deployment {status} (son deploy: {time_info})")
                logging.error(f"     🚨 {status} (son deploy: {time_info})")
            elif status in TRANSIENT_STATUSES:
                logging.info(f"     ⏳ {status} (geçici durum, {time_info})")
            else:
                logging.info(f"     ✅ {status} (son deploy: {time_info})")

            # Deep scan: log taraması
            if deep_scan and deploy_result.get("deployment_id"):
                logging.info(f"     📋 Log taranıyor...")
                logs = query_railway_deployment_logs(token, deploy_result["deployment_id"])
                if logs:
                    log_analysis = analyze_logs_for_errors(logs, hours=24)
                    result_entry["log_analysis"] = log_analysis
                    if log_analysis["error_count"] > 0:
                        logging.warning(f"     ⚠️  Son 24 saatte {log_analysis['error_count']} hata bulundu:")
                        for err in log_analysis["errors"][:3]:
                            logging.warning(f"        → {err[:120]}")
                        result_entry["problems"].append(
                            f"Son 24 saatte {log_analysis['error_count']} hata tespit edildi"
                        )
                    else:
                        logging.info(f"     ✅ Son 24 saatte hata yok")
                else:
                    logging.info(f"     ℹ️  Log verisi alınamadı")

        results.append(result_entry)
    return results


# ══════════════════════════════════════════════════════════
# ██  SELF-HEALING
# ══════════════════════════════════════════════════════════

# Healing playbook — gömülü (ayrı dosya gerektirmiyor)
HEALING_PLAYBOOK = {
    "version": "2.0",
    "description": "Railway-native healing playbook",
    "rate_limits": {
        "max_redeploy_per_hour": 2,
        "max_redeploy_per_day": 5,
        "cooldown_minutes": 30,
    },
    "patterns": [
        {
            "id": "railway_crashed",
            "match": "CRASHED",
            "context": "railway_status",
            "action": "redeploy",
            "description": "Railway servisi crash olmuş — otomatik redeploy",
        },
        {
            "id": "railway_failed",
            "match": "FAILED",
            "context": "railway_status",
            "action": "redeploy",
            "description": "Railway deployment başarısız — otomatik redeploy",
        },
        {
            "id": "railway_removed",
            "match": "REMOVED",
            "context": "railway_status",
            "action": "alert_only",
            "description": "Servis kaldırılmış — manuel müdahale gerekli",
        },
        {
            "id": "ssl_transient",
            "match": r"SSL.*Error|SSLError|CERTIFICATE_VERIFY_FAILED|ssl\.SSLError|EOF occurred in violation of protocol",
            "context": "railway_log",
            "action": "ignore_transient",
            "description": "Geçici SSL hatası — kendi kendine düzelir",
            "wait_minutes": 60,
        },
        {
            "id": "invalid_grant",
            "match": r"invalid_grant|Token has been expired|token.*revoked",
            "context": "railway_log",
            "action": "alert_only",
            "description": "OAuth token süresi dolmuş — token.json yenilenmeli",
        },
        {
            "id": "oom_killed",
            "match": r"OOMKilled|out of memory|Cannot allocate memory",
            "context": "railway_log",
            "action": "redeploy",
            "description": "Bellek yetersizliği — redeploy ile temiz başlangıç",
        },
        {
            "id": "rate_limit",
            "match": r"rate.?limit|429|Too Many Requests",
            "context": "railway_log",
            "action": "ignore_transient",
            "description": "API rate limit — geçici, kendi kendine düzelir",
            "wait_minutes": 30,
        },
        {
            "id": "connection_error",
            "match": r"ConnectionError|ConnectionRefused|Connection reset|ECONNREFUSED",
            "context": "railway_log",
            "action": "ignore_transient",
            "description": "Geçici bağlantı hatası — kendi kendine düzelir",
            "wait_minutes": 15,
        },
        {
            "id": "api_transient_connection",
            "match": r"Remote end closed|handshake.*timed out|Connection unexpectedly closed|closed connection without response",
            "context": "railway_log",
            "action": "ignore_transient",
            "description": "Geçici API bağlantı hatası — kendi kendine düzelir",
            "wait_minutes": 30,
        },
    ],
}

# In-memory heal state (Railway'de /tmp kullanılabilir ama restart'ta sıfırlanır)
_heal_state = {"actions": [], "last_cleanup": datetime.now(timezone.utc).isoformat()}


def check_rate_limit(project_name: str, action: str) -> bool:
    """Rate limit kontrolü. True = aksiyon alınabilir."""
    now = datetime.now(timezone.utc)
    rate_limits = HEALING_PLAYBOOK["rate_limits"]
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    one_day_ago = (now - timedelta(hours=24)).isoformat()

    recent_actions = _heal_state.get("actions", [])

    if action == "redeploy":
        hourly = sum(1 for a in recent_actions
                     if a["project"] == project_name and a["action"] == "redeploy"
                     and a["timestamp"] > one_hour_ago)
        if hourly >= rate_limits.get("max_redeploy_per_hour", 2):
            logging.warning(f"  ⛔ Rate limit: {project_name} saatlik redeploy limiti aşıldı")
            return False

        daily = sum(1 for a in recent_actions
                    if a["project"] == project_name and a["action"] == "redeploy"
                    and a["timestamp"] > one_day_ago)
        if daily >= rate_limits.get("max_redeploy_per_day", 5):
            logging.warning(f"  ⛔ Rate limit: {project_name} günlük redeploy limiti aşıldı")
            return False

    # Cooldown
    cooldown_min = rate_limits.get("cooldown_minutes", 30)
    cooldown_cutoff = (now - timedelta(minutes=cooldown_min)).isoformat()
    recent_same = [a for a in recent_actions
                   if a["project"] == project_name and a["action"] == action
                   and a["timestamp"] > cooldown_cutoff]
    if recent_same:
        logging.warning(f"  ⏳ Cooldown: {project_name} — {cooldown_min}dk bekleme süresi dolmadı")
        return False

    return True


def record_action(project_name: str, action: str, success: bool, detail: str = ""):
    """Aksiyonu state'e kaydeder."""
    _heal_state["actions"].append({
        "project": project_name,
        "action": action,
        "success": success,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # 24 saatten eski kayıtları temizle
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    _heal_state["actions"] = [a for a in _heal_state["actions"] if a["timestamp"] > cutoff]


def classify_problem(problem: dict) -> dict | None:
    """Sorunu playbook kalıplarıyla eşleştirir."""
    status = problem.get("status", "")
    detail = problem.get("detail", "")
    platform = problem.get("platform", "")

    for pattern in HEALING_PLAYBOOK["patterns"]:
        regex = pattern.get("match", "")
        context = pattern.get("context", "")

        try:
            compiled = re.compile(regex, re.IGNORECASE)
        except re.error:
            continue

        if context == "railway_status" and platform == "railway":
            if compiled.search(status):
                return pattern
        elif context == "railway_log" and platform == "railway":
            if compiled.search(detail):
                return pattern

    return None


def railway_redeploy(token: str, project_info: dict) -> dict:
    """Railway servisini yeniden deploy eder."""
    service_id = project_info.get("service_id", "")
    environment_id = project_info.get("environment_id", "")

    if not all([service_id, environment_id]):
        return {"success": False, "detail": "Eksik proje bilgileri"}

    mutation = """
    mutation($environmentId: String!, $serviceId: String!) {
        serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
    }
    """
    result = _gql_request(token, mutation, {
        "environmentId": environment_id,
        "serviceId": service_id,
    })

    if result and "errors" not in result:
        return {"success": True, "detail": "Redeploy başlatıldı"}
    else:
        error_msg = result.get("errors", [{}])[0].get("message", "Bilinmeyen hata") if result else "API yanıt vermedi"
        return {"success": False, "detail": f"Redeploy başarısız: {error_msg}"}


def attempt_heal(problem: dict, project_info: dict, token: str) -> dict:
    """Tek bir sorunu düzeltmeye çalışır."""
    result = {
        "healed": False,
        "action": "none",
        "detail": "",
        "pattern_id": None,
        "project": problem.get("name", "unknown"),
    }

    matching_pattern = classify_problem(problem)

    if not matching_pattern:
        result["action"] = "unknown"
        result["detail"] = "Playbook'ta eşleşen kalıp bulunamadı — manuel müdahale gerekli"
        logging.info(f"  ❓ {problem.get('name')}: Bilinmeyen hata — playbook'ta eşleşme yok")
        return result

    pattern_id = matching_pattern.get("id", "?")
    action = matching_pattern.get("action", "alert_only")
    description = matching_pattern.get("description", "")
    result["pattern_id"] = pattern_id
    result["action"] = action

    logging.info(f"  🔍 {problem.get('name')}: Kalıp eşleşti → [{pattern_id}] {description}")

    if action == "ignore_transient":
        wait_min = matching_pattern.get("wait_minutes", 30)
        result["healed"] = True
        result["detail"] = f"Geçici sorun — {wait_min}dk sonra kendi düzelecek."
        logging.info(f"  ⏳ Geçici sorun, aksiyon alınmadı (bekleme: {wait_min}dk)")
        return result

    if action == "alert_only":
        result["healed"] = False
        result["detail"] = f"Otomatik düzeltilemez: {description}"
        logging.info(f"  📧 Sadece alarm: {description}")
        return result

    if not check_rate_limit(problem.get("name", ""), action):
        result["healed"] = False
        result["detail"] = "Rate limit aşıldı — sonraki döngüde denenecek"
        return result

    if action == "redeploy":
        heal_result = railway_redeploy(token, project_info)
        result["healed"] = heal_result["success"]
        result["detail"] = heal_result["detail"]
        record_action(problem.get("name", ""), action, heal_result["success"], heal_result["detail"])
        if heal_result["success"]:
            logging.info(f"  ✅ Redeploy başarılı: {heal_result['detail']}")
        else:
            logging.error(f"  ❌ Redeploy başarısız: {heal_result['detail']}")
    else:
        result["detail"] = f"Bilinmeyen aksiyon: {action}"
        logging.warning(f"  ⚠️  Tanımsız aksiyon: {action}")

    return result


def heal_all(problems: list, projects: list, token: str) -> list:
    """Tüm sorunları sırayla iyileştirmeye çalışır."""
    if not problems:
        logging.info("  ✅ İyileştirilecek sorun yok")
        return []

    project_map = {p["name"]: p for p in projects}
    results = []
    healed_count = 0
    failed_count = 0

    logging.info("")
    logging.info("🩺 OTOMATİK İYİLEŞTİRME")
    logging.info("-" * 40)

    for problem in problems:
        name = problem.get("name", "unknown")
        project_info = project_map.get(name, {})

        if "platform" not in problem:
            problem["platform"] = project_info.get("platform", "unknown")

        heal_result = attempt_heal(problem, project_info, token)
        results.append(heal_result)

        if heal_result["healed"]:
            healed_count += 1
        elif heal_result["action"] not in ("unknown", "alert_only", "ignore_transient"):
            failed_count += 1

        time.sleep(1)

    logging.info("")
    logging.info("🩺 İYİLEŞTİRME SONUCU:")
    logging.info(f"  ✅ Düzeltildi: {healed_count}")
    logging.info(f"  ❌ Düzeltilemedi: {failed_count}")
    logging.info(f"  📧 Manuel müdahale: {len(results) - healed_count - failed_count}")

    return results


# ══════════════════════════════════════════════════════════
# ██  E-POSTA
# ══════════════════════════════════════════════════════════

def send_alert_email(smtp_user: str, smtp_password: str, problems: list):
    """Sorunlu servislerin listesini e-posta ile gönderir."""
    if not problems:
        return

    template_path = TEMPLATE_DIR / "alert_email.html"
    html_template = template_path.read_text(encoding="utf-8") if template_path.exists() else _default_html_template()

    rows_html = ""
    for p in problems:
        status = p.get('status', 'UNKNOWN')
        status_emoji = "&#128680;" if status in ALERT_STATUSES else "&#9888;&#65039;"

        if status in ALERT_STATUSES:
            badge_bg, badge_color = "#dc2626", "#ffffff"
        elif status in TRANSIENT_STATUSES:
            badge_bg, badge_color = "#f59e0b", "#78350f"
        else:
            badge_bg, badge_color = "#22c55e", "#052e16"

        rows_html += f"""
                <tr>
                    <td width="40%" style="padding: 16px 24px; border-bottom: 1px solid #334155; color: #e2e8f0; font-size: 14px;">{status_emoji} {p['name']}</td>
                    <td width="20%" style="padding: 16px; border-bottom: 1px solid #334155; text-align: center;">
                        <span style="background-color: {badge_bg}; color: {badge_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">{status}</span>
                    </td>
                    <td width="40%" style="padding: 16px 24px; border-bottom: 1px solid #334155; font-size: 13px; color: #94a3b8;">{p.get('detail', '&#8212;')}</td>
                </tr>
        """

    html_body = html_template.replace("{{ROWS}}", rows_html)
    html_body = html_body.replace("{{COUNT}}", str(len(problems)))
    html_body = html_body.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Antigravity Alarm: {len(problems)} serviste sorun tespit edildi"
    msg["From"] = smtp_user
    msg["To"] = ALERT_EMAIL

    plain_text = f"Antigravity Servis Alarmı\n{'='*40}\n"
    for p in problems:
        plain_text += f"\n• {p['name']}: {p.get('status', 'UNKNOWN')} — {p.get('detail', '')}"
    plain_text += f"\n\nKontrol zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logging.info(f"📧 Alarm e-postası gönderildi → {ALERT_EMAIL}")
    except Exception as e:
        logging.error(f"❌ E-posta gönderilemedi: {e}")


def send_healing_report_email(smtp_user: str, smtp_password: str, heal_results: list, original_problems: list):
    """Self-heal sonuçlarını e-posta ile gönderir."""
    template_path = TEMPLATE_DIR / "healing_report.html"
    html_template = template_path.read_text(encoding="utf-8") if template_path.exists() else "<html><body><h1>Self-Heal Raporu</h1>{{HEALED_SECTION}}{{FAILED_SECTION}}</body></html>"

    healed = [h for h in heal_results if h.get("healed") and h.get("action") != "ignore_transient"]
    failed = [h for h in heal_results if not h.get("healed") and h.get("action") not in ("ignore_transient",)]
    skipped = [h for h in heal_results if h.get("action") == "ignore_transient"]

    healed_html = ""
    if healed:
        healed_html = '<div style="padding: 0 24px 20px;"><h3 style="margin: 0 0 12px; font-size: 14px; color: #22c55e; text-transform: uppercase;">&#10003; Otomatik Düzeltildi</h3><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">'
        for h in healed:
            healed_html += f'<tr><td style="padding: 10px 16px; border-bottom: 1px solid #1e3a2f; color: #86efac; font-size: 14px;">&#10003; {h.get("project", "?")}</td><td style="padding: 10px 16px; border-bottom: 1px solid #1e3a2f; color: #4ade80; font-size: 12px;">{h.get("action", "?")}</td><td style="padding: 10px 16px; border-bottom: 1px solid #1e3a2f; color: #94a3b8; font-size: 12px;">{h.get("detail", "")[:120]}</td></tr>'
        healed_html += "</table></div>"

    failed_html = ""
    if failed:
        failed_html = '<div style="padding: 0 24px 20px;"><h3 style="margin: 0 0 12px; font-size: 14px; color: #ef4444; text-transform: uppercase;">&#10007; Müdahale Gerekli</h3><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">'
        for h in failed:
            failed_html += f'<tr><td style="padding: 10px 16px; border-bottom: 1px solid #3b1a1a; color: #fca5a5; font-size: 14px;">&#10007; {h.get("project", "?")}</td><td style="padding: 10px 16px; border-bottom: 1px solid #3b1a1a; color: #f87171; font-size: 12px;">{h.get("action", "?")}</td><td style="padding: 10px 16px; border-bottom: 1px solid #3b1a1a; color: #94a3b8; font-size: 12px;">{h.get("detail", "")[:120]}</td></tr>'
        failed_html += "</table></div>"

    html_body = html_template
    html_body = html_body.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
    html_body = html_body.replace("{{TOTAL_PROBLEMS}}", str(len(original_problems)))
    html_body = html_body.replace("{{HEALED_COUNT}}", str(len(healed)))
    html_body = html_body.replace("{{FAILED_COUNT}}", str(len(failed)))
    html_body = html_body.replace("{{SKIPPED_COUNT}}", str(len(skipped)))
    html_body = html_body.replace("{{HEALED_SECTION}}", healed_html)
    html_body = html_body.replace("{{FAILED_SECTION}}", failed_html)

    if healed and not failed:
        subject = f"✅ Antigravity: {len(healed)} sorun otomatik düzeltildi"
    elif healed and failed:
        subject = f"🩺 Antigravity: {len(healed)} düzeltildi, {len(failed)} müdahale bekliyor"
    else:
        subject = f"🚨 Antigravity: {len(failed)} sorun düzeltilemedi — müdahale gerekli"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ALERT_EMAIL

    plain_text = f"Antigravity Self-Heal Raporu\n{'='*40}\n"
    if healed:
        plain_text += "\n✅ Otomatik Düzeltildi:\n"
        for h in healed:
            plain_text += f"  • {h.get('project')}: {h.get('action')} — {h.get('detail', '')}\n"
    if failed:
        plain_text += "\n❌ Müdahale Gerekli:\n"
        for h in failed:
            plain_text += f"  • {h.get('project')}: {h.get('action')} — {h.get('detail', '')}\n"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logging.info(f"📧 Self-heal raporu gönderildi → {ALERT_EMAIL}")
    except Exception as e:
        logging.error(f"❌ Self-heal raporu gönderilemedi: {e}")


def _default_html_template() -> str:
    return """
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155;">
            <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 24px; color: white;">
                <h1 style="margin: 0; font-size: 20px;">🚨 Antigravity Servis Alarmı</h1>
                <p style="margin: 8px 0 0; opacity: 0.9;">{{COUNT}} serviste sorun tespit edildi</p>
            </div>
            <table style="width: 100%; border-collapse: collapse;">{{ROWS}}</table>
            <div style="padding: 16px; text-align: center; font-size: 13px; color: #64748b;">
                <p>Kontrol zamanı: {{TIMESTAMP}}</p>
                <a href="https://railway.app/dashboard" style="color: #4299e1;">Railway Dashboard →</a>
            </div>
        </div>
    </body>
    </html>
    """


# ══════════════════════════════════════════════════════════
# ██  ANA ÇALIŞTIRMA
# ══════════════════════════════════════════════════════════

def run_health_check() -> dict:
    """
    Ana kontrol fonksiyonu — Railway üzerinde çalışır.
    Her çalışmada:
      1. Tüm Railway servislerini kontrol eder (deployment + log tarama)
      2. Sorun varsa self-healing dener
      3. Kalan sorunları e-posta ile bildirir
    """
    logging.info("=" * 55)
    logging.info("🏥 RAILWAY HEALTH CHECK BAŞLADI")
    logging.info(f"   ⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logging.info("=" * 55)

    # 1. Credentials
    env = load_credentials()
    railway_token = env.get("RAILWAY_TOKEN")
    smtp_user = env.get("SMTP_USER")
    smtp_password = env.get("SMTP_APP_PASSWORD")

    if not railway_token:
        logging.error("❌ RAILWAY_TOKEN bulunamadı!")
        return {"total": 0, "healthy": 0, "problems": 0, "healed": 0}

    if not smtp_user or not smtp_password:
        logging.warning("⚠️ SMTP bilgileri eksik — alarm e-postaları gönderilemeyecek.")

    # 2. Projeleri yükle
    projects = load_projects()
    logging.info("")
    logging.info("🚂 RAILWAY SERVİSLERİ")
    logging.info("-" * 40)

    # 3. Railway kontrolü (deep scan her zaman açık)
    all_results = check_railway_projects(projects, railway_token, deep_scan=True)
    all_problems = []
    for r in all_results:
        if r["problems"]:
            all_problems.extend([
                {"name": r["name"], "status": r["status"], "detail": p, "platform": "railway"}
                for p in r["problems"]
            ])

    # 4. Self-Healing (her zaman aktif)
    heal_results = []
    if all_problems:
        heal_results = heal_all(all_problems, projects, railway_token)

    # 5. E-posta
    healed_problems = [h for h in heal_results if h.get("healed") and h.get("action") != "ignore_transient"]
    remaining_problems = [p for p in all_problems if not any(
        h.get("project") == p.get("name") and h.get("healed")
        for h in heal_results
    )]
    
    meaningful_heals = [h for h in heal_results if h.get("action") != "ignore_transient"]

    if meaningful_heals and smtp_user and smtp_password:
        send_healing_report_email(smtp_user, smtp_password, heal_results, all_problems)
    elif remaining_problems and smtp_user and smtp_password:
        send_alert_email(smtp_user, smtp_password, remaining_problems)

    # 6. Özet
    healthy_count = len(all_results) - len([r for r in all_results if r.get("problems")])
    logging.info("")
    logging.info("=" * 55)
    logging.info(f"📊 SONUÇ: {len(all_results)} Railway servisi kontrol edildi")
    logging.info(f"  ✅ Sağlıklı: {healthy_count}")
    logging.info(f"  🚨 Sorunlu: {len(all_problems)}")
    if heal_results:
        logging.info(f"  🩺 Otomatik düzeltildi: {len(healed_problems)}")

    if not all_problems:
        logging.info("🎉 Tüm servisler sağlıklı!")
    logging.info("=" * 55)

    return {
        "total": len(all_results),
        "healthy": healthy_count,
        "problems": len(all_problems),
        "healed": len(healed_problems),
        "details": all_results,
        "heal_results": heal_results,
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_health_check()
