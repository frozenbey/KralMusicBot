import os
import json
import ffmpeg
import aiohttp
import aiofiles
import asyncio
import requests
import converter
from os import path
from asyncio.queues import QueueEmpty
from pyrogram import Client, filters
from typing import Callable
from helpers.channelmusic import get_chat_id
from callsmusic import callsmusic
from callsmusic.queues import queues
from helpers.admins import get_administrators
from youtube_search import YoutubeSearch
from callsmusic.callsmusic import client as USER
from pyrogram.errors import UserAlreadyParticipant
from downloaders import youtube

from config import que, THUMB_IMG, DURATION_LIMIT, BOT_USERNAME, BOT_NAME, UPDATES_CHANNEL, GROUP_SUPPORT, ASSISTANT_NAME
from helpers.filters import command, other_filters
from helpers.decorators import authorized_users_only
from helpers.gets import get_file_name, get_url
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Voice
from cache.admins import admins as a
from PIL import Image, ImageFont, ImageDraw

aiohttpsession = aiohttp.ClientSession()
chat_id = None
DISABLED_GROUPS = []
useer ="NaN"


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("İzin yok. 🤦‍♀️ sadece Yöneticiler.!", show_alert=True)
            return
    return decorator                                                                       
                                          
                                                                                    
def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw",
        format="s16le",
        acodec="pcm_s16le",
        ac=2,
        ar="48k"
    ).overwrite_output().run() 
    os.remove(filename)

# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()
    image1 = Image.open("./background.png")
    image2 = Image.open("etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 60)
    draw.text((40, 550), f"Oynatılıyor....", (0, 0, 0), font=font)
    draw.text((40, 630),
        f"{title}",
        (0, 0, 0),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(command(["playlist", "bilgi"]) & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("**Akışta hiçbir şey yok!**")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**İstenilen Şarkılar**  {}".format(message.chat.title)
    msg += "\n• "+ now_playing
    msg += "\n• İstek üzerine "+by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Sırası**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n• {name}"
            msg += f"\n• Atas permintaan {usr}\n"
    await message.reply_text(msg)

# ============================= Ayar Menüsü Hoşgeldin =========================================
def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        stats = "Ayarlar **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "🎶 Ses: {}%\n".format(vol)
            stats += "🎵 Sırada şarkılar: `{}`\n".format(len(que))
            stats += "👨‍💼 Sanatçı ismi: **{}**\n".format(queue[0][0])
            stats += "👤 Talep eden: {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats

def r_ply(type_):
    if type_ == "oynat":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "son"),
                InlineKeyboardButton("⏸", "durdur"),
                InlineKeyboardButton("▶️", "devam"),
                InlineKeyboardButton("⏭", "atla")
            ],
            [
                InlineKeyboardButton("📖  Bilgiler", "playlist"),
            ],
            [       
                InlineKeyboardButton("❎ Kapat", "cls")
            ]        
        ]
    )
    return mar


@Client.on_message(command(["player"]) & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    playing = None
    if message.chat.id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))
            
        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("**Lütfen önce sesli sohbeti açın.**")


