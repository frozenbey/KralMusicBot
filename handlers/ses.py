# İster "https://t.me/{ASSISTANT_NAME}" Şeklinde yapın... App.json içini deki yerleri doldurun.. 
# Yazdım örnek gibi de yapabilirsiniz. Katılmak için @SohbetDestek 

from os import path

from pyrogram import Client
from pyrogram.types import Message, Voice

from callsmusic import callsmusic, queues

from converter import converter
from downloaders import youtube

from config import BOT_NAME, DURATION_LIMIT, UPDATES_CHANNEL,GROUP_SUPPORT
from helpers.filters import command, other_filters
from helpers.decorators import errors
from helpers.errors import DurationLimitError
from helpers.gets import get_url, get_file_name
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@Client.on_message(command("oynat") & other_filters)
@errors
async def oynat(_, message: Message):

    lel = await message.reply("🔁 **Başlatılıyor**.. 🔥")
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🇩🇪 RESMİ KANAL", url=f"https://t.me/TeamAlmanSexy"
                ),
            ]
        ]
    )


    audio = (message.reply_to_message.audio or message.reply_to_message.voice) if message.reply_to_message else None
    url = get_url(message)

    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ Daha uzun videolar {DURATION_LIMIT} dakikaların oynamasına izin verilmez!"
            )

        file_name = get_file_name(audio)
        file_path = await converter.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name)) else file_name
        )
    elif url:
        file_path = await converter.convert(youtube.download(url))
    else:
        return await lel.edit_text("Bana ses dosyası veya yt bağlantısı vermediniz!")

    if message.chat.id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(message.chat.id, file=file_path)
        costumer = message.from_user.mention
        await message.reply_photo(
        photo=f"https://telegra.ph/file/06128b8298df70f2d3c5f.jpg",
        reply_markup=keyboard,
        caption=f"🔢 **Sıraya  alınan parça **\n\n🎧 **İstek**: {costumer}\n♻️ **Parça konumu**: » `{position}` «")
        return await lel.delete()
    else:
        callsmusic.pytgcalls.join_group_call(message.chat.id, file_path)
        costumer = message.from_user.mention
        await message.reply_photo(
        photo=f"https://telegra.ph/file/06128b8298df70f2d3c5f.jpg",
        reply_markup=keyboard,
        caption=f"💡 **Durum**: **Oynatılıyor**\n\n🎧 **İstek:**: {costumer}\n🎛️ **Talia müzik tarafından**\nKeyifli Dinlemeler 🥰"
        )
        return await lel.delete()
