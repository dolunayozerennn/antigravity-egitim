#!/bin/bash
# ============================================
# Qwen Image Edit — Görsel Düzenleme
# Mevcut görseli revize etme, arka plan değişikliği, nesne ekleme/çıkarma
# ============================================
# Kullanım:
#   bash scripts/qwen_edit.sh "düzenleme talimatı (İngilizce)" "image_url" [strength]
#
# Örnekler:
#   bash scripts/qwen_edit.sh "Change background to tropical beach" "https://url/gorsel.jpg" 0.7
#   bash scripts/qwen_edit.sh "Add sunglasses to the person" "https://url/kisi.jpg" 0.5
#   bash scripts/qwen_edit.sh "Remove the text from the image" "https://url/poster.jpg" 0.6

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/kie_poll.sh"

PROMPT="${1:?Hata: Düzenleme talimatı gerekli (İngilizce). Kullanım: bash $0 \"edit instruction\" \"image_url\" [strength]}"
IMAGE_URL="${2:?Hata: Görsel URL'si gerekli.}"
STRENGTH="${3:-0.7}"

echo "✏️  Qwen Image Edit — Görsel Düzenleme"
echo "   Talimat: $PROMPT"
echo "   Görsel: $IMAGE_URL"
echo "   Strength: $STRENGTH"

JSON_BODY=$(jq -n \
  --arg prompt "$PROMPT" \
  --arg img "$IMAGE_URL" \
  --argjson strength "$STRENGTH" \
  '{
    model: "qwen/image-edit",
    input: {
      prompt: $prompt,
      image_url: $img,
      strength: $strength,
      output_format: "png"
    }
  }')

echo ""
echo "📤 Görev gönderiliyor..."
TASK_ID=$(create_task "$JSON_BODY")
echo "   Task ID: $TASK_ID"

poll_task "$TASK_ID" 60 5
