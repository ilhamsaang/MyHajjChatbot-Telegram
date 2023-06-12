import logging
import os
import torch
from pipeline_qa import pipeline
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi model dan tokenizer untuk pemrosesan Question Answering
model_name = pipeline()
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

def start(update: Update, context: CallbackContext) -> None:
    """Handler untuk perintah /start."""
    update.message.reply_text('Halo! Selamat datang di bot kami.')

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handler untuk pesan pengguna."""
    user_input = update.message.text

    # Melakukan klasifikasi niat (intent classification) berdasarkan pertanyaan
    intent_results = classify_intent(user_input)

    # Memperoleh hasil dengan skor tertinggi
    top_intent = intent_results[0]

    # Memproses pertanyaan dan memberikan jawaban yang sesuai
    if top_intent['label'] == "Masjid Nabawi":
        context_text, map_url = read_context()
        if context_text:
            answer = get_answer(user_input, context_text)
            if answer:
                update.message.reply_text(answer)
            else:
                update.message.reply_text("Maaf, tidak dapat menemukan jawaban.")
        else:
            update.message.reply_text("Maaf, tidak ada konteks yang tersedia.")
        if map_url:
            update.message.reply_text(f"URL Peta: {map_url}")
    elif top_intent['label'] == "Makam Al-Baqi":
        context_text, map_url = read_context()
        if map_url:
            update.message.reply_text(f"URL Peta: {map_url}")

def classify_intent(question):
    # Kode klasifikasi niat (intent classification) seperti sebelumnya
    pass

def read_context():
    file_path = "context.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
        if len(lines) >= 2:
            context_text = lines[0].strip()
            map_url = lines[1].strip()
            return context_text, map_url
    return None, None

def get_answer(question, context):
    inputs = tokenizer.encode_plus(question, context, return_tensors="pt")
    input_ids = inputs["input_ids"].tolist()[0]

    answer_start_scores, answer_end_scores = model(**inputs)

    answer_start = torch.argmax(answer_start_scores)
    answer_end = torch.argmax(answer_end_scores) + 1

    answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end]))

    return answer

def main() -> None:
    """Fungsi utama untuk menjalankan bot."""
    # Inisialisasi bot
    updater = Updater("TOKEN_BOT_ANDA", use_context=True)

    # Mendapatkan dispatcher untuk mendaftarkan handler
    dispatcher = updater.dispatcher

    # Mendaftarkan handler perintah /start
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Mendaftarkan handler pesan pengguna
    message_handler = MessageHandler(Filters.text & ~Filters.command, handle_message)
    dispatcher.add_handler(message_handler)

    # Mulai bot
    updater.start_polling()

    # Agar bot berjalan hingga dihentikan
    updater.idle()

if __name__ == '__main__':
    main()
