import os
import telebot
import requests
import time

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी NEET, Scanned या फोटो वाली English PDF भेजें। मैं Google Cloud Engine से उसकी डिज़ाइन और फिगर्स को सुरक्षित रखते हुए उसे पूरी तरह हिंदी PDF में बदल दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ Scanned PDF मिल गई है। Google Cloud OCR अनुवाद शुरू हो रहा है (इसमें 10-20 सेकंड लग सकते हैं), कृपया इंतज़ार करें...")

        # टेलीग्राम से फाइल डाउनलोड करना
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            # 🚀 Google Translate Document API का मुफ्त वेब गेटवे उपयोग करना
            # यह पूरी PDF को बिना तोड़े डिज़ाइन के साथ अनुवाद करता है
            url = "https://googleapis.com"
            
            with open(input_pdf_path, 'rb') as f:
                payload = {
                    'client': 'webapp',
                    'sl': 'en',  # Source Language: English
                    'tl': 'hi',  # Target Language: Hindi
                    'f': 'pdf'   # File type
                }
                files = [
                    ('file', ('document.pdf', f, 'application/pdf'))
                ]
                
                # गूगल सर्वर को फाइल भेजना
                response = requests.post(url, data=payload, files=files, timeout=60)
                
            if response.status_code == 200 and len(response.content) > 1000:
                # अनुवादित PDF को सेव करना
                with open(output_pdf_path, 'wb') as out_file:
                    out_file.write(response.content)

                # पुराना स्टेटस मैसेज डिलीट करके नई PDF भेजना
                bot.delete_message(chat_id, status_msg.message_id)
                with open(output_pdf_path, 'rb') as pdf_to_send:
                    bot.send_document(
                        chat_id, 
                        pdf_to_send, 
                        caption="✅ आपकी Scanned PDF का हिंदी अनुवाद (फिगर्स के साथ) तैयार है!"
                    )
            else:
                raise Exception("Google Cloud Server did not return a valid PDF.")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, "❌ इस फोटो वाली PDF को प्रोसेस करने में समस्या आई। कृपया फाइल साइज छोटा करके दोबारा प्रयास करें।")
            print(f"Cloud OCR Error: {e}")
            
        finally:
            # टेम्परेरी फाइलों को डिलीट करना
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    print("Cloud OCR PDF Bot is running successfully...")
    bot.infinity_polling()
