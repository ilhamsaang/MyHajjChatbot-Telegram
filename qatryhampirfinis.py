# -*- coding: utf-8 -*-
import re
import os
from dotenv import load_dotenv
import logging
import context_lokasi
import context_lokasi_url
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, PicklePersistence
from pipeline_qa import TaskPipeline
from fuzzywuzzy import fuzz
import nltk

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
qa_pipeline = TaskPipeline()
rute_contexts = context_lokasi_url.petunjuk_lokasi #context berisi lokasi,patokan, dan url
cari_contexts = context_lokasi.deskripsi_lokasi #context berisi deskripsi dan keterangan lokasi


def calculate_similarity_score(user_message, keyword):
    return fuzz.ratio(user_message, keyword)


def choose_context(user_message, context_dict, threshold=67):
    best_score = 0
    best_context = None
    for keyword, context in context_dict.items():
        score = fuzz.token_set_ratio(user_message, keyword)
        if score > best_score:
            best_score = score
            best_context = context
        print(f'Score for "{keyword}": {score}')
    print(f'Best context: {best_context}\n Best score: {best_score}')
    if best_score < threshold:
        return None
    return best_context


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Rute", callback_data='rute')],
        [InlineKeyboardButton("Cari", callback_data='cari')],
        [InlineKeyboardButton("Batal", callback_data='cancel')],  # Menambahkan tombol 'Batal'
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Halo! Saya adalah bot yang akan membantu navigasi anda selama sedang melaksanakan ibadah haji maupun umroh. Silakan pilih salah satu opsi berikut:', reply_markup=reply_markup)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    choice = query.data

    if choice == 'cancel':  # Menambahkan pilihan 'cancel'
        cancel(update, context)
    else:
        context.user_data['choice'] = choice

        if choice == 'rute':
            if update.callback_query.message.text != 'Anda telah memilih opsi "Rute". Silakan ajukan pertanyaan Anda:':
                update.callback_query.edit_message_text(text='Anda telah memilih opsi "Rute". Silakan ajukan pertanyaan Anda:')
        else:
            keyboard = [[InlineKeyboardButton(context, callback_data='cari_' + context)] for context in cari_contexts.keys()]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query.message.text != 'Anda telah memilih opsi "Cari". Silakan pilih topik yang ingin Anda ketahui:':
                update.callback_query.edit_message_text(text='Anda telah memilih opsi "Cari". Silakan pilih topik yang ingin Anda ketahui:', reply_markup=reply_markup)


def topic_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    topic = query.data.replace('cari_', '')
    context.user_data['cari_topik'] = topic

    update.callback_query.edit_message_text(text=f"Anda telah memilih topik '{topic}'. Silakan ajukan pertanyaan Anda:")


def start_rute(update: Update, context: CallbackContext) -> None:
    context.user_data['choice'] = 'rute'
    update.message.reply_text("Rute kemana yang ingin Anda tuju?")


def rute_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Anda memilih opsi "Rute". Silakan ajukan pertanyaan Anda:')
    context.user_data['choice'] = 'rute'
    if 'cari_topik' in context.user_data:
        del context.user_data['cari_topik']  # Hapus topik penjelasan saat berpindah ke rute lokasi


def cari_command(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton(context, callback_data='cari_' + context)] for context in cari_contexts.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Anda telah memilih opsi "Cari". Silakan pilih topik yang ingin Anda ketahui:', reply_markup=reply_markup)
    context.user_data['choice'] = 'cari'  # Atur pilihan pengguna ke cari


def cancel(update: Update, context: CallbackContext) -> None:
    if update.callback_query is not None:
        # Ini adalah callback query
        query = update.callback_query
        query.answer()
        query.edit_message_text('Anda telah membatalkan permintaan. Terima kasih!')
    else:
        # Ini adalah command
        update.message.reply_text('Anda telah membatalkan permintaan. Terima kasih!')

    context.user_data.clear()


def extract_info_from_context(context):
    url_matches = re.findall(r"<url>\s*(.*?)\s*</url>", context)
    lati_matches = re.findall(r"<lati>\s*(.*?)\s*</lati>", context)
    longi_matches = re.findall(r"<longi>\s*(.*?)\s*</longi>", context)
    description_matches = re.findall(r"<keterangan>\s*(.*?)\s*</keterangan>", context)
    return url_matches, lati_matches, longi_matches, description_matches


def answer_question(update: Update, context: CallbackContext) -> None:
    print(f"Debug: cari_topik = {context.user_data.get('cari_topik')}")
    message = update.message.text.lower().strip()
    print(f"Message: {message}")

    if not context.user_data.get("choice"):
        update.message.reply_text("Mohon pilih 'rute' atau 'Cari' terlebih dahulu sebelum mengajukan pertanyaan.")
        return

    if context.user_data["choice"] == "rute":
        best_context = choose_context(message, rute_contexts)
        print(f"Best context: {best_context}")
        if best_context is None:
            update.message.reply_text("Maaf, saya tidak dapat menemukan rute lokasi yang Anda cari.")
            return
        url, lati, longi, translations= extract_info_from_context(best_context)
        for i in range(len(url)):
            chat_id = update.effective_chat.id
            latitude = lati[0]
            longitude = longi[0]
            location_name = url[0].replace(" ", "+")
            answer = f"map lokasi yang anda cari: {translations[i]}\n\n https://www.google.com/maps/search/{location_name}"
            answer_map = context.bot.send_location(chat_id=chat_id,latitude=latitude, longitude=longitude)
            update.message.reply_text(answer) & message(answer_map)

    elif context.user_data["choice"] == "cari":
        if 'cari_topik' not in context.user_data:
            update.message.reply_text("Mohon pilih topik terlebih dahulu.")
            return
        best_context = cari_contexts.get(context.user_data['cari_topik'], None)
        if not best_context:
            update.message.reply_text("Maaf, konten Cari untuk topik ini belum tersedia.")
            return
        if best_context.strip() == "":
            update.message.reply_text("Maaf, konten Cari untuk topik ini kosong.")
            return
        print(f"Best context: {best_context}")
        answer = qa_pipeline({"question": message, "context": best_context})
        if answer.strip() == "":
            update.message.reply_text("Maaf, saya tidak dapat menemukan jawaban untuk pertanyaan Anda.")
            return
        update.message.reply_text(answer)


def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    pp = PicklePersistence(filename='userdata')
    updater = Updater(bot_token, persistence=pp, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("rute", rute_command))
    dispatcher.add_handler(CommandHandler("cari", cari_command))
    dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^rute$|^cari$'))
    dispatcher.add_handler(CallbackQueryHandler(topic_click, pattern='^cari_'))
    dispatcher.add_handler(CallbackQueryHandler(cancel, pattern='^cancel$'))  # Merubah ini menjadi CallbackQueryHandler
    dispatcher.add_handler(CommandHandler("cancel", cancel))  # Tambahkan baris ini
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer_question))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
