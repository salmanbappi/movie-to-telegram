import os
import sys
import requests
from tqdm import tqdm
from urllib.parse import unquote, urlparse

def download_file(url, filename):
    print(f"📥 Downloading: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
    }
    response = requests.get(url, headers=headers, stream=True, timeout=60)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        total=total_size, unit='iB', unit_scale=True, unit_divisor=1024, desc=filename[:20]
    ) as bar:
        for data in response.iter_content(chunk_size=1024*1024):
            if data:
                f.write(data)
                bar.update(len(data))
    print(f"✅ Download complete: {filename}")

def upload_to_telegram(bot_token, chat_id, filepath):
    print(f"🚀 Uploading to Telegram (2GB Mode)...")
    
    # We MUST use the local server address
    base_url = "http://localhost:8081"
    url = f"{base_url}/bot{bot_token}/sendDocument"
    
    # For local server, we just send the path, but since we are in Docker/Actions, 
    # we send it as a standard multipart file which the local server then proxies.
    with open(filepath, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': f"🎬 {os.path.basename(filepath)}"}
        response = requests.post(url, data=data, files=files, timeout=None)
        
    if response.status_code == 200:
        print(f"🎉 Upload Successful!")
    else:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    download_url = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    filename = unquote(download_url.split("/")[-1].split("?")[0])
    if not filename: filename = "file.mp4"
        
    try:
        download_file(download_url, filename)
        upload_to_telegram(bot_token, chat_id, filename)
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(filename):
            os.remove(filename)