import random
from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from ShrutixMusic import nand
from ShrutixMusic.core.call import Shruti
from ShrutixMusic.utils import bot_sys_stats
from ShrutixMusic.utils.decorators.language import language
from ShrutixMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL

MESSAGE_EFFECTS = [
    5107584321108051014,
    5159385139981059251,
    5104841245755180586,
    5046509860389126442,
]


@nand.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    is_private = message.chat.type == ChatType.PRIVATE
    kwargs = {"effect_id": random.choice(MESSAGE_EFFECTS)} if is_private else {}
    response = await message.reply_photo(
        photo=PING_IMG_URL,
        caption=_["ping_1"].format(nand.mention),
        **kwargs,
    )
    pytgping = await Shruti.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, nand.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
