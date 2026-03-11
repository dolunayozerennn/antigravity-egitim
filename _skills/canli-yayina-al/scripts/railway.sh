#!/bin/bash
# Railway GraphQL API + CLI Wrapper — Token'ı otomatik yükler
# 
# BİRİNCİL YÖNTEM: GraphQL API (her zaman çalışır)
# İKİNCİL YÖNTEM: CLI (varsa ve çalışıyorsa)
#
# Kullanım: ./railway.sh <komut> [argümanlar]
#
# API komutları (doğrudan GraphQL):
#   ./railway.sh api-test              ← Token doğrulama
#   ./railway.sh projects              ← Tüm projeleri listele
#   ./railway.sh envs <project_id>     ← Environment'ları listele
#   ./railway.sh vars <project_id> <env_id> <service_id>  ← Env var oku
#   ./railway.sh deploy-status <project_id> <env_id> <service_id>  ← Deploy durumu
#   ./railway.sh redeploy <service_id> <env_id>  ← Redeploy tetikle
#   ./railway.sh logs <deployment_id>  ← Deploy logları
#
# CLI komutları (CLI varsa):
#   ./railway.sh cli <herhangi_cli_komutu>

SCRIPT_DIR="/Users/dolunayozeren/Desktop/Antigravity/_skills/production-deploy/scripts"
ANTIGRAVITY_ROOT="/Users/dolunayozeren/Desktop/Antigravity"
KNOWLEDGE_FILE="$ANTIGRAVITY_ROOT/_knowledge/api-anahtarlari.md"

# --- 1. Railway Token'ı bul ---
find_token() {
    # Öncelik 1: Environment variable olarak zaten set edilmiş mi?
    if [ -n "$RAILWAY_TOKEN" ]; then
        echo "✅ Token: Environment variable'dan alındı" >&2
        return 0
    fi

    # Öncelik 2: Skill klasöründeki railway-token.txt dosyasından oku
    local token_file="$SCRIPT_DIR/railway-token.txt"
    if [ -f "$token_file" ]; then
        RAILWAY_TOKEN=$(cat "$token_file" | tr -d '[:space:]')
        if [ -n "$RAILWAY_TOKEN" ] && [ "$RAILWAY_TOKEN" != "HENÜZ_KAYDEDİLMEDİ" ]; then
            echo "✅ Token: railway-token.txt dosyasından alındı" >&2
            export RAILWAY_TOKEN
            return 0
        fi
        RAILWAY_TOKEN=""
    fi

    # Öncelik 3: _knowledge/api-anahtarlari.md'den oku
    if [ -f "$KNOWLEDGE_FILE" ]; then
        RAILWAY_TOKEN=$(grep -A1 "### Railway" "$KNOWLEDGE_FILE" 2>/dev/null | grep "Token:" | sed 's/.*`\(.*\)`.*/\1/' | head -1)
        if [ -n "$RAILWAY_TOKEN" ] && [ "$RAILWAY_TOKEN" != "HENÜZ_KAYDEDİLMEDİ" ]; then
            echo "✅ Token: _knowledge/api-anahtarlari.md'den alındı" >&2
            export RAILWAY_TOKEN
            return 0
        fi
        RAILWAY_TOKEN=""
    fi

    # Token bulunamadıysa hata ver
    echo "❌ Railway Token bulunamadı!" >&2
    echo "" >&2
    echo "Çözüm seçenekleri:" >&2
    echo "  1. _knowledge/api-anahtarlari.md → Railway bölümüne token'ı yaz" >&2
    echo "  2. export RAILWAY_TOKEN='senin-tokenin'" >&2
    echo "  3. https://railway.app/account/tokens adresinden yeni token al" >&2
    return 1
}

# --- 2. GraphQL API çağrı fonksiyonu ---
railway_api() {
    local query="$1"
    curl -s -X POST https://backboard.railway.app/graphql/v2 \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RAILWAY_TOKEN" \
        -d "{\"query\": \"$query\"}"
}

# JSON formatla (python3 varsa)
format_json() {
    python3 -m json.tool 2>/dev/null || cat
}

# --- 3. Token'ı bul ---
find_token || exit 1

