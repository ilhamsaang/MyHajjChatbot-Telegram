
import telebot
import pipeline_qa

TELEGRAM_TOKEN = "5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU"

qa = pipeline_qa.pipeline()

contexts = {
    "Masjid Nabawi": """
    Masjid Nabawi berada di kota madinah yang lokasinya dekat dengan makam al-baqi dimana sahabat nabi dimakamkan untuk menuju kesana jamaah bisa menggunakan kendaraan.
    """,
    "SAPTCO Bus Terminal": """
    Terminal Bus SAPTCO terletak di dekat tempat ibadah masjid Masjid Abu Dharr Al-Ghafari.
    """,
    "Bus Stops": """
    Beberapa tempat pemberhentian bus/bis terdekat di masjid nabawi dapat dilihat menggunakan.
    """
}

map_links = {
    "Masjid Nabawi": ["https://www.google.com/maps/search/?api=1&query=my+location+to+Masjid+nabawi+madinah&hl=id"],
    "SAPTCO Bus Terminal": ["https://www.google.com/maps/search/?api=1&query=my+location+to+SAPTCO+bus+Station+madinah&hl=id"],
    "Bus Stops": ["https://www.google.com/maps/search/?api=1&query=bus+stop+nearest+Masjid+nabawi+madinah&hl=id"],
    "Jewelry Stores": ["https://www.google.co.id/maps/search/jewelry+stores+near+masjid+nabawi+madinah&hl=id"],
    "Food": ["https://www.google.co.id/maps/search/food+near+masjid+nabawi+madinah&hl=id"],
    "Indonesian Food": ["https://www.google.co.id/maps/search/indonesian+food+near+masjid+nabawi+madinah&hl=id"],
    "Souvenirs": ["https://www.google.co.id/maps/search/souvenirs+near+masjid+nabawi+madinah&hl=id"],
    "Laundry": ["https://www.google.co.id/maps/search/laundry+near+masjid+nabawi+madinah&hl=id"],
    "Clothes": ["https://www.google.co.id/maps/search/clotesh+near+masjid+nabawi+madinah&hl=id"]
}


def find_answer_and_context(question):
    for key, context in contexts.items():
        response = qa({"context": context, "question": question})
        if response:
            return response, key
    return None, None

def send_map(message, map_url):
    bot.send_message(chat_id=message.chat.id, text=map_url)

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
        if "Masjid" in response:
            for map_path in map_links[context_key]:
                send_map(message, map_path)
        else:
            bot.send_message(chat_id=message.chat.id, text=response)
    else:
        bot.send_message(chat_id=message.chat.id, text="Maaf, saya tidak bisa menjawab pertanyaan Anda.")

bot.polling()
