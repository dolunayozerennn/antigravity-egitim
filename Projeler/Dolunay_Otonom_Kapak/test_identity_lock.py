"""
Identity Lock Test — DNS sorunu bypass.
Gemini tema üretimini atlayarak doğrudan Kie AI görsel üretimini test eder.
Master anchor + yeni PIXEL PRIORITY prompt ile 1 kapak üretir.
"""
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.reels_agent import run_autonomous_generation

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    # 1. cutout_tags.json'dan master anchor ve secondary'leri oku
    tags_path = os.path.join(PROJECT_DIR, "agents", "cutout_tags.json")
    with open(tags_path, "r") as f:
        config = json.load(f)

    master = config["master_anchor"]
    secondaries = config["secondary_anchors"]
    cutout_dir = os.path.join(PROJECT_DIR, "assets", "cutouts")

    master_path = os.path.join(cutout_dir, master)
    extra_paths = [os.path.join(cutout_dir, s) for s in secondaries if os.path.exists(os.path.join(cutout_dir, s))]

    print(f"🧑 Master Anchor : {master} ({os.path.getsize(master_path)/1024/1024:.1f} MB)")
    print(f"🧑 Extra Refs    : {secondaries}")
    print()

    # 2. Hardcoded tema — DNS sorunu nedeniyle Gemini'yi atlıyoruz
    video_name = "Kimi 5"
    cover_text = "TEK PROMPTLA\nSİTE YAP"
    scene_description = (
        "A young tech entrepreneur sitting at a sleek desk in a dark room, "
        "illuminated by multiple monitor screens showing code and website layouts. "
        "Dramatic blue and purple screen glow on the subject's face."
    )
    script_text = (
        "Kimi K2.6 ile tek promptta tam işlevli bir web sitesi oluştur! "
        "Bu yeni yapay zeka, sadece tasarım değil, arka plan sistem mantığını "
        "ve veritabanı entegrasyonunu da tek bir komutla sağlıyor."
    )

    print(f"📌 Cover Text: '{cover_text}'")
    print(f"🎬 Scene: {scene_description[:80]}...")
    print()

    # 3. Tek bir kapak üret
    os.makedirs("outputs", exist_ok=True)
    output_path = os.path.join("outputs", "identity_lock_test.png")

    print("🎨 Kapak üretiliyor (Identity Lock test — PIXEL PRIORITY MODE)...")
    print("=" * 60)

    success = run_autonomous_generation(
        local_person_image_path=master_path,
        video_topic=video_name,
        main_text=cover_text,
        output_path=output_path,
        max_retries=1,
        variant_index=1,
        script_text=script_text,
        scene_description=scene_description,
        extra_cutout_paths=extra_paths,
    )

    print("=" * 60)
    if success:
        size_kb = os.path.getsize(output_path) / 1024
        print(f"\n✅ Test kapak üretildi: {output_path} ({size_kb:.0f} KB)")
        print("👉 Görseli açıp yüz tutarlılığını kontrol et.")
    else:
        print("\n❌ Kapak üretimi başarısız. Logları kontrol et.")


if __name__ == "__main__":
    main()
