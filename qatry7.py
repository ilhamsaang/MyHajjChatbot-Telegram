import logging
import os
import re

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize

from config import TOKEN

# Inisialisasi bot Telegram
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Baca konteks teks dari file txt
with open('context.txt', 'r') as f:
    context_text = f.read()

# Inisialisasi model AI Question Answering pada Hugging Face
qa = pipeline('question-answering', model='rm8488/bert-multi-cased-finetuned-xquadv1', tokenizer='mrm8488/bert-multi-cased-finetuned-xquadv1', context=context_text)

# Fungsi untuk menangani perint /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Halo! Saya adalah bot Question Answering. Silakan ajukan pertanyaan Anda.')

# Fungsi untuk menangani pesan yang diterima
def echo(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text

    # Tokenisasi pesan menggunakan library NLTK
    tokens = word_tokenize(message_text)

    # Identifikasi keyword dalam pesan
    if 'lokasi' in tokens and ('masjid' in tokens or 'nabawi' in tokens):
        # Tambahkan tag map dengan URL dari Google Maps Masjid Nabawi di Madinah
        map_url = 'https://www.google.com/maps/place/Masjid+Al+Nabawi/@24.4678903,39.6110815,17z/data=!3m1!4b1!4m5!m4!s0x15c3b9d6c7c5c57:0x75e7c3d7cd5d!8m2!3d24.4678903!4d39.6132702'
        update.message.reply_text(f"Berikut adalah lokasi Masjid Nabawi di Google Maps\n{map_url}")
    elif 'lokasi' in tokens and 'makam' in tokens and 'baqi' in tokens:
        # Tambahkan tag map dengan URL dari Google Maps Makam Al Baqi di Madinah
        map_url = 'https://www.google.com/maps/place/Al-Baqi+Graveyard/@24.464722,39.610833,17z/data=!3m1!4b1!4m5!3m4!1s0x15c3b9dc7c5cc7:0x7d9c5e77c5d5d8m2!8m2!3d24.464722!439.613'
        update.message.reply_text(f"Berikut adalah lokasi Makam Al Baqi di Google Maps\n{map_url}")
    else:
        # Identifikasi pertanyaan dan jawabannya menggunakan model AI Question Answering pada Hugging Face
        result = qa(question=message_text, context=context.user_data['context'], max_answer_len=50)

        # Prediksi jawaban menggunakan model AI Text Generation pada Hugging Face
        generator = pipeline('text-generation', model='gpt2', tokenizer='gpt2')
        prompt = f"{result['answer']} adalah jawaban dari pertanyaan: {message_text}"
        generated_text = generator(prompt, max_length=100, num_return_sequences=1, temperature=0.7)[0]['generated_text']
        generated_text = generated_text.replace(prompt, '').strip()

        # Cari kalimat terbaik dalam teks konteks yang mengandung jawaban
        best_sentence = ''
        if result['answer']:
            context_sentences = re.split('[.!?]', context.user_data['context'])
            for sentence in context_sentences:
                if result['answer'] in sentence:
                    if len(sentence) > len(best_sentence):
                        best_sentence = sentence

        # Kirim jawaban dan kalimat terbaik ke pengguna
        if best_sentence:
            update.message.reply_text(f"{result['answer']} ({best_sentence})\n\n{generated_text}")
        else:
            update.message.reply_text(generated_text)

# Fungsi untuk menangani pesan yang mengandung konteks teks
def context(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text

    # Tambahkan konteks teks ke context_text
    context_text += f" {message_text}"
    context.user_data['context'] = context_text
    qa.context = context_text

    update.message.reply_text('Konteks teks telah diperbarui.')

# Tambahkan handler untuk menangani pesan yang diterima
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# Tambahkan handler untuk perintah /start
dispatcher.add_handler(CommandHandler("start", start))

# Tambahkan handler untuk perintah /context
dispatcher.add_handler(CommandHandler("context", context))

# Jalankan bot
updater.start_polling()
updater.idle()
