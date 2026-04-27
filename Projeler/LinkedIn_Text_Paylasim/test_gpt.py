from core.post_writer import PostWriter
from core.researcher import Researcher
from config import settings

settings.IS_DRY_RUN = False
researcher = Researcher()
content = researcher.research_weekly_news()
writer = PostWriter()
# I will temporarily patch PostWriter model in the script or just see what it outputs right now
print(writer.write_weekly_news_post(content))
