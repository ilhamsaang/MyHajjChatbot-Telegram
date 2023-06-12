import os
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def awal_bot(message):
    tahap1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    tahap2 = types.KeyboardButton("/start")
    tahap3 = types.KeyboardButton("Saya", request_location=True)
    tahap1.add(tahap2, tahap3)
    bot.send_message(message.chat.id, "Assalamualaikum Wr.Wb. Selamat datang pada aplikasi bantuan navigasi keperluan Jamaah haji", reply_markup=tahap1)

def send_welcome(message):
    bot.reply_to(message, 'halo apa kabar??')

@bot.message_handler(commands=['bantuan'])
def send_welcome(message):
    bot.reply_to(message, 'apa yang bisa saya bantu??')
    tahap1 = types.InlineKeyboardMarkup()
    tahapkd = types.InlineKeyboardButton(text="Kontak Developer", url="t.me/nomnomos")
    tahapTMH = types.InlineKeyboardButton(text="Tuntunan Manasik Haji", url="https://haji.kemenag.go.id/v4/")
    tahap1.add(tahapkd)
    tahap1.add(tahapTMH)
    bot.send_message(message.chat.id, "anda dapat memilih bantuan berikut ini, jika ada yang ingin ditanyakan/ kritik dan saran bisa menghubungi menggunkan kontak Developer.", reply_markup=tahap1)