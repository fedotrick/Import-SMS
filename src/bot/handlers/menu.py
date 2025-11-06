from __future__ import annotations

import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from src.bot.handlers.add_record import AddRecordState
from src.bot.keyboards.main_menu import (
    MENU_ADD_RECORD,
    MENU_DOWNLOAD,
    MENU_HELP,
    MENU_LAST_RECORDS,
    build_main_menu,
)
from src.bot.services.excel import ExcelServiceError, ExcelValidationError, get_last_rows
from src.core.config import get_settings

logger = logging.getLogger(__name__)

router = Router()

RECENT_RECORDS_LIMIT = 10


def _format_last_rows(rows: list[list[str | int | None]]) -> str:
    if not rows:
        return "Записей пока нет."

    lines: list[str] = []
    for row in reversed(rows):
        if len(row) >= 6:
            if len(row) > 10:
                id_plavka = row[0]
                uchetny_nomer = row[1]
                plavka_data = row[2]
                nomer_plavki = row[3]
                naimenovanie = row[10] if len(row) > 10 else "—"
                display_date = plavka_data.strftime("%d.%m.%Y") if hasattr(plavka_data, 'strftime') else str(plavka_data)
                lines.append(
                    f"Плавка {nomer_plavki}\n"
                    f"Дата: {display_date}\n"
                    f"Изделие: {naimenovanie}\n"
                    f"Учётный №: {uchetny_nomer}"
                )
            else:
                timestamp, _user_id, username, _chat_id, message_id, text = row[:6]
                display_timestamp = timestamp or "—"
                display_username = username or "—"
                display_text = text or ""
                lines.append(
                    f"{display_timestamp}\n{display_text}\nID сообщения: {message_id}, Автор: {display_username}"
                )
    return "\n\n".join(lines)


@router.callback_query(F.data == MENU_ADD_RECORD)
async def menu_add_record(callback: CallbackQuery, state: FSMContext) -> None:
    message = callback.message
    if message is None:
        await callback.answer("Сообщение недоступно.", show_alert=True)
        return

    await callback.answer()
    await state.set_state(AddRecordState.waiting_for_text)
    await message.answer(
        "Отправьте текст сообщения, который необходимо добавить в plavka.xlsx."
    )


@router.callback_query(F.data == MENU_LAST_RECORDS)
async def menu_last_records(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        await callback.answer("Сообщение недоступно.", show_alert=True)
        return

    await callback.answer()

    try:
        rows = get_last_rows(RECENT_RECORDS_LIMIT)
    except ExcelValidationError as exc:
        logger.exception("Validation error while reading recent rows: %s", exc)
        await message.answer(
            "⚠️ Не удалось прочитать plavka.xlsx: структура файла отличается от ожидаемой."
        )
        return
    except ExcelServiceError as exc:
        logger.exception("Service error while reading recent rows: %s", exc)
        await message.answer(str(exc))
        return
    except Exception as exc:  # pragma: no cover - safety net for unexpected issues
        logger.exception("Unexpected error while reading recent rows: %s", exc)
        await message.answer("Произошла непредвиденная ошибка при чтении файла.")
        return

    formatted_rows = _format_last_rows(rows)
    await message.answer(formatted_rows, reply_markup=build_main_menu())


@router.callback_query(F.data == MENU_DOWNLOAD)
async def menu_download(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        await callback.answer("Сообщение недоступно.", show_alert=True)
        return

    await callback.answer()

    settings = get_settings()
    xlsx_path: Path = settings.xlsx_path
    if not xlsx_path.exists():
        await message.answer(
            "Файл plavka.xlsx пока не создан. Добавьте запись, чтобы создать файл автоматически."
        )
        return

    document = FSInputFile(xlsx_path)
    await message.answer_document(document)


@router.callback_query(F.data == MENU_HELP)
async def menu_help(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        await callback.answer("Сообщение недоступно.", show_alert=True)
        return

    await callback.answer()

    help_text = (
        "ℹ️ Журнал смен — управление через меню:\n\n"
        "• «Добавить запись» — отправьте текст, и он попадёт в plavka.xlsx.\n"
        "• «Последние записи» — покажет последние 10 записей из журнала.\n"
        "• «Скачать plavka.xlsx» — получите актуальный файл.\n"
        "• «Справка» — это сообщение."
    )
    await message.answer(help_text, reply_markup=build_main_menu())
