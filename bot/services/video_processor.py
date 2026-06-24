import asyncio
import contextlib
import logging
import tempfile
from pathlib import Path

from bot.config import settings

logger = logging.getLogger(__name__)


async def run_ffmpeg(*args: str, timeout: int = 300) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.communicate()
        raise RuntimeError(f"FFmpeg timed out after {timeout}s") from None
    return proc.returncode, stdout.decode(), stderr.decode()


async def convert_to_video_note(
    input_path: str,
    output_path: str | None = None,
    duration: int = 60,
    size: int = 360,
) -> str:
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp4", dir=settings.TEMP_DIR)

    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)

    filter_complex = (
        f"scale={size}:{size}:force_original_aspect_ratio=increase,"
        f"crop={size}:{size},"
        f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2"
    )

    rc, _, stderr = await run_ffmpeg(
        "-y",
        "-i",
        input_path,
        "-t",
        str(duration),
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output_path,
    )

    if rc != 0:
        logger.error("FFmpeg failed: %s", stderr[-500:])
        raise RuntimeError(f"FFmpeg exited with code {rc}")

    return output_path


async def cleanup_files(*paths: str) -> None:
    for path in paths:
        with contextlib.suppress(OSError):
            Path(path).unlink(missing_ok=True)
