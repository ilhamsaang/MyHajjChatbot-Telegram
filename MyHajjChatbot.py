import sqlite3
import logging
import threading
from dotenv import load_dotenv
import geocoder
from geopy.geocoders import Nominatim
import socket
import datetime
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from fuzzywuzzy import fuzz
from pipeline_qa import TaskPipeline
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
mode_selesai = False


def start(update, context):
    global mode_selesai

    mode_selesai = True
    Mulai = "✈️"
    Selesai = "✅"
    Jalan = "📍"
    markeyboard = [
        [KeyboardButton(Mulai + " Mulai", resize_keyboard=True, one_time_keyboard=True), KeyboardButton(Selesai + " Selesai", resize_keyboard=True, one_time_keyboard=True)],
        [KeyboardButton(Jalan + " Nama Jalan", resize_keyboard=True, one_time_keyboard=True)]
    ]
    reply_markupkeyboard = ReplyKeyboardMarkup(markeyboard)
    update.effective_message.reply_text('Assalamualaikum Wr.Wb.\n Halo! Saya adalah bot yang akan membantu navigasi anda selama sedang melaksanakan ibadah haji maupun umroh. ', reply_markup=reply_markupkeyboard)


# Fungsi untuk menghitung rasio kesamaan menggunakan FuzzyWuzzy
def calculate_similarity_ratio(str1, str2):
    return fuzz.ratio(str1, str2)


def find_best_context(input_str, threshold):
    global mode_selesai

    if not mode_selesai:
        conn = get_database_connection()
        cursor = conn.cursor()

        query = "SELECT tempat, latitude, longitude, like, dislike FROM fuzzy"
        cursor.execute(query)
        results = cursor.fetchall()

        context_dict = {}
        for row in results:
            context = row[0]
            latitude = row[1]
            longitude = row[2]
            like = row[3]
            dislike = row[4]
            context_dict[context] = (latitude, longitude, like, dislike)

        best_context = choose_context(input_str, context_dict, threshold)
        if best_context:
            logger.info("Konteks terbaik adalah: {}".format(best_context))
            return best_context
        else:
            logger.info("Tidak ada konteks yang cocok.")
            return "Tidak ada konteks yang cocok."


def choose_context(user_message, context_dict, threshold=60):
    global mode_selesai

    if not mode_selesai:
        best_score = 0
        best_context = None
        best_latitude = None
        best_longitude = None
        best_like = None
        best_dislike = None
        for keyword, context in context_dict.items():
            score = fuzz.token_set_ratio(user_message, keyword)
            if score > best_score:
                best_score = score
                best_context = keyword
                best_latitude, best_longitude, best_like, best_dislike = context
            logger.info(f'Skor untuk "{keyword}": {score}')
        logger.info(f'Konteks terbaik: {best_context}\nSkor terbaik: {best_score}')
        if best_score < threshold:
            return None, None, None, None, None
        return best_context, best_latitude, best_longitude, best_like, best_dislike


def handle_message(update, context):
    global mode_selesai
    message = update.message.text.lower().strip()
    if message == '@my_hajj_bot':
        start(update, context)
    elif message == '✈️ mulai':
        mulai(update, context)
    elif message == '✅ selesai':
        selesai(update, context)
    elif message == '📍 nama jalan':
        get_location(update, context)
    elif message == 'Dimana saya':
        mylocation_message(update, context)
    else:
        if not mode_selesai:
            message = update.message.text.lower().strip()
            input_str = update.message.text
            threshold = 60

            best_context, latitude, longitude, like, dislike = find_best_context(input_str, threshold)

            if best_context:
                qa_pipeline = TaskPipeline()
                answer = qa_pipeline({"question": message, "context": best_context})

                conn = get_database_connection()
                cursor = conn.cursor()
                query = "SELECT last_like, last_dislike FROM fuzzy WHERE tempat = ?"
                cursor.execute(query, (best_context,))
                result = cursor.fetchone()
                last_like = result[0] if result else None
                last_dislike = result[1] if result else None

                response = f"\nJawaban: {answer}\nKonteks terbaik: {best_context}\nlatitude: {latitude}\nlongitude: {longitude}\nlike: {like}\ndislike: {dislike}"
                if last_like:
                    response += f"\nTerakhir kali disukai: {last_like}"
                if last_dislike:
                    response += f"\nTerakhir kali tidak disukai: {last_dislike}"

                reply_markup = create_inline_keyboard()
                context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)
                context.bot.send_location(chat_id=update.effective_chat.id, latitude=latitude, longitude=longitude)

                # Store the best context in chat data for future reference
                context.chat_data['best_context'] = best_context
            else:
                response = "Tidak ada konteks yang cocok."
                context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    pass


def create_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("like", callback_data='like')],
        [InlineKeyboardButton("dislike", callback_data='dislike')]
    ]
    return InlineKeyboardMarkup(keyboard)


