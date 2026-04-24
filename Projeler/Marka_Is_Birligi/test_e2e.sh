#!/usr/bin/env bash
# Marka İş Birliği E2E Test (Dry Run) 
# Bu betik, APIFY_API_KEY, OPENAI_API_KEY ve NOTION tokenleri dahil tüm boru hattını
# e-posta atmadan ve veritabanına yazmadan gerçek verilerle test eder.

# Proje dizinine git
cd "$(dirname "$0")"

# Local environment variables yükle
if [ -f "../../_knowledge/credentials/master.env" ]; then
    export $(cat ../../_knowledge/credentials/master.env | grep -v '^#' | xargs)
    echo "✅ Master env yüklendi."
else
    echo "⚠️ master.env bulunamadı. Environment variable'lar sistemden alınacak."
fi

# Sanal ortama geçiş
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ .venv bulunamadı. Sistem python'u kullanılacak."
fi

echo "============================================================"
echo "🧪 Marka İş Birliği - Uçtan Uca Dry Run Testi Başlıyor"
echo "============================================================"

# Ana pipeline testini dry-run ile başlat
PYTHONPATH=. python3 src/outreach.py --dry-run
PIPELINE_STATUS=$?

if [ $PIPELINE_STATUS -ne 0 ]; then
    echo "❌ BÜYÜK HATA: Pipeline testi çöktü. Lütfen hataları kontrol et."
    exit 1
else
    echo "✅ Pipeline scripti başarıyla test edildi."
fi

echo "============================================================"
echo "🧪 Response Checker Testi Başlıyor"
echo "============================================================"
# Cevap okuyucuyu test et
PYTHONPATH=. python3 src/response_checker.py --dry-run
REPONSE_STATUS=$?

if [ $REPONSE_STATUS -ne 0 ]; then
    echo "❌ BÜYÜK HATA: Response checker çöktü."
    exit 1
else
    echo "✅ Response checker başarıyla test edildi."
fi

echo "============================================================"
echo "✅ TÜM SISTEM TESTLERİ BAŞARIYLA TAMAMLANDI."
echo "     Bu proje üretimde sorunsuz çalışabilir."
echo "============================================================"
exit 0
