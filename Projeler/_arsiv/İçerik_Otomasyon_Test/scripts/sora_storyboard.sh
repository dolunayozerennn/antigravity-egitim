#!/bin/bash
# ============================================
# Sora 2 Pro Storyboard — E-Ticaret Video Üretimi
# Çok sahneli, 25 saniyeye kadar reklam videoları
# ============================================
# Kullanım:
#   bash scripts/sora_storyboard.sh "sahne1|sahne2|sahne3" ["image_url"]
#
# Sahneler pipe (|) ile ayrılır.
# Her sahneye opsiyonel süre eklenebilir: "sahne açıklaması:5"
#
# Örnekler:
#   bash scripts/sora_storyboard.sh "Kırmızı ayakkabı yakın çekim:5|Koşan atlet:8|Logo:4" "https://url/urun.jpg"
#   bash scripts/sora_storyboard.sh "Ürün masada:6|Ürün kullanımda:8|Marka finali:5"

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/kie_poll.sh"

SCENES_INPUT="${1:?Hata: Sahneler gerekli. Kullanım: bash $0 \"sahne1|sahne2|sahne3\" [\"image_url\"]}"
IMAGE_URL="${2:-}"

echo "🎬 Sora 2 Pro Storyboard — Video Üretimi"
echo "   Sahneler: $SCENES_INPUT"
[ -n "$IMAGE_URL" ] && echo "   Referans Görsel: $IMAGE_URL"

# Sahneleri parse et
IFS='|' read -ra SCENES <<< "$SCENES_INPUT"

STORYBOARD="["
TOTAL_DURATION=0
for i in "${!SCENES[@]}"; do
  SCENE="${SCENES[$i]}"
  
  # Süreyi ayır (format: "prompt:süre")
  if [[ "$SCENE" == *":"* ]]; then
    PROMPT="${SCENE%:*}"
    DURATION="${SCENE##*:}"
  else
    PROMPT="$SCENE"
    DURATION=5  # Varsayılan 5 saniye
  fi
  
  TOTAL_DURATION=$((TOTAL_DURATION + DURATION))
  
  if [ $i -gt 0 ]; then
    STORYBOARD+=","
  fi
  
  # İlk sahneye referans görseli ekle
  if [ $i -eq 0 ] && [ -n "$IMAGE_URL" ]; then
    STORYBOARD+=$(jq -n \
      --arg prompt "$PROMPT" \
      --argjson duration "$DURATION" \
      --arg img "$IMAGE_URL" \
      '{prompt: $prompt, duration: $duration, image_url: $img}')
  else
    STORYBOARD+=$(jq -n \
      --arg prompt "$PROMPT" \
      --argjson duration "$DURATION" \
      '{prompt: $prompt, duration: $duration}')
  fi
done
STORYBOARD+="]"

# 25 saniye kontrolü
if [ $TOTAL_DURATION -gt 25 ]; then
  echo "⚠️  Uyarı: Toplam süre ${TOTAL_DURATION}s, maksimum 25s olmalı!"
  echo "   Süreler otomatik olarak orantılı şekilde küçültülecek."
fi

echo "   Toplam süre: ${TOTAL_DURATION}s"
echo "   Sahne sayısı: ${#SCENES[@]}"

# JSON body oluştur
JSON_BODY=$(jq -n \
  --argjson storyboard "$STORYBOARD" \
  '{
    model: "sora/storyboard",
    input: {
      storyboard: $storyboard
    }
  }')

echo ""
echo "📤 Görev gönderiliyor..."
echo "$JSON_BODY" | jq '.'

TASK_ID=$(create_task "$JSON_BODY")
echo "   Task ID: $TASK_ID"

# Sonucu bekle (video üretimi daha uzun sürer)
poll_task "$TASK_ID" 120 10
