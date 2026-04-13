import os
import sys
import asyncio

# Proje dizinleri
sys.path.insert(0, os.path.dirname(__file__))
from infrastructure.kie_client import KieClient

TEST_CASES = {
    "cat_snitching": {
        "absurd": "Smartphone video. The living room is destroyed with trash. A cat meows angrily and points its paw at a guilty-looking golden retriever.",
    },
    "getaway_cat": {
        "absurd": "Police bodycam at night. Cop approaches a pulled-over car. A cat is sitting in the driver seat, slams the gas pedal and drives off quickly.",
    }
}

kie = KieClient()

async def run_visual_tests():
    print("🚀 İnsan-Gözü Kalibrasyon Testleri Başlıyor (SESLİ, 10sn)...\n")
    
    for case_name, styles in TEST_CASES.items():
        print(f"==============================================")
        print(f"🎬 KONSEPT: {case_name.upper()}")
        print(f"==============================================")
        
        for style, prompt_text in styles.items():
            print(f"  → Stil: SHORT & ABSURD")
            print(f"  → Prompt: '{prompt_text}'")
            print("    [1/2] Seedance 2.0 sunucusuna gönderildi...")
            
            try:
                # Gerçek kullanım ayarları: audio=True, duration=10
                video_url = await kie.create_video(
                    model="seedance-2",
                    prompt=prompt_text,
                    orientation="portrait",
                    duration=10,
                    audio=True,
                )
                print(f"    ✅ VİDEO HAZIR (SESLİ): {video_url}\n")
            except Exception as ex:
                print(f"    ❌ Üretim Hatası: {ex}\n")

if __name__ == "__main__":
    asyncio.run(run_visual_tests())

