#!/usr/bin/env python3
"""
🏥 Railway Servis Sağlık Kontrolü
==================================
deploy-registry.md'deki tüm projeleri okur,
Railway GraphQL API ile durumlarını sorgular,
sorun varsa Gmail SMTP ile bildirim gönderir.

Kullanım:
    python3 health_check.py              # Tam kontrol + e-posta
    python3 health_check.py --dry-run    # Sadece kontrol, e-posta göndermez
    python3 health_check.py --project X  # Tek proje kontrol
"""

import os
import re
import ssl
import sys
import json
import time
import logging
import argparse
import smtplib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# macOS Python framework SSL sertifika sorununun çözümü
# Python 3.13 framework kurulumu certifi yüklemeden gelir
def _create_ssl_context():
    """SSL context oluşturur. Sertifika doğrulaması başarısız olursa unverified fallback."""
    ctx = ssl.create_default_context()
    try:
        # Gerçek bir HTTPS bağlantısı ile test et
        import urllib.request as _ur
        _ur.urlopen("https://railway.app", timeout=5, context=ctx)
        return ctx
    except Exception:
        # Sertifika sorunu — unverified context kullan
        ctx = ssl._create_unverified_context()
        return ctx

_ssl_ctx = _create_ssl_context()

# ── Sabitler ──────────────────────────────────────────────
ANTIGRAVITY_ROOT = Path(__file__).resolve().parents[3]  # _skills/servis-izleyici/scripts/ → Antigravity/
MASTER_ENV = ANTIGRAVITY_ROOT / "_knowledge" / "credentials" / "master.env"
DEPLOY_REGISTRY = ANTIGRAVITY_ROOT / "_knowledge" / "deploy-registry.md"
ENV_CACHE = Path("/tmp/antigravity_env.json")  # Cron-safe token cache
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "health_check.log"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

RAILWAY_GQL_URL = "https://backboard.railway.app/graphql/v2"
ALERT_EMAIL = "ozerendolunay@gmail.com"

# Alarm verilmeyecek durumlar
HEALTHY_STATUSES = {"SUCCESS", "SLEEPING", "BUILDING", "DEPLOYING", "INITIALIZING", "WAITING"}
# Geçici durumlar (log'a yazılır ama alarm yok)
TRANSIENT_STATUSES = {"BUILDING", "DEPLOYING", "INITIALIZING", "WAITING", "SLEEPING"}
# Alarm verilecek durumlar
ALERT_STATUSES = {"FAILED", "CRASHED", "REMOVED"}


# ── Env Yükleme ──────────────────────────────────────────
def load_env_from_file(env_path: Path) -> dict:
    """master.env dosyasından key=value çiftlerini parse eder."""
    env = {}
    try:
        if not env_path.exists():
            return env
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
    except (PermissionError, OSError):
        pass  # macOS izin kısıtlaması — diğer kaynakları dene
    return env


def load_env_from_cache(cache_path: Path) -> dict:
    """JSON cache dosyasından token bilgilerini okur."""
    env = {}
    try:
        if cache_path.exists():
            with open(cache_path, "r") as f:
                data = json.load(f)
                env.update(data)
    except (PermissionError, OSError, json.JSONDecodeError):
        pass
    return env


def load_credentials() -> dict:
    """
    Token bilgilerini 3 kaynaktan yüklemeye çalışır (öncelik sırası):
    1. Environment variables (RAILWAY_TOKEN, SMTP_USER, SMTP_APP_PASSWORD)
    2. /tmp/antigravity_env.json (cron-safe cache — setup_cron.sh tarafından oluşturulur)
    3. master.env (doğrudan dosya okuma)
    """
    creds = {}
    
    # Kaynak 3: master.env (en düşük öncelik)
    creds.update(load_env_from_file(MASTER_ENV))
    
    # Kaynak 2: JSON cache
    creds.update(load_env_from_cache(ENV_CACHE))
    
    # Kaynak 1: Environment variables (en yüksek öncelik)
    for key in ["RAILWAY_TOKEN", "SMTP_USER", "SMTP_APP_PASSWORD"]:
        val = os.environ.get(key)
        if val:
            creds[key] = val
    
    return creds


