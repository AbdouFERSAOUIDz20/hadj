import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up intents (required to read messages)
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with the prefix '!'
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready to play audio!')

@bot.command()
async def play(ctx):
    # Check if the user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You need to join a voice channel first!")
        return

    channel = ctx.author.voice.channel

    # Connect to the voice channel
    try:
        voice_client = await channel.connect()
    except discord.ClientException:
        # Already connected, so we get the existing voice client
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    # Check if the audio file exists
    audio_file = "audio.mp3"
    if not os.path.exists(audio_file):
        await ctx.send(f"Error: `{audio_file}` not found in the bot's folder.")
        # Disconnect if it's not going to play
        await voice_client.disconnect()
        return

    # Play the audio file
    def after_playing(error):
        if error:
            print(f"Error during playback: {error}")
            return
            
        # If the bot is still connected, loop the audio
        if voice_client.is_connected():
            try:
                new_source = discord.FFmpegPCMAudio(audio_file)
                voice_client.play(new_source, after=after_playing)
            except Exception as e:
                print(f"Error looping audio: {e}")

    if not voice_client.is_playing():
        try:
            # FFmpeg is required to stream the audio
            source = discord.FFmpegPCMAudio(audio_file)
            voice_client.play(source, after=after_playing)
            await ctx.send(f"🎵 Playing `{audio_file}` in **{channel.name}**")
        except Exception as e:
            await ctx.send("Error playing audio. Is FFmpeg installed?")
            print(e)
            await voice_client.disconnect()
    else:
        await ctx.send("Already playing audio.")

@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Audio stopped and bot left the channel.")
    else:
        await ctx.send("Not connected to a voice channel.")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
