#!/bin/zsh
# ============================================================
# 🚂 Railway Tüm Projeleri Linkle — Tek Seferlik Kurulum
# ============================================================

export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

PROJELER_DIR="$HOME/Desktop/Antigravity/Projeler"
SUCCESS=0
FAIL=0
SKIP=0

link_project() {
  local name="$1"
  local id="$2"
  local service="$3"
  local path="$PROJELER_DIR/$name"
  
  if [ -d "$path" ]; then
    cd "$path"
    if /usr/local/bin/node /usr/local/bin/railway link --project "$id" --environment production --service "$service" 2>&1; then
      echo "   ✅ $name → $service"
      ((SUCCESS++))
    else
      echo "   ❌ $name başarısız"
      ((FAIL++))
    fi
  else
    echo "   ⏭️  $name → Klasör yok"
    ((SKIP++))
  fi
}

echo "🚂 Railway Tüm Projeleri Linkleniyor..."
echo "========================================="

link_project "WhatsApp_Onboarding"        "5f346c33-6af1-4788-8405-34133c98451b" "whatsapp-onboarding"
link_project "Lead_Notifier_Bot"          "7c5d3081-1487-4b02-a60f-1cb7a04bb135" "lead-notifier-bot-v3"
link_project "Ceren_Marka_Takip"          "c563b334-2a3c-49bf-8461-9852ca649112" "ceren-marka-takip-cron"
link_project "YouTube_Otomasyonu"         "87e24335-52c9-460f-8b2e-0f481f5501bd" "youtube-bot"
link_project "eCom_Reklam_Otomasyonu"     "8797307d-7b80-41cb-add0-976c09eaeed4" "ecom-bot"
link_project "Dolunay_Otonom_Kapak"       "9a55cc02-4e75-44f9-993c-31c6f0616c55" "reels-kapak"
link_project "Ceren_izlenme_notifier"     "b5117788-3979-45b3-a92c-eae3606e0dc2" "ceren-izlenme-notifier"
link_project "Twitter_Video_Paylasim"     "24c3d0d1-58e7-4213-826b-c7e2d1c45a30" "twitter-video-cron"
link_project "LinkedIn_Text_Paylasim"     "5465753a-2653-400a-ae3a-d4593de9c40e" "linkedin-text-cron"
link_project "LinkedIn_Video_Paylasim"    "59d79d0c-bd8c-46af-80e1-1b64ade41304" "linkedin-video-cron"
link_project "Isbirligi_Tahsilat_Takip"   "8f70b293-dc33-426a-95f7-19741d3ae03c" "tahsilat-bot"
link_project "Lead_Pipeline"              "fc91edb9-5d93-413d-b9b7-75ae81033204" "lead-pipeline"
link_project "Akilli_Watchdog"            "ec3ea7b1-9bdb-4886-a197-026ee2d2126c" "akilli-watchdog"
link_project "Marka_Is_Birligi"           "6994adc2-edb2-4c91-b43d-237f28d41a69" "marka-is-birligi"

echo ""
echo "========================================="
echo "🏁 Sonuç: $SUCCESS başarılı, $FAIL başarısız, $SKIP atlandı"
