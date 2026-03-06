import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from keep_alive import keep_alive 
from database import Database

# --- 1. Smart Prefix Logic (MongoDB Version) ---
def get_prefix(bot, message):
    default_prefix = "Nova"
    prefixes = [default_prefix]
    
    if not message.guild:
        return prefixes

    # MongoDB থেকে কাস্টম প্রেফিক্স চেক করা (JSON এর বদলে)
    col = Database.get_collection("server_settings")
    if col is not None:
        data = col.find_one({"_id": str(message.guild.id)})
        if data and "prefix" in data:
            custom_prefix = data["prefix"]
            if custom_prefix != default_prefix:
                prefixes.append(custom_prefix)

    return prefixes

# --- 2. Main Bot Class Setup ---
class NovaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all() 
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None, 
            case_insensitive=True,
            strip_after_prefix=True # ✅ আপনার পছন্দের স্পেস হ্যান্ডলিং
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
        
        try:
            synced = await self.tree.sync()
            print(f"🛰️ Synced {len(synced)} slash commands globally!")
        except Exception as e:
            print(f"❌ Slash sync failed: {e}")

# Create bot instance
bot = NovaBot()

# --- 3. Events ---
@bot.event
async def on_ready():
    print(f"🚀 Logged in as {bot.user} (ID: {bot.user.id})")
    print("------ Nova is Ready! ------")
    await bot.change_presence(activity=discord.Game(name="Nova help | /help"))

# --- 4. Prefix Change Command (MongoDB Version) ---
@bot.hybrid_command(name="set_prefix", description="⚙️ Add a custom prefix (Default 'Nova' will ALWAYS work)")
@commands.has_permissions(administrator=True)
@app_commands.describe(new_prefix="Type the new prefix (e.g., ?)")
async def set_prefix(ctx, new_prefix: str):
    clean_prefix = new_prefix.strip()
    
    # MongoDB তে নতুন প্রেফিক্স সেভ করা
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
            f"✅ `{clean_prefix} help` (Space works automatically!)\n"
            f"✅ `Nova help` (Default 'Nova' is always active)"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# --- 5. Run ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ Error: 'DISCORD_TOKEN' not found in Environment Variables!")
          
