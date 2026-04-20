import sys
import os
import asyncio

# Setup env for testing
os.environ["TELEGRAM_ECOM_BOT_TOKEN"] = "test"
os.environ["TELEGRAM_ADMIN_CHAT_ID"] = "1238877494"
os.environ["OPENAI_API_KEY"] = "sk-test"

from config import settings
from core.conversation_manager import ConversationManager
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    class MockOpenAI:
        async def chat_with_tools(self, *args, **kwargs):
            class Msg:
                tool_calls = None
                content = "Merhaba LLM yaniti"
            return Msg()
    
    mgr = ConversationManager(MockOpenAI())
    res = await mgr.handle_text_message(1238877494, "https://www.lecolor.com.tr/tranz-a5-ciz--mavi-def-200-sy.-2180", "TestUser")
    print(f"Res url send: {res}")

if __name__ == "__main__":
    asyncio.run(test())
