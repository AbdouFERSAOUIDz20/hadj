import discord
from discord.ext import commands
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Dummy web server to keep Render happy and provide a health check API
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/healthz', '/api/health']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Bot is running!"}')
        else:
            self.send_response(404)
            self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

# Start the background web server thread
threading.Thread(target=run_dummy_server, daemon=True).start()

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
async def play(ctx, *, target_channel: discord.VoiceChannel = None):
    # Use specified channel or author's current channel
    if target_channel:
        channel = target_channel
    elif ctx.author.voice:
        channel = ctx.author.voice.channel
    else:
        await ctx.send("You need to join a voice channel first, or mention one like `!play #channel-name`!")
        return

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

    if voice_client.is_playing():
        await ctx.send("Already playing audio.")
        return

    # Play the audio file infinitely
    def play_loop(error=None):
        if error:
            print(f"Error during playback: {error}")
            return
            
        if voice_client and voice_client.is_connected():
            try:
                def play_next():
                    if voice_client.is_connected():
                        new_source = discord.FFmpegPCMAudio(audio_file)
                        voice_client.play(new_source, after=play_loop)
                
                bot.loop.call_soon_threadsafe(play_next)
            except Exception as e:
                print(f"Error looping audio: {e}")

    try:
        # Start the first playback
        source = discord.FFmpegPCMAudio(audio_file)
        voice_client.play(source, after=play_loop)
        await ctx.send(f"🎵 Playing `{audio_file}` continuously in **{channel.name}**")
    except Exception as e:
        await ctx.send("Error playing audio. Is FFmpeg installed?")
        print(e)
        await voice_client.disconnect()

@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        if voice_client.is_playing():
            voice_client.stop()
        await voice_client.disconnect()
        await ctx.send("Audio stopped and bot left the channel.")
    else:
        await ctx.send("Not connected to a voice channel.")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
