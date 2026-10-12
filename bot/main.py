import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.database import Database
from bot.handlers import user, admin


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    if not config.bot_token:
        raise RuntimeError("BOT_TOKEN не задан. Скопируй .env.example в .env и заполни его.")

    db = Database()
    await db.init()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(user.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=True)
    # config и db передаются во все хендлеры как именованные аргументы
    await dp.start_polling(bot, config=config, db=db)


if __name__ == "__main__":
    asyncio.run(main())
