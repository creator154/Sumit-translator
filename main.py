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
    """हिंदी फॉन्ट सुनिश्चित करना"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे इंग्लिश PDF भेजें। मैं पुरानी इंग्लिश को पूरी तरह साफ करके उसे शुद्ध हिंदी PDF में बदल दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ PDF मिल गई है। पुरानी परतों को साफ करके हिंदी अनुवाद किया जा रहा है, कृपया थोड़ा इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            
            # ओरिजिनल PDF और आउटपुट के लिए एक खाली PDF बनाना
            src_doc = fitz.open(input_pdf_path)
            out_doc = fitz.open()
            
            for page in src_doc:
                # 1. पेज के सारे टेक्स्ट ब्लॉक्स और उनकी लोकेशन निकालना
                blocks = page.get_text("blocks")
                text_to_translate = []
                valid_blocks = []
                
                for b in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = b
                    if block_type == 0 and text.strip():
                        text_to_translate.append(text)
                        valid_blocks.append(b)
                
                # 2. पूरे पेज का अनुवाद (Batch Mode)
                translations = []
                if text_to_translate:
                    try:
                        translations = translator.translate(text_to_translate, src='en', dest='hi')
                        if not isinstance(translations, list):
                            translations = [translations]
                    except Exception as e:
                        print(f"Translation failed for a page: {e}")
                        translations = []
                
                # 3. पेज को साफ करने का मास्टर स्ट्रोक: पेज की क्लीन इमेज (Pixmap) बनाना
                # इससे पुराना सारा छुपा हुआ टेक्स्ट इमेजिस में लॉक हो जाता है, पर टेक्स्ट ब्लॉक्स को हम हाइड कर सकते हैं
                pix = page.get_pixmap(dpi=150) # अच्छी क्वालिटी के लिए 150 DPI
                
                # आउटपुट डॉक्यूमेंट में एक नया खाली पेज जोड़ें जिसका साइज ओरिजिनल जैसा हो
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                
                # नया पेज बिल्कुल साफ़ है, इसपर बैकग्राउंड इमेज लगाएं
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                # 4. अब पुरानी इंग्लिश लाइनों के ऊपर सफेद पट्टी खींचकर उसे जड़ से मिटाना और हिंदी लिखना
                if translations and len(translations) == len(valid_blocks):
                    for b, trans in zip(valid_blocks, translations):
                        x0, y0, x1, y1, text, block_no, block_type = b
                        translated_text = trans.text
                        rect = fitz.Rect(x0, y0, x1, y1)
                        
                        # वाइट रेक्टेंगल से पुरानी इंग्लिश को 100% छुपाना
                        new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        
                        # ठीक उसी जगह हिंदी लिखना
                        new_page.insert_textbox(
                            rect, 
                            translated_text, 
                            fontname="sans", 
                            fontfile=FONT_PATH, 
                            fontsize=9,
                            align=0
                        )
            
            # फाइनल क्लीन PDF को सेव करना
            out_doc.save(output_pdf_path, garbage=3, deflate=True)
            out_doc.close()
            src_doc.close()

            # पुराना स्टेटस डिलीट करके फ्रेश हिंदी PDF भेजना
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ पुरानी इंग्लिश को पूरी तरह हटाकर, आपकी शुद्ध हिंदी PDF तैयार है!")

        except Exception as e:
            bot.reply_to(message, "❌ इस PDF को ट्रांसलेट करने में कोई टेक्निकल समस्या आई।")
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
    print("Layer-Proof PDF Translator Bot is running...")
    bot.infinity_polling()
