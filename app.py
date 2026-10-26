from __future__ import annotations

import logging
import threading

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from config import Settings
from dashboard.app import run_dashboard
from services.analytics import AnalyticsStore
from utils.logging_config import setup_logging
from routers.callbacks import router as callbacks_router
from routers.commands import router as commands_router
from routers.intake import router as intake_router
from routers.thumbnails import router as thumbnails_router
from services.cooldown import CooldownManager
from services.request_store import RequestStore
from services.thumbnail_store import ThumbnailStore


def create_dispatcher(settings: Settings, analytics_store: AnalyticsStore | None = None) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(commands_router)
    dispatcher.include_router(thumbnails_router)
    dispatcher.include_router(intake_router)
    dispatcher.include_router(callbacks_router)
    if analytics_store is None:
        analytics_store = AnalyticsStore(settings.analytics_db)
    dispatcher.workflow_data.update(
        settings=settings,
        cooldown=CooldownManager(timeout_seconds=settings.process_max_timeout),
        request_store=RequestStore(settings.requests_dir, settings.work_dir),
        thumbnail_store=ThumbnailStore(settings.thumbnails_dir),
        analytics_store=analytics_store,
    )
    return dispatcher


async def run() -> None:
    setup_logging()
    settings = Settings.from_env()
    settings.ensure_directories()

    analytics_store = AnalyticsStore(settings.analytics_db)

    session = AiohttpSession(
        api=TelegramAPIServer.from_base("http://127.0.0.1:8081", is_local=True),
        timeout=settings.process_max_timeout,
    )
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher(settings, analytics_store)

    logging.getLogger(__name__).info(
        "Bot is starting | download_dir=%s requests_dir=%s proxy=%s cooldown=%ss",
        settings.download_location,
        settings.requests_dir,
        "enabled" if settings.http_proxy else "disabled",
        settings.process_max_timeout,
    )

    if settings.dashboard_enabled and settings.dashboard_token:
        dashboard_thread = threading.Thread(
            target=run_dashboard,
            args=(analytics_store, settings.dashboard_token, settings.dashboard_host, settings.dashboard_port),
            daemon=True,
        )
        dashboard_thread.start()
        logging.getLogger(__name__).info(
            "Dashboard started | host=%s port=%s",
            settings.dashboard_host,
            settings.dashboard_port,
        )

    await dispatcher.start_polling(bot)