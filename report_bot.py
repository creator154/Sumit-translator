import os
import time
import platform
from telethon.sync import TelegramClient
from telethon.tl import types
from telethon import functions
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from prettytable import PrettyTable

# कलर कोडिंग (Visual Anchors)
rd, gn, lgn, lrd = '\033[00;31m', '\033[00;32m', '\033[01;32m', '\033[01;31m'
cn, k, g = '\033[00;36m', '\033[90m', '\033[38;5;130m'

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# अपनी कॉमन API ID और HASH यहाँ एक बार डाल दें
API_ID = 1234567          # अपना API ID यहाँ बदलें (Integer)
API_HASH = "your_api_hash_here"  # अपना API HASH यहाँ बदलें (String)

def clear():
    if 'Windows' in platform.uname():
        try:
            from colorama import init
            init()
        except ImportError:
            os.system("pip install colorama")
        os.system("cls")
    else:
        os.system("clear")

def banner():
    clear()
    print(f"""{g}
  _____      __      _   _________     ____    
 (_   _)    /  \\    / ) (_   _____)   / __ \\   

   | |     / /\\ \\  / /    ) (___     / /  \\ \\  
   | |     ) ) ) ) ) )   (   ___)   ( ()  () ) 
   | |    ( ( ( ( ( (     ) (       ( ()  () ) 
  _| |__  / /  \\ \\/ /    (   )       \\ \\__/ /  
 /_____( (_/    \\__/      \\_/         \\____/
    {cn}=== MULTI-ACCOUNT ADVANCED SYSTEM ===
    """)

# विधि (Method) चुनने के लिए टेबल
method_table = PrettyTable([f'{cn}Number{lrd}', f'{cn}Method{lrd}'])
method_table.add_row([f'{lgn}1{lrd}', f'{gn}Report Spam{lrd}'])
method_table.add_row([f'{lgn}2{lrd}', f'{gn}Reporter Other{lrd}'])
method_table.add_row([f'{lgn}3{lrd}', f'{gn}Reporter Violence{lrd}'])
method_table.add_row([f'{lgn}4{lrd}', f'{gn}Reporter Pornography{lrd}'])
method_table.add_row([f'{lgn}5{lrd}', f'{gn}Reporter Copyright{lrd}'])
method_table.add_row([f'{lgn}6{lrd}', f'{gn}Reporter Fake/Scam{lrd}'])
method_table.add_row([f'{lgn}7{lrd}', f'{gn}Reporter Geo Irrelevant{lrd}'])
method_table.add_row([f'{lgn}8{lrd}', f'{gn}Reporter Illegal Drugs{lrd}'])
method_table.add_row([f'{lgn}9{lrd}', f'{gn}Reporter Personal Details{lrd}'])

def add_new_session():
    """इसी बॉट के अंदर नया अकाउंट लॉगिन करके सेशन सेव करने के लिए"""
    banner()
    print(f"{gn}[+] --- ADD NEW TELEGRAM ACCOUNT ---{k}\n")
    phone = input(f"{lgn}[+] Enter Phone Number with Country Code (e.g., +919876543210): {gn}").strip()
    
    if not phone.startswith('+'):
        print(f"{lrd}[- ] Error: Country code (+91) लगाना ज़रूरी है।")
        input(f"\n{k}Press Enter to return to Menu...")
        return

    session_name = phone.replace('+', '')
    session_path = os.path.join(SESSION_DIR, session_name)
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        client.connect()
        if not client.is_user_authorized():
            print(f"{cn}[*] Sending OTP to {phone}...")
            client.send_code_request(phone)
            otp = input(f"{lgn}[?] Enter the OTP received on Telegram: {gn}").strip()
            try:
                client.sign_in(phone, otp)
            except SessionPasswordNeededError:
                password = input(f"{lrd}[!] 2-Step Verification enabled. Enter Password: {gn}")
                client.sign_in(password=password)
                
        if client.is_user_authorized():
            print(f"{lgn}[✔] Success! Account login saved in bot storage.")
        else:
            print(f"{lrd}[- ] Authentication failed.")
    except Exception as e:
        print(f"{lrd}[!] Error: {str(e)}")
    finally:
        client.disconnect()
    input(f"\n{k}Press Enter to return to Menu...")