def update_answer(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    message = update.message
    chat_id = query.message.chat_id
    current_time = datetime.datetime.now().strftime('%d-%m-%Y')
    # %Y-%m-%d % H: % M: % S

    if query.data == 'like':
        best_context = context.chat_data.get('best_context')
        if best_context:
            conn = get_database_connection()
            cursor = conn.cursor()
            query = "UPDATE fuzzy SET like = like + 1, last_like = ? WHERE tempat = ?"
            cursor.execute(query, (current_time, best_context))
            conn.commit()

        context.bot.send_message(chat_id=chat_id, text="Terima kasih atas rating-nya!")

    elif query.data == 'dislike':
        best_context = context.chat_data.get('best_context')
        if best_context:
            conn = get_database_connection()
            cursor = conn.cursor()
            query = "UPDATE fuzzy SET dislike = dislike + 1, last_dislike = ? WHERE tempat = ?"
            cursor.execute(query, (current_time, best_context))
            conn.commit()

        context.bot.send_message(chat_id=chat_id, text="Terima kasih atas rating-nya!")


# Threading-local storage for database objects
thread_local = threading.local()


def get_database_connection():
    global mode_selesai

    if not mode_selesai:
        # Create a new database connection if it doesn't exist for this thread
        if not hasattr(thread_local, 'connection'):
            thread_local.connection = sqlite3.connect('cari_tempat&keperluan.db')

        return thread_local.connection


def get_ip():
    global mode_selesai

    mode_selesai = True
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


# Fungsi untuk mendapatkan lokasi berdasarkan alamat IP
def get_location_by_ip():
    global mode_selesai

    mode_selesai = True
    g = geocoder.ip('me')
    return g.latlng


# Fungsi untuk mendapatkan lokasi berdasarkan GPS
def get_location_by_gps(lat, lon):
    global mode_selesai

    mode_selesai = True
    return lat, lon


def mylocation_message(update, context):
    global mode_selesai

    mode_selesai = True
    message = update.message
    chat_id = message.chat_id

    if message.text.lower() == 'dimana saya' or 'saya dimana' or 'lokasi saya' or 'posisi saya':
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = get_location_by_gps(latitude, longitude)

            if location:
                # Kirim lokasi ke pengguna
                context.bot.send_location(chat_id=chat_id, latitude=location[0], longitude=location[1])
                context.bot.send_message(chat_id=chat_id, text="Lokasi Anda ditemukan menggunakan GPS.")
            else:
                # Tangani jika tidak dapat mendapatkan lokasi
                context.bot.send_message(chat_id=chat_id, text="Maaf, tidak dapat menemukan lokasi saat ini.")

        else:
            location = get_location_by_ip()

            if location:
                # Kirim lokasi ke pengguna
                context.bot.send_location(chat_id=chat_id, latitude=location[0], longitude=location[1])
                context.bot.send_message(chat_id=chat_id, text="Lokasi Anda ditemukan menggunakan IP. Lokasi yang diperoleh menggunakan alamat IP tidak selalu akurat. Metode untuk mendapatkan lokasi berdasarkan IP dapat memberikan perkiraan yang kasar, terutama ketika menggunakan layanan gratis atau terbatas seperti WiFi")
            else:
                # Tangani jika tidak dapat mendapatkan lokasi
                context.bot.send_message(chat_id=chat_id, text="Maaf, tidak dapat menemukan lokasi saat ini.")


def get_location(update, context):
    global mode_selesai

    mode_selesai = True
    context.bot.send_message(chat_id=update.effective_chat.id, text='Silakan kirim lokasi Anda.', request_location=True)
    context.bot.send_location(chat_id=update.effective_chat.id, request_location=True)


def location_received(update, context):
    global mode_selesai

    mode_selesai = True
    location = update.message.location
    geolocator = Nominatim(user_agent="myGeocoder")
    address = geolocator.reverse([location.latitude, location.longitude])
    context.bot.send_message(chat_id=update.effective_chat.id, text=(str(address), location.latitude, location.longitude))


def selesai(update, context):
    global mode_selesai

    mode_selesai = True
    response = "Chatbot selesai menjawab pesan. Ketik mulai untuk memulai lagi."
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def mulai(update, context):
    global mode_selesai

    mode_selesai = False
    response = "Chatbot mulai menjawab pesan lagi."
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def answer_group_message(update: Update, context: CallbackContext) -> None:
    # Periksa apakah pesan masuk dari grup
    if update.message.chat.type == 'group':
        # Tangani pesan grup di sini
        message = update.message.text.lower().strip()

        # Lakukan pemrosesan pesan grup sesuai kebutuhan

        # Misalnya, periksa apakah pesan dimulai dengan "/start"
        if message.startswith('start'):
            start(update, context)
        # Atau periksa apakah pesan adalah perintah "/penting"
        elif message == '@my_hajj_bot':
            start(update, context)
        elif message == '✈️ mulai':
            mulai(update, context)
        elif message == '✅ selesai':
            selesai(update, context)
        elif message == '📍 nama jalan':
            get_location(update, context)
        elif message == 'Dimana saya':
            mylocation_message(update, context)

        # Jika tidak ada perintah yang cocok, tangani sebagai pertanyaan
        else:
            handle_message(update, context)


def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    iplocquestion = '^(dimana saya|ini dimana|dimanakah saya|Dimana saya|Ini dimana|Dimanakah saya)$'
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_handler(MessageHandler(Filters.regex('^@my_hajj_bot'), start))
    dispatcher.add_handler(MessageHandler(Filters.regex('^✈️ Mulai$'), mulai))
    dispatcher.add_handler(MessageHandler(Filters.regex('^✅ Selesai$'), selesai))
    dispatcher.add_handler(CommandHandler('selesai', selesai))
    dispatcher.add_handler(CommandHandler('mulai', mulai))
    dispatcher.add_handler(MessageHandler(Filters.regex(iplocquestion), mylocation_message))
    dispatcher.add_handler(MessageHandler(Filters.regex('^📍 Nama Jalan$'), get_location))
    dispatcher.add_handler(CommandHandler('location', get_location))
    dispatcher.add_handler(MessageHandler(Filters.location, location_received))
    callback_query_handler2 = CallbackQueryHandler(update_answer, pattern='^like$')
    dispatcher.add_handler(callback_query_handler2)
    callback_query_handler = CallbackQueryHandler(update_answer, pattern='^dislike$')
    dispatcher.add_handler(callback_query_handler)
    dispatcher.add_handler(MessageHandler(Filters.group & (~Filters.command), answer_group_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
