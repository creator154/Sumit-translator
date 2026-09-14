import os
import telebot
import requests
import fitz  # PyMuPDF
import easyocr
from deep_translator import GoogleTranslator

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ट्रांसलेटर और OCR रीडर सेटअप
translator = GoogleTranslator(source='en', target='hi')
# 'en' मतलब यह इंग्लिश शब्दों को स्कैन करेगा, gpu=False क्योंकि Heroku CPU पर चलता है
reader = easyocr.Reader(['en'], gpu=False)

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
    bot.reply_to(message, "👋 नमस्ते! मुझे NEET या कोई भी Scanned/Photo वाली English PDF भेजें। मैं Google Lens की तरह फोटो के अंदर से इंग्लिश मिटाकर वहीं हिंदी लिख दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ Scanned PDF मिल गई है। Google OCR इंजन चालू हो रहा है (फोटो से टेक्स्ट स्कैन किया जा रहा है), कृपया थोड़ा इंतज़ार करें...")

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
                # 1. पेज का हाई-क्वालिटी स्क्रीनशॉट (Pixmap) लें ताकि डायग्राम्स सुरक्षित रहें
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                
                # 2. EasyOCR से फोटो के अंदर लिखे शब्दों और उनकी लोकेशन (Coordinates) को स्कैन करना
                ocr_results = reader.readtext(img_bytes)
                
                # आउटपुट डॉक्यूमेंट में एक नया खाली पेज जोड़ें जिसका साइज ओरिजिनल जैसा हो
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                # Pixmap और PDF कोऑर्डिनेट्स का अनुपात (Scale Factor) निकालना
                scale_x = page.rect.width / pix.width
                scale_y = page.rect.height / pix.height
                
                # 3. OCR द्वारा ढूंढे गए हर इंग्लिश शब्द पर प्रोसेस करना
                for bbox, text, confidence in ocr_results:
                    if text.strip() and confidence > 0.3: # 30% से ज्यादा सटीक होने पर ही प्रोसेस करें
                        try:
                            # इंग्लिश शब्द का हिंदी अनुवाद
                            translated_text = translator.translate(text)
                            
                            # OCR के बाउंडिंग बॉक्स को PDF के साइज के अनुसार एडजस्ट करना
                            top_left, top_right, bottom_right, bottom_left = bbox
                            x0 = top_left[0] * scale_x
                            y0 = top_left[1] * scale_y
                            x1 = bottom_right[0] * scale_x
                            y1 = bottom_right[1] * scale_y
                            
                            rect = fitz.Rect(x0, y0, x1, y1)
                            
                            # फोटो के उस हिस्से की इंग्लिश को सफेद पट्टी से मिटाना
                            new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            
                            # ठीक उसी खाली जगह पर हिंदी फॉन्ट टाइप करना
                            new_page.insert_textbox(
                                rect, 
                                translated_text, 
                                fontname="sans", 
                                fontfile=FONT_PATH, 
                                fontsize=8,
                                align=0
                            )
                        except Exception as e:
                            print(f"OCR Word Error: {e}")
                            continue
            
            # फाइनल क्लीन पीडीएफ को सेव करना
            out_doc.save(output_pdf_path, garbage=3, deflate=True)
            out_doc.close()
            src_doc.close()

            # पुराना स्टेटस डिलीट करके नई PDF सेंड करें
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ Google OCR तकनीक द्वारा अनुवादित हिंदी PDF तैयार है!")

        except Exception as e:
            bot.reply_to(message, f"❌ टेक्निकल एरर: {e}")
            print(f"Global OCR Error: {e}")
            
        finally:
            if os.path.exists(input_pdf_path):
                os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("Google Lens Style OCR Bot is running...")
    bot.infinity_polling()