# ── Deploy Registry Parse ────────────────────────────────
def parse_deploy_registry(registry_path: Path) -> list:
    """
    deploy-registry.md dosyasını parse eder.
    Her proje için dict döner:
    {
        'name': 'shorts-demo-bot',
        'project_id': '...',
        'service_id': '...',
        'environment_id': '...',
        'github_repo': '...',
        'status': '✅ Aktif'
    }
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"Deploy registry bulunamadı: {registry_path}")

    content = registry_path.read_text(encoding="utf-8")
    projects = []
    # Her '### proje-adi' bloğunu bul
    blocks = re.split(r"^### ", content, flags=re.MULTILINE)

    for block in blocks[1:]:  # İlk blok header
        lines = block.strip().split("\n")
        name = lines[0].strip()

        project = {"name": name}
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("- **Railway Project ID:**"):
                match = re.search(r"`([^`]+)`", line)
                if match:
                    project["project_id"] = match.group(1)
            elif line.startswith("- **Service ID:**"):
                match = re.search(r"`([^`]+)`", line)
                if match:
                    project["service_id"] = match.group(1)
            elif line.startswith("- **Environment ID:**"):
                match = re.search(r"`([^`]+)`", line)
                if match:
                    project["environment_id"] = match.group(1)
            elif line.startswith("- **GitHub Repo:**"):
                match = re.search(r"`([^`]+)`", line)
                if match:
                    project["github_repo"] = match.group(1)
            elif line.startswith("- **Durum:**"):
                project["registry_status"] = line.split(":**")[1].strip()

        if "project_id" in project and "service_id" in project:
            projects.append(project)

    return projects


# ── Railway GraphQL Sorgusu ──────────────────────────────
def query_railway(token: str, project_id: str, service_id: str, environment_id: str = None) -> dict:
    """
    Railway GraphQL API ile deployment durumunu sorgular.
    En son deployment'ın status bilgisini döner.
    """
    # Eğer environment_id yoksa, önce proje environments'ı sorgula
    if not environment_id:
        env_query = """
        query($projectId: String!) {
            project(id: $projectId) {
                environments {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
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

    # Son deployment'ı sorgula
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
                node {
                    id
                    status
                    createdAt
                    staticUrl
                }
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
    }


def _gql_request(token: str, query: str, variables: dict) -> dict:
    """Railway GraphQL API'ye istek gönderir."""
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")

    req = urllib.request.Request(
        RAILWAY_GQL_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Antigravity-HealthCheck/1.0",
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


# ── E-posta Gönderimi ────────────────────────────────────
def send_alert_email(smtp_user: str, smtp_password: str, problems: list):
    """Sorunlu servislerin listesini e-posta ile gönderir."""
    if not problems:
        return

    # HTML şablon
    template_path = TEMPLATE_DIR / "alert_email.html"
    if template_path.exists():
        html_template = template_path.read_text(encoding="utf-8")
    else:
        html_template = _default_html_template()

    # Tablo satırları oluştur
    rows_html = ""
    for p in problems:
        status_emoji = "🚨" if p["status"] in ALERT_STATUSES else "⚠️"
        rows_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">{status_emoji} <strong>{p['name']}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                <span style="background: #fed7d7; color: #c53030; padding: 4px 10px; border-radius: 12px; font-size: 13px;">
                    {p['status']}
                </span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #718096;">{p.get('detail', '—')}</td>
        </tr>
        """

    html_body = html_template.replace("{{ROWS}}", rows_html)
    html_body = html_body.replace("{{COUNT}}", str(len(problems)))
    html_body = html_body.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # E-posta oluştur
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Railway Alarm: {len(problems)} serviste sorun tespit edildi"
    msg["From"] = smtp_user
    msg["To"] = ALERT_EMAIL

    # Düz metin alternatifi
    plain_text = f"Railway Servis Alarmı\n{'='*40}\n"
    for p in problems:
        plain_text += f"\n• {p['name']}: {p['status']} — {p.get('detail', '')}"
    plain_text += f"\n\nKontrol zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    plain_text += "\nDashboard: https://railway.app/dashboard"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # SMTP ile gönder
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logging.info(f"📧 Alarm e-postası gönderildi → {ALERT_EMAIL}")
    except Exception as e:
        logging.error(f"❌ E-posta gönderilemedi: {e}")


def _default_html_template() -> str:
    """Şablon dosyası yoksa varsayılan HTML."""
    return """
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f7fafc; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #e53e3e, #c53030); padding: 24px; color: white;">
                <h1 style="margin: 0; font-size: 20px;">🚨 Railway Servis Alarmı</h1>
                <p style="margin: 8px 0 0; opacity: 0.9;">{{COUNT}} serviste sorun tespit edildi</p>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f7fafc;">
                        <th style="padding: 12px; text-align: left; font-size: 13px; color: #718096;">Servis</th>
                        <th style="padding: 12px; text-align: left; font-size: 13px; color: #718096;">Durum</th>
                        <th style="padding: 12px; text-align: left; font-size: 13px; color: #718096;">Detay</th>
                    </tr>
                </thead>
                <tbody>
                    {{ROWS}}
                </tbody>
            </table>
            <div style="padding: 16px; background: #f7fafc; text-align: center; font-size: 13px; color: #a0aec0;">
                <p>Kontrol zamanı: {{TIMESTAMP}}</p>
                <a href="https://railway.app/dashboard" style="color: #4299e1;">Railway Dashboard →</a>
            </div>
        </div>
    </body>
    </html>
    """


# ── Ana Kontrol Fonksiyonu ───────────────────────────────
def run_health_check(dry_run: bool = False, target_project: str = None):
    """Tüm servisleri kontrol eder, sorun varsa alarm verir."""

    # Logging ayarla
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Log dosyasına yazmayı dene, izin hatası olursa /tmp'ye fallback
    log_file_path = LOG_FILE
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file_path, encoding="utf-8"))
    except (PermissionError, OSError):
        fallback_log = Path("/tmp/antigravity_health_check.log")
        try:
            handlers.append(logging.FileHandler(fallback_log, encoding="utf-8"))
            log_file_path = fallback_log
        except Exception:
            pass  # Sadece stdout'a yaz
    
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    logging.info("=" * 50)
    logging.info("🏥 SAĞLIK KONTROLÜ BAŞLADI")
    logging.info("=" * 50)

    # 1. Credentials yükle (3 kaynaktan: env vars → JSON cache → master.env)
    env = load_credentials()
    railway_token = env.get("RAILWAY_TOKEN")
    smtp_user = env.get("SMTP_USER")
    smtp_password = env.get("SMTP_APP_PASSWORD")

    if not railway_token:
        logging.error("❌ RAILWAY_TOKEN bulunamadı!")
        logging.error("  Çözüm 1: bash _skills/servis-izleyici/scripts/setup_cron.sh")
        logging.error("  Çözüm 2: export RAILWAY_TOKEN=<token>")
        sys.exit(1)

    if not smtp_user or not smtp_password:
        logging.warning("⚠️ SMTP bilgileri eksik — alarm e-postaları gönderilemeyecek.")

    # 2. Projeleri oku
    # deploy-registry yolu: env cache'de override edilmiş olabilir
    registry_path = Path(env.get("DEPLOY_REGISTRY", str(DEPLOY_REGISTRY)))
    try:
        projects = parse_deploy_registry(registry_path)
    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"❌ {e}")
        sys.exit(1)

    if target_project:
        projects = [p for p in projects if p["name"] == target_project]
        if not projects:
            logging.error(f"❌ '{target_project}' adlı proje deploy-registry.md'de bulunamadı.")
            sys.exit(1)

    logging.info(f"📋 {len(projects)} proje kontrol edilecek")

    # 3. Her projeyi kontrol et
    problems = []
    results = []

    for project in projects:
        time.sleep(1)  # Rate limit koruması
        name = project["name"]
        logging.info(f"🔍 Kontrol ediliyor: {name}")

        result = query_railway(
            token=railway_token,
            project_id=project["project_id"],
            service_id=project["service_id"],
            environment_id=project.get("environment_id"),
        )

        if "error" in result:
            status = "API_ERROR"
            detail = result["error"]
            logging.error(f"  🚨 {name}: {status} — {detail}")
            problems.append({"name": name, "status": status, "detail": detail})
        else:
            status = result.get("status", "UNKNOWN")
            created_at = result.get("created_at", "—")
            
            # Zaman bilgisini oku
            time_info = ""
            if created_at and created_at != "—":
                try:
                    deploy_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    delta = datetime.now(timezone.utc) - deploy_time
                    hours = int(delta.total_seconds() / 3600)
                    if hours < 1:
                        time_info = f"({int(delta.total_seconds() / 60)} dk önce)"
                    elif hours < 24:
                        time_info = f"({hours} saat önce)"
                    else:
                        time_info = f"({hours // 24} gün önce)"
                except Exception:
                    time_info = ""

            if status in ALERT_STATUSES:
                detail = f"Son deploy: {time_info}"
                logging.error(f"  🚨 {name}: {status} {time_info}")
                problems.append({"name": name, "status": status, "detail": detail})
            elif status in TRANSIENT_STATUSES:
                logging.info(f"  ⏳ {name}: {status} {time_info} (geçici durum)")
            elif status == "NO_DEPLOYMENTS":
                logging.warning(f"  ⚠️ {name}: Hiç deployment bulunamadı")
                problems.append({"name": name, "status": status, "detail": "Hiç deployment yok"})
            else:
                logging.info(f"  ✅ {name}: {status} {time_info}")

        results.append({"name": name, "status": status})

    # 4. Sorun varsa e-posta gönder
    problem_count = len(problems)
    healthy_count = len(results) - problem_count

    if problems and not dry_run:
        if smtp_user and smtp_password:
            send_alert_email(smtp_user, smtp_password, problems)
        else:
            logging.warning("⚠️ SMTP bilgileri eksik → e-posta gönderilemedi")
    elif problems and dry_run:
        logging.info(f"🏃 DRY-RUN modu — {problem_count} sorun tespit edildi, e-posta gönderilmedi")

    # 5. Özet
    logging.info("=" * 50)
    logging.info(f"📊 SONUÇ: {len(results)} proje kontrol edildi")
    logging.info(f"  ✅ Sağlıklı: {healthy_count}")
    logging.info(f"  🚨 Sorunlu: {problem_count}")
    if not problems:
        logging.info("🎉 Tüm servisler sağlıklı!")
    logging.info("=" * 50)

    return {"total": len(results), "healthy": healthy_count, "problems": problem_count, "details": results}


# ── CLI ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🏥 Railway Servis Sağlık Kontrolü",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 health_check.py                   # Tam kontrol + e-posta
  python3 health_check.py --dry-run         # Kontrol, e-posta göndermez
  python3 health_check.py --project X       # Tek proje kontrol
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="E-posta göndermeden sadece kontrol yap")
    parser.add_argument("--project", type=str, help="Belirli bir projeyi kontrol et (deploy-registry'deki adı)")

    args = parser.parse_args()
    run_health_check(dry_run=args.dry_run, target_project=args.project)


if __name__ == "__main__":
    main()
