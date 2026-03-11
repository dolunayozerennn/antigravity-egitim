#!/bin/bash
# ============================================
# NanoBanana Pro — Tekli Görsel Üretimi
# Instagram post, poster, banner
# ============================================
# Kullanım:
#   bash scripts/nanobananapro_image.sh "prompt" "aspect_ratio" ["image_url"]
#
# Örnekler:
#   bash scripts/nanobananapro_image.sh "Modern yaz kampanyası postu" "4:5"
#   bash scripts/nanobananapro_image.sh "Bu ürünü Instagram postu yap" "1:1" "https://url/urun.jpg"

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/kie_poll.sh"

PROMPT="${1:?Hata: Prompt gerekli. Kullanım: bash $0 \"prompt\" \"aspect_ratio\" [\"image_url\"]}"
ASPECT_RATIO="${2:-4:5}"
IMAGE_URL="${3:-}"

echo "🖼️  NanoBanana Pro — Görsel Üretimi"
echo "   Prompt: $PROMPT"
echo "   Aspect Ratio: $ASPECT_RATIO"
[ -n "$IMAGE_URL" ] && echo "   Referans Görsel: $IMAGE_URL"

# JSON body oluştur
if [ -n "$IMAGE_URL" ]; then
  JSON_BODY=$(jq -n \
    --arg prompt "$PROMPT" \
    --arg ratio "$ASPECT_RATIO" \
    --arg img "$IMAGE_URL" \
    '{
      model: "nano-banana-pro",
      input: {
        prompt: $prompt,
        aspect_ratio: $ratio,
        image_input: [$img]
      }
    }')
else
  JSON_BODY=$(jq -n \
    --arg prompt "$PROMPT" \
    --arg ratio "$ASPECT_RATIO" \
    '{
      model: "nano-banana-pro",
      input: {
        prompt: $prompt,
        aspect_ratio: $ratio
      }
    }')
fi

echo "📤 Görev gönderiliyor..."
TASK_ID=$(create_task "$JSON_BODY")
echo "   Task ID: $TASK_ID"

# Sonucu bekle
poll_task "$TASK_ID" 60 5
