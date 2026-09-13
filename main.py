import os
import telebot
import requests
import fitz  # PyMuPDF
from googletrans import Translator

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()

FONT_PATH = "NotoSansDevanagari.ttf"
FONT_URL = "https://github.com"

def download_hindi_font():
    """Heroku पर हिंदी फॉन्ट सुनिश्चित करना"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी English PDF फ़ाइल भेजें। मैं लेआउट और फिगर्स को सुरक्षित रखते हुए तुरंत उसे हिंदी PDF में बदल दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ आपकी PDF मिल गई है। तेज़ स्पीड (Batch Mode) में अनुवाद शुरू हो रहा है, कृपया थोड़ा इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            doc = fitz.open(input_pdf_path)
            
            for page in doc:
                blocks = page.get_text("blocks")
                text_to_translate = []
                valid_blocks = []
                
                # 1. इस पेज के सभी टेक्स्ट ब्लॉक्स को इकट्ठा करें
                for b in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = b
                    if block_type == 0 and text.strip():
                        text_to_translate.append(text)
                        valid_blocks.append(b)
                
                # 2. पूरे पेज का अनुवाद एक ही बार (Batch) में करें ताकि बॉट न अटके
                if text_to_translate:
                    try:
                        translations = translator.translate(text_to_translate, src='en', dest='hi')
                        
                        # अगर केवल 1 ब्लॉक है तो उसे लिस्ट में बदलें
                        if not isinstance(translations, list):
                            translations = [translations]
                            
                        # 3. अनुवादित टेक्स्ट को वापस PDF लेआउट पर उसी जगह सेट करें
                        for b, trans in zip(valid_blocks, translations):
                            x0, y0, x1, y1, text, block_no, block_type = b
                            translated_text = trans.text
                            
                            # पुराना टेक्स्ट छिपाएं और नया हिंदी टेक्स्ट ओवरले करें
                            rect = fitz.Rect(x0, y0, x1, y1)
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            
                            page.insert_textbox(
                                rect, 
                                translated_text, 
                                fontname="sans", 
                                fontfile=FONT_PATH, 
                                fontsize=9,
                                align=0
                            )
                    except Exception as page_err:
                        print(f"Page translation error: {page_err}")
                        continue

            # मॉडिफाइड PDF सेव करें
            doc.save(output_pdf_path)
            doc.close()

            # पुरानी स्टेटस मैसेज डिलीट करके नई PDF भेजें
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ लेआउट, फिगर्स और डायग्राम्स के साथ आपकी हिंदी PDF तैयार है!")

        except Exception as e:
            bot.reply_to(message, "❌ इस PDF को प्रोसेस करने में कोई समस्या आई।")
            print(f"Global Error: {e}")
            
        finally:
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("Fast Layout-Preserving Bot is running...")
    bot.infinity_polling()
