import os
import telebot as tb
from PIL import Image

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = tb.TeleBot(BOT_TOKEN)
bot_info = bot.get_me()
welcome_text= "Welcome to the club, buddy! Send me a sticker from any pack and I'll create you your own personal pack. If you send me a sticker from this pack, I'll delete it. Enjoy"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=["sticker"])
def sticker(message):
    if message.sticker.is_animated:
        pack_name = f"animated_{message.from_user.username}_by_{bot_info.username}"
        file_info = bot.get_file(message.sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, tgs_sticker = downloaded_file)
        except:
            print("1")
        if bot.get_sticker_set(pack_name):
            if message.sticker.set_name == pack_name:
                bot.delete_sticker_from_set(message.sticker.file_id)
                bot.send_message(message.chat.id, "Deleted!")
            else:
                bot.add_sticker_to_set(message.from_user.id, pack_name, message.sticker.emoji,tgs_sticker = downloaded_file)
        else:
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji,tgs_sticker = downloaded_file)

    else:
        pack_name = f"static_{message.from_user.username}_by_{bot_info.username}"
        try:
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)
        except:
            print("2")
        if bot.get_sticker_set(pack_name):
            if message.sticker.set_name == pack_name:
                bot.delete_sticker_from_set(message.sticker.file_id)
                bot.send_message(message.chat.id, "Deleted!")
            else:
                bot.add_sticker_to_set(message.from_user.id, pack_name, message.sticker.emoji, message.sticker.file_id)
        else:
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)

    bot.send_message(message.chat.id, f"t.me/addstickers/{pack_name}")


@bot.message_handler(content_types=["photo"])
def image2sticker(message):
    #print('message.photo =', message.photo)
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    #print('file.file_path =', file_info.file_path)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.png", 'wb') as new_file:
        new_file.write(downloaded_file)

    image = Image.open('image.png')
    image_format = image.width/image.height
    #print(image.width, image.height, image_format)
    if image_format  == 1:
        new_image = image.resize((512, 512))
    elif image_format > 1:
        new_image = image.resize((512, int(512/image_format)))
    else:
        new_image = image.resize((int(512*image_format), 512))
    new_image.save('image_512.png')

    with open('image_512.png', 'rb') as file:
        upload_image = file.read()

    pack_name = f"static_{message.from_user.username}_by_{bot_info.username}"
    try:
        bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)
    except:
        print("3")
    if bot.get_sticker_set(pack_name):
        bot.add_sticker_to_set(message.from_user.id, pack_name, "😀", upload_image)
    else:
        bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, message.sticker.emoji, message.sticker.file_id)
    bot.send_message(message.chat.id, f"t.me/addstickers/{pack_name}")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.send_message(message.chat.id, "pong")


bot.infinity_polling()

