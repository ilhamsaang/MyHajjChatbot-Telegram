#import re
import datetime
import telebot
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import storage
import pipeline_qa

TELEGRAM_TOKEN = "5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU"

# Inisialisasi Firebase Admin SDK
# cred = credentials.Certificate("tugas-akhir-chatbot.json")
# firebase_admin.initialize_app(cred, {
#     'storageBucket': 'gs://tugas-akhir-chatbot.appspot.com/Audio Doa'
# })

qa = pipeline_qa.pipeline()

contexts = {
    "context1": """
    masjid nabawi berada di kota madinah yang lokasinya dekat dengan makam al-baqi dimana sahabat nabi dimakamkan. untuk menuju kesana jamaah bisa menggunakan kendaraan. Rute Menuju lokasi tersebut.
    """,
    "context2": """
    didekat masjid nabawi terdapat Terminal Bus SAPTCO terletak di dekat tempat ibadah masjid Masjid Abu Dharr Al-Ghafari.
    """,
    "context3": """
    adapun beberapa tempat pemberhentian bus/bis terdekat di masjid nabawi dapat dilihat menggunakan.
    """
}

map_links = {
    "context1": ["https://www.google.com/maps/search/?api=1&query=my+location+to+Masjid+nabawi+madinah&hl=id"],#lokasi masjid nabawi
    "context2": ["https://www.google.com/maps/search/?api=1&query=my+location+to+SAPTCO+bus+Station+madinah&hl=id"],#terminal bus di dekat masjid nabawi
    "context3": ["https://www.google.com/maps/search/?api=1&query=bus+stop+nearest+Masjid+nabawi+madinah&hl=id"],#tempat pemberhentian bus di sekitar masjid nabawi
    "context4": ["https://www.google.co.id/maps/search/jewelry+stores+near+masjid+nabawi+madinah&hl=id"],#perhiasan di sekitar masjid nabawi
    "context5": ["https://www.google.co.id/maps/search/food+near+masjid+nabawi+madinah&hl=id"],#makanan di sekitar masjid nabawi
    "context6": ["https://www.google.co.id/maps/search/indonesian+food+near+masjid+nabawi+madinah&hl=id"],#makanan indonesia di sekitar masjid nabawi
    "context7": ["https://www.google.co.id/maps/search/souvenirs+near+masjid+nabawi+madinah&hl=id"],#souvenir di sekitar masjid nabawi
    "context8": ["https://www.google.co.id/maps/search/laundry+near+masjid+nabawi+madinah&hl=id"],#laundry di sekitar masjid nabawi
    "context9": ["https://www.google.co.id/maps/search/clotesh+near+masjid+nabawi+madinah&hl=id"],#baju di sekitar masjid nabawi


}

def find_answer_and_context(question):
    for key, context in contexts.items():
        response = qa({"context": context, "question": question})
        if response:
            return response, key
    return None, None

def send_map(message, map_path):
    bucket = storage.bucket()
    blob = bucket.blob(map_path)
    url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')

    bot.send_map(chat_id=message.chat.id, map=url)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Selamat datang! Silakan ajukan pertanyaan Anda atau ketik 'Halo, Assalamualaikum'.")

@bot.message_handler(func=lambda m: m.text.lower() == 'halo, assalamualaikum')
def greeting_handler(message):
    bot.send_message(chat_id=message.chat.id, text="Waalaikumsalam, ada yang bisa saya bantu?")

@bot.message_handler(func=lambda m: True)
def message_handler(message):
    text = message.text
    response, context_key = find_answer_and_context(text)

    if response:
        if "Rute menuju lokasi tersebut" in response:
            for map_path in map_links[context_key]:
                send_map(message, map_path)
        else:
            bot.send_message(chat_id=message.chat.id, text=response)
    else:
        if context_key not in map_links:
            bot.send_message(chat_id=message.chat.id,
                             text="Maaf, saya tidak dapat menemukan informasi untuk lokasi yang diminta.")
            return

bot.polling()