@Client.on_message(
    command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "**Sadece biliyorum. ** `/müzik çalar açık` **ve** `/Müzik çalar kapalı`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`İşleme Alıdm...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("**Müzik çalar zaten etkinleştirildi.**")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"✅ **Müzik çalar bu sohbette etkinleştirildi.** {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`İşleniyor...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("**Müzik çalar zaten devre dışı.**")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"✅ **Müzik çalar bu sohbette devre dışı bırakıldı.** {message.chat.id}"
        )
    else:
        await message.reply_text(
            "**Sadece biliyorum.** `/müzik çalar açık` **ve** `/müzik çalar kapalı`"
        )


@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que    
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("**Hiçbir şey oynamıyor.❗**")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Şimdi yürütülen**  {}".format(cb.message.chat.title)
        msg += "\n• " + now_playing
        msg += "\n• Talep eden kişi " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Sırası**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n• {name}"
                msg += f"\n• Req by {usr}\n"
        await cb.message.edit(msg)      


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|durdur|atla|son|puse|devam|menü|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que   
    if (
        cb.message.chat.title.startswith("Kanal Müziği: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if (
            chet_id not in callsmusic.pytgcalls.active_calls
                ) or (
                    callsmusic.pytgcalls.active_calls[chet_id] == "paused"
                ):
            await cb.answer("Asistan sesli sohbete bağlı değil!", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)
            
            await cb.answer("Müzik duraklatıldı!")
            await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply("play"))
                
    elif type_ == "play":       
        if (
            chet_id not in callsmusic.pytgcalls.active_calls
            ) or (
                callsmusic.pytgcalls.active_calls[chet_id] == "playing"
            ):
                await cb.answer("Asistan sesli sohbete bağlı değil!", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Müzik devam etti!")
            await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply("pause"))

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:   
            await cb.message.edit("Akışta hiçbir şey yok!")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Çalınan Şarkılar** di {}".format(cb.message.chat.title)
        msg += "\n• "+ now_playing
        msg += "\n• İstek üzerine "+by
        temp.pop(0)
        if temp:
             msg += "\n\n"
             msg += "**Şarkı Sırası**"
             for song in temp:
                 name = song[0]
                 usr = song[1].mention(style="md")
                 msg += f"\n• {name}"
                 msg += f"\n• İstek üzerine {usr}\n"
        await cb.message.edit(msg)      
                      
    elif type_ == "devam":     
        if (
            chet_id not in callsmusic.pytgcalls.active_calls
            ) or (
                callsmusic.pytgcalls.active_calls[chet_id] == "playing"
            ):
                await cb.answer("Sesli sohbet bağlı değil veya zaten oynatılıyor", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Müzik devam etti!")
     
    elif type_ == "durdur":         
        if (
            chet_id not in callsmusic.pytgcalls.active_calls
                ) or (
                    callsmusic.pytgcalls.active_calls[chet_id] == "paused"
                ):
            await cb.answer("Sesli sohbet bağlı değil veya zaten duraklatıldı", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)
            
            await cb.answer("Müzik duraklatıldı!")

    elif type_ == "cls":          
        await cb.answer("Menü kapalı")
        await cb.message.delete()       

    elif type_ == "menü":  
        stats = updated_stats(cb.message.chat, qeue)  
        await cb.answer("Menü ve Butonlar")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "son"),
                    InlineKeyboardButton("⏸", "durdur"),
                    InlineKeyboardButton("▶️", "devam"),
                    InlineKeyboardButton("⏭", "atla")
                
                ],
                [
                    InlineKeyboardButton("📖 Bilgiler", "playlist"),
                
                ],
                [       
                    InlineKeyboardButton("❌ Kapat", "cls")
                ]        
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)

    elif type_ == "atla":        
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.pytgcalls.active_calls:
            await cb.answer("Asistan sesli sohbete bağlı değil!", show_alert=True)
        else:
            callsmusic.queues.task_done(chet_id)

            if callsmusic.queues.is_empty(chet_id):
                callsmusic.pytgcalls.leave_group_call(chet_id)

                await cb.message.edit("• No more playlist\n• Sesli sohbeti bırakma")
            else:
                callsmusic.pytgcalls.change_stream(
                    chet_id, callsmusic.queues.get(chet_id)["file"]
                )
                await cb.answer("Atlatıldı")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"⫸ Atlatılan parça\n⫸ Şimdi oynatıyor: **{qeue[0][0]}**"
                )

    elif type_ == "son":
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass

            callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit("⏹ **Müzik durduruldu!**")
        else:
            await cb.answer("Asistan sesli sohbete bağlı değil!", show_alert=True)



@Client.on_message(command("play") & other_filters)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return    
    lel = await message.reply("🔁 **Sesler işleniyor...**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "TaliaMusicProject"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>Eklemeyi unutmayın {user.first_name} kanalınıza</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Önce beni grup yöneticisi olarak ekle</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "Sesli sohbette bir şarkı çalmak için katıldım!"
                    )
                    await lel.edit(
                        "<b>yardımcı userbot sohbetinize katıldı</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Taşan Bekleme Hatası! ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nVeya @Sesmusicasistan grubunuza el ile el ile ve yeniden deneyin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} Bu Grubun yasağından etkilenerek, yöneticiden bir komut göndermesini isteyin `/play` ilk kez veya ekleyin @TaliaMusicasistant Elle</i>"
        )
        return
    text_links=None
    await lel.edit("🔁 **İşleniyor..**")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"**Süresi daha fazla olan şarkılar ** `{DURATION_LIMIT}` **Süresi Fazla hata verebilir!**"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏏️ Butonlar", callback_data="menü"),
                    InlineKeyboardButton("❌ Kapat", callback_data="cls"),
                ],[
                    InlineKeyboardButton("🇩🇪 Resmi Kanal", url=f"https://t.me/TeamAlmanSexy")
                ],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/fa2cdb8a14a26950da711.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Yerel olarak eklendi"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🗃️ **Aranıyor ve İşleniyor...**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:25]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "**Şarkı bulunamadı.** Daha net bir başlık parçası aramayı deneyin, Yaz `/help` Yardıma ihtiyacın olursa."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏏️ Butonlar", callback_data="menü"),
                    InlineKeyboardButton("⛔ Kapat", callback_data="cls"),
                ],[
                    InlineKeyboardButton("🇩🇪 Resmi Kanal", url=f"https://t.me/TeamAlmanSexy")
                ],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("📥 **İndiriyorum..**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        
        try:
          results = YoutubeSearch(query, max_results=7).to_dict()
        except:
          await lel.edit("**Bana çalmak istediğin şarkının adını ver. !**")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "**__Lütfen çalmak istediğiniz şarkıyı seçin__⚡**\n\n"
            j = 0
            useer=user_name

            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
            while j < 7:
                toxxt += f"{emojilist[j]} [{results[j]['title'][:25]}](https://youtube.com{results[j]['url_suffix']})\n"
                toxxt += f" ├ 🕛 **Süresi** - {results[j]['duration']}\n"
                toxxt += f" └ 🎶 __Sizin için En iyisi @SohbetDestek__\n\n"

                j += 1            
            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}'),    
                    ],
                    [
                        InlineKeyboardButton("6️⃣", callback_data=f'plll 5|{query}|{user_id}'),
                        InlineKeyboardButton("7️⃣", callback_data=f'plll 6|{query}|{user_id}'),
                    ],
                    [InlineKeyboardButton(text="⛔ Kapat", callback_data="cls")],
                ]
            )     
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            # WHY PEOPLE ALWAYS LOVE PORN ?? (A point to think)
            return
            # Returning to pornhub
        except:
            await lel.edit("**Aralarından seçim yapabileceğiniz yeterli sonuç yok...Otomatik başlatıyorum..**")
                        
            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:25]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                "**Şarkı bulunamadı.** Daha net bir başlık parçası aramayı deneyin, Yaz `/help` Yardıma ihtiyacın olursa."
            )
                print(str(e))
                return
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
                    [
                [
                    InlineKeyboardButton("⏏️ Butonlar", callback_data="menü"),
                    InlineKeyboardButton("⛔ Kapat", callback_data="cls"),
                ],[
                    InlineKeyboardButton("🇩🇪 Resmi Kanal", url=f"https://t.me/TeamAlmanSexy")
                ],
            ]
        )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption = f"🎵 **İsmi:** [{title[:30]}]({url})\n⏱ **Süre:** {duration}\n💡 **Durum:** Sıraya Alma `{position}`\n" \
                    + f"👨‍💼 **İstek:** {message.from_user.mention}",
                   reply_markup=keyboard)
       
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("**Sesli Sohbet Grubu kapalı, Katılamam.**")
            return
        await message.reply_photo(
            photo="final.png",
            caption = f"🎵 **İsmi:** [{title[:30]}]({url})\n⏱ **Süre:** {duration}\n💡 **Durum:** Oynatılıyor\n" \
                    + f"👨‍💼 **İstek:** {message.from_user.mention}",
                   reply_markup=keyboard)

    os.remove("final.png")
    return await lel.delete()


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que
    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("❌ Şarkı bulunamadı")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("Siz bu şarkıyı isteyen insanlar değilsiniz.!", show_alert=True)
        return
    #await cb.message.edit("🔁 **Hazırlanıyor...**")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    results = YoutubeSearch(query, max_results=6).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:25]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://www.youtube.com{resultss}"
    try:    
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
             await cb.message.edit(f"❌ Süresi daha fazla olan şarkılar `{DURATION_LIMIT}` dakika çalınamaz.")
             return
    except:
        pass
    try:
        thumb_name = f"thumb-{title}cybermusic.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube", "youtubepp")
    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏏️ Butonlar", callback_data="menü"),
                    InlineKeyboardButton("❌ Kapat", callback_data="cls"),
                ],[
                    InlineKeyboardButton("🇩🇪 Resmi Kanal", url=f"https://t.me/TeamAlmanSexy")
                ],
            ]
    )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await converter.convert(youtube.download(url))  
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(
        chat_id,
        photo="final.png",
        caption=f"💡 **Kuyruğa eklenen parça**\n\n🎵 **İsmi:** [{title[:35]}]({url})\n⏱ **Süre:** `{duration}`\n👨‍💼 **İstek:** {r_by.mention}\n" \
               +f"🔢 **Konumda:** » `{position}` «",
        reply_markup=keyboard,
        )
        os.remove("final.png")
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        await cb.message.delete()
        await b.send_photo(
        chat_id,
        photo="final.png",
        caption=f"🎵 **İsmi:** [{title[:35]}]({url})\n⏱ **Süre:** `{duration}`\n💡 **Durum:** `Oynatılıyor`\n" \
               +f"👨‍💼 **İstek:** {r_by.mention}",
        reply_markup=keyboard,
        )
        os.remove("final.png")
 
