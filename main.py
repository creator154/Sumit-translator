import os
import telebot
import requests
import traceback
from pypdf import PdfReader
from fpdf import FPDF
from deep_translator import GoogleTranslator

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ट्रांसलेटर सेटअप (यह बहुत ही स्टेबल है)
translator = GoogleTranslator(source='en', target='hi')

FONT_PATH = "NotoSansDevanagari.ttf"
FONT_URL = "https://github.com"

def download_hindi_font():
    """हिंदी फॉन्ट सुनिश्चित करना ताकि PDF में सही अक्षर दिखें"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी English PDF भेजें। मैं उसका पूरा टेक्स्ट हिंदी में बदलकर आपको एक नई PDF फ़ाइल सेंड कर दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ PDF मिल गई है। टेक्स्ट का हिंदी अनुवाद करके नई PDF फाइल बनाई जा रही है, कृपया थोड़ा इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            
            # 1. इंग्लिश PDF से टेक्स्ट निकालना
            reader = PdfReader(input_pdf_path)
            extracted_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

            if not extracted_text.strip():
                bot.delete_message(chat_id, status_msg.message_id)
                bot.reply_to(message, "❌ इस PDF में कोई सेलेक्ट होने वाला टेक्स्ट नहीं मिला (यह पूरी तरह इमेज/फोटो वाली PDF है)।")
                return

            # 2. टेक्स्ट का हिंदी अनुवाद (टुकड़ों में ताकि API क्रैश न हो)
            # 2000 अक्षरों के छोटे टुकड़े बनाना बेस्ट रहता है
            chunks = [extracted_text[i:i+2000] for i in range(0, len(extracted_text), 2000)]
            translated_text = ""
            
            for chunk in chunks:
                if chunk.strip():
                    translation = translator.translate(chunk)
                    translated_text += translation + "\n"

            # 3. fpdf2 का उपयोग करके नई हिंदी PDF बनाना (यह बहुत सरल और सटीक है)
            pdf = FPDF()
            pdf.add_page()
            
            # हिंदी देवनागरी फॉन्ट रजिस्टर करना
            pdf.add_font("HindiFont", style="", fname=FONT_PATH)
            pdf.set_font("HindiFont", size=11)
            
            # टेक्स्ट को ऑटोमैटिक लाइन ब्रेक के साथ PDF में लिखना
            pdf.multi_cell(0, 8, txt=translated_text)
            
            # फाइल सेव करना
            pdf.output(output_pdf_path)

            # 4. यूजर को ट्रांसलेटेड PDF भेजना
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ आपके इंग्लिश टेक्स्ट का शुद्ध हिंदी अनुवादित PDF तैयार है!")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            error_details = traceback.format_exc()
            bot.reply_to(message, f"❌ कोई तकनीकी समस्या आई।")
            print(f"Error Details:\n{error_details}")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("New Stable Text-to-PDF Bot is running...")
    bot.infinity_polling()
