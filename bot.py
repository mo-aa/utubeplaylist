from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import load_settings
from downloader import DownloadError, PlaylistDownloader


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MODE_LABELS = {
    "audio": "music only",
    "video": "video 360p",
}


def mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Music only", callback_data="mode:audio"),
                InlineKeyboardButton("Video 360p", callback_data="mode:video"),
            ]
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["download_mode"] = "audio"
    await update.effective_message.reply_text(
        "Send me a YouTube playlist link after choosing a mode.",
        reply_markup=mode_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "1. Press Music only or Video 360p.\n"
        "2. Paste a YouTube playlist URL.\n"
        "3. I will download the playlist and send the files I can upload.\n\n"
        "Use /cancel to clear the current mode."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("download_mode", None)
    await update.effective_message.reply_text(
        "Selection cleared. Pick a mode again when you're ready.",
        reply_markup=mode_keyboard(),
    )


async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    _, mode = query.data.split(":", maxsplit=1)
    context.user_data["download_mode"] = mode

    await query.edit_message_text(
        f"Mode set to {MODE_LABELS[mode]}. Now send a YouTube playlist URL.",
        reply_markup=mode_keyboard(),
    )


def looks_like_playlist_url(text: str) -> bool:
    value = text.lower()
    return "youtube.com" in value and "list=" in value


async def handle_playlist_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or message.text is None:
        return

    if not looks_like_playlist_url(message.text):
        await message.reply_text(
            "That does not look like a YouTube playlist URL. Make sure the link includes `list=`.",
            reply_markup=mode_keyboard(),
        )
        return

    mode = context.user_data.get("download_mode", "audio")
    downloader: PlaylistDownloader = context.application.bot_data["downloader"]
    upload_limit: int = context.application.bot_data["upload_limit"]

    status_message = await message.reply_text(
        f"Downloading playlist as {MODE_LABELS[mode]}. This can take a while for big playlists."
    )

    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    try:
        files = await asyncio.to_thread(
            downloader.download_playlist,
            message.text.strip(),
            mode,
            chat.id,
        )
    except DownloadError as exc:
        await asyncio.to_thread(downloader.cleanup_chat_downloads, chat.id)
        await status_message.edit_text(
            "Download failed. Check that the playlist is public and that `ffmpeg` is installed for audio mode.\n\n"
            f"Details: {exc}"
        )
        return
    except Exception:
        logger.exception("Unexpected download failure")
        await asyncio.to_thread(downloader.cleanup_chat_downloads, chat.id)
        await status_message.edit_text("Something unexpected happened while downloading that playlist.")
        return

    sent_count = 0
    skipped_count = 0

    await status_message.edit_text(
        f"Download finished. Sending {len(files)} file(s) in {MODE_LABELS[mode]} mode."
    )

    try:
        for item in files:
            if item.size_bytes > upload_limit:
                skipped_count += 1
                continue

            await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.UPLOAD_DOCUMENT)
            with item.path.open("rb") as file_handle:
                await message.reply_document(
                    document=file_handle,
                    filename=item.path.name,
                    caption=item.title[:1024],
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=120,
                    pool_timeout=120,
                )
            sent_count += 1
    finally:
        await asyncio.to_thread(downloader.cleanup_chat_downloads, chat.id)

    summary = f"Done. Sent {sent_count} file(s)."
    if skipped_count:
        summary += (
            f" Skipped {skipped_count} file(s) because they were bigger than the configured Telegram upload limit."
        )
    await message.reply_text(summary)


async def fallback_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Choose a mode and send a YouTube playlist URL.",
        reply_markup=mode_keyboard(),
    )


def build_application() -> Application:
    settings = load_settings()
    downloader = PlaylistDownloader(settings.downloads_dir)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["downloader"] = downloader
    application.bot_data["upload_limit"] = settings.telegram_max_upload_bytes

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(choose_mode, pattern=r"^mode:(audio|video)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_playlist_url))
    application.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, fallback_message))

    return application


def main() -> None:
    app = build_application()
    logger.info("Bot is starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
