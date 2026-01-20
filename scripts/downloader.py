import os
import sys
import asyncio
from pyrogram import Client
from urllib.parse import unquote
import subprocess
import time

# Official Telegram Desktop public test keys
API_ID = 2040
API_HASH = "b18441a17074072000020c086a3746a4"

async def upload_file(bot_token, chat_id, filepath):
    print(f"🚀 Initializing Pyrogram (2GB Upload Mode)...")
    
    # We use a unique session name to avoid conflicts
    session_name = f"tgd_{int(time.time())}"
    
    app = Client(
        session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=bot_token,
        in_memory=True
    )
    
    async with app:
        print(f"📤 Uploading: {os.path.basename(filepath)}")
        
        last_update_time = 0
        def progress(current, total):
            nonlocal last_update_time
            now = time.time()
            if now - last_update_time > 5 or current == total:
                percentage = (current / total) * 100
                speed = current / (now - start_time + 0.1)
                print(f"📊 Uploading: {percentage:.1f}% | Speed: {speed / (1024*1024):.1f} MB/s")
                last_update_time = now

        start_time = time.time()
        await app.send_document(
            chat_id=int(chat_id),
            document=filepath,
            caption=f"🎬 {os.path.basename(filepath)}",
            progress=progress
        )
        print("\n🎉 Upload Successful!")

def download_with_aria2(url):
    print(f"📥 Downloading with Aria2: {url}")
    # Extract filename or use default
    filename = unquote(url.split("/")[-1].split("?")[0])
    if not filename or len(filename) < 3: 
        filename = f"file_{int(time.time())}.mp4"
    
    # We use a temp directory to avoid picking up wrong files
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", filename)

    cmd = [
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--console-log-level=warn", "--summary-interval=5",
        "--allow-overwrite=true",
        "-d", "downloads",
        "-o", filename,
        url
    ]
    subprocess.run(cmd, check=True)
    
    if os.path.exists(file_path):
        return file_path
    
    raise Exception("Download failed: File not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    if not token or not chat:
        print("Error: Missing credentials.")
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
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"🧹 Cleaned up: {file_path}")
