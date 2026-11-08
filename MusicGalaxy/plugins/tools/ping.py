import random
from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from MusicGalaxy import galaxy
from MusicGalaxy.core.call import Galaxy
from MusicGalaxy.utils import bot_sys_stats
from MusicGalaxy.utils.decorators.language import language
from MusicGalaxy.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL

MESSAGE_EFFECTS = [
    5107584321108051014,
    5159385139981059251,
    5104841245755180586,
    5046509860389126442,
]


@galaxy.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    is_private = message.chat.type == ChatType.PRIVATE
    kwargs = {"effect_id": random.choice(MESSAGE_EFFECTS)} if is_private else {}
    response = await message.reply_photo(
        photo=PING_IMG_URL,
        caption=_["ping_1"].format(galaxy.mention),
        **kwargs,
    )
    pytgping = await Galaxy.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, galaxy.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
