import transformers
import pipeline_qa
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Load a pre-trained question answering model (in this case, the mrm8488/bert-base-indonesian-1.5G model)
qa =pipeline_qa.pipeline()
# Define a function to handle the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello! I'm a question answering bot. Please send me a question and I'll do my best to answer it!")


# Define a function to handle incoming messages
def answer_question(update, context):
    # Get the text of the incoming message
    question = update.message.text

    # Use the question answering model to generate a response
    answer = qa({
        "context": "Some text that the model should search for the answer in.",
        "question": question
    })["answer"]

    # Send the response back to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


# Set up the Telegram bot
updater = Updater(token='5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU', use_context=True)
dispatcher = updater.dispatcher

# Register the start function to be called when the /start command is issued
dispatcher.add_handler(CommandHandler('start', start))

# Register the answer_question function to be called whenever a message is received
dispatcher.add_handler(MessageHandler(Filters.text, answer_question))

# Start the bot
updater.start_polling()