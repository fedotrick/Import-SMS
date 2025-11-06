from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from src.bot.keyboards.main_menu import build_main_menu
from src.bot.services.excel import ExcelServiceError, ExcelValidationError, append_message_row, append_plavka_rows
from src.bot.services.parser import ParserError, parse_shift_report

logger = logging.getLogger(__name__)

router = Router()


class AddRecordState(StatesGroup):
    waiting_for_text = State()


@router.message(Command("cancel"), AddRecordState.waiting_for_text)
async def cancel_add_record(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добавление записи отменено.", reply_markup=build_main_menu())


@router.message(AddRecordState.waiting_for_text)
async def process_add_record(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, отправьте текстовое сообщение для записи в журнал.")
        return

    record_text = message.text.strip()
    user = message.from_user

    if user is None:
        await message.answer("Не удалось определить отправителя сообщения.")
        logger.warning("Received message without sender data. message_id=%s", message.message_id)
        return

    try:
        report = parse_shift_report(record_text)
        logger.info("Parsed shift report with %d plavok", len(report.plavki))
        
        rows = []
        next_id = 1
        for plavka in report.plavki:
            rows.append(plavka.to_excel_row(next_id))
            next_id += 1
        
        rows_added = append_plavka_rows(rows)
        await state.clear()
        await message.answer(
            f"✅ Отчёт о смене успешно импортирован!\n\n"
            f"Всего плавок: {report.total_plavok}\n"
            f"Записано в Excel: {rows_added}\n"
            f"Дата: {report.header.get('Дата', 'не указана')}\n"
            f"Старший смены: {report.header.get('Старший_смены', 'не указан')}",
            reply_markup=build_main_menu()
        )
        return
    except ParserError as exc:
        logger.info("Failed to parse as shift report, falling back to simple text: %s", exc)
    
    try:
        append_message_row(
            user_id=user.id,
            username=user.username or user.full_name,
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=record_text,
        )
    except ExcelValidationError as exc:
        logger.exception("Excel validation error while appending a row: %s", exc)
        await message.answer(
            "⚠️ Не удалось сохранить запись: структура plavka.xlsx отличается от ожидаемой. "
            "Обратитесь к администратору."
        )
        return
    except ExcelServiceError as exc:
        logger.exception("Excel service error while appending a row: %s", exc)
        await message.answer(str(exc))
        return
    except Exception as exc:  # pragma: no cover - safety net for unexpected issues
        logger.exception("Unexpected error while appending a row: %s", exc)
        await message.answer("Произошла непредвиденная ошибка. Попробуйте позже.")
        return

    await state.clear()
    await message.answer("✅ Запись сохранена в plavka.xlsx.", reply_markup=build_main_menu())
