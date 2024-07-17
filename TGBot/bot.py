import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telebot import apihelper
from TGmanager import BotAssistantManager
from DB.database import save_rating, create_database
from env import TELEGRAM_BOT_API_KEY
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, api_key):
        self.bot = telebot.TeleBot(api_key)
        self.assistant_manager = BotAssistantManager()
        self.INTENTS = {
            'get_time': 'узнать время',
            'get_date': 'узнать дату',
            'greet': 'приветствие',
            'goodbye': 'прощание',
            'No Intent': 'Нет намерения' 
        }
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            try:
                self.log_admin_activity("User started interaction", message.chat.id)
                self.bot.reply_to(message, "Добро пожаловать! Напишите сообщение, чтобы начать. Используйте /help для списка доступных команд.\nВерсия alpha0.1")
            except Exception as e:
                self.handle_error(message, e)

        @self.bot.message_handler(commands=['help'])
        def send_help(message):
            try:
                help_text = (
                    "Доступные команды:\n"
                    "/start - Начать взаимодействие с ботом\n"
                    "/help - Показать это сообщение помощи\n"
                    "/intents - Список доступных намерений и их переводов\n"
                )
                self.log_admin_activity("User requested help", message.chat.id)
                self.bot.reply_to(message, help_text)
            except Exception as e:
                self.handle_error(message, e)

        @self.bot.message_handler(commands=['intents'])
        def list_intents(message):
            try:
                response = "Список намерений:\n"
                for intent, translation in self.INTENTS.items():
                    response += f"{intent} - {translation}\n"
                self.log_admin_activity("User requested intents", message.chat.id)
                self.bot.reply_to(message, response)
            except Exception as e:
                self.handle_error(message, e)

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            try:
                user_input = message.text
                response, confidence, intent, intent_id, inputs = self.assistant_manager.process_input(user_input)
                bot_reply = self.bot.reply_to(message, f"Бот: {response}\nУверенность: {confidence:.2f}\nНамерение: {intent}\nintent_id: {intent_id}\ninputs: {inputs}")

                markup = ReplyKeyboardMarkup(row_width=5, resize_keyboard=True, one_time_keyboard=True)
                markup.add(KeyboardButton('1'), KeyboardButton('2'), KeyboardButton('3'), KeyboardButton('4'), KeyboardButton('5'))
                msg_rating = self.bot.send_message(message.chat.id, "Оцените ответ (1-5):", reply_markup=markup)


                self.bot.register_next_step_handler(msg_rating, process_rating, user_input, response, intent, confidence, bot_reply, msg_rating)

                time.sleep(1)
                self.bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                self.handle_error(message, e)

        def process_rating(message, user_input, response, intent, confidence, bot_reply, msg_rating):
            try:
                rating = int(message.text)
                markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
                for intent_name, translation in self.INTENTS.items():
                    markup.add(KeyboardButton(intent_name))

                msg_intent = self.bot.send_message(message.chat.id, "Какое намерение вы ожидали?", reply_markup=markup)

                self.bot.register_next_step_handler(msg_intent, process_expected_intent, user_input, response, rating, intent, confidence, bot_reply, msg_rating, msg_intent)

                time.sleep(1)
                self.bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                self.handle_error(message, e)


        def process_expected_intent(message, user_input, response, rating, intent, confidence, bot_reply, msg_rating, msg_intent):
            try:
                expected_intent = message.text
                if expected_intent not in self.INTENTS:
                    self.bot.reply_to(message, "Некорректное намерение. Пожалуйста, попробуйте еще раз.")
                    return

                self.assistant_manager.save_user_feedback(user_input, response, rating, intent, expected_intent, confidence)

                thank_you_msg = self.bot.send_message(message.chat.id, "Спасибо за ваш отзыв!", reply_markup=ReplyKeyboardRemove())

                time.sleep(1)
                self.bot.delete_message(message.chat.id, bot_reply.message_id)
                self.bot.delete_message(message.chat.id, msg_rating.message_id)
                self.bot.delete_message(message.chat.id, msg_intent.message_id)
                self.bot.delete_message(message.chat.id, thank_you_msg.message_id)
                self.bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                self.handle_error(message, e)


    def log_admin_activity(self, activity, user_id):
        logger.info(f"Admin Activity: {activity} by User ID: {user_id}")

    def handle_error(self, message, error):
        logger.error(f"An error occurred: {error}", exc_info=True)
        error_message = "Произошла ошибка. Пожалуйста, попробуйте еще раз позже."
        self.bot.reply_to(message, error_message)

    def run(self):
        logger.info("Bot is starting...")
        while True:
            try:
                self.bot.polling(none_stop=True, interval=0)
            except apihelper.ApiException as e:
                logger.error(f"API error occurred: {e}")
                time.sleep(15)  
            except Exception as e:
                logger.critical(f"Critical error: {e}", exc_info=True)
                time.sleep(15) 

if __name__ == '__main__':
    bot = TelegramBot(TELEGRAM_BOT_API_KEY)
    bot.run()
