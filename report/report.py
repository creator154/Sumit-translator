import os
import time
import sys

try:
    from telethon.sync import TelegramClient
except ImportError:
    os.system("pip install telethon")

from telethon.tl import types
from telethon import functions
from telethon.errors import FloodWaitError

# एनवायरनमेंट वेरिएबल्स से इनपुट लेना (Heroku Config Vars)
# अपने Heroku Dashboard में Settings -> Config Vars में ये नाम जोड़ें
API_ID = int(os.environ.get("API_ID", 1234567))  # अपना डिफ़ॉल्ट ID यहाँ भी डाल सकते हैं
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "@example_channel")
REPORT_COUNT = int(os.environ.get("REPORT_COUNT", 5))

# आपके लॉग के हिसाब से '2' नंबर (Reporter Other) सिलेक्टेड है
METHOD = os.environ.get("REPORT_METHOD", "2") 

# SyntaxWarning को ठीक करने के लिए 'r' लगाया गया है
account = r"""
 ____                             _               

|  _ \   ___  _ __    ___   _ __ | |_   ___  _ __ 
| |_) | / _ \| '_ \  / _ \ | '__|| __| / _ \| '__|
|  _ < |  __/| |_) || (_) || |   | |_ |  __/| |    
|_| \_\ \___|| .__/  \___/ |_|    \__| \___||_|   
             |_|	
"""

SESSION_DIR = "sessions"

def start_reporting():
    if not os.path.exists(SESSION_DIR):
        print(f"[-] '{SESSION_DIR}' folder not found. Please add your .session files.")
        sys.exit(0)

    session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if not session_files:
        print("[-] No session files found in the sessions directory.")
        sys.exit(0)

    print(f"[+] Total {len(session_files)} accounts loaded. Target: {TARGET_CHANNEL}")

    reasons = {
        "1": (types.InputReportReasonSpam(), "This channel contains spam content."),
        "2": (types.InputReportReasonOther(), "This channel is leaking copyrighted coaching lectures without authorization."),
        "3": (types.InputReportReasonViolence(), "This channel contains violent content."),
        "4": (types.InputReportReasonPornography(), "This channel has pornographic content."),
        "5": (types.InputReportReasonCopyright(), "Block this channel due to copyright violation."),
        "6": (types.InputReportReasonFake(), "Block this channel due to scam and impersonation."),
    }

    reason_obj, default_message = reasons.get(METHOD, (types.InputReportReasonOther(), "Copyright infringement."))

    for session_file in session_files:
        session_name = session_file.replace('.session', '')
        session_path = os.path.join(SESSION_DIR, session_name)
        
        print(f"[*] Connecting account: {session_name}")
        client = TelegramClient(session_path, API_ID, API_HASH)
        
        try:
            client.connect()
            if not client.is_user_authorized():
                print(f"[-] Session {session_name} is unauthorized. Skipping.")
                continue
            
            try:
                channel_entity = client.get_entity(TARGET_CHANNEL)
            except Exception:
                print(f"[-] Target channel {TARGET_CHANNEL} not found.")
                break

            # यहाँ पर ब्रैकेट को सही ढंग से बंद (Fix) कर दिया गया है
            for i in range(1, REPORT_COUNT + 1):
                try:
                    client(functions.messages.ReportRequest(
                        peer=channel_entity,
                        id=[42],
                        reason=reason_obj,
                        message=default_message
                    ))
                    print(f"[+] Report #{i} sent successfully from {session_name}")
                    time.sleep(2)
                except FloodWaitError as e:
                    print(f"[!] FloodWait error: {e.seconds} seconds. Moving to next account.")
                    break
        except Exception as e:
            print(f"[!] Error with account {session_name}: {str(e)}")
        finally:
            client.disconnect()
            print("-" * 40)
            time.sleep(4)

if __name__ == "__main__":
    start_reporting()
