from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

MENU_ADD_RECORD = "menu:add_record"
MENU_LAST_RECORDS = "menu:last_records"
MENU_DOWNLOAD = "menu:download"
MENU_HELP = "menu:help"


def build_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить запись", callback_data=MENU_ADD_RECORD)
    builder.button(text="Последние записи", callback_data=MENU_LAST_RECORDS)
    builder.button(text="Скачать plavka.xlsx", callback_data=MENU_DOWNLOAD)
    builder.button(text="Справка", callback_data=MENU_HELP)
    builder.adjust(1)
    return builder.as_markup()
