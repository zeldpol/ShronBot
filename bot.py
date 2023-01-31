import os
import telebot as tb
from PIL import Image
import io
import requests


BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = tb.TeleBot(BOT_TOKEN)
bot_info = bot.get_me()
MAX_IMAGE_SIZE = 512
welcome_text= "Welcome to the club, buddy! Send me a sticker from any pack and I'll create you your own personal pack. If you send me a sticker from this pack, I'll delete it. Enjoy"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=["sticker"])
def sticker(message):
    if message.sticker.is_animated:
        file_info = bot.get_file(message.sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        add_or_delete_sticker(message, tgs_sticker=downloaded_file)
    else:
        add_or_delete_sticker(message, png_sticker=message.sticker.file_id)


def add_or_delete_sticker(message, tgs_sticker=None, png_sticker=None, emoji=None):
    assert bool(tgs_sticker) != bool(png_sticker), "exactly one of tgs_sticker and png_sticker should be passed" 
    if not emoji:
        emoji = message.sticker.emoji
    if message.sticker.set_name == get_pack_name(message):
        del_sticker(message)
    else:
        add_sticker(message, tgs_sticker, png_sticker, emoji=emoji)


def add_sticker(message, tgs_sticker, png_sticker, emoji):
    pack_name = get_pack_name(message)
    try:
        bot.add_sticker_to_set(message.from_user.id, pack_name, emojis=emoji, tgs_sticker=tgs_sticker, png_sticker=png_sticker)
        bot.send_message(message.chat.id, f"Sticker added! t.me/addstickers/{pack_name}")
    except tb.apihelper.ApiTelegramException as e:
        if e.description.strip() == 'Bad Request: STICKERSET_INVALID':
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, emoji, tgs_sticker=tgs_sticker)
            bot.send_message(message.chat.id, f"New stickerset created. Sticker added! t.me/addstickers/{pack_name}")
        else:
            raise e

def get_pack_name(message):
    if message.sticker and message.sticker.is_animated:
        return f"animated_{message.from_user.username}_by_{bot_info.username}"    
    return f"static_{message.from_user.username}_by_{bot_info.username}"

def del_sticker(message):
    bot.delete_sticker_from_set(message.sticker.file_id)
    bot.send_message(message.chat.id, f"Deleted! t.me/addstickers/{get_pack_name(message)}")


@bot.message_handler(content_types=["photo"])
def image2sticker(message):
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    resized_image = resize(downloaded_file)
    add_sticker(message, tgs_sticker=None, png_sticker=resized_image, emoji="😃")


def resize(downloaded_file: bytes):
    image = Image.open(io.BytesIO(downloaded_file))
    image_format = image.width/image.height
    if image.width ==image.height:
        new_image = image.resize((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    elif image_format > 1:
        new_image = image.resize((MAX_IMAGE_SIZE, int(MAX_IMAGE_SIZE/image_format)))
    else:
        new_image = image.resize((int(MAX_IMAGE_SIZE*image_format), MAX_IMAGE_SIZE))
    img_byte_arr = io.BytesIO()
    new_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
     


@bot.message_handler(content_types=['video_note'])
def vn2sticker(message):
    print(message)
    fileID = message.video_note.file_id
    file_info = bot.get_file(fileID)
    ln = int(message.video_note.length / 1.41)
    print(message.video_note.length, ln)
    downloaded_file = bot.download_file(file_info.file_path)
    pack_name = f"nv_by_{bot_info.username}"
    with open("tmp/video_note.mp4", 'wb') as new_file:
        new_file.write(downloaded_file)
    if code := os.system(f'ffmpeg -i tmp/video_note.mp4 -vf "crop={ln}:{ln},scale=512:512" -y tmp/output.mp4'):
        bot.send_message(message.chat.id, f'BONK, something wrong! *бунт.jpg*, ffmpeg returned code {code}')
    elif code := os.system('ffmpeg -i tmp/output.mp4 -y -c:v libvpx-vp9 -crf 30 -b:v 0 -b:a 128k -loop 0 -an -c:a libopus tmp/output.webm'):
        bot.send_message(message.chat.id, f'BONK, something wrong! *бунт2.jpg*, ffmpeg returned code {code}')
    else:
        with  open('tmp/output.webm', 'rb') as video_file:
            video = video_file.read()
            bot.create_new_sticker_set(message.from_user.id, pack_name, pack_name, "😀", webm_sticker = video)
        bot.send_message(message.chat.id, f"t.me/addstickers/{pack_name}")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.send_message(message.chat.id, "pong")

bot.infinity_polling()

