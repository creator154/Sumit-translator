import os
import time
import sys
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import types
from telethon import functions

# Heroku Config Vars से डेटा उठाना
API_ID = int(os.environ.get("API_ID", 1234567))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@example_channel")

# जो String आपने Termux से कॉपी की थी, उसे Heroku Dashboard में 'TELEGRAM_STRING' नाम से सेव करें
STRING_SESSION = os.environ.get("TELEGRAM_STRING")

def start_reporting():
    if not STRING_SESSION:
        print("[-] TELEGRAM_STRING variable is missing in Heroku Config Vars!")
        sys.exit(0)

    print(f"[+] Connecting account via String Session. Target: {TARGET_CHANNEL}")
    
    # यहाँ बिना किसी फाइल के सीधे स्ट्रिंग से लॉगिन हो रहा है
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    try:
        client.connect()
        if not client.is_user_authorized():
            print("[-] String Session is invalid or expired.")
            return

        try:
            channel_entity = client.get_entity(TARGET_CHANNEL)
        except Exception:
            print(f"[-] Target channel {TARGET_CHANNEL} not found.")
            return

        # रिपोर्ट सबमिट करना
        client(functions.messages.ReportRequest(
            peer=channel_entity,
            id=[42],
            reason=types.InputReportReasonCopyright(),
            message="This channel is leaking copyrighted educational lectures without authorization."
        ))
        print("[+] Report sent successfully via String Session!")

    except Exception as e:
        print(f"[!] Error: {str(e)}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    start_reporting()
