from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

from filelock import FileLock, Timeout
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from src.core.config import get_settings

logger = logging.getLogger(__name__)

EXPECTED_HEADERS: Sequence[str] = (
    "timestamp",
    "user_id",
    "username",
    "chat_id",
    "message_id",
    "text",
)
LOCK_TIMEOUT = 15  # seconds


class ExcelServiceError(Exception):
    """Base class for Excel service errors."""


class ExcelValidationError(ExcelServiceError):
    """Raised when the Excel sheet does not match the expected structure."""


def _get_lock(path: Path) -> FileLock:
    return FileLock(f"{path}.lock", timeout=LOCK_TIMEOUT)


def _prepare_workbook(path: Path) -> None:
    if not path.exists():
        logger.info("Excel file not found. Creating a new workbook at %s", path)
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Journal"
        worksheet.append(list(EXPECTED_HEADERS))
        workbook.save(path)
        workbook.close()
        return

    try:
        workbook = load_workbook(path)
    except InvalidFileException as exc:
        raise ExcelValidationError(
            "Не удалось открыть plavka.xlsx. Проверьте, что файл не поврежден и используется формат XLSX."
        ) from exc

    worksheet = workbook.active
    header_values = [worksheet.cell(row=1, column=index + 1).value for index in range(len(EXPECTED_HEADERS))]

    if all(value in (None, "") for value in header_values) and worksheet.max_row == 1:
        logger.info("Excel file found without headers. Writing default headers to %s", path)
        for column, header in enumerate(EXPECTED_HEADERS, start=1):
            worksheet.cell(row=1, column=column, value=header)
        workbook.save(path)
        workbook.close()
        return

    if list(header_values) != list(EXPECTED_HEADERS):
        workbook.close()
        raise ExcelValidationError(
            "Структура листа plavka.xlsx не соответствует ожидаемой. "
            "Проверьте заголовки: timestamp, user_id, username, chat_id, message_id, text."
        )

    workbook.close()


def ensure_workbook_ready() -> None:
    settings = get_settings()
    xlsx_path = settings.xlsx_path
    lock = _get_lock(xlsx_path)

    try:
        with lock:
            _prepare_workbook(xlsx_path)
    except Timeout as exc:
        raise ExcelServiceError(
            "Файл plavka.xlsx сейчас используется. Попробуйте повторить попытку позже."
        ) from exc



def append_message_row(*, user_id: int, username: str | None, chat_id: int, message_id: int, text: str) -> None:
    settings = get_settings()
    xlsx_path = settings.xlsx_path
    lock = _get_lock(xlsx_path)

    try:
        with lock:
            _prepare_workbook(xlsx_path)

            try:
                workbook = load_workbook(xlsx_path)
            except InvalidFileException as exc:
                raise ExcelValidationError(
                    "Не удалось открыть plavka.xlsx для записи. Проверьте структуру файла."
                ) from exc

            worksheet = workbook.active
            timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            worksheet.append(
                [
                    timestamp,
                    user_id,
                    username or "",
                    chat_id,
                    message_id,
                    text,
                ]
            )
            workbook.save(xlsx_path)
            workbook.close()
            logger.info(
                "Добавлена запись в журнал: user_id=%s, chat_id=%s, message_id=%s",
                user_id,
                chat_id,
                message_id,
            )
    except Timeout as exc:
        raise ExcelServiceError(
            "Файл plavka.xlsx сейчас используется. Попробуйте повторить попытку позже."
        ) from exc


def get_last_rows(limit: int) -> List[List[str | int | None]]:
    if limit <= 0:
        return []

    settings = get_settings()
    xlsx_path = settings.xlsx_path
    lock = _get_lock(xlsx_path)

    try:
        with lock:
            _prepare_workbook(xlsx_path)

            try:
                workbook = load_workbook(xlsx_path, read_only=True)
            except InvalidFileException as exc:
                raise ExcelValidationError(
                    "Не удалось прочитать plavka.xlsx. Проверьте структуру файла."
                ) from exc

            worksheet = workbook.active
            rows = [list(row) for row in worksheet.iter_rows(min_row=2, values_only=True)]
            workbook.close()
    except Timeout as exc:
        raise ExcelServiceError(
            "Файл plavka.xlsx сейчас используется. Попробуйте повторить попытку позже."
        ) from exc

    if not rows:
        return []

    return rows[-limit:]
