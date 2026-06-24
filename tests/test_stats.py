from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.stats import get_hourly_activity, get_stats


@pytest.mark.asyncio
async def test_get_stats_returns_dict():
    with patch("bot.services.stats.async_session") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        stats = await get_stats()
        assert isinstance(stats, dict)
        assert "total_users" in stats
        assert "total_videos" in stats
        assert "errors" in stats


@pytest.mark.asyncio
async def test_get_hourly_activity_returns_list():
    with patch("bot.services.stats.async_session") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_result

        activity = await get_hourly_activity()
        assert isinstance(activity, list)
