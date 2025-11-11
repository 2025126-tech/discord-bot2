import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# === Flask部分（Renderのスリープ防止用） ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === Discord Bot設定 ===
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ ログインしました: {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    channel = after.channel or before.channel
    if not channel:
        return

    # Bot通知を送るチャンネルIDを設定（後で変更）
    notify_channel_id = 123456789012345678  # ←ここに通知用テキストチャンネルのIDを入れてね
    notify_channel = bot.get_channel(notify_channel_id)
    if not notify_channel:
        return

    if before.channel is None and after.channel is not None:
        await notify_channel.send(f"🎤 {member.display_name} がボイスチャンネル「{after.channel.name}」に参加しました！")
    elif before.channel is not None and after.channel is None:
        await notify_channel.send(f"👋 {member.display_name} がボイスチャンネル「{before.channel.name}」から退出しました！")

# === 起動 ===
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")  # Renderの環境変数で設定
bot.run(TOKEN)
