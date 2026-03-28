from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yt_dlp


class DownloadError(Exception):
    """Raised when yt-dlp cannot complete a download."""


@dataclass(slots=True)
class DownloadedFile:
    path: Path
    title: str
    size_bytes: int


class PlaylistDownloader:
    def __init__(self, base_dir: Path, cookies_path: Path | None = None) -> None:
        self.base_dir = base_dir
        self.cookies_path = cookies_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def download_playlist(self, playlist_url: str, mode: str, chat_id: int) -> list[DownloadedFile]:
        work_dir = self.base_dir / str(chat_id)
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        options = self._build_options(work_dir, mode)

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([playlist_url])
        except yt_dlp.utils.DownloadError as exc:
            raise DownloadError(str(exc)) from exc

        files = self._collect_downloads(work_dir, mode)
        if not files:
            raise DownloadError("No downloadable files were produced for that playlist.")

        return files

    def cleanup_chat_downloads(self, chat_id: int) -> None:
        work_dir = self.base_dir / str(chat_id)
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

    def _build_options(self, work_dir: Path, mode: str) -> dict:
        common = {
            "noplaylist": False,
            "ignoreerrors": True,
            "quiet": True,
            "no_warnings": True,
            "outtmpl": str(work_dir / "%(playlist)s" / "%(playlist_index)03d - %(title)s.%(ext)s"),
            "restrictfilenames": True,
            "windowsfilenames": True,
        }

        if self.cookies_path is not None:
            common["cookiefile"] = str(self.cookies_path)

        if mode == "audio":
            return {
                **common,
                "format": "best/bestvideo+bestaudio",
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

        if mode == "video":
            return {
                **common,
                "format": (
                    "bestvideo[height<=360]+bestaudio/"
                    "best[height<=360]/"
                    "bestvideo+bestaudio/"
                    "best"
                ),
                "merge_output_format": "mp4",
            }

        raise DownloadError(f"Unsupported mode: {mode}")

    def _collect_downloads(self, work_dir: Path, mode: str) -> list[DownloadedFile]:
        extensions = {".mp3"} if mode == "audio" else {".mp4", ".mkv", ".webm"}
        files = [
            DownloadedFile(path=path, title=path.stem, size_bytes=path.stat().st_size)
            for path in self._iter_files(work_dir)
            if path.suffix.lower() in extensions
        ]
        return sorted(files, key=lambda item: item.path.name)

    def _iter_files(self, work_dir: Path) -> Iterable[Path]:
        return (path for path in work_dir.rglob("*") if path.is_file())
