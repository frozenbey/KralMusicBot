from time import time
from datetime import datetime
from config import BOT_USERNAME, BOT_NAME, ASSISTANT_NAME, OWNER_NAME, UPDATES_CHANNEL, GROUP_SUPPORT
from helpers.filters import command
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helpers.decorators import authorized_users_only


START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ('week', 60 * 60 * 24 * 7),
    ('day', 60 * 60 * 24),
    ('hour', 60 * 60),
    ('min', 60),
    ('sec', 1)
)

async def _human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'
                         .format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)


@Client.on_message(command("start") & filters.private & ~filters.edited)
async def start_(client: Client, message: Message):
    await message.reply_text(
        f"""<b>✨ **Merhabalar {message.from_user.first_name}** \n
🎯 **[Kral Müzik](https://t.me/TeamAlmanSexy) Telegramın Sesli sohbetinde bana, Müzik çalmam için izin veriniz.**

🔮 **Üzerine tıklayarak komutları çalıştırın ve ögreniniz.**

❓ **Bu botun tüm özellikleri hakkında bilgi almak için, basınız. /help**

🔉 **Sesli sohbetlerde müzik çalmak için, [Kral Resmi Kanal](https://t.me/AlmanTeamSexy) Tarafından yapılmıştır.**
</b>""",
        reply_markup=InlineKeyboardMarkup(
            [ 
                [
                    InlineKeyboardButton(
                        "➕ Beni Grubuna Ekle➕", url=f"https://t.me/KralMusicTrBot?startgroup=true")
                ],[
                    InlineKeyboardButton(
                         "🎯 Tagger Bot", url="https://t.me/autotagger_bot"
                    ),
                    InlineKeyboardButton(
                        "🏷️ Resmi Kanal", url=f"https://t.me/FrozenBio")
                ],[
                    InlineKeyboardButton(
                        "💬 Grubumuz", url=f"https://t.me/TeamAlmanSexy"
                    ),
                    InlineKeyboardButton(
                        "▶️ Mp3 Botu", url=f"https://t.me/Mp3_aramaBot")               
                 ],[
                    InlineKeyboardButton(
                        "🧑‍🔧Sahibim", url="https://t.me/FrozenBey"
                    )
                ]
            ]
        ),
     disable_web_page_preview=True
    )


@Client.on_message(command(["start", f"start@Mp3dinleme_Bot"]) & filters.group & ~filters.edited)
async def start(client: Client, message: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await message.reply_text(
        f"""✔ **ʙᴏᴛ ɪs ʀᴜɴɴɪɴɢ**\n<b>☣ **ᴜᴘᴛɪᴍᴇ:**</b> `{uptime}`""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "☢ Grub", url=f"https://t.me/TeamAlmanSexy"
                    ),
                    InlineKeyboardButton(
                        "📣 Kanal", url=f"https://t.me/FrozenBio"
                    )
                ]
            ]
        )
    )

@Client.on_message(command(["help", f"help@Mp3dinleme_Bot"]) & filters.group & ~filters.edited)
async def help(client: Client, message: Message):
    await message.reply_text(
        f"""<b>☢ ʜᴇʟʟᴏ {message.from_user.mention()}, ᴘʟᴇᴀsᴇ ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴄᴀɴ ʀᴇᴀᴅ ғᴏʀ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ</b>""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="✔ Beni nasıl kullanılırsın", url=f"https://t.me/Mp3dinleme_Bot?start=help"
                    )
                ]
            ]
        )
    )

@Client.on_message(command("help") & filters.private & ~filters.edited)
async def help_(client: Client, message: Message):
    await message.reply_text(
        f"""<b>Merhaba {message.from_user.mention()}, yardım menüsüne hoş geldiniz✨
\n📙 𝙱𝙴𝙽İ 𝙽𝙰𝚂𝙸𝙻 𝙺𝚄𝙻𝙻𝙰𝙽𝙸𝚁𝚂𝙸𝙽?
\n1. önce beni grubunuza ekleyin.
2. beni yönetici olarak tanıtın ve tüm izinleri verin.
3. ardından, @Sesmusicasistan grubunuza veya türünüze /asistan.
3. müzik çalmaya başlamadan önce sesli sohbeti açtığınızdan emin olun.
\n💁🏻‍♀️ **tüm kullanıcı için komutlar:**
\n/play (song name) - youtube'dan şarkı çalmak
/oynat - (reply to audio) - ses dosyasını kullanarak şarkı çalma youtube linki veya Mp3 oynatıcı
/liste - listedeki şarkıyı sırada gösterme
/bul (song name) - youtube'dan şarkı indirme
/arama (video name) - youtube'dan video arama detayı
/vsong (video name) - youtube'dan video indirme ayrıntılı
/lyric - (song name) şarkı sözleri scrapper 
\n👷🏻‍♂️ **yöneticiler için komutlar:**
\n/player - müzik çalar ayarları panelini açma
/durdur - müzik akışını duraklatma
/devam - devam et müzik duraklatıldı 
/atla - sonraki şarkıya atlamak 
/son - müzik akışını durdurma 
/asistan - grubunuza asistan katılmayı davet etme 
/reload - yönetici listesini yenilemek için 
/cache - temizlenmiş yönetici önbelleği için 
/yetki - müzik botu kullanmak için yetkili kullanıcı 
/yetkial - müzik botu kullanmak için yetkisiz 
/musicplayer (on / off) - devre dışı bırakmak / etkinleştirmek grubunuzdaki müzik çalar için
\n🎧 kanal akışı komutları:
\n/cplay - kanal sesli sohbetinde müzik akışı 
/cplayer - şarkıyı akışta gösterme 
/cpause - müzik akışını duraklatma 
/cresume - akışın duraklatıldığını sürdürme 
/cskip - akışı bir sonraki şarkıya atlamak 
/cend - müzik akışını sonlandırmak 
/admincache - yönetici önbelleğini yenileme 
\n🧙‍♂️ sudo kullanıcıları için komut:
\n/asistanayril- asistanın tüm gruptan ayrılmasını emretmek 
/gcast - yayın iletisi gönderme yardımcıya göre 
</b>""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "☣ Grub", url=f"https://t.me/TeamAlmanSexy"
                    ),
                    InlineKeyboardButton(
                        "📣 Kanal", url=f"https://t.me/FrozenBio"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "♞🏻‍ Developer 🇩🇪", url=f"https://t.me/FrozenBey"
                    )
                ]
            ]
        )
    )


@Client.on_message(command(["ping", f"ping@mp3dinleme_Bot"]) & ~filters.edited)
async def ping_pong(client: Client, message: Message):
    start = time()
    m_reply = await message.reply_text("ᴘɪɴɢɪɴɢ...")
    delta_ping = time() - start
    await m_reply.edit_text(
        "✈ `ᴘᴏɴɢ!!`\n"
        f"☣ `{delta_ping * 1000:.3f} ᴍs`"
    )


@Client.on_message(command(["uptime", f"uptime@Mp3dinleme_Bot"]) & ~filters.edited)
@authorized_users_only
async def get_uptime(client: Client, message: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await message.reply_text(
        "🤖 ʙᴏᴛ sᴛᴀᴛᴜs:\n"
        f"➤ **ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"➤ **sᴛᴀʀᴛ ᴛɪᴍᴇ:** `{START_TIME_ISO}`"
    )
