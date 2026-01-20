import os
import sys
import requests
from tqdm import tqdm

def download_file(url, filename):
    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024*1024):
            size = f.write(data)
            bar.update(size)
    print(f"Download complete: {filename}")

def upload_to_telegram(bot_token, chat_id, filepath):
    print(f"Uploading to Telegram...")
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    with open(filepath, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': chat_id, 'caption': os.path.basename(filepath)}
        response = requests.post(url, data=data, files=files)
        
    if response.status_code == 200:
        print("Upload successful!")
    else:
        print(f"Upload failed: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <URL>")
        sys.exit(1)
        
    download_url = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_TOKEN or TELEGRAM_TO environment variables not set.")
        sys.exit(1)
        
    # Extract filename from URL
    filename = download_url.split("/")[-1].split("?")[0]
    if not filename:
        filename = "movie.mp4"
        
    try:
        download_file(download_url, filename)
        upload_to_telegram(bot_token, chat_id, filename)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
