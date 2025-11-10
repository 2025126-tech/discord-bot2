import os
import discord
from discord.ext import commands

# ボットのトークンはあとで差し替える
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # これが重要（ボイスチャンネルのイベントを受け取る）
intents.members = True       # VC参加者の情報を取得するために必要


bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    # テキストチャンネル（通知を送りたい場所）
    text_channel = discord.utils.get(member.guild.text_channels, name="雑談")

    # 🎙️ 参加したとき
    if before.channel is None and after.channel is not None:
        if text_channel:
            await text_channel.send(f"🎙️ {member.display_name} さんが {after.channel.name} に参加しました！")
        else:
            print(f"🎙️ {member.display_name} さんが {after.channel.name} に参加（通知チャンネルなし）")

    # 👋 退出したとき
    elif before.channel is not None and after.channel is None:
        if text_channel:
            await text_channel.send(f"👋 {member.display_name} さんが {before.channel.name} から退出しました。")
        else:
            print(f"👋 {member.display_name} さんが {before.channel.name} から退出（通知チャンネルなし）")

    # 🔄 別のボイスチャンネルに移動したとき
    elif before.channel != after.channel:
        if text_channel:
            await text_channel.send(f"🔄 {member.display_name} さんが {before.channel.name} から {after.channel.name} に移動しました！")
        else:
            print(f"🔄 {member.display_name} さんが {before.channel.name} から {after.channel.name} に移動（通知チャンネルなし）")


@bot.command()
async def hello(ctx):
    await ctx.send("こんにちは！")

bot.run(TOKEN)

