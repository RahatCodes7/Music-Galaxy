import random
from typing import Union

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message
from ShrutixMusic import nand
from ShrutixMusic.utils import help_pannel
from ShrutixMusic.utils.database import get_lang
from ShrutixMusic.utils.decorators.language import LanguageStart, languageCB
from ShrutixMusic.utils.inline.help import help_back_markup, private_help_panel
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT
from strings import get_string, helpers

MESSAGE_EFFECTS = [
    5107584321108051014,
    5159385139981059251,
    5104841245755180586,
    5046509860389126442,
]

HELP_TOPICS = {
    "hb1": helpers.HELP_1,
    "hb2": helpers.HELP_2,
    "hb3": helpers.HELP_3,
    "hb4": helpers.HELP_4,
    "hb5": helpers.HELP_5,
    "hb6": helpers.HELP_6,
    "hb7": helpers.HELP_7,
    "hb8": helpers.HELP_8,
    "hb9": helpers.HELP_9,
    "hb10": helpers.HELP_10,
    "hb11": helpers.HELP_11,
    "hb12": helpers.HELP_12,
    "hb13": helpers.HELP_13,
    "hb14": helpers.HELP_14,
    "hb15": helpers.HELP_15,
    "hb16": helpers.HELP_16,
}


def _topic_page(cb):
    return 1 if int(cb[2:]) <= 9 else 2


@nand.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@nand.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client: nand, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, True, 1)
        await update.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT), reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = help_pannel(_, None, 1)
        await update.reply_photo(
            photo=START_IMG_URL,
            caption=_["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
            effect_id=random.choice(MESSAGE_EFFECTS),
        )


@nand.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    await message.reply_text(_["help_2"], reply_markup=InlineKeyboardMarkup(keyboard))


@nand.on_callback_query(filters.regex("help_page") & ~BANNED_USERS)
@languageCB
async def help_page_cb(client, CallbackQuery, _):
    parts = CallbackQuery.data.split()
    page = int(parts[1])
    sf = parts[2] if len(parts) > 2 else "0"
    START = sf == "1"
    keyboard = help_pannel(_, START, page)
    await CallbackQuery.edit_message_text(
        _["help_1"].format(SUPPORT_CHAT), reply_markup=keyboard
    )


@nand.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    parts = CallbackQuery.data.strip().split()
    cb = parts[1]
    sf = parts[2] if len(parts) > 2 else "0"
    START = sf == "1"
    page = _topic_page(cb)
    keyboard = help_back_markup(_, page, START)
    await CallbackQuery.edit_message_text(HELP_TOPICS[cb], reply_markup=keyboard)