# --- 4. Komut işleme ---
case "$1" in
    # === API KOMUTLARI (BİRİNCİL) ===
    
    api-test)
        echo "🔍 Railway API Token testi..."
        railway_api '{ projects { edges { node { id name } } } }' | format_json
        ;;

    projects)
        echo "📋 Railway Projeleri:" >&2
        railway_api '{ projects { edges { node { id name services { edges { node { id name } } } } } } }' | format_json
        ;;

    envs)
        if [ -z "$2" ]; then
            echo "❌ Kullanım: ./railway.sh envs <project_id>" >&2
            exit 1
        fi
        railway_api "{ project(id: \\\"$2\\\") { environments { edges { node { id name } } } } }" | format_json
        ;;

    vars)
        if [ -z "$4" ]; then
            echo "❌ Kullanım: ./railway.sh vars <project_id> <env_id> <service_id>" >&2
            exit 1
        fi
        railway_api "{ variables(projectId: \\\"$2\\\", environmentId: \\\"$3\\\", serviceId: \\\"$4\\\") }" | format_json
        ;;

    set-var)
        if [ -z "$6" ]; then
            echo "❌ Kullanım: ./railway.sh set-var <project_id> <env_id> <service_id> <key> <value>" >&2
            exit 1
        fi
        railway_api "mutation { variableCollectionUpsert(input: { projectId: \\\"$2\\\", environmentId: \\\"$3\\\", serviceId: \\\"$4\\\", variables: { $5: \\\"$6\\\" } }) }" | format_json
        ;;

    deploy-status)
        if [ -z "$4" ]; then
            echo "❌ Kullanım: ./railway.sh deploy-status <project_id> <env_id> <service_id>" >&2
            exit 1
        fi
        echo "📊 Son deployment'lar:" >&2
        railway_api "{ deployments(first: 5, input: { projectId: \\\"$2\\\", environmentId: \\\"$3\\\", serviceId: \\\"$4\\\" }) { edges { node { id status createdAt } } } }" | format_json
        ;;

    redeploy)
        if [ -z "$3" ]; then
            echo "❌ Kullanım: ./railway.sh redeploy <service_id> <env_id>" >&2
            exit 1
        fi
        echo "🚀 Redeploy tetikleniyor..." >&2
        railway_api "mutation { serviceInstanceRedeploy(serviceId: \\\"$2\\\", environmentId: \\\"$3\\\") }" | format_json
        ;;

    logs)
        if [ -z "$2" ]; then
            echo "❌ Kullanım: ./railway.sh logs <deployment_id> [limit]" >&2
            exit 1
        fi
        local limit="${3:-50}"
        railway_api "{ deploymentLogs(deploymentId: \\\"$2\\\", limit: $limit) { message timestamp severity } }" | format_json
        ;;

    # === CLI KOMUTLARI (İKİNCİL) ===
    
    cli)
        shift  # 'cli' argümanını kaldır
        # CLI binary'yi bul
        RAILWAY_BIN=""
        if command -v railway &>/dev/null; then
            RAILWAY_BIN="railway"
        else
            KNOWN_LOCATIONS=(
                "$ANTIGRAVITY_ROOT/Projeler/shorts-demo-otomasyonu/.railway-bin/railway"
                "$ANTIGRAVITY_ROOT/_skills/production-deploy/scripts/railway-bin"
                "/usr/local/bin/railway"
                "$HOME/.railway/bin/railway"
            )
            for loc in "${KNOWN_LOCATIONS[@]}"; do
                if [ -x "$loc" ]; then
                    RAILWAY_BIN="$loc"
                    break
                fi
            done
        fi

        if [ -z "$RAILWAY_BIN" ]; then
            echo "❌ Railway CLI bulunamadı." >&2
            echo "💡 CLI yerine API komutlarını kullan: ./railway.sh projects" >&2
            echo "   CLI kurmak için: curl -fsSL https://railway.app/install.sh | sh" >&2
            exit 1
        fi

        echo "🔧 CLI: $RAILWAY_BIN" >&2
        "$RAILWAY_BIN" "$@"
        ;;

    # === YARDIM ===
    
    help|--help|-h|"")
        echo "🚂 Railway API + CLI Wrapper"
        echo ""
        echo "📡 API Komutları (BİRİNCİL — her zaman çalışır):"
        echo "  api-test                                  Token doğrulama"
        echo "  projects                                  Tüm projeleri listele"
        echo "  envs <project_id>                         Environment'ları listele"
        echo "  vars <proj_id> <env_id> <svc_id>          Env variable oku"
        echo "  set-var <proj_id> <env_id> <svc_id> K V   Env variable yaz"
        echo "  deploy-status <proj_id> <env_id> <svc_id> Son deployment durumu"
        echo "  redeploy <service_id> <env_id>            Redeploy tetikle"
        echo "  logs <deployment_id> [limit]              Deploy logları"
        echo ""
        echo "🔧 CLI Komutları (İKİNCİL — CLI kuruluysa):"
        echo "  cli <komut> [args]                        Railway CLI komutunu çalıştır"
        echo ""
        echo "📋 Örnekler:"
        echo "  ./railway.sh projects"
        echo "  ./railway.sh deploy-status abc-123 def-456 ghi-789"
        echo "  ./railway.sh redeploy ghi-789 def-456"
        echo "  ./railway.sh cli up"
        ;;

    *)
        echo "❌ Bilinmeyen komut: $1" >&2
        echo "💡 ./railway.sh help komutunu kullanarak mevcut komutları gör" >&2
        exit 1
        ;;
esac
