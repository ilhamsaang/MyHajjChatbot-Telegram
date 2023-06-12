# import os
import re
import logging
import telegram
# from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from pipeline_qa import TaskPipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk import sent_tokenize

# load_dotenv()
# bot_token= os.getenv('BOT_TOKEN')
nltk.download('punkt')

qa_pipeline = TaskPipeline()

contexts = [
    """
    Masjid nabawi berada di kota madinah yang lokasinya dekat dengan makam al-baqi dimana sahabat nabi dimakamkan untuk menuju kesana jamaah bisa menggunakan kendaraan dengan rute <lokasi>Masjid nabawi madinah</lokasi>
    """,
    """
    didekat kampus ITS terdapat ayam geprek yang enak <lokasi> Ayam Geprek Joder Ka dhani</lokasi> 
    """,
    """
    di surabaya bagian timur teradapat institut teknologi penelitian yang terkenal dengan sebutan ITS atau <lokasi>Institut Teknologi Sepuluh Nopember Surabaya</lokasi>
    """,
]

all_contexts = " ".join(contexts)


def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Selamat datang di MyHajj.Bot! Silakan ajukan pertanyaan Anda:', reply_markup=get_about_keyboard())


def about(update: Update, _: CallbackContext) -> None:
    about_text = """MyHajj.Bot adalah bot yang dapat membantu mencari tempat tujuan anda selama masa ibadah haji maupun umroh."""
    query = update.callback_query
    query.answer()
    query.edit_message_text(about_text)


def get_about_keyboard():
    about_button = InlineKeyboardButton("About", callback_data="about")
    keyboard = [[about_button]]
    return InlineKeyboardMarkup(keyboard)


def choose_context(message):
    sentences = sent_tokenize(all_contexts)
    vectorizer = TfidfVectorizer()
    sentence_vectors = vectorizer.fit_transform(sentences)
    query_vector = vectorizer.transform([message])
    similarity_scores = cosine_similarity(query_vector, sentence_vectors)
    best_sentence_index = similarity_scores.argmax()
    surrounding_sentences = []
    if best_sentence_index > 0:
        surrounding_sentences.append(sentences[best_sentence_index - 1])
    surrounding_sentences.append(sentences[best_sentence_index])
    if best_sentence_index < len(sentences) - 1:
        surrounding_sentences.append(sentences[best_sentence_index + 1])
    return " ".join(surrounding_sentences)


def extract_location(context):
    location_pattern = re.compile(r'<lokasi>(.*?)</lokasi>', re.IGNORECASE | re.DOTALL)
    matches = location_pattern.findall(context)
    return matches


def answer_question(update: Update, context: CallbackContext) -> None:
    message = update.message.text.lower()
    selected_context = choose_context(message)

    # Mengecek jika user meminta lokasi
    if "lokasi" in message:#bisa kasih or kalau mau pake yang lain
        locations = extract_location(selected_context)
        if locations:
            # Ubah spasi dalam nama lokasi menjadi '+'
            location_name = locations[0].replace(" ", "+")
            map_url = f"https://www.google.com/maps/search/{location_name}"
            update.message.reply_text(f"Lokasi yang Anda cari:\n{map_url}")
        # else :
        #     update.message.reply_text("Maaf, tautan peta tidak tersedia.")
            return
        #buat else selain location agar tidak merubah spasi menjadi +

def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    updater = Updater("5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU", use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer_question))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
