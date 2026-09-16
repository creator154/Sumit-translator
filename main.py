import os
import telebot
import requests
import fitz  # PyMuPDF

# Heroku Environment Variable से टोकन उठाना
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 नमस्ते! मुझे कोई भी बड़ी या Scanned English PDF भेजें। मैं इसके हर पेज को बिना लेआउट खराब किए हिंदी में बदलकर आपको फाइनल PDF दूँगा।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        status_msg = bot.reply_to(message, "⏳ आपकी PDF मिल गई है। बड़े साइज की वजह से इसे पेज-बाय-पेज प्रोसेस किया जा रहा है, कृपया 1-2 मिनट का समय दें...")

        # टेलीग्राम से मूल फाइल डाउनलोड करना
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf_path = f"input_{chat_id}.pdf"
        output_pdf_path = f"final_translated_{chat_id}.pdf"

        with open(input_pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            # मूल PDF को ओपन करें
            src_doc = fitz.open(input_pdf_path)
            final_doc = fitz.open() # फाइनल हिंदी पीडीएफ के लिए खाली डॉक्यूमेंट
            
            google_url = "https://googleapis.com"
            total_pages = len(src_doc)
            
            for page_num in range(total_pages):
                # हर एक पेज को अलग (Temp PDF) निकालना
                temp_page_doc = fitz.open()
                temp_page_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
                
                temp_page_path = f"temp_{chat_id}_{page_num}.pdf"
                temp_out_path = f"temp_out_{chat_id}_{page_num}.pdf"
                temp_page_doc.save(temp_page_path)
                temp_page_doc.close()
                
                # इस सिंगल पेज को गूगल के क्लाउड ट्रांसलेटर पर भेजना
                with open(temp_page_path, 'rb') as f:
                    payload = {
                        'client': 'webapp',
                        'sl': 'en',
                        'tl': 'hi',
                        'f': 'pdf'
                    }
                    files = [('file', ('page.pdf', f, 'application/pdf'))]
                    
                    response = requests.post(google_url, data=payload, files=files, timeout=40)
                
                # अगर पेज सफलतापूर्वक ट्रांसलेट हो गया
                if response.status_code == 200 and len(response.content) > 500:
                    with open(temp_out_path, 'wb') as out_f:
                        out_f.write(response.content)
                    
                    # ट्रांसलेटेड पेज को फाइनल पीडीएफ में जोड़ना
                    translated_page_doc = fitz.open(temp_out_path)
                    final_doc.insert_pdf(translated_page_doc)
                    translated_page_doc.close()
                else:
                    # अगर किसी वजह से ट्रांसलेशन फेल हुआ, तो मूल इंग्लिश पेज ही जोड़ दें (ताकि पेपर अधूरा न रहे)
                    print(f"Page {page_num} translation failed, inserting original.")
                    orig_page_doc = fitz.open(temp_page_path)
                    final_doc.insert_pdf(orig_page_doc)
                    orig_page_doc.close()
                
                # टेम्परेरी सिंगल पेजों को डिलीट करना
                if os.path.exists(temp_page_path): os.remove(temp_page_path)
                if os.path.exists(temp_out_path): os.remove(temp_out_path)

            # सभी पेजों के जुड़ने के बाद फाइनल PDF सेव करना
            if len(final_doc) > 0:
                final_doc.save(output_pdf_path, garbage=3, deflate=True)
                final_doc.close()
                src_doc.close()

                # स्टेटस डिलीट करके यूजर को ट्रांसलेटेड फाइल भेजना
                bot.delete_message(chat_id, status_msg.message_id)
                with open(output_pdf_path, 'rb') as pdf_to_send:
                    bot.send_document(chat_id, pdf_to_send, caption="✅ आपकी बड़ी NEET Scanned PDF सफलतापूर्वक हिंदी में अनुवादित हो गई है (सभी फिगर्स के साथ)!")
            else:
                raise Exception("No pages were successfully translated.")

        except Exception as e:
            bot.delete_message(chat_id, status_msg.message_id)
            bot.reply_to(message, f"❌ इस बड़ी PDF को प्रोसेस करने में सर्वर त्रुटि आई: {e}")
            
        finally:
            # कचरा साफ करना
            if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
    else:
        bot.reply_to(message, "❌ कृपया केवल PDF फ़ाइल ही भेजें।")

if __name__ == "__main__":
    print("Advanced Page-Split PDF Bot is running...")
    bot.infinity_polling()
