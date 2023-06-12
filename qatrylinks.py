import telebot
from telebot import types

TELEGRAM_TOKEN = "5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU"

# Inisialisasi bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Fungsi untuk mencari link berdasarkan lokasi
def get_location_link(location):
    # Anda bisa mengganti dengan implementasi pencarian link sesuai dengan nama lokasi yang Anda inginkan
    if location == "Jakarta":
        return "https://www.google.com/maps/place/Jakarta"
    elif location == "Bandung":
        return "https://www.google.com/maps/place/Bandung"
    else:
        return None

# Fungsi untuk menangani pesan yang diterima
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Mengambil teks pesan yang diterima
    text = message.text

    # Jika teks pesan adalah "/start" atau "/help"
    if text.lower() == "/start" or text.lower() == "/help":
        # Menampilkan pesan balasan dengan menggunakan inline keyboard
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Jakarta", callback_data="location_jkt"))
        keyboard.add(types.InlineKeyboardButton("Bandung", callback_data="location_bdg"))

        bot.reply_to(message, "Silakan pilih lokasi:", reply_markup=keyboard)
    else:
        # Mencari link sesuai dengan nama lokasi yang diberikan
        link = get_location_link(text)

        # Jika link ditemukan
        if link:
            # Mengirimkan link sebagai pesan balasan
            bot.reply_to(message, link)
        else:
            # Jika link tidak ditemukan
            bot.reply_to(message, "Maaf, lokasi yang Anda berikan tidak ditemukan.")

# Fungsi untuk menangani callback dari inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    # Mengambil data callback
    data = call.data

    # Mencari link sesuai dengan lokasi yang dipilih
    if data == "location_jkt":
        link = get_location_link("Jakarta")
    elif data == "location_bdg":
        link = get_location_link("Bandung")
    else:
        link = None

    # Jika link ditemukan
    if link:
        # Mengirimkan link sebagai pesan balasan
        bot.answer_callback_query(callback_query_id=call.id, text=link)
    else:
        # Jika link tidak ditemukan
        bot.answer_callback_query(callback_query_id=call.id, text="Maaf, terjadi kesalahan.")

# Menjalankan bot
bot.polling()
