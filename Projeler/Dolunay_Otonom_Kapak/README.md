# Antigravity V2 Starter Kit

Bu proje, otonom agent'ların ve Mono-Repo dağıtımlarının standart mimarisini yansıtır.

## Mimari Kurallar
1. **`config.py`**: Uygulamanın tüm ENV değişkenleri 1. saniyede burada kontrol edilir. Sistem bağımlılıkları (`ffmpeg` vb.) `_check_system_deps()` ile doğrulanır. Eksik varsa baştan çöker.
2. **`logger.py`**: Tüm `print()` çağrıları yasaklanmıştır. Detaylı stack trace takibi için oluşturulmuştur.
3. **`main.py`**: Temel döngü ve Dry-Run ayrımı burada başlar.
4. **`requirements.txt`**: Tüm bağımlılıklar versiyonlanmalı eşleşmiş olmalıdır.
5. **`nixpacks.toml`**: Railway'de sistem seviyesi bağımlılıklar (ffmpeg, chromium vb.) **SADECE** bu dosya ile yüklenir. `Aptfile` ve `apt.txt` dosyaları Nixpacks builder tarafından YOKSAYILIR.

> Yeni bir projeye başlarken AI bu template içeriğini ilgili klasöre kopyalar (`cp -r` ile).
