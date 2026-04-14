import sys
import os

sys.path.append(os.getcwd())

modules_to_test = [
    "services.web_scraper_service",
    "services.openai_service",
    "core.scenario_engine",
    "core.conversation_manager",
    "main"
]

for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"SUCCESS: {mod}")
    except Exception as e:
        print(f"FAILED {mod}: {e}")
