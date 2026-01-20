import os
import sys
import requests
from urllib.parse import unquote

def send_telegram_link(bot_token, chat_id, filename, download_url):
    print(f"🔗 Sending high-speed link to Telegram...")
    message = (
        f"🎬 *File Ready for Download*\n\n"
        f"📦 *Name:* `{filename}`\n"
        f"🚀 *Speed:* Maximum Server Bandwidth\n\n"
        f"📥 [Click to Download High Speed]({download_url})"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        print("✅ Link sent successfully!")
    else:
        print(f"❌ Failed to send link: {r.text}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
        
    file_name = sys.argv[1]
    dl_url = sys.argv[2]
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_TO")
    
    send_telegram_link(token, chat, file_name, dl_url)