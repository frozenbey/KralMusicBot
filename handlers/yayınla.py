# Copyright (C) 2021 By TaliaProject
# Originally written by Anonim on github
# Broadcast function
#YAYIN

import asyncio

from pyrogram import Client, filters
from pyrogram.types import Dialog, Chat, Message
from pyrogram.errors import UserAlreadyParticipant

from callsmusic.callsmusic import client as cyber
from config import SUDO_USERS

@Client.on_message(filters.command(["gcast"]))
async def broadcast(_, message: Message):
    sent=0
    failed=0
    if message.from_user.id not in SUDO_USERS:
        return
    else:
        wtf = await message.reply("`Yayın başlatılıyor...`")
        if not message.reply_to_message:
            await wtf.edit("Yayını başlatmak için lütfen bir iletiyi yanıtlayın!")
            return
        lmao = message.reply_to_message.text
        async for dialog in veez.iter_dialogs():
            try:
                await veez.send_message(dialog.chat.id, lmao)
                sent = sent+1
                await wtf.edit(f"`Yayın...` \n\n**Gönderileceği yer:** `{sent}` chats \n**Başarısız oldu:** {failed} chats")
                await asyncio.sleep(3)
            except:
                failed=failed+1
        await message.reply_text(f"`Gcast başarıyla` \n\n**Gönderileceği yer:** `{sent}` chats \n**Başarısız oldu:** {failed} chats")
