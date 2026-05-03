"""
3 farklı sahne ile GPT Image 2 entegrasyon testi.
Gemini sahne üretimini bypass ederek doğrudan kapak üretir, URL'leri toplar.
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.reels_agent import run_autonomous_generation

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


SCENES = [
    {
        "video_name": "Scene 1 — Klavye dağı",
        "cover_text": "KLAVYEYİ\nÇÖPE AT",
        "scene_description": (
            "Cinematic shot of a person standing triumphantly on top of a giant mountain "
            "of broken keyboards under dramatic golden hour lighting. Wide angle, movie poster style. "
            "No screens, no monitors, no computers visible anywhere."
        ),
        "script_text": "Yapay zeka asistanları artık klavyeye gerek bırakmıyor.",
    },
    {
        "video_name": "Scene 2 — Para yağmuru",
        "cover_text": "AJANSA\nPARA VERME",
        "scene_description": (
            "Cinematic shot of a person catching a rain of cash falling from the sky in an empty "
            "parking lot at sunset. Dramatic backlight, dust particles in the air. "
            "No screens, no monitors, no computers visible."
        ),
        "script_text": "Pazarlama ajanslarına bütçe ödemenin sonu geldi; AI ile kendin yapabilirsin.",
    },
    {
        "video_name": "Scene 3 — CV kurtarma",
        "cover_text": "CV'Nİ\nKURTAR",
        "scene_description": (
            "Cinematic shot of a person pulling a glowing CV document out of a dark trash can on a "
            "rainy street at night. Cinematic neon reflections on wet pavement. "
            "No screens, no monitors, no computers visible."
        ),
        "script_text": "İK departmanları artık AI tarafından okunan CV'leri istiyor.",
    },
]


def main():
    tags_path = os.path.join(PROJECT_DIR, "agents", "cutout_tags.json")
    with open(tags_path, "r") as f:
        config = json.load(f)
    master = config["master_anchor"]
    secondaries = config["secondary_anchors"]
    cutout_dir = os.path.join(PROJECT_DIR, "assets", "cutouts")
    master_path = os.path.join(cutout_dir, master)
    extra_paths = [
        os.path.join(cutout_dir, s)
        for s in secondaries
        if os.path.exists(os.path.join(cutout_dir, s))
    ]

    print(f"🧑 Master: {master}")
    print(f"🧑 Extras: {len(extra_paths)} cutout(s)")
    print()

    os.makedirs("outputs", exist_ok=True)
    results = []

    for i, scene in enumerate(SCENES, start=1):
        print("=" * 70)
        print(f"▶️  SAHNE {i}/3: {scene['video_name']}")
        print(f"   Text : {scene['cover_text']}")
        print(f"   Scene: {scene['scene_description'][:80]}...")
        print("=" * 70)

        output_path = os.path.join("outputs", f"gpt_image_2_scene_{i}.png")
        t0 = time.time()
        success = run_autonomous_generation(
            local_person_image_path=master_path,
            video_topic=scene["video_name"],
            main_text=scene["cover_text"],
            output_path=output_path,
            max_retries=1,  # tek deneme, kalite gözlemi için
            variant_index=i,
            script_text=scene["script_text"],
            scene_description=scene["scene_description"],
            extra_cutout_paths=extra_paths,
        )
        elapsed = time.time() - t0

        size_kb = (os.path.getsize(output_path) / 1024) if os.path.exists(output_path) else 0
        results.append(
            {
                "scene": scene["video_name"],
                "ok": success,
                "path": output_path,
                "size_kb": size_kb,
                "elapsed_s": round(elapsed, 1),
            }
        )

    print("\n" + "=" * 70)
    print("📊 ÖZET")
    print("=" * 70)
    for r in results:
        status = "✅" if r["ok"] else "❌"
        print(f"{status} {r['scene']}  ·  {r['size_kb']:.0f} KB  ·  {r['elapsed_s']}s")
        print(f"    → {r['path']}")


if __name__ == "__main__":
    main()
