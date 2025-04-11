import re
import discord
import truthbrush
from discord.ext import tasks
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo


# Load environment variables
load_dotenv()

# Timezone configuration
PST = ZoneInfo("America/Los_Angeles")

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
        try:
            print(f"🔄 Looking up user ID for @{self.username}...")
            self.user_id = self.tb.lookup(self.username)["id"]
            print(f"✅ Successfully fetched user ID: {self.user_id}")
        except Exception as e:
            print(f"❌ Failed to lookup user: {str(e)}")
            raise
        
        print("⏳ Starting post monitoring...")
        self.check_posts.start()

    @tasks.loop(seconds=30)
    async def check_posts(self):
        try:
            now_pst = datetime.now(PST).strftime('%H:%M:%S %Z')
            print(f"\n🔍 [{now_pst}] Checking for new posts...")
            
            posts = self.tb._get(
                f"/v1/accounts/{self.user_id}/statuses?limit=1"
            )

            if posts:
                post = posts[0]
                if self.last_post_id != post['id']:
                    if not self.initial_check:
                        post_time = datetime.fromisoformat(post['created_at']).astimezone(PST)
                        print(f"🎯 New post detected! ID: {post['id']}")
                        print(f"🕒 Post time: {post_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        await self.post_to_discord(post)
                    else:
                        print(f"⚙️ Initial check - baseline ID set to {post['id']}")
                        self.initial_check = False
                    
                    self.last_post_id = post['id']
            else:
                print("ℹ️ No posts found in this check")

        except Exception as e:
            print(f"⚠️ Check failed: {str(e)}")
            await asyncio.sleep(60)

    async def post_to_discord(self, post):
        try:
            channel = self.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
            
            # Convert and format timestamps
            post_time = datetime.fromisoformat(post['created_at']).astimezone(PST)
            time_str = post_time.strftime("%B %d, %Y at %I:%M %p %Z")
            
            # Remove all HTML tags and format content
            clean_content = re.sub(r'<[^>]+>', '', post['content'])
            content = clean_content.replace('\n', '\n\n')  # Preserve paragraph breaks
            
            # Build message
            message = (
                f"**Latest Truth Social Post from {post['account']['display_name']} @{post['account']['username']}**\n"
                f"*Posted on {time_str}*\n\n"
                f"{content}\n\n"
                f"[View on Truth Social](https://truthsocial.com/@{post['account']['username']}/{post['id']})"
            )
            
            # Add media attachments
            if media := post.get('media_attachments'):
                media_links = "\n".join([f"📷 {m['url']}" for m in media])
                message += f"\n\n**Media Attachments:**\n{media_links}"
            
            await channel.send(message)
            print(f"📨 Successfully posted to Discord channel {os.getenv('DISCORD_CHANNEL_ID')}")
            print(f"🔗 Post URL: https://truthsocial.com/@{self.username}/{post['id']}")

        except Exception as e:
            print(f"❌ Failed to post to Discord: {str(e)}")

    async def on_ready(self):
        startup_time = datetime.now(PST).strftime('%Y-%m-%d %H:%M:%S %Z')
        print("\n" + "="*40)
        print(f"🤖 Bot successfully logged in as {self.user}")
        print(f"🕒 Current System Time: {startup_time}")
        print(f"👤 Monitoring account: @{self.username}")
        print(f"⏱ Check interval: Every 30 seconds")
        print(f"📡 Channel ID: {os.getenv('DISCORD_CHANNEL_ID')}")
        print("="*40 + "\n")

# Run the bot
intents = discord.Intents.default()
TruthBot(intents=intents).run(os.getenv("DISCORD_BOT_TOKEN"))