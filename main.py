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
    """Heroku पर हिंदी फॉन्ट सुनिश्चित करना ताकि अक्षर सही दिखें"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी English PDF फाइल भेजें। मैं उसके लेआउट, फिगर्स और डायग्राम्स को वैसे ही रखते हुए सिर्फ टेक्स्ट को हिंदी में बदलकर आपको दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        bot.reply_to(message, "⏳ आपकी PDF मिल गई है। लेआउट और फिगर्स को सुरक्षित रखते हुए हिंदी अनुवाद किया जा रही है, कृपया कुछ सेकंड इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            
            # ओरिजिनल PDF को खोलना
            doc = fitz.open(input_pdf_path)
            
            for page in doc:
                # पेज से सारे टेक्स्ट ब्लॉक्स और उनकी लोकेशन (Coordinates) निकालना
                blocks = page.get_text("blocks")
                
                for b in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = b
                    
                    # अगर ब्लॉक में टेक्स्ट है (block_type 0 मतलब टेक्स्ट, फिगर्स/इमेज नहीं)
                    if block_type == 0 and text.strip():
                        try:
                            # इंग्लिश टेक्स्ट का हिंदी अनुवाद
                            translation = translator.translate(text, src='en', dest='hi')
                            translated_text = translation.text
                            
                            # पुराना इंग्लिश टेक्स्ट छुपाने के लिए उसपर वाइट रेक्टेंगल बनाना
                            rect = fitz.Rect(x0, y0, x1, y1)
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            
                            # उसी बॉक्स के अंदर हिंदी फॉन्ट के साथ नया टेक्स्ट लिखना
                            # इससे फिगर्स और डायग्राम्स अपनी जगह पर सुरक्षित रहेंगे
                            page.insert_textbox(
                                rect, 
                                translated_text, 
                                fontname="sans", 
                                fontfile=FONT_PATH, 
                                fontsize=9,
                                align=0
                            )
                        except Exception as translation_error:
                            print(f"Block translation error: {translation_error}")
                            continue

            # नई मॉडिफाइड PDF सेव करना
            doc.save(output_pdf_path)
            doc.close()

            # यूजर को ट्रांसलेटेड PDF वापस भेजना
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ लेआउट और फिगर्स के साथ आपकी हिंदी PDF तैयार है!")

        except Exception as e:
            bot.reply_to(message, "❌ इस PDF को प्रोसेस करने में कोई समस्या आई। कृपया सुनिश्चित करें कि यह स्कैन की हुई इमेज न हो।")
            print(f"Error: {e}")
            
        finally:
            # टेम्परेरी फाइलों को डिलीट करना
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("Layout-Preserving Bot is running on Heroku...")
    bot.infinity_polling()
