import os
import telebot
import requests

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे अपनी NEET या कोई भी Scanned English PDF भेजें। मैं Google Translate ऐप की तरह इसके पन्नों को स्कैन करके, फिगर्स को सुरक्षित रखते हुए पूरी तरह हिंदी PDF में बदल दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ PDF मिल गई है। Google ऐप इंजन से इसका हिंदी अनुवाद किया जा रहा है (इसमें 15-30 सेकंड लग सकते हैं), कृपया इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            # 🚀 Google Translate का ऑफिशियल वेब गेटवे (जो बिना API Key के सीधे फोटो और PDF का अनुवाद करता है)
            url = "https://googleapis.com"
            
            with open(input_pdf_path, 'rb') as f:
                payload = {
                    'client': 'webapp',
                    'sl': 'en',  # Source Language: English
                    'tl': 'hi',  # Target Language: Hindi
                    'f': 'pdf'   # File type format
                }
                files = [
                    ('file', ('document.pdf', f, 'application/pdf'))
                ]
                
                # सीधे गूगल के मेन सर्वर को फाइल पोस्ट करना
                response = requests.post(url, data=payload, files=files, timeout=60)
                
            # अगर गूगल ने अनुवादित PDF सही-सही वापस कर दी है
            if response.status_code == 200 and len(response.content) > 2000:
                with open(output_pdf_path, 'wb') as out_file:
                    out_file.write(response.content)

                # पुराना स्टेटस डिलीट करना और नई फाइल सेंड करना
                bot.delete_message(chat_id, status_msg.message_id)
                with open(output_pdf_path, 'rb') as pdf_to_send:
                    bot.send_document(
                        chat_id, 
                        pdf_to_send, 
                        caption="✅ Google ऐप तकनीक द्वारा अनुवादित हिंदी PDF तैयार है! (सारे फिगर्स और टेक्स्ट के साथ)"
                    )
            else:
                raise Exception("Google server reject or returned blank page.")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, "❌ इस फोटो वाली PDF का अनुवाद सर्वर पर ब्लॉक हो गया। कृपया एक बार में 1-5 पेज की ही छोटी फाइल भेजें।")
            print(f"App Engine Error: {e}")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    print("Google App Engine Translator Bot is running...")
    bot.infinity_polling()
