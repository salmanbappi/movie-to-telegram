import os
import sys
import requests
import time
import subprocess
from urllib.parse import unquote, urlparse

def download_with_aria2(url):
    print(f"📥 Downloading with Aria2: {url}")
    filename = unquote(url.split("/")[-1].split("?")[0])
    if not filename or len(filename) < 3: 
        filename = f"file_{int(time.time())}.mp4"
    
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join(os.getcwd(), "downloads", filename)

    cmd = [
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
        "--user-agent=Mozilla/5.0",
        "--console-log-level=warn", "--summary-interval=5",
        "--allow-overwrite=true",
        "-d", "downloads",
        "-o", filename,
        url
    ]
    subprocess.run(cmd, check=True)
    return file_path

def upload_to_telegram(bot_token, chat_id, filepath):
    # 1. LOGOUT from official server (Crucial for Local Server to work)
    print("🔌 Disconnecting bot from official Telegram servers...")
    requests.get(f"https://api.telegram.org/bot{bot_token}/logOut")
    
    # 2. Wait for local server
    print(f"🚀 Uploading to Telegram (2GB Mode)...")
    base_url = "http://localhost:8081"
    url = f"{base_url}/bot{bot_token}/sendDocument"
    
    # Use the absolute path for the local server
    abs_path = os.path.abspath(filepath)
    
    data = {
        'chat_id': chat_id,
        'document': f"file://{abs_path}", # Special local server syntax
        'caption': f"🎬 {os.path.basename(filepath)}"
    }
    
    # Since it's a local file, the server handles the upload internally and instantly
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print("🎉 Upload Successful!")
    else:
        print(f"❌ Upload failed: {response.text}")
        # Fallback to standard upload if local fails
        print("🔄 Attempting standard upload fallback...")
        with open(filepath, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", 
                          data={'chat_id': chat_id}, files={'document': f})

if __name__ == "__main__":
    url = sys.argv[1]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    try:
        path = download_with_aria2(url)
        print(f"✅ Downloaded to: {path}")
        upload_to_telegram(token, chat, path)
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'path' in locals() and os.path.exists(path):
            os.remove(path)