#!/usr/bin/env python3
"""
Antigravity Proje Audit — Kod Kalitesi & Güvenlik Tarayıcı

Projeler/ klasöründeki tüm projeleri 8 boyutta tarar:
  1. Syntax Check      — Python dosyaları derleniyor mu?
  2. Dependency Lock   — Paket versiyonları kilitli mi?
  3. Security Scan     — Hardcoded API key / token var mı?
  4. .env Leak         — .env dosyası proje içinde mi?
  5. README Check      — README.md var mı, yeterli mi?
  6. Logging Quality   — print(e), except:pass anti-pattern var mı?
  7. .gitignore Check  — Hassas dosyalar ignore ediliyor mu?
  8. Proje Yapısı      — Fail-fast config, büyük dosya uyarısı

Watchdog'dan FARKI:
  - Watchdog → "Proje çalışıyor mu?" (runtime, Railway, Notion, Sheets)
  - Bu script → "Proje sağlıklı yazılmış mı?" (kod kalitesi, güvenlik)

Kullanım:
    python3 _agents/proje_audit.py                          # Tüm projeler
    python3 _agents/proje_audit.py --project YouTube        # Tek proje (kısmi isim)
    python3 _agents/proje_audit.py --report ozel_rapor.md   # Özel rapor yolu
    python3 _agents/proje_audit.py --no-report              # Sadece terminal çıktısı
"""

import os
import sys
import re
import py_compile
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

# ── Paths ──────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PROJELER_DIR = ROOT_DIR / "Projeler"
DEFAULT_REPORT_PATH = ROOT_DIR / "_knowledge" / "son-audit-raporu.md"

# ── Skip patterns ─────────────────────────────────────────
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv",
    "_arsiv", ".next", "dist", "build", ".eggs", ".mypy_cache",
    ".pytest_cache", ".tox", "egg-info", ".vercel",
}
SKIP_FILENAMES = {".DS_Store", "Thumbs.db"}

# Files where tokens are EXPECTED — don't flag these
TOKEN_EXPECTED_FILES = {
    ".env", ".env.example", ".env.sample", "master.env",
    ".env.local", ".env.production", ".env.development",
}

# Large file threshold (satır)
LARGE_FILE_THRESHOLD = 500

# ── Severity ──────────────────────────────────────────────
CRITICAL = "CRITICAL"
WARNING = "WARNING"
INFO = "INFO"


# ═════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═════════════════════════════════════════════════════════════

@dataclass
class Finding:
    """Bir audit bulgusunu temsil eder."""
    severity: str       # CRITICAL, WARNING, INFO
    category: str       # syntax, dependency, security, readme, logging, gitignore, structure
    message: str
    file: str = ""
    line: int = 0
    fix_hint: str = ""


@dataclass
class ProjectReport:
    """Bir projenin audit sonuçlarını toplar."""
    name: str
    path: Path
    project_type: str = "unknown"  # python, node, mixed, other
    findings: list = field(default_factory=list)
    file_count: int = 0
    total_lines: int = 0
    py_file_count: int = 0

    @property
    def criticals(self) -> int:
        return sum(1 for f in self.findings if f.severity == CRITICAL)

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity == WARNING)

    @property
    def infos(self) -> int:
        return sum(1 for f in self.findings if f.severity == INFO)

    @property
    def health_icon(self) -> str:
        if self.criticals > 0:
            return "🔴"
        elif self.warnings > 0:
            return "🟡"
        return "🟢"


# ═════════════════════════════════════════════════════════════
#  UTILITIES
# ═════════════════════════════════════════════════════════════

