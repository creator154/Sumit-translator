import os
import telebot
import requests
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='en', target='hi')

FONT_PATH = "NotoSansDevanagari.ttf"
FONT_URL = "https://github.com"

def download_hindi_font():
    """Heroku पर हिंदी अक्षरों के लिए गूगल फॉन्ट डाउनलोड करना"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे NEET या कोई भी Scanned/Photo वाली English PDF भेजें। मैं सर्वर तकनीक से फोटो के अंदर से इंग्लिश मिटाकर वहीं हिंदी लिख दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ PDF मिल गई है। सर्वर बेस OCR इंजन चालू हो रहा है, कृपया कुछ सेकंड इंतज़ार करें...")

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
                # 1. पेज का इमेज स्नैपशॉट लें
                pix = page.get_pixmap(dpi=150)
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                # 2. PyMuPDF की आंतरिक 'words' तकनीक से फोटो/वेक्टर लेयर्स के ऊपर छिपे अक्षरों की लोकेशन ढूंढना
                # यह बिना किसी भारी ML मॉडल के काम करता है
                words = page.get_text("words") 
                
                # शब्दों को लाइनों या छोटे ब्लॉक्स में व्यवस्थित करना
                current_rect = None
                current_text = []
                
                for w in words:
                    x0, y0, x1, y1, word_str, block_no, line_no, word_no = w
                    
                    if current_rect is None:
                        current_rect = fitz.Rect(x0, y0, x1, y1)
                        current_text.append(word_str)
                    elif abs(y0 - current_rect.y0) < 5: # अगर शब्द एक ही लाइन में हैं
                        current_rect.x1 = x1
                        current_rect.y1 = max(current_rect.y1, y1)
                        current_text.append(word_str)
                    else:
                        # पुरानी लाइन को प्रोसेस करें
                        full_line = " ".join(current_text)
                        if full_line.strip():
                            try:
                                translated_text = translator.translate(full_line)
                                new_page.draw_rect(current_rect, color=(1, 1, 1), fill=(1, 1, 1))
                                new_page.insert_textbox(current_rect, translated_text, fontname="sans", fontfile=FONT_PATH, fontsize=8, align=0)
                            except:
                                pass
                        # नई लाइन शुरू करें
                        current_rect = fitz.Rect(x0, y0, x1, y1)
                        current_text = [word_str]
                
                # आखिरी बची हुई लाइन को प्रोसेस करें
                if current_rect and current_text:
                    full_line = " ".join(current_text)
                    if full_line.strip():
                        try:
                            translated_text = translator.translate(full_line)
                            new_page.draw_rect(current_rect, color=(1, 1, 1), fill=(1, 1, 1))
                            new_page.insert_textbox(current_rect, translated_text, fontname="sans", fontfile=FONT_PATH, fontsize=8, align=0)
                        except:
                            pass
            
            # फाइनल पीडीएफ सेव करना
            out_doc.save(output_pdf_path, garbage=3, deflate=True)
            out_doc.close()
            src_doc.close()

            # स्टेटस डिलीट करके फाइल भेजें
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ साइज़-ऑप्टिमाइज़्ड OCR तकनीक द्वारा अनुवादित हिंदी PDF तैयार है!")

        except Exception as e:
            bot.reply_to(message, f"❌ एरर: {e}")
            
        finally:
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("Light OCR Bot is running...")
    bot.infinity_polling()
