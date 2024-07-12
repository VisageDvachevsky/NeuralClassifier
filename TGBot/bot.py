import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telebot import apihelper
from TGmanager import BotAssistantManager
from DB.database import save_rating, create_database
from env import TELEGRAM_BOT_API_KEY
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, api_key):
        self.bot = telebot.TeleBot(api_key)
        self.assistant_manager = BotAssistantManager()
        self.INTENTS = {
            'get_time': 'узнать время',
            'get_date': 'узнать дату',
            'greet': 'приветствие',
            'goodbye': 'прощание'
        }
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            try:
                self.log_admin_activity("User started interaction", message.chat.id)
                self.bot.reply_to(
                    message,
                    "Напишите сообщение, чтобы начать. "
                    "Используйте /help для списка доступных команд.\n"
                    "Версия: alpha:0.1"
                )
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
                bot_reply = self.bot.reply_to(
                    message,
                    f"Бот: {response}\nУверенность: {confidence:.2f}\nНамерение: {intent}\n"
                    f"intent_id: {intent_id}\ninputs: {inputs}"
                )

                markup = ReplyKeyboardMarkup(row_width=5, resize_keyboard=True, one_time_keyboard=True)
                markup.add(
                    KeyboardButton('1'), KeyboardButton('2'), 
                    KeyboardButton('3'), KeyboardButton('4'), 
                    KeyboardButton('5')
                )
                msg_rating = self.bot.send_message(
                    message.chat.id, 
                    "Оцените ответ (1-5):", 
                    reply_markup=markup
                )

                # Сохранение контекста для идентификации оценки
                self.bot.register_next_step_handler(
                    msg_rating, self.process_rating, user_input, response, intent, confidence, bot_reply, msg_rating
                )

                # Удаление сообщения пользователя через секунду
                self.schedule_delete(message.chat.id, message.message_id, 1)
            except Exception as e:
                self.handle_error(message, e)

        def process_rating(self, message, user_input, response, intent, confidence, bot_reply, msg_rating):
            try:
                rating = int(message.text)
                markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
                for intent_name, translation in self.INTENTS.items():
                    markup.add(KeyboardButton(intent_name))

                msg_intent = self.bot.send_message(
                    message.chat.id, 
                    "Какое намерение вы ожидали?", 
                    reply_markup=markup
                )

                # Сохранение контекста для идентификации ожидаемого намерения
                self.bot.register_next_step_handler(
                    msg_intent, self.process_expected_intent, user_input, response, rating, intent, confidence, bot_reply, msg_rating, msg_intent
                )

                # Удаление сообщения с запросом оценки через секунду
                self.schedule_delete(message.chat.id, message.message_id, 1)
            except Exception as e:
                self.handle_error(message, e)

        def process_expected_intent(self, message, user_input, response, rating, intent, confidence, bot_reply, msg_rating, msg_intent):
            try:
                expected_intent = message.text
                self.assistant_manager.save_user_feedback(user_input, response, rating, intent, expected_intent, confidence)

                thank_you_msg = self.bot.send_message(
                    message.chat.id, 
                    "Спасибо за ваш отзыв!", 
                    reply_markup=ReplyKeyboardRemove()
                )

                # Удаление всех соответствующих сообщений с интервалом
                self.schedule_delete(message.chat.id, bot_reply.message_id, 1)
                self.schedule_delete(message.chat.id, msg_rating.message_id, 2)
                self.schedule_delete(message.chat.id, msg_intent.message_id, 3)
                self.schedule_delete(message.chat.id, thank_you_msg.message_id, 4)
                self.schedule_delete(message.chat.id, message.message_id, 5)
            except Exception as e:
                self.handle_error(message, e)

    def schedule_delete(self, chat_id, message_id, delay):
        threading.Timer(delay, lambda: self.bot.delete_message(chat_id, message_id)).start()

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
                time.sleep(15)  # Avoid hitting API rate limits
            except Exception as e:
                logger.critical(f"Critical error: {e}", exc_info=True)
                time.sleep(15)  # Give some time before restarting polling


if __name__ == '__main__':
    bot = TelegramBot(TELEGRAM_BOT_API_KEY)
    bot.run()
