import os
os.environ['IS_DRY_RUN'] = 'False'
from config import settings
settings.IS_DRY_RUN = False

from core.post_writer import PostWriter

writer = PostWriter()
res = writer.write_weekly_news_post("1. X released new AI model\n2. Apple announced AI features\n3. OpenAI introduces GPT-5\n4. Midjourney v7 is out\n5. Groq speeds up inference by 10x")
print("LEN:", len(res))
print(res)
