import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
from keep_alive import keep_alive 
from database import Database

# --- ১. স্মার্ট প্রেফিক্স লজিক (MongoDB Version) ---
def get_prefix(bot, message):
    default_prefix = "Nova"
    prefixes = [default_prefix]
    
    if not message.guild:
        return prefixes

    # MongoDB থেকে কাস্টম প্রেফিক্স চেক করা
    try:
        col = Database.get_collection("server_settings")
        if col is not None:
            data = col.find_one({"_id": str(message.guild.id)})
            if data and "prefix" in data:
                custom_prefix = data["prefix"]
                if custom_prefix != default_prefix:
                    prefixes.append(custom_prefix)
    except:
        pass

    return prefixes

# --- ২. মেইন বট ক্লাস (AutoShardedBot ব্যবহার করা হয়েছে ১০০+ সার্ভারের জন্য) ---
class NovaBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all() 
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None, 
            case_insensitive=True,
            strip_after_prefix=True,
            chunk_guilds_at_startup=False, # স্টার্টআপে প্রেসার কমাবে (Rate Limit রক্ষা করবে)
            heartbeat_timeout=60.0
        )

    async def setup_hook(self):
        print("🔄 Loading Commands (Cogs)...")
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"  ✅ Loaded: {filename}")
                    except Exception as e:
                        print(f"  ❌ Failed to load {filename}: {e}")
        
        # স্ল্যাশ কমান্ড সিঙ্ক করার সময় রেট লিমিট হ্যান্ডলিং
        try:
            print("🛰️ Syncing slash commands...")
            synced = await self.tree.sync()
            print(f"🛰️ Synced {len(synced)} slash commands globally!")
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("⚠️ Sync failed: Rate limited by Discord. They will sync eventually.")
            else:
                print(f"❌ Slash sync error: {e}")

# বটের ইনস্ট্যান্স তৈরি
bot = NovaBot()

# --- ৩. ইভেন্টসমূহ ---
@bot.event
async def on_ready():
    print(f"🚀 Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"📊 Currently in {len(bot.guilds)} servers")
    print("------ Nova is Ready! ------")
    await bot.change_presence(activity=discord.Game(name="Nova help | /help"))

# --- ৪. প্রেফিক্স চেঞ্জ কমান্ড (MongoDB Version) ---
@bot.hybrid_command(name="set_prefix", description="⚙️ Add a custom prefix (Default 'Nova' will ALWAYS work)")
@commands.has_permissions(administrator=True)
@app_commands.describe(new_prefix="Type the new prefix (e.g., ?)")
async def set_prefix(ctx, new_prefix: str):
    clean_prefix = new_prefix.strip()
    
    col = Database.get_collection("server_settings")
    if col is not None:
        col.update_one(
            {"_id": str(ctx.guild.id)}, 
            {"$set": {"prefix": clean_prefix}}, 
            upsert=True
        )

    embed = discord.Embed(
        title="✅ Custom Prefix Set",
        description=(
            f"Prefix updated to **`{clean_prefix}`**\n\n"
            f"**Usage Examples:**\n"
            f"✅ `{clean_prefix}help`\n"
            f"✅ `Nova help` (Always works)"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# --- ৫. রান এবং রেট লিমিট এরর হ্যান্ডলিং ---
if __name__ == "__main__":
    keep_alive() # Render-এর জন্য সার্ভার চালু করবে
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        try:
            bot.run(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("\n❌ FATAL ERROR: Discord is blocking this IP (Rate Limit).")
                print("💡 Solution: Suspend the bot on Render for 15-30 minutes, then resume.\n")
                time.sleep(10) # এরর লুপ আটকানোর জন্য ছোট বিরতি
            else:
                raise e
    else:
        print("❌ Error: 'DISCORD_TOKEN' not found in Environment Variables!")
        
