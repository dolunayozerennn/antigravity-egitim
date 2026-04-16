import argparse
import os
import re
import sys

def main():
    parser = argparse.ArgumentParser(description="Proje/Klasör Dışa Aktarım Güvenlik Tarayıcısı")
    parser.add_argument("--target", required=True, help="Taranacak hedef klasör")
    args = parser.parse_args()

    target_dir = args.target

    if not os.path.exists(target_dir):
        print(f"HATA: Hedef klasör bulunamadı: {target_dir}")
        sys.exit(1)

    print(f"🔎 Güvenlik taraması başlatılıyor: {target_dir}")

    # Genişletilmiş Regex Pattern'leri
    patterns = {
        "Apify Token": r"apify_api_[A-Za-z0-9]{20,}",
        "Generic/OpenAI/Anthropic Key": r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,})",
        "Google/Firebase Token": r"AIza[0-9A-Za-z-_]{35}",
        "Bearer Token": r"(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
        "Telefon": r"(\+90|0)?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}",
        "IBAN": r"TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}",
        "Kredi/Banka Kartı": r"\b(?:\d[ -]*?){13,16}\b"
    }

    # Özel olarak tamamen hariç tutulacak dosya ve klasörler
    ignore_dirs = {'.venv', 'node_modules', '.git', '__pycache__', 'my_lib', 'build', 'dist'}
    ignore_ext = {'.pdf', '.jpg', '.jpeg', '.png', '.mp4', '.ttf', '.pyc', '.exe', '.zip', '.tar'}

    issues_found = []

    for root, dirs, files in os.walk(target_dir):
        # Klasörleri filtrele
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ignore_ext:
                continue

            # .env dosyalarının paylaşılan klasörde bulunması başlı başına güvenlik ihlalidir
            # (Ancak .env.example gibi şablonlara izin verilir)
            if file == '.env' or file.endswith('.env'):
                # Sadece '.env.example' gibi exception'lar hariç tutulabilir.
                # Eğer Starter Kit için config.env vb varsa, isimlerine izin verebiliriz ama
                # genel best practice, secret isimli dosyaların gitmemesidir.
                pass

            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        for label, regex in patterns.items():
                            if re.search(regex, line):
                                issues_found.append(f"⚠️ {label} Tespiti: {filepath} (Satır {line_no})")
            except Exception:
                pass # UTF-8 okunamayan binary dosyalar atlanır

    if issues_found:
        print("\n" + "="*50)
        print("❌ GÜVENLİK İHLALİ TESPİT EDİLDİ! PAYLAŞIM DURDURULDU.")
        print("="*50)
        for issue in issues_found:
            print(issue)
        print("\nLütfen bu sızıntıları temizleyip süreci tekrar başlatın.")
        sys.exit(1)
    else:
        print("\n✅ Tarama Temiz! Herhangi bir PII veya API Key sızıntısı bulunamadı.")
        print("Paylaşım güvenlidir.")
        sys.exit(0)

if __name__ == "__main__":
    main()
