import os
import telebot
import requests
from googletrans import Translator
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()

FONT_PATH = "NotoSansDevanagari.ttf"
FONT_URL = "https://github.com"

def download_hindi_font():
    """हिंदी फॉन्ट डाउनलोड करना ताकि PDF में बॉक्स न बनें"""
    if not os.path.exists(FONT_PATH):
        print("Downloading Hindi Font...")
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
        print("Font Downloaded!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे इंग्लिश PDF भेजें। मैं उसका पूरा टेक्स्ट हिंदी में अनुवाद करके आपको एक नई हिंदी PDF फ़ाइल बनाकर दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ आपकी PDF मिल गई है। टेक्स्ट का हिंदी अनुवाद करके नई PDF फाइल तैयार की जा रही है, कृपया थोड़ा इंतज़ार करें...")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            download_hindi_font()
            
            # 1. इंग्लिश PDF से सारा टेक्स्ट निकालना
            reader = PdfReader(input_pdf_path)
            extracted_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

            if not extracted_text.strip():
                bot.reply_to(message, "❌ इस PDF में कोई टेक्स्ट नहीं मिला (शायद यह पूरी तरह फोटो वाली PDF है)।")
                return

            # 2. Google Translate से टेक्स्ट का हिंदी अनुवाद करना (Batch Mode)
            chunks = [extracted_text[i:i+3000] for i in range(0, len(extracted_text), 3000)]
            translated_text = ""
            for chunk in chunks:
                translation = translator.translate(chunk, src='en', dest='hi')
                translated_text += translation.text + "\n"

            # 3. ReportLab का उपयोग करके बिल्कुल नई हिंदी PDF तैयार करना
            pdfmetrics.registerFont(TTFont('HindiFont', FONT_PATH))
            
            c = canvas.Canvas(output_pdf_path, pagesize=letter)
            width, height = letter
            
            textobject = c.beginText()
            textobject.setTextOrigin(50, height - 50)
            textobject.setFont("HindiFont", 10)
            textobject.setLeading(14) # लाइनों के बीच का गैप

            # टेक्स्ट को लाइनों में बांटकर PDF पेज पर लिखना
            lines = translated_text.split('\n')
            for line in lines:
                # अगर पेज भरने वाला हो तो नया पेज जोड़ें
                if textobject.getY() < 50:
                    c.drawText(textobject)
                    c.showPage()
                    textobject = c.beginText()
                    textobject.setTextOrigin(50, height - 50)
                    textobject.setFont("HindiFont", 10)
                    textobject.setLeading(14)
                
                textobject.textLine(line)
            
            c.drawText(textobject)
            c.save()

            # 4. पुरानी स्टेटस मैसेज डिलीट करके नई हिंदी PDF भेजना
            bot.delete_message(chat_id, status_msg.message_id)
            with open(output_pdf_path, 'rb') as pdf_to_send:
                bot.send_document(chat_id, pdf_to_send, caption="✅ आपके इंग्लिश टेक्स्ट का शुद्ध हिंदी अनुवादित PDF तैयार है!")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, f"❌ अनुवाद करने या PDF बनाने में समस्या आई।")
            print(f"Error: {e}")
            
        finally:
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    download_hindi_font()
    print("Text-to-PDF Translator Bot is running...")
    bot.infinity_polling()
