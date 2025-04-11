import truthbrush
from dotenv import load_dotenv
import os

load_dotenv()

try:
    # Initialize API with credentials
    tb = truthbrush.Api(
        username=os.getenv("TRUTHSOCIAL_USERNAME"),
        password=os.getenv("TRUTHSOCIAL_PASSWORD")
    )

    # Fetch the latest post from Trump
    username = "realDonaldTrump"
    user_id = tb.lookup(username)["id"]
    
    # Get only the most recent post (limit=1)
    posts = tb._get(f"/v1/accounts/{user_id}/statuses?exclude_replies=true&limit=1")

    if posts:
        latest_post = posts[0]
        print(f"""
        Latest Post from @{username} ({latest_post['created_at']}):
        Content: {latest_post['content']}
        Media: {[media['url'] for media in latest_post.get('media_attachments', [])]}
        URL: https://truthsocial.com/@{username}/{latest_post['id']}
        """)
    else:
        print("No posts found for this user")

except Exception as e:
    print(f"Error fetching posts: {str(e)}")