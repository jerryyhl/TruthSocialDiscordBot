import truthbrush
from dotenv import load_dotenv
import os

load_dotenv()

tb = truthbrush.Api(
    username=os.getenv("TRUTHSOCIAL_USERNAME"),
    password=os.getenv("TRUTHSOCIAL_PASSWORD")
)

# Get your latest post
posts = tb._get(f"/v1/accounts/{tb.lookup('bignews123')['id']}/statuses?limit=1")
print("Latest Post:", posts[0]['content'] if posts else "No posts found")