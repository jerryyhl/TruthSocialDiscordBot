import discord
import truthbrush
from discord.ext import tasks
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime

load_dotenv()

class TruthBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_post_id = None
        self.tb = truthbrush.Api(
            username=os.getenv("TRUTHSOCIAL_USERNAME"),
            password=os.getenv("TRUTHSOCIAL_PASSWORD")
        )
        self.username = "bignews123"  # Your Truth Social username
        self.user_id = None
        self.initial_check = True

    async def setup_hook(self):
        self.user_id = self.tb.lookup(self.username)["id"]
        self.check_posts.start()

    @tasks.loop(seconds=30)
    async def check_posts(self):
        try:
            posts = self.tb._get(
                f"/v1/accounts/{self.user_id}/statuses?limit=1"
            )

            if posts:
                post = posts[0]
                if self.last_post_id != post['id']:
                    if not self.initial_check:
                        await self.post_to_discord(post)
                    self.last_post_id = post['id']
                    self.initial_check = False

        except Exception as e:
            print(f"Check failed: {str(e)}")
            await asyncio.sleep(60)

    async def post_to_discord(self, post):
        channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        
        # Format timestamp
        post_time = datetime.fromisoformat(post['created_at']).strftime("%B %d, %Y at %I:%M %p UTC")
        
        # Format content with proper line breaks
        content = post['content'].replace('\n', '\n\n')  # Double newlines for Discord paragraphs
        
        # Create message embed
        message = (
            f"**Latest Truth Social Post from {post['account']['display_name']} @{post['account']['username']}**\n"
            f"*Posted on {post_time}*\n\n"
            f"{content}\n\n"
            f"[View on Truth Social](https://truthsocial.com/@{post['account']['username']}/{post['id']})"
        )
        
        # Add media if available (corrected section)
        if media := post.get('media_attachments'):
            media_links = "\n".join([f"📷 {m['url']}" for m in media])  # Added camera emoji
            message += f"\n\n**Media Attachments:**\n{media_links}"
        
        await channel.send(message)
        
    async def on_ready(self):
        print(f'Bot ready! Monitoring @{self.username} for new posts')

intents = discord.Intents.default()
TruthBot(intents=intents).run(os.getenv("DISCORD_BOT_TOKEN"))