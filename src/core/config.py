from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    xlsx_path: Path
    locale: str


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is not configured. Please set it in the environment or .env file.")

    xlsx_path_value = os.getenv("XLSX_PATH", "./Контроль/plavka.xlsx")
    xlsx_path = _resolve_path(xlsx_path_value)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    locale_value = os.getenv("LOCALE", "ru")

    return Settings(bot_token=bot_token, xlsx_path=xlsx_path, locale=locale_value)
