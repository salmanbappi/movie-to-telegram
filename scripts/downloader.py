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
    
    # We download directly into /data (which is mapped to the container root)
    # The runner path is /home/runner/work/movie-to-telegram/movie-to-telegram/
    # We'll create a 'files' subdir
    os.makedirs("files", exist_ok=True)
    
    cmd = [
        "aria2c", "-x", 16, "-s", 16, "-k", "1M",
        "--user-agent=Mozilla/5.0",
        "--console-log-level=warn",
        "-d", "files",
        "-o", filename,
        url
    ]
    subprocess.run(cmd, check=True)
    return filename

def upload_to_telegram(bot_token, chat_id, filename):
    # 1. LOGOUT from official server
    print("🔌 Logging out from official API...")
    requests.get(f"https://api.telegram.org/bot{bot_token}/logOut")
    time.sleep(2) # Give it a moment
    
    # 2. Local Server Upload
    print(f"🚀 Uploading {filename} (Local Server mode)...")
    base_url = "http://localhost:8081"
    
    # In the container, the 'files' folder is at /data/files/
    container_path = f"/data/files/{filename}"
    
    url = f"{base_url}/bot{bot_token}/sendDocument"
    data = {
        'chat_id': chat_id,
        'document': f"file://{container_path}",
        'caption': f"🎬 {filename}"
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print("🎉 SUCCESS! File sent to Telegram.")
    else:
        print(f"❌ FAILED: {response.text}")
        # Fallback
        print("🔄 Trying standard upload (max 50MB)...")
        real_path = os.path.join("files", filename)
        with open(real_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", 
                          data={'chat_id': chat_id}, files={'document': f})

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    
    download_url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    try:
        fname = download_with_aria2(download_url)
        upload_to_telegram(token, chat, fname)
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'fname' in locals() and os.path.exists(os.path.join("files", fname)):
            os.remove(os.path.join("files", fname))
