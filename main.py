import os
import telebot
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
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
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी Scanned या फोटो वाली English PDF भेजें। मैं इसके फिगर्स को सुरक्षित रखते हुए टेक्स्ट को हिंदी में बदल दूंगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ Scanned PDF मिल गई है। फोटो से टेक्स्ट को स्कैन करके अनुवाद किया जा रहा है, कृपया 1 मिनट का समय दें...")

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
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Tesseract से फोटो के अंदर लिखे शब्दों का डेटा (Text + Location) निकालना
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                scale_x = page.rect.width / pix.width
                scale_y = page.rect.height / pix.height
                
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    text = data['text'][i]
                    # अगर बॉक्स में कोई इंग्लिश शब्द मिला है
                    if text.strip() and len(text.strip()) > 1:
                        try:
                            translated_text = translator.translate(text)
                            if translated_text.strip() == text.strip():
                                continue
                                
                            x = data['left'][i] * scale_x
                            y = data['top'][i] * scale_y
                            w = data['width'][i] * scale_x
                            h = data['height'][i] * scale_y
                            
                            rect = fitz.Rect(x, y, x + w, y + h)
                            
                            # पुरानी इंग्लिश फोटो को वाइट बॉक्स से छुपाना
                            new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            # नई हिंदी टाइप करना
                            new_page.insert_textbox(rect, translated_text, fontname="sans", fontfile=FONT_PATH, fontsize=8, align=0)
                        except:
                            continue
            
            out_doc.save(output_pdf_path, garbage=3, deflate=True)
            out_doc.close()
            src_doc.close()

            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ OCR तकनीक द्वारा पूरी तरह अनुवादित हिंदी PDF तैयार है!")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, f"❌ एरर: {e}\nसुनिश्चित करें कि आपने Heroku Settings में Buildpack ऐड कर लिया है।")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)

if __name__ == "__main__":
    print("Final OCR Bot is running...")
    bot.infinity_polling()
