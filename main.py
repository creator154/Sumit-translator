import os
import telebot
import time
import traceback
from pypdf import PdfReader
from fpdf import FPDF
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ट्रांसलेटर इंजन सेटअप
translator = GoogleTranslator(source='en', target='hi')

# फॉन्ट का नाम जो अब सीधे GitHub प्रोजेक्ट में है
FONT_PATH = "NotoSansDevanagari.ttf"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मैं आपका फिक्स्ड PDF ट्रांसलेटर हूँ। मुझे English PDF भेजें, मैं उसे हिंदी PDF में बदलकर दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ PDF मिल गई है। लोकल फॉन्ट का उपयोग करके सुरक्षित अनुवाद शुरू हो रहा है, कृपया थोड़ा इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            # 1. PDF से टेक्स्ट रीड करना
            reader = PdfReader(input_pdf_path)
            chunks = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    page_text = text.strip()
                    # 1500 अक्षरों के छोटे टुकड़ों में बांटना
                    page_chunks = [page_text[i:i+1500] for i in range(0, len(page_text), 1500)]
                    chunks.extend(page_chunks)

            if not chunks:
                bot.delete_message(chat_id, status_msg.message_id)
                bot.reply_to(message, "❌ इस PDF में कोई टेक्स्ट नहीं मिला (यह पूरी तरह इमेज/फोटो वाली PDF है)।")
                return

            # 2. Google Batch Translation + Anti-Block Delay
            translated_text = ""
            for chunk in chunks:
                if chunk.strip():
                    try:
                        translation = translator.translate(chunk)
                        translated_text += translation + "\n\n"
                        time.sleep(1.5) # Google ब्लॉक से बचने के लिए गैप
                    except Exception as translate_err:
                        print(f"Translation skipped for a chunk: {translate_err}")
                        time.sleep(3)
                        continue

            # 3. fpdf2 से हिंदी PDF तैयार करना
            pdf = FPDF()
            pdf.add_page()
            
            # प्रोजेक्ट में मौजूद लोकल फॉन्ट को लोड करना (अब यह कभी फेल नहीं होगा)
            if os.path.exists(FONT_PATH):
                pdf.add_font("HindiFont", style="", fname=FONT_PATH)
                pdf.set_font("HindiFont", size=11)
            else:
                raise FileNotFoundError("Font file is still missing in directory.")
            
            # टेक्स्ट को PDF में लिखना
            pdf.multi_cell(0, 7, txt=translated_text)
            pdf.output(output_pdf_path)

            # 4. यूज़र को फाइनल PDF सेंड करना
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ आपके इंग्लिश टेक्स्ट का शुद्ध हिंदी अनुवादित PDF सुरक्षित रूप से तैयार है!")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            error_details = traceback.format_exc()
            bot.reply_to(message, f"❌ तकनीकी समस्या आई: {e}")
            print(f"Error Details:\n{error_details}")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    print("Local Font PDF Bot is running successfully...")
    bot.infinity_polling()
