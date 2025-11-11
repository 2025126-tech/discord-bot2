import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# ====== Flaskサーバー（UptimeRobot用） ======
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Discord Bot is running on Render!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# ====== 設定ファイル ======
CONFIG_FILE = "guild_config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                return {}
            return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ====== Discord Bot 設定 ======
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot起動完了: {bot.user}")

# ====== コマンド: 通知チャンネル設定 ======
@bot.command()
async def set_notify(ctx, channel: discord.TextChannel):
    cfg = load_config()
    cfg[str(ctx.guild.id)] = channel.id
    save_config(cfg)
    await ctx.send(f"✅ 通知チャンネルを {channel.mention} に設定しました。")

@bot.command()
async def show_notify(ctx):
    cfg = load_config()
    ch_id = cfg.get(str(ctx.guild.id))
    if ch_id:
        channel = bot.get_channel(ch_id)
        await ctx.send(f"🔔 現在の通知チャンネルは {channel.mention} です。")
    else:
        await ctx.send("⚠️ 通知チャンネルはまだ設定されていません。")

# ====== VC通知 ======
@bot.event
async def on_voice_state_update(member, before, after):
    cfg = load_config()
    ch_id = cfg.get(str(member.guild.id))
    if not ch_id:
        return

    channel = bot.get_channel(ch_id)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(f"🎤 {member.display_name} が {after.channel.name} に参加しました！")
    elif before.channel is not None and after.channel is None:
        await channel.send(f"👋 {member.display_name} がボイスチャットから退出しました！")

# ====== Flask + Bot同時起動 ======
def start_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ 環境変数 DISCORD_TOKEN が設定されていません。")
        return
    bot.run(token)

if __name__ == "__main__":
    Thread(target=run_web).start()
    start_bot()
