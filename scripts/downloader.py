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
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
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
        requests.get(f"https://api.telegram.org/bot{bot_token}/logOut", timeout=10)
    except: pass
    
    time.sleep(3)
    
    # 2. Local Server Upload
    print(f"🚀 Uploading to Local Bot API Server...")
    base_url = "http://localhost:8081"
    
    filename = os.path.basename(filepath)
    # The container maps the workspace to /data
    container_path = f"/data/files/{filename}"
    
    url = f"{base_url}/bot{bot_token}/sendDocument"
    params = {
        'chat_id': chat_id,
        'document': f"file://{container_path}",
        'caption': f"🎬 {filename}"
    }
    
    try:
        response = requests.get(url, params=params, timeout=None)
        if response.status_code == 200:
            print("🎉 SUCCESS! File sent to Telegram.")
            return
    except Exception as e:
        print(f"⚠️ Local upload error: {e}")

    # FINAL FALLBACK: Official API (Max 50MB)
    print("🔄 Falling back to official API...")
    with open(filepath, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", 
                      data={'chat_id': chat_id, 'caption': f"🎬 {filename}"}, 
                      files={'document': f})

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    download_url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    fpath = None
    try:
        fpath = download_with_aria2(download_url)
        upload_to_telegram(token, chat, fpath)
    except Exception as e:
        print(f"💥 Task failed: {e}")
        sys.exit(1)
    finally:
        if fpath and os.path.exists(fpath):
            os.remove(fpath)
