import os
import sys
import requests
from tqdm import tqdm
from urllib.parse import unquote, urlparse

def download_file(url, filename):
    print(f"📥 Downloading: {url}")
    
    # Parse domain for Referer
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': base_url,
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            print("💥 Error 403: Forbidden.")
            print("💡 Possible causes:")
            print("1. The link is IP-bound (generated for your IP, but running on GitHub's server IP).")
            print("2. The link has expired.")
            print("3. The site blocks automated downloads.")
        raise e

    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
        desc=filename[:20]
    ) as bar:
        for data in response.iter_content(chunk_size=1024*1024):
            if data:
                f.write(data)
                bar.update(len(data))
    print(f"✅ Download complete: {filename} ({total_size} bytes)")

def upload_to_telegram(bot_token, chat_id, filepath):
    print(f"🚀 Uploading to Telegram...")
    
    try:
        requests.get("http://localhost:8081", timeout=1)
        base_url = "http://localhost:8081"
        print("⚡ Using local Bot API server (2GB support)")
    except:
        base_url = "https://api.telegram.org"
        print("⚠️ Official API (50MB limit)")

    url = f"{base_url}/bot{bot_token}/sendDocument"
    
    files = {'document': open(filepath, 'rb')}
    data = {'chat_id': chat_id, 'caption': f"🎬 {os.path.basename(filepath)}"}
    
    response = requests.post(url, data=data, files=files, timeout=None)
    files['document'].close()
        
    if response.status_code == 200:
        print("🎉 Upload successful!")
    else:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <URL>")
        exit(1)
        
    download_url = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    if not bot_token or not chat_id:
        print("Error: Missing credentials.")
        exit(1)
        
    filename = unquote(download_url.split("/")[-1].split("?")[0])
    if not filename or len(filename) < 3:
        filename = "downloaded_file.mp4"
        
    try:
        download_file(download_url, filename)
        upload_to_telegram(bot_token, chat_id, filename)
    except Exception as e:
        print(f"💥 Task failed: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
