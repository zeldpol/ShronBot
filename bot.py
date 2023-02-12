import os
import telebot as tb
from PIL import Image
import io


BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = tb.TeleBot(BOT_TOKEN)
bot_info = bot.get_me()

MAX_IMAGE_SIZE = 512
MAX_VN_LEN = 3

welcome_text = """Welcome to the club, buddy! 
* I'll create your own personalised pack by sending you a static or animated sticker from any pack. Note: Animated stickers and static stickers are stored in separate sets of stickers. 
* Send me a sticker from our set, I'll delete it. 
* Send me an image. I'll add it to your static set.
Enjoy!"""


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, welcome_text)


@bot.message_handler(content_types=["sticker"])
def sticker(message):
    if message.sticker.is_animated:
        file_info = bot.get_file(message.sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        add_or_delete_sticker(
            message, png_sticker=None, tgs_sticker=downloaded_file, webm_sticker=None
        )
    else:
        add_or_delete_sticker(
            message,
            png_sticker=message.sticker.file_id,
            tgs_sticker=None,
            webm_sticker=None,
        )


def add_or_delete_sticker(
    message, emoji=None, png_sticker=None, tgs_sticker=None, webm_sticker=None
):
    assert (
        bool(tgs_sticker) != bool(png_sticker) != bool(webm_sticker)
    ), "Exactly one of tgs_sticker, png_sticker or webm_sticker should be passed"
    if not emoji:
        emoji = message.sticker.emoji
    if message.sticker.set_name == get_pack_name(message):
        del_sticker(message)
    else:
        add_sticker(
            message,
            emoji=emoji,
            tgs_sticker=tgs_sticker,
            png_sticker=png_sticker,
            webm_sticker=webm_sticker,
        )


def add_sticker(message, emoji, tgs_sticker, png_sticker, webm_sticker):
    pack_name = get_pack_name(message)
    try:
        bot.add_sticker_to_set(
            message.from_user.id,
            pack_name,
            emojis=emoji,
            png_sticker=png_sticker,
            tgs_sticker=tgs_sticker,
            webm_sticker=webm_sticker,
        )
        bot.send_message(
            message.chat.id, f"Sticker added! t.me/addstickers/{pack_name}"
        )
    except tb.apihelper.ApiTelegramException as e:
        if e.description.strip() == "Bad Request: STICKERSET_INVALID":
            bot.create_new_sticker_set(
                message.from_user.id,
                pack_name,
                pack_name,
                emoji,
                png_sticker=png_sticker,
                tgs_sticker=tgs_sticker,
                webm_sticker=webm_sticker,
            )
            bot.send_message(
                message.chat.id,
                f"New sticker set created. Sticker added! t.me/addstickers/{pack_name}",
            )
        else:
            raise e


def get_pack_name(message):
    if message.video_note or message.sticker.is_video:
        return f"vn_{message.from_user.username}_by_{bot_info.username}"
    elif message.sticker and message.sticker.is_animated:
        return f"animated_{message.from_user.username}_by_{bot_info.username}"
    else:
        return f"static_{message.from_user.username}_by_{bot_info.username}"


def del_sticker(message):
    try:
        bot.delete_sticker_from_set(message.sticker.file_id)
        bot.send_message(
            message.chat.id, f"Deleted! t.me/addstickers/{get_pack_name(message)}"
        )
    except tb.apihelper.ApiTelegramException as e:
        if e.description.strip() == "Bad Request: STICKERSET_NOT_MODIFIED":
            error_hanlder(message, "The sticker does not exist, restart the client")
        else:
            raise e


@bot.message_handler(content_types=["photo"])
def image2sticker(message):
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    resized_image = resize(downloaded_file)
    add_sticker(
        message,
        emoji="😃",
        png_sticker=resized_image,
        tgs_sticker=None,
        webm_sticker=None,
    )


def resize(downloaded_file: bytes):
    image = Image.open(io.BytesIO(downloaded_file))
    image_format = image.width / image.height
    if image.width == image.height:
        new_image = image.resize((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    elif image_format > 1:
        new_image = image.resize((MAX_IMAGE_SIZE, int(MAX_IMAGE_SIZE / image_format)))
    else:
        new_image = image.resize((int(MAX_IMAGE_SIZE * image_format), MAX_IMAGE_SIZE))
    img_byte_arr = io.BytesIO()
    new_image.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()


@bot.message_handler(content_types=["video_note"])
def vn2sticker(message):
    fileID = message.video_note.file_id
    file_info = bot.get_file(fileID)
    ln = int(message.video_note.length / 1.41)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("tmp/video_note.mp4", "wb") as new_file:
        new_file.write(downloaded_file)
    if code := os.system(
        f"ffmpeg -i tmp/video_note.mp4 -c copy -map 0 -segment_time {MAX_VN_LEN} -f segment -reset_timestamps 1 tmp/video_note%d.mp4"
    ):
        error_hanlder(message, f"BONK, something wrong! ffmpeg returned code {code}")

    for i in range(int(message.video_note.duration / MAX_VN_LEN)):
        if code := os.system(
            f'ffmpeg -i tmp/video_note{i}.mp4 -y -vf "crop={ln}:{ln},scale={MAX_IMAGE_SIZE}:{MAX_IMAGE_SIZE}" -c:v libvpx-vp9 -crf 30 -b:v 0 -b:a 128k -loop 0 -an tmp/output{i}.webm'
        ):
            error_hanlder(
                message, f"BONK, something wrong! ffmpeg returned code {code}"
            )
        else:
            with open(f"tmp/output{i}.webm", "rb") as video_file:
                video = video_file.read()
                add_sticker(
                    message,
                    emoji="😃",
                    png_sticker=None,
                    tgs_sticker=None,
                    webm_sticker=video,
                )


def error_hanlder(message, error_message):
    bot.send_message(message.chat.id, error_message)
    with open("resources/error.jpg", "rb") as img:
        error_ing = img.read()
    bot.send_photo(message.chat.id, photo=error_ing)


@bot.message_handler(func=lambda msg: True)
def echo_text(message):
    bot.send_message(message.chat.id, "pong")


bot.infinity_polling()
