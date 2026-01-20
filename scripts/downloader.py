import os
import sys
import requests
import time
import subprocess
from urllib.parse import unquote

def download_with_aria2(url):
    print(f"📥 Downloading: {url}")
    filename = unquote(url.split("/")[-1].split("?")[0])
    if not filename or len(filename) < 3: 
        filename = f"file_{int(time.time())}.mp4"
    
    os.makedirs("files", exist_ok=True)
    
    cmd = [
        "aria2c", "-x", "16", "-s", 16, "-k", "1M",
        "--user-agent=Mozilla/5.0",
        "--console-log-level=warn",
        "-d", "files",
        "-o", filename,
        url
    ]
    print(f"🛠️ Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    full_path = os.path.join(os.getcwd(), "files", filename)
    if os.path.exists(full_path):
        return full_path
    raise Exception(f"File not found after download: {full_path}")

def upload_to_telegram(bot_token, chat_id, filepath):
    # 1. LOGOUT from official API
    print("🔌 Requesting Logout from official Telegram API...")
    try:
        r = requests.get(f"https://api.telegram.org/bot{bot_token}/logOut", timeout=10)
        print(f"📡 Logout Response: {r.text}")
    except Exception as e:
        print(f"⚠️ Logout failed (might already be logged out): {e}")
    
    time.sleep(3)
    
    # 2. Local Server Upload
    print(f"🚀 Uploading to Local Bot API Server...")
    base_url = "http://localhost:8081"
    
    # The container mount maps github.workspace to /data
    # Runner: /home/runner/work/movie-to-telegram/movie-to-telegram/files/filename
    # Container: /data/files/filename
    
    filename = os.path.basename(filepath)
    container_path = f"/data/files/{filename}"
    
    url = f"{base_url}/bot{bot_token}/sendDocument"
    params = {
        'chat_id': chat_id,
        'document': f"file://{container_path}",
        'caption': f"🎬 {filename}"
    }
    
    print(f"📤 Sending request to local server for: {container_path}")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("🎉 SUCCESS! Telegram accepted the file.")
        print(f"📝 Server Response: {response.text}")
    else:
        print(f"❌ LOCAL FAILED ({response.status_code}): {response.text}")
        
        # FINAL FALLBACK: If under 50MB, use official API
        size_mb = os.path.getsize(filepath) / (1024*1024)
        if size_mb < 49:
            print("🔄 File is small. Using official API fallback...")
            with open(filepath, 'rb') as f:
                r2 = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", 
                                  data={'chat_id': chat_id, 'caption': f"🎬 {filename}"}, 
                                  files={'document': f})
                print(f"📡 Official API Response: {r2.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py [url]")
        sys.exit(1)
        
    download_url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    if not token or not chat:
        print("❌ Error: TELEGRAM_TOKEN or TELEGRAM_TO not set.")
        sys.exit(1)
        
    fpath = None
    try:
        fpath = download_with_aria2(download_url)
        print(f"✅ Downloaded: {fpath}")
        upload_to_telegram(token, chat, fpath)
    except Exception as e:
        print(f"💥 Task failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if fpath and os.path.exists(fpath):
            os.remove(fpath)
            print(f"🧹 Cleaned up: {fpath}")