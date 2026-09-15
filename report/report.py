hereimport os
import telebot
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import types
from telethon import functions

# Heroku Config Vars से सिर्फ Bot Token लें (इसे बदलना नहीं पड़ेगा)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 1234567))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")

bot = telebot.TeleBot(BOT_TOKEN)

print("[*] Bot is running and waiting for your commands on Telegram...")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    help_text = (
        "👋 **Welcome to Copyright Protection Bot**\n\n"
        "बिना रेपो छुए रिपोर्ट भेजने के लिए नीचे दिए गए फॉर्मेट में मैसेज भेजें:\n\n"
        "`/report <Target_Channel> <String_Session>`\n\n"
        "Example:\n"
        "`/report @leaked_channel 1BJW...`"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['report'])
def handle_report_command(message):
    try:
        # कमांड से आर्गुमेंट्स अलग करना
        arguments = message.text.split(maxsplit=2)
        if len(arguments) < 3:
            bot.reply_to(message, "❌ **Error:** पूरा फॉर्मेट लिखें: `/report @channel_username string_session`")
            return

        target_channel = arguments[1]
        string_session = arguments[2]

        bot.reply_to(message, f"⏳ अकाउंट कनेक्ट किया जा रहा है और {target_channel} पर एक्शन लिया जा रहा है...")

        # टेलीथॉन क्लाइंट को लाइव स्ट्रिंग से चालू करना (Temporary Memory)
        client = TelegramClient(StringSession(string_session), API_ID, API_HASH)
        
        client.connect()
        if not client.is_user_authorized():
            bot.reply_to(message, "❌ **Error:** यह String Session अमान्य (Invalid) या एक्सपायर हो चुका है।")
            client.disconnect()
            return

        try:
            channel_entity = client.get_entity(target_channel)
        except Exception:
            bot.reply_to(message, f"❌ **Error:** टारगेट चैनल `{target_channel}` नहीं मिला।")
            client.disconnect()
            return

        # कॉपीराइट उल्लंघन की रिपोर्ट सबमिट करना
        client(functions.messages.ReportRequest(
            peer=channel_entity,
            id=[42],
            reason=types.InputReportReasonCopyright(),
            message="This channel is leaking copyrighted premium educational lectures without authorization."
        ))
        
        client.disconnect()
        bot.reply_to(message, f"🎯 **Success:** {target_channel} के खिलाफ कॉपीराइट रिपोर्ट सफलतापूर्वक सबमिट कर दी गई है!")

    except Exception as e:
        bot.reply_to(message, f"⚠️ **An error occurred:** {str(e)}")

# बॉट को लाइव रखना
bot.infinity_polling()
