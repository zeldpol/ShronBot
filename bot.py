import os
import telebot as tb

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = tb.TeleBot(BOT_TOKEN)
default_sticker = 'CAACAgIAAxkBAAMkY88BJRnBwyokVQ6BzCq6SgHs0NEAAuEAA7I2kBle3L5OTD-jGC0E'
bot_info = bot.get_me()
welcome_text= "Welcome to the club, buddy! Send me a sticker from any pack and I'll create you your own personal pack. If you send me a sticker from this pack, I'll delete it. Enjoy"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=["sticker"])
def sticker(message):
    pack_name = f"{message.from_user.username}_by_{bot_info.username}"
    try:
        bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)
    except:
        print("1")
    if bot.get_sticker_set(pack_name):
        if message.sticker.set_name == pack_name:
            bot.delete_sticker_from_set(message.sticker.file_id)
            bot.send_message(message.chat.id, "Deleted!")
        else:
            bot.add_sticker_to_set(message.from_user.id, pack_name, message.sticker.emoji, message.sticker.file_id)
    else:
        bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)

    bot.send_message(message.chat.id, f"t.me/addstickers/{pack_name}")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.send_message(message.chat.id, 'pong')

bot.infinity_polling()

