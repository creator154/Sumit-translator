import os
import telebot
import requests
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='en', target='hi')

FONT_PATH = "NotoSansDevanagari.ttf"
FONT_URL = "https://github.com"

def download_hindi_font():
    if not os.path.exists(FONT_PATH):
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी Scanned या फोटो वाली NEET English PDF भेजें। मैं क्लाउड OCR से अक्षरों को हिंदी में बदल दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ Scanned PDF मिल गई है। Google Cloud OCR चालू हो रहा है, कृपया कुछ सेकंड इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            src_doc = fitz.open(input_pdf_path)
            out_doc = fitz.open()
            
            for page in src_doc:
                # 1. पेज का इमेज स्नैपशॉट
                pix = page.get_pixmap(dpi=150)
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                # 2. Google Web OCR API को रिक्वेस्ट भेजना (यह बिना किसी भारी लाइब्रेरी के फोटो स्कैन करता है)
                img_bytes = pix.tobytes("png")
                url = "https://googleapis.com"
                payload = {'client': 'webapp', 'sl': 'en', 'tl': 'hi'}
                files = [('image', ('page.png', img_bytes, 'image/png'))]
                
                response = requests.post(url, data=payload, files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    # OCR से मिले टेक्स्ट ब्लॉक्स को प्रोसेस करना
                    if 'textBlocks' in data:
                        for block in data['textBlocks']:
                            text = block.get('text', '')
                            box = block.get('box', {})
                            
                            if text.strip() and box:
                                try:
                                    translated_text = translator.translate(text)
                                    
                                    # गूगल के बॉक्स कोऑर्डिनेट्स को PDF साइज में बदलना
                                    x0 = box.get('x', 0) * (page.rect.width / pix.width)
                                    y0 = box.get('y', 0) * (page.rect.height / pix.height)
                                    x1 = (box.get('x', 0) + box.get('w', 0)) * (page.rect.width / pix.width)
                                    y1 = (box.get('y', 0) + box.get('h', 0)) * (page.rect.height / pix.height)
                                    
                                    rect = fitz.Rect(x0, y0, x1, y1)
                                    
                                    # पुरानी इंग्लिश मिटाना और नई हिंदी छापना
                                    new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                    new_page.insert_textbox(rect, translated_text, fontname="sans", fontfile=FONT_PATH, fontsize=8, align=0)
                                except:
                                    continue
            
            out_doc.save(output_pdf_path, garbage=3, deflate=True)
            out_doc.close()
            src_doc.close()

            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ Google Cloud OCR द्वारा पूरी तरह अनुवादित हिंदी PDF तैयार है!")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, f"❌ अनुवाद में समस्या आई: {e}")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    print("Cloud OCR Web Bot is running...")
    bot.infinity_polling()
