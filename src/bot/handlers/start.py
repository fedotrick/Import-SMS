from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.keyboards.main_menu import build_main_menu

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Это журнал смен. Используйте меню, чтобы добавить запись или посмотреть последние события.",
        reply_markup=build_main_menu(),
    )
