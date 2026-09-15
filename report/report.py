import os
import time
import telebot
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import types
from telethon import functions
from telethon.errors import FloodWaitError

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 1234567))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")

bot = telebot.TeleBot(BOT_TOKEN)

print("[*] Strong Multi-Session Bot is running...")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    help_text = (
        "🔥 **Welcome to Powerful Copyright Protection Bot (Multi-Session)**\n\n"
        "अब आप एक साथ कई अकाउंट्स से रिपोर्ट भेज सकते हैं। नीचे दिए गए फॉर्मेट का पालन करें:\n\n"
        "`/report <Target_Channel>`\n"
        "`<String_Session_1>`\n"
        "`<String_Session_2>`\n"
        "`<String_Session_3>`\n\n"
        "💡 **नोट:** चैनल नेम के बाद **Next Line (Shift+Enter)** दबाकर अपने सारे सेशन्स एक के नीचे एक पेस्ट कर दें।"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['report'])
def handle_multi_report(message):
    try:
        # पूरे टेक्स्ट को लाइन्स में तोड़ना
        lines = [line.strip() for line in message.text.split('\n') if line.strip()]
        
        # पहली लाइन में कमांड और चैनल का नाम होगा
        first_line_parts = lines[0].split()
        if len(first_line_parts) < 2 or len(lines) < 2:
            bot.reply_to(message, "❌ **Format Error!** सही तरीका:\n`/report @channel`\n`string1`\n`string2`")
            return

        target_channel = first_line_parts[1]
        string_sessions = lines[1:] # पहली लाइन के बाद की सभी लाइन्स स्ट्रिंग्स हैं

        status_msg = bot.reply_to(message, f"⏳ **कुल {len(string_sessions)} अकाउंट्स मिले।** मास रिपोर्टिंग की कतार (Queue) शुरू हो रही है...")

        success_count = 0
        failed_count = 0

        for idx, session in enumerate(string_sessions, start=1):
            bot.edit_message_text(f"⏳ [{idx}/{len(string_sessions)}] अकाउंट को कनेक्ट किया जा रहा है...", chat_id=message.chat.id, message_id=status_msg.message_id)
            
            client = TelegramClient(StringSession(session), API_ID, API_HASH)
            try:
                client.connect()
                if not client.is_user_authorized():
                    failed_count += 1
                    continue

                try:
                    channel_entity = client.get_entity(target_channel)
                except Exception:
                    bot.edit_message_text(f"❌ चैनल `{target_channel}` नहीं मिला। प्रोसेस रोक दी गई है।", chat_id=message.chat.id, message_id=status_msg.message_id)
                    client.disconnect()
                    return

                # हर एक अकाउंट से 2 बार रिपोर्ट सबमिट करना (सेफ और स्ट्रॉन्ग लिमिट)
                for _ in range(2):
                    try:
                        client(functions.messages.ReportRequest(
                            peer=channel_entity,
                            id=[42],
                            reason=types.InputReportReasonCopyright(),
                            message="This channel is infringing copyright by distributing premium educational content without authorization."
                        ))
                        time.sleep(1.5)
                    except FloodWaitError:
                        break # अगर इस अकाउंट पर लिमिट आई तो अगले पर बढ़ें
                
                success_count += 1

            except Exception as e:
                failed_count += 1
            finally:
                client.disconnect()
                time.sleep(3) # टेलीग्राम एंटी-स्पैम से बचने के लिए सेफ डिले

        # फाइनल रिजल्ट रिपोर्ट
        final_text = (
            "🎯 **मास रिपोर्टिंग पूरी हुई!**\n\n"
            f"👤 **सफल अकाउंट्स:** {success_count}\n"
            f"❌ **फ़ेल / इनवैलिड अकाउंट्स:** {failed_count}\n"
            f"📢 **टारगेट चैनल:** {target_channel}\n\n"
            "चैनल पर बहुत जल्द एक्शन लिया जाएगा।"
        )
        bot.edit_message_text(final_text, chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"⚠️ **सिस्टम एरर:** {str(e)}")

bot.infinity_polling()
