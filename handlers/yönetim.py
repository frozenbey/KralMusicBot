# Admins.py (Yönetim) kontrol..
#Ğ 

from asyncio import QueueEmpty
from config import que
from pyrogram import Client, filters
from pyrogram.types import Message

from cache.admins import admins
from helpers.channelmusic import get_chat_id
from helpers.decorators import authorized_users_only, errors
from helpers.filters import command, other_filters
from callsmusic import callsmusic
from callsmusic.queues import queues


@Client.on_message(filters.command(["reload", "r"]))
async def update_admin(client, message):
    global admins
    new_admins = []
    new_ads = await client.get_chat_members(message.chat.id, filter="administrators")
    for u in new_ads:
        new_admins.append(u.user.id)
    admins[message.chat.id] = new_admins
    await message.reply_text("✔️ Bot ** Dogru yüklendi! **\n✔️ **𝚈önetici listesi** Dogru **Güncellendi!**")


@Client.on_message(command(["durdur", "d"]) & other_filters)
@errors
@authorized_users_only
async def durdur(_, message: Message):
    chat_id = get_chat_id(message.chat)
    if (chat_id not in callsmusic.pytgcalls.active_calls) or (
        callsmusic.pytgcalls.active_calls[chat_id] == "paused"
    ):
        await message.reply_text("✘ 𝙰𝙺𝙸Ş𝚃𝙰 𝙷İÇ𝙱İ𝚁 Ş𝙴𝚈 𝚈𝙾𝙺!")
    else:
        callsmusic.pytgcalls.pause_stream(chat_id)
        await message.reply_text("⏸️ Müzik duraklatıldı!")


@Client.on_message(command(["devam", "d"]) & other_filters)
@errors
@authorized_users_only
async def devam(_, message: Message):
    chat_id = get_chat_id(message.chat)
    if (chat_id not in callsmusic.pytgcalls.active_calls) or (
        callsmusic.pytgcalls.active_calls[chat_id] == "playing"
    ):
        await message.reply_text("✘ Akış durdurulması..!")
    else:
        callsmusic.pytgcalls.resume_stream(chat_id)
        await message.reply_text("🥳 Müzik Devam Etti!")


@Client.on_message(command(["son", "s"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    chat_id = get_chat_id(message.chat)
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply_text("✘ Çalışan hiç bir şey yok!")
    else:
        try:
            queues.clear(chat_id)
        except QueueEmpty:
            pass

        callsmusic.pytgcalls.leave_group_call(chat_id)
        await message.reply_text("☑️ Müzik Kapatıldı.!\n **İyi günler dileğiyle 🥰**")


@Client.on_message(command(["atla", "a"]) & other_filters)
@errors
@authorized_users_only
async def atla(_, message: Message):
    global que
    chat_id = get_chat_id(message.chat)
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply_text("✘ Oynatılan hiç bir akış yok 🙄!")
    else:
        queues.task_done(chat_id)

        if queues.is_empty(chat_id):
            callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            callsmusic.pytgcalls.change_stream(
                chat_id, queues.get(chat_id)["file"]
            )

    qeue = que.get(chat_id)
    if qeue:
        skip = qeue.pop(0)
    if not qeue:
        return
    await message.reply_text(f"✘ Atlatıldı: **{skip[0]}**\n✔️ Şimdi oynatılıyor: **{qeue[0][0]}**")


@Client.on_message(filters.command(["ver", "auth"]))
@authorized_users_only
async def authenticate(client, message):
    global admins
    if not message.reply_to_message:
        await message.reply("Kullanıcıya Yetki Vermek için yanıtlayınız!")
        return
    if message.reply_to_message.from_user.id not in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.append(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply("✔️ Kullanıcı yetkili.")
    else:
        await message.reply("🛑 Kullanıcı Zaten Yetkili!")


@Client.on_message(filters.command(["al", "deauth"]))
@authorized_users_only
async def deautenticate(client, message):
    global admins
    if not message.reply_to_message:
        await message.reply("✘ Kullanıcıyı yetkisizleştirmek için mesaj atınız!")
        return
    if message.reply_to_message.from_user.id in admins[message.chat.id]:
        new_admins = admins[message.chat.id]
        new_admins.remove(message.reply_to_message.from_user.id)
        admins[message.chat.id] = new_admins
        await message.reply("kullanıcı yetkisiz")
    else:
        await message.reply("🛑 Kullanıcının yetkisi alındı!")
