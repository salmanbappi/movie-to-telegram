import os
import sys
import requests
from tqdm import tqdm

def download_file(url, filename):
    print(f"📥 Downloading: {url}")
    # Use a realistic User-Agent to avoid blocks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
        desc=filename
    ) as bar:
        for data in response.iter_content(chunk_size=1024*1024):
            size = f.write(data)
            bar.update(size)
    print(f"✅ Download complete: {filename} ({total_size} bytes)")

def upload_to_telegram(bot_token, chat_id, filepath):
    print(f"🚀 Uploading to Telegram (via local server for 2GB support)...")
    
    # Check if local server is running, otherwise fallback to official API (50MB limit)
    try:
        requests.get("http://localhost:8081", timeout=1)
        base_url = "http://localhost:8081"
        print("⚡ Using local Bot API server (2GB limit supported)")
    except:
        base_url = "https://api.telegram.org"
        print("⚠️ Local server not found. Using official API (50MB limit!)")

    url = f"{base_url}/bot{bot_token}/sendDocument"
    
    with open(filepath, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': f"🎬 {os.path.basename(filepath)}"}
        # No timeout for large uploads
        response = requests.post(url, data=data, files=files, timeout=None)
        
    if response.status_code == 200:
        print("🎉 Upload successful!")
    else:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <URL>")
        sys.exit(1)
        
    download_url = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_TOKEN or TELEGRAM_TO not set.")
        sys.exit(1)
        
    # Extract filename from URL and handle encoding
    from urllib.parse import unquote
    filename = unquote(download_url.split("/")[-1].split("?")[0])
    if not filename:
        filename = "movie.mp4"
        
    try:
        download_file(download_url, filename)
        upload_to_telegram(bot_token, chat_id, filename)
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(filename):
            os.remove(filename)