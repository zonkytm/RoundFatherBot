import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.video_processor import cleanup_files, convert_to_video_note, run_ffmpeg


@pytest.fixture
def tmp_video(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"\x00" * 1024)
    return str(video)


@pytest.mark.asyncio
async def test_run_ffmpeg_success():
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"ok", b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("asyncio.wait_for", return_value=(b"ok", b"")):
            rc, stdout, stderr = await run_ffmpeg("-version")
            assert rc == 0


@pytest.mark.asyncio
async def test_run_ffmpeg_timeout():
    mock_proc = AsyncMock()
    mock_proc.communicate.side_effect = asyncio.TimeoutError
    mock_proc.kill = MagicMock()
    mock_proc.communicate = AsyncMock()

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(RuntimeError, match="timed out"):
                await run_ffmpeg("-i", "test.mp4", timeout=1)


@pytest.mark.asyncio
async def test_convert_to_video_note_ffmpeg_error(tmp_video, tmp_path):
    output = str(tmp_path / "output.mp4")

    with (
        patch(
            "bot.services.video_processor.run_ffmpeg",
            new_callable=AsyncMock,
            return_value=(1, "", "error message"),
        ),
        pytest.raises(RuntimeError, match="exited with code 1"),
    ):
        await convert_to_video_note(tmp_video, output_path=output)


@pytest.mark.asyncio
async def test_convert_to_video_note_success(tmp_video, tmp_path):
    output = str(tmp_path / "output.mp4")

    with (
        patch(
            "bot.services.video_processor.run_ffmpeg",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        ),
        patch.object(
            __import__("bot.config", fromlist=["settings"]).settings,
            "TEMP_DIR",
            str(tmp_path),
        ),
    ):
        result = await convert_to_video_note(tmp_video, output_path=output)
        assert result == output


@pytest.mark.asyncio
async def test_cleanup_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    f2.write_text("b")

    await cleanup_files(str(f1), str(f2))
    assert not f1.exists()
    assert not f2.exists()


@pytest.mark.asyncio
async def test_cleanup_files_missing():
    await cleanup_files("/nonexistent/file.txt")


@pytest.mark.asyncio
async def test_convert_auto_generates_output_path(tmp_video, tmp_path):
    with (
        patch(
            "bot.services.video_processor.run_ffmpeg",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        ),
        patch.object(
            __import__("bot.config", fromlist=["settings"]).settings,
            "TEMP_DIR",
            str(tmp_path),
        ),
    ):
        result = await convert_to_video_note(tmp_video)
        assert result.endswith(".mp4")
