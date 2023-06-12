import telegram
from telegram import InlineQueryResultLocation, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler

BOT_TOKEN = '5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU'
def share_location(update, context):
    chat_id = update.effective_chat.id
    latitude = 40.7128  # Replace with the desired latitude
    longitude = -74.0060  # Replace with the desired longitude
    context.bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)

def start(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text='Hello! Use the /location command to share a location.')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('location', share_location))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()