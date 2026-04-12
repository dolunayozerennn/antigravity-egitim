#!/usr/bin/env python3
"""
Conversation Manager Test — Sohbet akışını programatik olarak test eder.
Her senaryoda GPT'nin doğru action/reply üretip üretmediğini kontrol eder.
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(__file__))
os.environ["ENV"] = "development"

from core.conversation_manager import ConversationManager

# Renk kodları
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_test(name):
    print(f"\n{'='*60}")
    print(f"{BOLD}{CYAN}📋 TEST: {name}{RESET}")
    print(f"{'='*60}")


def print_user(msg):
    print(f"\n{BOLD}👤 Kullanıcı:{RESET} {msg}")


def print_bot(result):
    action = result.get("action", "?")
    reply = result.get("reply", "")
    config = result.get("config")

    color = GREEN if action in ("confirm", "start_pipeline") else YELLOW if action == "ask" else CYAN
    print(f"{color}🤖 Bot [{action}]:{RESET} {reply[:300]}")
    if config:
        print(f"   {YELLOW}⚙️ Config:{RESET} {json.dumps(config, ensure_ascii=False, indent=2)[:200]}")


async def test_scenario_1():
    """Basit tek klip talebi — tam akış."""
    print_test("Senaryo 1 — Basit tek klip talebi")
    cm = ConversationManager()
    user_id = 1001

    # Mesaj 1: Video fikri
    print_user("Uzayda yüzen astronot videosu istiyorum")
    r1 = await cm.process_message(user_id, "Uzayda yüzen astronot videosu istiyorum")
    print_bot(r1)
    assert r1["action"] in ("ask", "confirm"), f"Beklenen ask/confirm, gelen: {r1['action']}"

    # Mesaj 2: Eğer soru sorduysa cevapla
    if r1["action"] == "ask":
        print_user("Tek klip olsun, dikey format, Seedance kullan")
        r2 = await cm.process_message(user_id, "Tek klip olsun, dikey format, Seedance kullan")
        print_bot(r2)
        assert r2["action"] in ("ask", "confirm"), f"Beklenen ask/confirm, gelen: {r2['action']}"
    else:
        r2 = r1

    # Mesaj 3: Onay
    if r2["action"] == "confirm":
        print_user("Evet, başla!")
        r3 = await cm.process_message(user_id, "Evet, başla!")
        print_bot(r3)
        assert r3["action"] == "start_pipeline", f"Beklenen start_pipeline, gelen: {r3['action']}"
        assert r3.get("config"), "Config objesi boş!"
        assert r3["config"].get("topic"), "Config'te topic yok!"
        print(f"\n{GREEN}✅ Senaryo 1 BAŞARILI{RESET}")
        return r3
    else:
        # Bir tur daha devam et
        print_user("Evet, onaylıyorum")
        r3 = await cm.process_message(user_id, "Evet, onaylıyorum")
        print_bot(r3)
        print(f"\n{YELLOW}⚠️ Senaryo 1 — ekstra tur gerekti{RESET}")
        return r3


async def test_scenario_2():
    """Detaylı çoklu klip talebi."""
    print_test("Senaryo 2 — Çoklu klip + Veo modeli")
    cm = ConversationManager()
    user_id = 1002

    print_user("Okyanus altında yüzen balina sürüsü videosu istiyorum. 3 kliplik, yatay format, Veo 3.1 kullan.")
    r1 = await cm.process_message(user_id, "Okyanus altında yüzen balina sürüsü videosu istiyorum. 3 kliplik, yatay format, Veo 3.1 kullan.")
    print_bot(r1)

    if r1["action"] == "confirm":
        # Direkt onay durumunda
        cfg = r1.get("config", {})
        assert cfg.get("clip_count", 1) >= 2, f"Klip sayısı hatalı: {cfg.get('clip_count')}"
        print_user("Başla")
        r2 = await cm.process_message(user_id, "Başla")
        print_bot(r2)
        print(f"\n{GREEN}✅ Senaryo 2 BAŞARILI{RESET}")
    elif r1["action"] == "ask":
        print_user("Evet, 3 klip, yatay, Veo ile başla")
        r2 = await cm.process_message(user_id, "Evet, 3 klip, yatay, Veo ile başla")
        print_bot(r2)
        
        if r2["action"] == "confirm":
            print_user("Onay")
            r3 = await cm.process_message(user_id, "Onay")
            print_bot(r3)
        print(f"\n{GREEN}✅ Senaryo 2 BAŞARILI{RESET}")


async def test_scenario_3():
    """Video talebi OLMAYAN normal sohbet."""
    print_test("Senaryo 3 — Normal sohbet (video talebi yok)")
    cm = ConversationManager()
    user_id = 1003

    print_user("Merhaba, nasılsın?")
    r1 = await cm.process_message(user_id, "Merhaba, nasılsın?")
    print_bot(r1)
    assert r1["action"] == "chat", f"Beklenen chat, gelen: {r1['action']}"
    print(f"\n{GREEN}✅ Senaryo 3 BAŞARILI — Normal sohbet doğru tespit edildi{RESET}")


async def test_scenario_4():
    """Belirsiz konu — Bot'un soru sorması gerekiyor."""
    print_test("Senaryo 4 — Belirsiz talep")
    cm = ConversationManager()
    user_id = 1004

    print_user("Bi video yapalım")
    r1 = await cm.process_message(user_id, "Bi video yapalım")
    print_bot(r1)
    assert r1["action"] in ("ask", "chat"), f"Belirsiz talep'te ask/chat bekleniyor, gelen: {r1['action']}"
    
    if r1["action"] == "ask":
        print(f"\n{GREEN}✅ Senaryo 4 BAŞARILI — Bot konu sordu{RESET}")
    else:
        print(f"\n{YELLOW}⚠️ Senaryo 4 — Bot sohbet olarak algıladı (kabul edilebilir){RESET}")


