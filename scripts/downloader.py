import os
import sys
import asyncio
from telethon import TelegramClient
from urllib.parse import unquote, urlparse
import subprocess

# Official Telegram Android API credentials (Public)
API_ID = 6
API_HASH = "eb06d4ab35275919747c3507256d98d1"

async def upload_file(bot_token, chat_id, filepath):
    print(f"🚀 Initializing Telethon (2GB Upload Mode)...")
    async with TelegramClient('bot_session', API_ID, API_HASH) as client:
        await client.start(bot_token=bot_token)
        
        print(f"📤 Uploading: {os.path.basename(filepath)}")
        
        # Define progress callback
        def progress_callback(current, total):
            percentage = (current / total) * 100
            print(f"\r📊 Uploading: {percentage:.1f}% ({current}/{total})", end="", flush=True)

        await client.send_file(
            int(chat_id), 
            filepath, 
            caption=f"🎬 {os.path.basename(filepath)}",
            progress_callback=progress_callback
        )
        print("\n🎉 Upload Successful!")

def download_with_aria2(url):
    print(f"📥 Downloading with Aria2: {url}")
    # Extract filename or use default
    filename = unquote(url.split("/")[-1].split("?")[0])
    if not filename: filename = "file.mp4"
    
    cmd = [
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--console-log-level=warn", "--summary-interval=1",
        url
    ]
    subprocess.run(cmd, check=True)
    
    # Find the file (aria2 might have changed the name slightly)
    # We look for the most recently modified file that isn't a script
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f not in ['downloader.py', 'main.yml']]
    if not files:
        raise Exception("Download failed: No file found.")
    
    return max(files, key=os.path.getmtime)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <URL>")
        sys.exit(1)
        
    url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    if not token or not chat:
        print("Error: Missing environment variables.")
        sys.exit(1)
        
    try:
        # 1. Download
        file_path = download_with_aria2(url)
        print(f"✅ Downloaded: {file_path}")
        
        # 2. Upload
        asyncio.run(upload_file(token, chat, file_path))
        
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