def find_files(project_path: Path, extensions: set) -> list:
    """Proje klasöründe verilen uzantılara sahip dosyaları bulur."""
    results = []
    for root, dirs, files in os.walk(project_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILENAMES:
                continue
            if any(f.endswith(ext) for ext in extensions):
                results.append(Path(root) / f)
    return results


def count_lines(file_path: Path) -> int:
    """Bir dosyanın satır sayısını döner."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return 0


def read_lines(file_path: Path) -> list:
    """Dosyayı satır listesi olarak okur."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.readlines()
    except Exception:
        return []


# ═════════════════════════════════════════════════════════════
#  CHECK FUNCTIONS
# ═════════════════════════════════════════════════════════════

def check_syntax(project_path: Path) -> list:
    """Python dosyalarını py_compile ile derler."""
    findings = []
    py_files = find_files(project_path, {".py"})

    for f in py_files:
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            findings.append(Finding(
                severity=CRITICAL,
                category="syntax",
                message=f"Syntax hatası: {e.msg}",
                file=str(f.relative_to(project_path)),
                fix_hint="Dosyadaki syntax hatasını düzelt — proje çalışamaz",
            ))

    return findings


def check_dependencies(project_path: Path) -> list:
    """requirements.txt ve package.json bağımlılık sağlığını kontrol eder."""
    findings = []

    # ── Python: requirements.txt ──
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        unpinned = []
        with open(req_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Pinned = has ==
                if "==" not in line:
                    pkg = re.split(r"[>=<~!;\[]", line)[0].strip()
                    if pkg:
                        unpinned.append(pkg)

        if unpinned:
            pkg_list = ", ".join(f"`{p}`" for p in unpinned[:8])
            extra = f" (+{len(unpinned) - 8} daha)" if len(unpinned) > 8 else ""
            findings.append(Finding(
                severity=WARNING,
                category="dependency",
                message=f"{len(unpinned)} paket versiyonsuz: {pkg_list}{extra}",
                file="requirements.txt",
                fix_hint="Her paketin ardına ==X.Y.Z ekle (pip freeze ile versiyonları al)",
            ))
    elif find_files(project_path, {".py"}):
        # Has Python files but no requirements.txt
        findings.append(Finding(
            severity=WARNING,
            category="dependency",
            message="Python projesi ama requirements.txt yok",
            fix_hint="pip freeze > requirements.txt ile oluştur",
        ))

    # ── Node.js: package.json + lock file ──
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        lock_files = [
            project_path / "package-lock.json",
            project_path / "yarn.lock",
            project_path / "pnpm-lock.yaml",
        ]
        if not any(lf.exists() for lf in lock_files):
            findings.append(Finding(
                severity=WARNING,
                category="dependency",
                message="package.json var ama lock dosyası yok",
                file="package.json",
                fix_hint="npm install ile package-lock.json oluştur",
            ))

    return findings


def check_security(project_path: Path) -> list:
    """Kaynak dosyalarda hardcoded secret taraması yapar."""
    findings = []

    source_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml", ".toml"}
    source_files = find_files(project_path, source_exts)

    # (regex_pattern, label) — her pattern value group'u yakalar
    secret_patterns = [
        # API key / secret direct assignment
        (r'''(?i)(?:api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*["']([A-Za-z0-9_\-/+=\.]{20,})["']''',
         "Hardcoded API Key"),
        # Token / auth direct assignment
        (r'''(?i)(?:(?:auth|access|bearer)[_-]?token|secret[_-]?key)\s*[=:]\s*["']([A-Za-z0-9_\-/+=\.]{20,})["']''',
         "Hardcoded Token"),
        # Password direct assignment
        (r'''(?i)(?:password|passwd|pwd)\s*[=:]\s*["']([^\s"']{8,})["']''',
         "Hardcoded Password"),
        # Known token prefixes (very high confidence)
        (r'''["'](sk-[A-Za-z0-9]{20,})["']''', "OpenAI API Key"),
        (r'''["'](ntn_[A-Za-z0-9]{20,})["']''', "Notion Token"),
        (r'''["'](secret_[A-Za-z0-9]{20,})["']''', "Notion Secret"),
        (r'''["'](ghp_[A-Za-z0-9]{20,})["']''', "GitHub PAT"),
        (r'''["'](gho_[A-Za-z0-9]{20,})["']''', "GitHub OAuth Token"),
        (r'''["'](xoxb-[A-Za-z0-9\-]{20,})["']''', "Slack Token"),
        # Telegram bot token: 123456789:ABCdef...
        (r'''["'](\d{8,10}:[A-Za-z0-9_-]{35})["']''', "Telegram Bot Token"),
    ]

    # Placeholder values to ignore
    placeholder_keywords = {
        "your-", "your_", "xxx", "todo", "change", "placeholder",
        "example", "test", "dummy", "fake", "sample", "replace",
    }

    for f in source_files:
        # Skip files where tokens are expected
        if f.name.lower() in TOKEN_EXPECTED_FILES:
            continue
        if "example" in f.name.lower() or "sample" in f.name.lower():
            continue

        lines = read_lines(f)
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            # Skip lines reading from environment (correct pattern)
            if "os.environ" in line or "os.getenv" in line or "process.env" in line:
                continue

            for pattern, label in secret_patterns:
                match = re.search(pattern, line)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    # Skip obvious placeholders
                    if any(kw in value.lower() for kw in placeholder_keywords):
                        continue
                    # Skip empty-ish values
                    if len(value.strip("\"' ")) < 8:
                        continue

                    findings.append(Finding(
                        severity=CRITICAL,
                        category="security",
                        message=f"{label} bulundu",
                        file=str(f.relative_to(project_path)),
                        line=line_num,
                        fix_hint="Bu değeri .env dosyasına taşı, os.environ ile oku",
                    ))
                    break  # Satır başına tek bulgu yeterli

    return findings


def check_env_leak(project_path: Path) -> list:
    """.env dosyasının proje klasöründe olup olmadığını kontrol eder."""
    findings = []

    for f in project_path.rglob(".env"):
        if not f.is_file():
            continue
        # Skip files in .git directory
        if ".git" in f.parts:
            continue

        findings.append(Finding(
            severity=CRITICAL,
            category="security",
            message=".env dosyası proje klasöründe (commit riski!)",
            file=str(f.relative_to(project_path)),
            fix_hint=".env'yi .gitignore'a ekle, git rm --cached .env ile tracking'den çıkar",
        ))

    return findings


def check_readme(project_path: Path) -> list:
    """README.md varlığını ve anlamlılığını kontrol eder."""
    findings = []
    readme = project_path / "README.md"

    if not readme.exists():
        findings.append(Finding(
            severity=WARNING,
            category="readme",
            message="README.md dosyası yok",
            fix_hint="Projenin ne yaptığını, nasıl çalıştırıldığını anlatan bir README ekle",
        ))
    else:
        content = readme.read_text(encoding="utf-8", errors="ignore").strip()
        if len(content) < 50:
            findings.append(Finding(
                severity=WARNING,
                category="readme",
                message=f"README.md çok kısa ({len(content)} karakter)",
                file="README.md",
                fix_hint="Proje açıklaması, kurulum ve kullanım bilgisi ekle",
            ))

    return findings


def check_logging(project_path: Path) -> list:
    """Python dosyalarında logging anti-pattern'lerini tespit eder."""
    findings = []
    py_files = find_files(project_path, {".py"})

    # Tek satırlık anti-pattern'ler
    single_line_patterns = [
        (r"\bprint\s*\(\s*(?:e|err|error|ex|exc|exception)\s*\)",
         "print(e) — exception stack trace kayboluyor"),
        (r"^\s*except\s*:\s*$",
         "bare except: — tüm hataları yakalar, spesifik exception kullan"),
    ]

    for f in py_files:
        lines = read_lines(f)
        rel_path = str(f.relative_to(project_path))

        # Tek satırlık kontroller
        for line_num, line in enumerate(lines, 1):
            for pattern, msg in single_line_patterns:
                if re.search(pattern, line):
                    findings.append(Finding(
                        severity=WARNING,
                        category="logging",
                        message=msg,
                        file=rel_path,
                        line=line_num,
                        fix_hint="logging.error('...', exc_info=True) kullan",
                    ))

        # except...pass çok satırlı kontrol
        for i in range(len(lines) - 1):
            current = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            if re.match(r"except\b", current) and next_line == "pass":
                # Aynı except bloğunda logging var mı kontrol et
                # (except ve pass arasında sadece whitespace olmalı)
                findings.append(Finding(
                    severity=WARNING,
                    category="logging",
                    message="except...pass — hata sessizce yutuldu",
                    file=rel_path,
                    line=i + 1,
                    fix_hint="En azından logging.warning('Hata: ...', exc_info=True) ekle",
                ))

    return findings


def check_gitignore(project_path: Path) -> list:
    """.gitignore varlığını ve kapsamını kontrol eder."""
    findings = []
    gitignore = project_path / ".gitignore"

    # Eğer proje kendi .gitignore'u yoksa root'taki kontrol edilir
    if not gitignore.exists():
        root_gitignore = ROOT_DIR / ".gitignore"
        if root_gitignore.exists():
            # Root gitignore var, proje düzeyinde zorunlu değil
            return findings

        findings.append(Finding(
            severity=WARNING,
            category="gitignore",
            message=".gitignore dosyası yok",
            fix_hint=".env, __pycache__, *.pyc, node_modules gibi dosyaları ignore et",
        ))
        return findings

    content = gitignore.read_text(encoding="utf-8", errors="ignore")

    # Python projesi ise Python-specific pattern'ler kontrol et
    if find_files(project_path, {".py"}):
        essential = {".env": ".env", "__pycache__": "__pycache__"}
        missing = [pat for pat, text in essential.items() if text not in content]
        if missing:
            findings.append(Finding(
                severity=INFO,
                category="gitignore",
                message=f".gitignore'da eksik: {', '.join(missing)}",
                file=".gitignore",
                fix_hint=f"Ekle: {', '.join(missing)}",
            ))

    return findings


def check_structure(project_path: Path) -> list:
    """Proje yapısı ve fail-fast config kontrolü."""
    findings = []
    py_files = find_files(project_path, {".py"})

    if not py_files:
        return findings

    # ── Fail-fast config kontrolü ──
    config_file = project_path / "config.py"
    if config_file.exists():
        content = config_file.read_text(encoding="utf-8", errors="ignore")
        if "os.environ" in content or "os.getenv" in content:
            has_validation = (
                "raise" in content
                or "sys.exit" in content
                or "validate" in content.lower()
            )
            if not has_validation:
                findings.append(Finding(
                    severity=INFO,
                    category="structure",
                    message="config.py env okuyor ama fail-fast doğrulama yok",
                    file="config.py",
                    fix_hint="Zorunlu env var'lar eksikse EnvironmentError fırlat",
                ))
    elif len(py_files) > 3:
        # 3'ten fazla .py dosya = ciddi proje, config.py olmalı
        findings.append(Finding(
            severity=INFO,
            category="structure",
            message="config.py yok — env variable'lar dağınık olabilir",
            fix_hint="Merkezi config.py oluştur, tüm env okumalarını orada topla",
        ))

    # ── Büyük dosya uyarısı ──
    for f in py_files:
        line_count = count_lines(f)
        if line_count > LARGE_FILE_THRESHOLD:
            findings.append(Finding(
                severity=INFO,
                category="structure",
                message=f"Büyük dosya: {line_count} satır (bakım riski)",
                file=str(f.relative_to(project_path)),
                fix_hint="Dosyayı daha küçük modüllere bölmeyi düşün",
            ))

    return findings


# ═════════════════════════════════════════════════════════════
#  AUDIT RUNNER
# ═════════════════════════════════════════════════════════════

def detect_project_type(project_path: Path) -> str:
    """Projenin Python, Node.js veya karma olduğunu algılar."""
    has_py = bool(find_files(project_path, {".py"}))
    has_node = (project_path / "package.json").exists()

    if has_py and has_node:
        return "mixed"
    elif has_node:
        return "node"
    elif has_py:
        return "python"
    return "other"


def collect_file_stats(project_path: Path) -> tuple:
    """Dosya sayısı ve toplam satır sayısını hesaplar."""
    all_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css"}
    files = find_files(project_path, all_exts)
    total_lines = sum(count_lines(f) for f in files)
    py_count = sum(1 for f in files if f.suffix == ".py")
    return len(files), total_lines, py_count


def audit_project(project_path: Path) -> ProjectReport:
    """Tek bir proje üzerinde tüm kontrolleri çalıştırır."""
    report = ProjectReport(
        name=project_path.name,
        path=project_path,
        project_type=detect_project_type(project_path),
    )

    # Dosya istatistikleri
    report.file_count, report.total_lines, report.py_file_count = \
        collect_file_stats(project_path)

    # Tüm kontroller
    checks = [
        check_syntax,
        check_dependencies,
        check_security,
        check_env_leak,
        check_readme,
        check_logging,
        check_gitignore,
        check_structure,
    ]

    for check_fn in checks:
        try:
            new_findings = check_fn(project_path)
            report.findings.extend(new_findings)
        except Exception as e:
            report.findings.append(Finding(
                severity=WARNING,
                category="audit-error",
                message=f"{check_fn.__name__} çalıştırılamadı: {e}",
            ))

    return report


def audit_all_projects(filter_name: str = None) -> list:
    """Projeler/ altındaki tüm projeleri tarar."""
    reports = []

    for entry in sorted(PROJELER_DIR.iterdir()):
        if not entry.is_dir():
            continue
        # Skip hidden and archive dirs
        if entry.name.startswith(".") or entry.name.startswith("_"):
            continue
        # Apply name filter
        if filter_name and filter_name.lower() not in entry.name.lower():
            continue

        report = audit_project(entry)
        reports.append(report)

    return reports


# ═════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═════════════════════════════════════════════════════════════

CATEGORY_LABELS = {
    "syntax": "🔧 Syntax",
    "dependency": "📦 Dependency",
    "security": "🔐 Güvenlik",
    "readme": "📄 README",
    "logging": "📝 Logging",
    "gitignore": "🚫 .gitignore",
    "structure": "🏗️ Proje Yapısı",
    "audit-error": "⚙️ Audit Hatası",
}


def generate_markdown_report(reports: list) -> str:
    """Detaylı markdown audit raporu üretir."""
    now = datetime.now().strftime("%d %B %Y, %H:%M")

    total_c = sum(r.criticals for r in reports)
    total_w = sum(r.warnings for r in reports)
    total_i = sum(r.infos for r in reports)
    total_all = total_c + total_w + total_i
    total_files = sum(r.file_count for r in reports)
    total_lines = sum(r.total_lines for r in reports)

    lines = []
    lines.append("# 🔍 Antigravity Proje Audit Raporu\n")
    lines.append(f"**Tarih:** {now}  ")
    lines.append(f"**Taranan proje:** {len(reports)}  ")
    lines.append(f"**Taranan dosya:** {total_files} ({total_lines:,} satır)  ")
    lines.append(f"**Toplam bulgu:** {total_all} "
                 f"({total_c} kritik, {total_w} uyarı, {total_i} bilgi)\n")

    # Genel sağlık durumu
    if total_c == 0 and total_w == 0:
        lines.append("> [!TIP]\n> ✅ Tüm projeler temiz! Kritik veya uyarı seviyesinde sorun yok.\n")
    elif total_c > 0:
        lines.append(f"> [!CAUTION]\n> 🔴 **{total_c} kritik sorun** tespit edildi — acil müdahale gerekli!\n")
    else:
        lines.append(f"> [!WARNING]\n> 🟡 **{total_w} uyarı** var — planlı düzeltme önerilir.\n")

    lines.append("---\n")

    # ── Özet Tablo ──
    lines.append("## 📊 Özet Tablo\n")
    lines.append("| Proje | Tip | Dosya | Satır | Kritik | Uyarı | Bilgi | Durum |")
    lines.append("|-------|-----|-------|-------|--------|-------|-------|-------|")

    sorted_reports = sorted(reports, key=lambda x: (-x.criticals, -x.warnings, x.name))
    for r in sorted_reports:
        lines.append(
            f"| {r.name} | {r.project_type} | {r.file_count} | "
            f"{r.total_lines:,} | {r.criticals} | {r.warnings} | "
            f"{r.infos} | {r.health_icon} |"
        )

    lines.append("\n---\n")

    # ── Detaylı Bulgular (sadece sorunlu projeler) ──
    problem_reports = [r for r in sorted_reports if r.findings]
    if problem_reports:
        lines.append("## 🔎 Detaylı Bulgular\n")

        for r in problem_reports:
            icon = "🔴" if r.criticals else "🟡" if r.warnings else "ℹ️"
            lines.append(f"### {icon} {r.name}\n")
            lines.append(f"*{r.project_type} projesi — {r.file_count} dosya, "
                         f"{r.total_lines:,} satır*\n")

            # Kategoriye göre grupla
            by_cat = {}
            for f in r.findings:
                by_cat.setdefault(f.category, []).append(f)

            for cat, cat_findings in by_cat.items():
                label = CATEGORY_LABELS.get(cat, cat)
                lines.append(f"**{label}**\n")

                for f in cat_findings:
                    icon_f = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[f.severity]
                    loc = ""
                    if f.file:
                        loc = f" — `{f.file}`"
                        if f.line:
                            loc += f" satır {f.line}"

                    lines.append(f"- {icon_f} {f.message}{loc}")
                    if f.fix_hint:
                        lines.append(f"  - 💡 *{f.fix_hint}*")

                lines.append("")

            lines.append("---\n")

    # ── Temiz Projeler ──
    clean = [r for r in reports if not r.findings]
    if clean:
        lines.append("## ✅ Temiz Projeler\n")
        for r in clean:
            lines.append(f"- 🟢 **{r.name}** — Sorun bulunamadı "
                         f"({r.file_count} dosya, {r.total_lines:,} satır)")
        lines.append("")

    # ── Kategori Bazlı İstatistik ──
    lines.append("---\n")
    lines.append("## 📈 Kategori Özeti\n")
    cat_counter = {}
    for r in reports:
        for f in r.findings:
            key = CATEGORY_LABELS.get(f.category, f.category)
            cat_counter.setdefault(key, {"c": 0, "w": 0, "i": 0})
            if f.severity == CRITICAL:
                cat_counter[key]["c"] += 1
            elif f.severity == WARNING:
                cat_counter[key]["w"] += 1
            else:
                cat_counter[key]["i"] += 1

    if cat_counter:
        lines.append("| Kategori | Kritik | Uyarı | Bilgi |")
        lines.append("|----------|--------|-------|-------|")
        for cat, counts in sorted(cat_counter.items(),
                                   key=lambda x: -(x[1]["c"] * 100 + x[1]["w"] * 10 + x[1]["i"])):
            lines.append(f"| {cat} | {counts['c']} | {counts['w']} | {counts['i']} |")
    else:
        lines.append("*Bulgu yok — tüm projeler temiz!*")

    lines.append("")
    return "\n".join(lines)


def print_terminal_summary(reports: list):
    """Terminal'e kısa özet basar."""

    total_c = sum(r.criticals for r in reports)
    total_w = sum(r.warnings for r in reports)
    total_i = sum(r.infos for r in reports)

    print()
    print("=" * 62)
    print("  🔍 ANTIGRAVITY PROJE AUDIT")
    print("  " + datetime.now().strftime("%d %B %Y, %H:%M"))
    print("=" * 62)
    print()

    sorted_reports = sorted(reports, key=lambda x: (-x.criticals, -x.warnings, x.name))
    for r in sorted_reports:
        detail_parts = []
        if r.criticals:
            detail_parts.append(f"{r.criticals} kritik")
        if r.warnings:
            detail_parts.append(f"{r.warnings} uyarı")
        if r.infos:
            detail_parts.append(f"{r.infos} bilgi")
        detail = ", ".join(detail_parts) if detail_parts else "✓ temiz"

        print(f"  {r.health_icon} {r.name:<32} {detail}")

    print()
    print("-" * 62)
    print(f"  TOPLAM: {total_c} kritik | {total_w} uyarı | {total_i} bilgi")
    if total_c > 0:
        print(f"  🚨 {total_c} kritik sorun acil düzeltme gerektiriyor!")
    elif total_w > 0:
        print(f"  ⚡ {total_w} uyarı var — planlı düzeltme önerilir.")
    else:
        print("  🎉 Tüm projeler temiz!")
    print("=" * 62)
    print()


# ═════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Antigravity Proje Audit — Kod Kalitesi & Güvenlik Tarayıcı"
    )
    parser.add_argument(
        "--project", "-p",
        help="Tek proje filtresi (kısmi isim eşleşmesi, örn: 'YouTube')",
    )
    parser.add_argument(
        "--report", "-r",
        help=f"Markdown rapor dosya yolu (varsayılan: {DEFAULT_REPORT_PATH})",
        default=str(DEFAULT_REPORT_PATH),
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Markdown rapor dosyası oluşturma (sadece terminal çıktısı)",
    )
    args = parser.parse_args()

    if not PROJELER_DIR.exists():
        print(f"❌ Projeler klasörü bulunamadı: {PROJELER_DIR}")
        sys.exit(1)

    # Audit çalıştır
    reports = audit_all_projects(filter_name=args.project)

    if not reports:
        print("❌ Hiç proje bulunamadı.")
        sys.exit(1)

    # Terminal çıktısı
    print_terminal_summary(reports)

    # Markdown rapor
    if not args.no_report:
        report_md = generate_markdown_report(reports)
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_md, encoding="utf-8")
        print(f"📄 Detaylı rapor: {report_path}\n")

    # Exit code: 1 if critical findings
    total_critical = sum(r.criticals for r in reports)
    sys.exit(1 if total_critical > 0 else 0)


if __name__ == "__main__":
    main()
