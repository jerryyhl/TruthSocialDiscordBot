import re
import discord
import truthbrush
from discord.ext import tasks
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import aiohttp
import io
import traceback

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
            post_time = datetime.fromisoformat(post['created_at']).astimezone(PST)
            
            # Create base embed
            embed = discord.Embed(
                title="📢 New Truth Social Post",
                description=re.sub(r'<[^>]+>', '', post['content']),
                color=0x1DA1F2,
                timestamp=post_time,
                url=f"https://truthsocial.com/@{post['account']['username']}/{post['id']}"
            )
            
            # Add author with profile link
            embed.set_author(
                name=f"{post['account']['display_name']} (@{post['account']['username']})",
                icon_url=post['account']['avatar_static']
            )

            # Handle media attachments
            media = post.get('media_attachments', [])
            image_urls = [m['url'] for m in media if m['type'] == 'image']
            other_media = [m for m in media if m['type'] != 'image']

            files = []
            # Add first image as embed image using file attachment
            if image_urls:
                try:
                    image_url = image_urls[0]
                    print(f"🖼️ Downloading image from: {image_urls[0]}")  # Debug log
                    
                    # Download the image
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                data = io.BytesIO(await resp.read())
                                
                                # Create discord.File object
                                file = discord.File(data, filename="truth_image.png")
                                files.append(file)
                                
                                # Set image using attachment reference
                                embed.set_image(url="attachment://truth_image.png")
                            else:
                                print(f"⚠️ Failed to download image: HTTP {resp.status}")
                except Exception as e:
                    print(f"🚨 Image download failed: {str(e)}")
        #     media = post.get('media_attachments', [])
        #     image_urls = [m['url'] for m in media if m['type'] == 'image']
        #     other_media = [m for m in media if m['type'] != 'image']

        #     # Add first image as embed image
        #     if image_urls:
        #         print(f"🖼️ Found image URL: {image_urls[0]}")  # Debug log
        #         embed.set_image(url=image_urls[0])
                
        #     # Add other media as links
            if media:
                embed.add_field(
                    name="Attachments",
                    value="\n".join([f"🔗 {m['url']}" for m in media]),
                    inline=False
                )

        #     # Add footer with platform info
            embed.set_footer(text="Posted on Truth Social")
            
            await channel.send(embed=embed, files=files)
            print(f"✅ Posted embed with {len(media)} media items")

        except Exception as e:
            print(f"❌ Failed to post embed: {str(e)}")
            traceback.print_exc()

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