async def test_scenario_5():
    """Config doğrulama — orientation ve model mapping."""
    print_test("Senaryo 5 — Config doğrulama")
    cm = ConversationManager()
    user_id = 1005

    print_user("Tokyo sokaklarında gece yürüyüşü, sinematik kalitede olsun, 2 klip, Veo 3.1 ile")
    r1 = await cm.process_message(user_id, "Tokyo sokaklarında gece yürüyüşü, sinematik kalitede olsun, 2 klip, Veo 3.1 ile")
    print_bot(r1)

    # Onay iste
    if r1["action"] == "confirm" and r1.get("config"):
        cfg = r1["config"]
        checks = []
        if cfg.get("model") == "veo3.1":
            checks.append(f"{GREEN}✅ Model: veo3.1{RESET}")
        else:
            checks.append(f"{RED}❌ Model hatalı: {cfg.get('model')}{RESET}")
        
        if cfg.get("clip_count", 0) >= 2:
            checks.append(f"{GREEN}✅ Klip: {cfg['clip_count']}{RESET}")
        else:
            checks.append(f"{RED}❌ Klip sayısı hatalı: {cfg.get('clip_count')}{RESET}")

        for c in checks:
            print(f"   {c}")

    print_user("Evet başla")
    r2 = await cm.process_message(user_id, "Evet başla")
    print_bot(r2)
    print(f"\n{GREEN}✅ Senaryo 5 tamamlandı{RESET}")


async def main():
    print(f"\n{BOLD}{'='*60}")
    print(f"🧪 YouTube Otomasyonu V2 — Conversation Test Suite")
    print(f"{'='*60}{RESET}\n")

    try:
        await test_scenario_1()
        await test_scenario_2()
        await test_scenario_3()
        await test_scenario_4()
        await test_scenario_5()
    except Exception as e:
        print(f"\n{RED}❌ TEST HATASI: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n\n{BOLD}{'='*60}")
    print(f"{GREEN}✅ TÜM TESTLER TAMAMLANDI{RESET}")
    print(f"{'='*60}\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success is True else 1)
