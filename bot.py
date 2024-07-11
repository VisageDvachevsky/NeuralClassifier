import telebot
from TGManager import TelegramAssistantManager
from telebot import types
from env import token

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot = telebot.TeleBot(token)

# Initialize the TelegramAssistantManager
model_dir = ''  # Adjust the path as needed
assistant_manager = TelegramAssistantManager(model_dir=model_dir)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = "Hello! I'm your assistant. Here are the intents I support:\n"
    help_text += "\n".join(assistant_manager.response_generator.intent_labels.values())
    help_text += "\n\nYou can start by typing any query."
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    response, confidence, intent = assistant_manager.process_input(user_input)
    bot.reply_to(message, f"Response: {response}\nConfidence: {confidence:.2f}\nIntent: {intent}")

    # Ask for feedback
    msg = bot.reply_to(message, "Please rate the response (1-5):")
    bot.register_next_step_handler(msg, lambda msg: save_feedback(msg, user_input, response, intent, confidence))

def save_feedback(message, user_input, response, intent, confidence):
    try:
        rating = int(message.text)
        if not (1 <= rating <= 5):
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Invalid rating. Please enter a number between 1 and 5.")
        return
    
    expected_intent = assistant_manager.response_generator.intent_labels[intent] if intent is not None else "unknown"
    assistant_manager.save_interaction(user_input, response, rating, intent, expected_intent, confidence)
    bot.reply_to(message, "Thank you for your feedback!")

if __name__ == '__main__':
    bot.polling(none_stop=True)