import os
import sys
import requests
from tqdm import tqdm

def upload_to_gofile(filepath):
    """Fallback for files > 50MB until API keys are fixed"""
    print(f"☁️ File is large. Uploading to GoFile for high-speed sharing...")
    try:
        # 1. Get best server
        server = requests.get("https://api.gofile.io/getServer").json()['data']['server']
        # 2. Upload
        url = f"https://{server}.gofile.io/uploadFile"
        with open(filepath, 'rb') as f:
            response = requests.post(url, files={'file': f})
        
        data = response.json()
        if data['status'] == 'ok':
            return data['data']['downloadPage']
    except Exception as e:
        print(f"GoFile error: {e}")
    return None

def send_to_telegram(bot_token, chat_id, filepath):
    filesize = os.path.getsize(filepath)
    limit = 45 * 1024 * 1024 # 45MB safety limit
    
    if filesize > limit:
        print(f"⚠️ File too large for Bot API ({filesize / 1024 / 1024:.1f}MB)")
        link = upload_to_gofile(filepath)
        message = f"🎬 *{os.path.basename(filepath)}*\n\n📏 Size: {filesize / 1024 / 1024:.1f} MB\n🚀 [Download High Speed]({link})"
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                      data={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'})
        print("✅ Sent GoFile link to Telegram.")
    else:
        print(f"🚀 Uploading {os.path.basename(filepath)} to Telegram...")
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(filepath, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"🎬 {os.path.basename(filepath)}"}, files={'document': f})
        print("✅ Upload complete.")

if __name__ == "__main__":
    filepath = sys.argv[1]
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_TO")
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
        
    try:
        send_to_telegram(bot_token, chat_id, filepath)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)