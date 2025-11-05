from __future__ import annotations

import asyncio
import locale
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import add_record, menu, start
from src.bot.services.excel import ensure_workbook_ready
from src.core.config import get_settings

LOG_FORMAT = (
    '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S%z", force=True)


async def on_startup(dispatcher: Dispatcher) -> None:
    logger = logging.getLogger(__name__)
    try:
        ensure_workbook_ready()
        logger.info("Excel workbook is ready for use.")
    except Exception as exc:  # pragma: no cover - startup safety
        logger.exception("Failed to prepare Excel workbook: %s", exc)
        raise


async def run_bot() -> None:
    setup_logging()
    settings = get_settings()

    try:
        locale.setlocale(locale.LC_TIME, settings.locale)
    except locale.Error:
        logging.getLogger(__name__).warning("Locale '%s' is not available on this system.", settings.locale)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=None))
    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.include_router(start.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(add_record.router)

    dispatcher.startup.register(on_startup)

    logging.getLogger(__name__).info("Starting Telegram bot polling.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped.")
