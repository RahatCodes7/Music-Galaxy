from pyrogram import filters
from pyrogram.types import Message

from MusicGalaxy import galaxy
from MusicGalaxy.core.call import Galaxy

welcome = 20
close = 30


@galaxy.on_message(filters.video_chat_started, group=welcome)
@galaxy.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    await Galaxy.stop_stream_force(message.chat.id)
