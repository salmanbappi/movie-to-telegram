import os
import sys
import requests
import subprocess
from tqdm import tqdm
from urllib.parse import unquote, urlparse

def split_file(filepath, chunk_size_mb=45):
    """Splits a file into chunks of specified size in MB"""
    print(f"✂️ Splitting file into {chunk_size_mb}MB chunks...")
    chunk_size = chunk_size_mb * 1024 * 1024
    chunks = []
    
    file_name = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        part_num = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_name = f"{file_name}.part{part_num}"
            with open(chunk_name, 'wb') as chunk_file:
                chunk_name_final = chunk_name
                chunk_file.write(chunk)
            chunks.append(chunk_name_final)
            part_num += 1
    return chunks

def download_file(url, filename):
    print(f"📥 Downloading: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
    }
    response = requests.get(url, headers=headers, stream=True, timeout=30)
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

def upload_to_telegram(bot_token, chat_id, filepath, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    if not caption:
        caption = os.path.basename(filepath)
        
    print(f"🚀 Uploading {os.path.basename(filepath)} to Telegram...")
    with open(filepath, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, data=data, files=files, timeout=None)
        
    if response.status_code == 200:
        print(f"🎉 Uploaded: {os.path.basename(filepath)}")
    else:
        print(f"❌ Upload failed: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    download_url = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    # Filename cleanup
    filename = unquote(download_url.split("/")[-1].split("?")[0])
    if not filename: filename = "file.mp4"
        
    try:
        download_file(download_url, filename)
        
        filesize_mb = os.path.getsize(filename) / (1024 * 1024)
        
        if filesize_mb > 49:
            print(f"📦 File size ({filesize_mb:.1f}MB) exceeds 50MB limit. Splitting...")
            parts = split_file(filename)
            total_parts = len(parts)
            for i, part in enumerate(parts):
                caption = f"🎬 {filename}\n📦 Part {i+1} of {total_parts}"
                upload_to_telegram(bot_token, chat_id, part, caption)
                os.remove(part)
        else:
            upload_to_telegram(bot_token, chat_id, filename)
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
