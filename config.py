from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    downloads_dir: Path
    telegram_max_upload_bytes: int


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing. Add it to your .env file.")

    downloads_dir = Path(os.getenv("DOWNLOADS_DIR", "downloads")).resolve()
    max_upload_mb = int(os.getenv("TELEGRAM_MAX_UPLOAD_MB", "49"))

    return Settings(
        telegram_bot_token=token,
        downloads_dir=downloads_dir,
        telegram_max_upload_bytes=max_upload_mb * 1024 * 1024,
    )
