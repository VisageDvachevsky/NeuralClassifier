# TGBot/bot.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import telebot
from TGmanager import BotAssistantManager
from DB.database import save_rating, create_database
from env import TELEGRAM_BOT_API_KEY

# Initialize the assistant manager
assistant_manager = BotAssistantManager()

# Initialize the bot with your API key
bot = telebot.TeleBot(TELEGRAM_BOT_API_KEY)

create_database()

# Handle '/start' command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I'm your AI assistant. How can I help you today?")

# Handle '/help' command
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "You can ask me anything and I will try to assist you.")

# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    response, confidence, intent = assistant_manager.process_input(user_input)
    bot.reply_to(message, response)

    # Ask for a rating
    msg = bot.reply_to(message, "Please rate my response (1-5):")
    bot.register_next_step_handler(msg, handle_rating, user_input, response, confidence, intent)

def handle_rating(message, user_input, response, confidence, intent):
    try:
        rating = int(message.text)
        if 1 <= rating <= 5:
            expected_intent = 'unknown'  # Modify as needed
            save_rating(user_input, response, rating, intent, expected_intent, confidence)
            bot.reply_to(message, "Thank you for your feedback!")
        else:
            msg = bot.reply_to(message, "Please enter a valid rating (1-5).")
            bot.register_next_step_handler(msg, handle_rating, user_input, response, confidence, intent)
    except ValueError:
        msg = bot.reply_to(message, "Please enter a valid rating (1-5).")
        bot.register_next_step_handler(msg, handle_rating, user_input, response, confidence, intent)

# Start the bot
if __name__ == '__main__':
    bot.polling()
