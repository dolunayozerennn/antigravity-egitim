import sys
import os

sys.path.append(os.getcwd())

modules_to_test = [
    "services.firecrawl_service",
    "services.openai_service",
    "services.kie_api",
    "services.elevenlabs_service",
    "services.replicate_service",
    "services.notion_service",
    "core.scenario_engine",
    "core.conversation_manager",
    "core.production_pipeline",
    "core.url_data_extractor",
    "main",
]

for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"SUCCESS: {mod}")
    except Exception as e:
        print(f"FAILED {mod}: {e}")
