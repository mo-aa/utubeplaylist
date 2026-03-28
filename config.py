from __future__ import annotations

import base64
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
    yt_dlp_cookies_path: Path | None


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing. Add it to your .env file.")

    downloads_dir = Path(os.getenv("DOWNLOADS_DIR", "downloads")).resolve()
    max_upload_mb = int(os.getenv("TELEGRAM_MAX_UPLOAD_MB", "49"))
    cookies_path = _prepare_cookies_file(downloads_dir)

    return Settings(
        telegram_bot_token=token,
        downloads_dir=downloads_dir,
        telegram_max_upload_bytes=max_upload_mb * 1024 * 1024,
        yt_dlp_cookies_path=cookies_path,
    )


def _prepare_cookies_file(downloads_dir: Path) -> Path | None:
    cookies_file = os.getenv("YTDLP_COOKIES_FILE", "").strip()
    if cookies_file:
        path = Path(cookies_file).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"YTDLP_COOKIES_FILE does not exist: {path}")
        return path

    cookies_text = os.getenv("YTDLP_COOKIES", "")
    cookies_b64 = os.getenv("YTDLP_COOKIES_B64", "").strip()
    if not cookies_text and not cookies_b64:
        return None

    if cookies_b64:
        try:
            cookies_text = base64.b64decode(cookies_b64).decode("utf-8")
        except Exception as exc:
            raise ValueError("YTDLP_COOKIES_B64 is not valid base64-encoded UTF-8 text.") from exc

    runtime_dir = downloads_dir / ".runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    cookies_path = runtime_dir / "youtube-cookies.txt"
    cookies_path.write_text(cookies_text, encoding="utf-8")
    return cookies_path
