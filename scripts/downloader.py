import os
import sys
import asyncio
from pyrogram import Client
from urllib.parse import unquote
import subprocess
import time

# Official Telegram Android API credentials (Public)
API_ID = 6
API_HASH = "eb06d4ab35275919747c3507256d98d1"

async def upload_file(bot_token, chat_id, filepath):
    print(f"🚀 Initializing Pyrogram (2GB Upload Mode)...")
    app = Client(
        "bot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=bot_token,
        in_memory=True
    )
    
    async with app:
        print(f"📤 Uploading: {os.path.basename(filepath)}")
        
        # Define progress callback
        last_update_time = 0
        def progress(current, total):
            nonlocal last_update_time
            now = time.time()
            if now - last_update_time > 2 or current == total:
                percentage = (current / total) * 100
                print(f"📊 Uploading: {percentage:.1f}% ({current // (1024*1024)}MB / {total // (1024*1024)}MB)")
                last_update_time = now

        await app.send_document(
            chat_id=int(chat_id),
            document=filepath,
            caption=f"🎬 {os.path.basename(filepath)}",
            progress=progress
        )
        print("🎉 Upload Successful!")

def download_with_aria2(url):
    print(f"📥 Downloading with Aria2: {url}")
    # Extract filename or use default
    filename = unquote(url.split("/")[-1].split("?")[0])
    if not filename or len(filename) < 3: 
        filename = f"file_{int(time.time())}.mp4"
    
    cmd = [
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--console-log-level=warn", "--summary-interval=5",
        "--allow-overwrite=true",
        "-o", filename,
        url
    ]
    subprocess.run(cmd, check=True)
    
    if os.path.exists(filename):
        return filename
    
    # Fallback search if -o didn't work as expected
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f not in ['downloader.py', 'main.yml', 'bot_session.session']]
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
        print("Error: Missing TELEGRAM_TOKEN or TELEGRAM_TO environment variables.")
        sys.exit(1)
        
    file_path = None
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
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"🧹 Cleaned up: {file_path}")