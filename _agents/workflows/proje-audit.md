# Proje Audit Workflow
> **Tetikleyici:** `/proje-audit` komutu veya "Projeleri tara" talebi.

## 🎯 Amaç
Antigravity ekosistemindeki tüm projelerin kod kalitesini, güvenlik zafiyetlerini (sızdırılmış API key vb.), dependency sağlıklarını (versiyonsız paketler) ve proje mimarisini kontrol etmek.

> **Watchdog'dan Farkı:** Watchdog projenin Cloud'da "ayakta" olup olmadığını kontrol eder. Bu audit ise projenin "sağlıklı yazılıp yazılmadığını" kontrol eder. (Statik Kod Analizi).

## 🚀 Adım 1: Audit Script'ini Çalıştır

Tüm projeleri taramak için aşağıdaki komutu çalıştır.
// turbo
```bash
python3 _agents/proje_audit.py
```

Spesifik bir proje için:
```bash
python3 _agents/proje_audit.py --project YouTube
```

## 📋 Adım 2: Çıktıyı İncele ve Klasifiye Et

Script terminale özet bir çıktı basacak ve `_knowledge/son-audit-raporu.md` dosyasına detaylı raporu kaydedecektir.

1. **Raporu Oku:**
   ```
   view_file -> _knowledge/son-audit-raporu.md
   ```
2. Kullanıcıya **SADECE ÖZETİ** sun. Tüm raporu kopyalama!
3. Şöyle bir özet geç:
   - Toplam kaç kritik, kaç uyarı var?
   - En acil (Kritik) soruna sahip projeler hangileri? (Örn: "YouTube otomasyonunda hardcoded API key var", "Blog yazıcıda syntax hatası var proje çalışamaz")

## 🛠️ Adım 3: Operasyon Stratejisi Belirle

Kullanıcı tüm sorunların anında çözülmesini isteyebilir, ama **context window'u korumak ZORUNLUDUR**.

1. Eğer toplam sorun sayısı azsa (2-3 proje, basit fixler):
   - "Sorunlar kritik ama az sayıda, hemen bu chat'te çözüyorum" de ve düzelt.
2. Eğer sorun sayısı çoksa veya mimari değişiklik gerektiriyorsa (Örn: Env fail-fast eksikliği 10 projede var):
   - **Kullanıcıya şunu söyle:** *"Birçok projede sorun var. Hepsini burada çözersek yapay zekanın hafızası (context window) dolacak ve kafam karışacak. Lütfen en kritik olan `[PROJE_ADI]` projesi için yeni bir chat açıp 'Buna audit fix uygula' de."*

## 💡 Hata Giderme Rehberi (Fix Hints)

Rapor sana her sorun için ipucu (fix hint) verecektir. En yaygın olanları:

- **Security (Hardcoded Key):** Key'i kopyala, projede `master.env`'ye veya bir Env dosyasına koy, kodda `os.environ.get("KEY_NAME")` ile oku.
- **Dependency (Versiyonsuz Paket):** Package için uygun ve stabil bir makul versiyon bul (veya `pip freeze` ile anlık durumu kontrol et) ve `==X.Y.Z` şeklinde kilit koy. (Asla `requests` bırakma, `requests==2.31.0` yap).
- **Logging (print(e) / except pass):** O satırları `logging.error("Açıklama", exc_info=True)` şeklinde değiştir.
- **Syntax:** İlgili `.py` dosyasını `view_file` ile oku, Syntax Error olan satırı bulup düzelt.
