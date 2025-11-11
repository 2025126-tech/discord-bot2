# main.py
import os
import json
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands

# ========== keep-alive (Flask) ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== config persistence (simple JSON) ==========
CONFIG_FILE = "guild_config.json"
_config_lock = asyncio.Lock()

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

async def save_config(cfg):
    async with _config_lock:
        # write atomically
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_FILE)

# ========== Discord bot setup ==========
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("✅ Logged in as", bot.user)

# ---------- admin-only helper ----------
def is_guild_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# ========== Commands to configure per-guild notify channel ==========
@bot.command(name="set_notify")
@is_guild_admin()
async def set_notify(ctx, channel: discord.TextChannel):
    """
    サーバー管理者のみが実行可能:
    !set_notify #channel
    """
    cfg = load_config()
    guild_id = str(ctx.guild.id)
    cfg[guild_id] = {"notify_channel_id": channel.id}
    await save_config(cfg)
    await ctx.send(f"✅ 通知先を {channel.mention} に設定しました。")

@bot.command(name="remove_notify")
@is_guild_admin()
async def remove_notify(ctx):
    cfg = load_config()
    guild_id = str(ctx.guild.id)
    if guild_id in cfg:
        del cfg[guild_id]
        await save_config(cfg)
        await ctx.send("✅ 通知設定を削除しました。")
    else:
        await ctx.send("⚠️ このサーバーに設定はありません。")

@bot.command(name="show_notify")
async def show_notify(ctx):
    cfg = load_config()
    guild_id = str(ctx.guild.id)
    if guild_id in cfg:
        ch_id = cfg[guild_id].get("notify_channel_id")
        ch = bot.get_channel(ch_id)
        if ch:
            await ctx.send(f"📌 現在の通知先: {ch.mention}")
            return
    await ctx.send("ℹ️ 通知先が設定されていません。管理者は !set_notify #channel で設定できます。")

# ========== Voice state handling ==========
@bot.event
async def on_voice_state_update(member, before, after):
    # before/after: discord.VoiceState
    guild = member.guild
    cfg = load_config()
    guild_cfg = cfg.get(str(guild.id))
    if not guild_cfg:
        return  # このギルドは通知未設定

    notify_channel_id = guild_cfg.get("notify_channel_id")
    if not notify_channel_id:
        return

    notify_channel = bot.get_channel(notify_channel_id)
    if notify_channel is None:
        # Bot がチャンネルを見つけられない（アクセス権がない等）
        try:
            # optional: try fetch_channel
            notify_channel = await bot.fetch_channel(notify_channel_id)
        except Exception:
            return

    # 参加
    if before.channel is None and after.channel is not None:
        try:
            await notify_channel.send(f"🎤 **{member.display_name}** さんが `{after.channel.name}` に参加しました。")
        except discord.Forbidden:
            print(f"Forbidden to send message in {notify_channel.id} for guild {guild.id}")
    # 退出
    elif before.channel is not None and after.channel is None:
        try:
            await notify_channel.send(f"👋 **{member.display_name}** さんが `{before.channel.name}` から退出しました。")
        except discord.Forbidden:
            print(f"Forbidden to send message in {notify_channel.id} for guild {guild.id}")
    # チャンネル移動（before/after 両方存在するが異なる）
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        try:
            await notify_channel.send(f"🔄 **{member.display_name}** さんが `{before.channel.name}` から `{after.channel.name}` に移動しました。")
        except discord.Forbidden:
            print(f"Forbidden to send message in {notify_channel.id} for guild {guild.id}")

# ========== Start ==========
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set")
    else:
        bot.run(TOKEN)
