import json

files = [
    "Projeler/WhatsApp_Onboarding/config/env.js",
    "Projeler/WhatsApp_Onboarding/server.js",
    "Projeler/WhatsApp_Onboarding/services/manychat.js",
    "Projeler/WhatsApp_Onboarding/services/phoneValidator.js",
    "_knowledge/bekleyen-gorevler.md",
    "_knowledge/calisma-kurallari.md"
]

out = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            out.append({
                "path": f,
                "content": file.read()
            })
    except Exception as e:
        print(f"Error reading {f}: {e}")

with open("push_files.json", "w", encoding="utf-8") as f:
    json.dump(out, f)
