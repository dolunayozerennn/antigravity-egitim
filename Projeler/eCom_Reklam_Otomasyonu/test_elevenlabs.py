import os
import sys
sys.path.append(os.getcwd())
from services.elevenlabs_service import ElevenLabsService

def get_master_env():
    api_key = None
    with open("/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env", "r") as f:
        for line in f:
            if line.startswith("ELEVENLABS_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip("\"'\n")
                break
    return api_key

def main():
    api_key = get_master_env()
    if not api_key:
        print("API Key not found!")
        return

    service = ElevenLabsService(api_key=api_key)
    try:
        audio = service.generate_speech("Bu bir test anonsudur.", voice_name="Sarah")
        print(f"Başarılı! Ses boyutu: {len(audio)}")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