def start_reporting():
    """सभी सेव्ड सेशन्स का उपयोग करके रिपोर्टिंग शुरू करने के लिए"""
    banner()
    session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    
    if not session_files:
        print(f"{lrd}[!] कोई भी अकाउंट नहीं मिला! कृपया पहले ऑप्शन 1 से अकाउंट्स जोड़ें।")
        input(f"\n{k}Press Enter to return to Menu...")
        return

    print(f"{gn}[+] Total {len(session_files)} accounts loaded from bot storage.{k}\n")
    print(method_table)
    
    method = input(f"{lrd}[?]{gn} Choose a method (1-9): {k}").strip()
    channel_username = input(f"{lrd}[+]{gn} Enter Target Channel Username (e.g., @username): {k}").strip()
    
    # रिपोर्ट का कारण तय करना
    reasons = {
        "1": (types.InputReportReasonSpam(), "This channel contains spam content."),
        "2": (types.InputReportReasonOther(), "Other safety violation."),
        "3": (types.InputReportReasonViolence(), "This channel contains violent content."),
        "4": (types.InputReportReasonPornography(), "This channel has pornographic content."),
        "5": (types.InputReportReasonCopyright(), "Block this channel due to copyright infringement of educational lectures."),
        "6": (types.InputReportReasonFake(), "Block this channel due to scam and impersonation."),
        "7": (types.InputReportReasonGeoIrrelevant(), "Irrelevant geographical content."),
        "8": (types.InputReportReasonIllegalDrugs(), "Selling illegal substances."),
        "9": (types.InputReportReasonPersonalDetails(), "Leaking private personal details.")
    }

    if method not in reasons:
        print(f"{lrd}[!] Invalid choice!")
        input(f"\n{k}Press Enter to return to Menu...")
        return

    reason_obj, default_message = reasons[method]
    if method == "2":
        default_message = input(f"{lrd}[+]{gn} Enter your custom message: {g}")

    print(f"\n{cn}[*] Starting mass report queue... Please wait.")
    print(f"{k}----------------------------------------")

    for session_file in session_files:
        session_name = session_file.replace('.session', '')
        session_path = os.path.join(SESSION_DIR, session_name)
        
        print(f"{cn}[*] Connecting account: {session_name}")
        client = TelegramClient(session_path, API_ID, API_HASH)
        
        try:
            client.connect()
            if not client.is_user_authorized():
                print(f"{lrd}[-] Session {session_name} expired/invalid. Skipping...")
                continue
            
            try:
                channel_entity = client.get_entity(channel_username)
            except Exception:
                print(f"{lrd}[- ] Target channel username not found.")
                break

            # हर अकाउंट से सेफ लिमिट में 2 रिपोर्ट्स भेजना
            for i in range(1, 3):
                try:
                    client(functions.messages.ReportRequest(
                        peer=channel_entity,
                        id=[42],
                        reason=reason_obj,
                        message=default_message
                    ))
                    print(f"{lgn}[✔] Report #{i} sent successfully from {session_name}")
                    time.sleep(2)
                except FloodWaitError as e:
                    print(f"{lrd}[!] FloodWait: Account limited for {e.seconds}s. Switching account...")
                    break
        except Exception as e:
            print(f"{lrd}[!] Connection error on {session_name}: {str(e)}")
        finally:
            client.disconnect()
            print(f"{k}----------------------------------------")
            time.sleep(3) # अकाउंट्स ब्लॉक होने से बचाने के लिए सेफ टाइम गैप

    print(f"\n{gn}[✔] Task finished! All active accounts processed.")
    input(f"\n{k}Press Enter to return to Menu...")

def main_menu():
    while True:
        banner()
        print(f"{cn}[1] {gn}Add/Login New Telegram Account")
        print(f"{cn}[2] {gn}Start Mass Reporting Menu")
        print(f"{cn}[3] {lrd}Exit Bot")
        print(f"{k}----------------------------------------")
        choice = input(f"{lrd}[?]{gn} Choose an option: {k}").strip()
        
        if choice == "1":
            add_new_session()
        elif choice == "2":
            start_reporting()
        elif choice == "3":
            print(f"\n{lrd}[!] Exiting bot system. Goodbye!")
            break
        else:
            print(f"{lrd}[!] Invalid choice, try again.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()

