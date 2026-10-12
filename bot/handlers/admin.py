from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from bot.config import Config
from bot.database import Database
from bot.keyboards import admin_delivered_kb

router = Router()


def _is_admin(callback: CallbackQuery, config: Config) -> bool:
    # Простая проверка: разрешаем действия только из админ-чата.
    return callback.message.chat.id == config.admin_chat_id


@router.callback_query(F.data.startswith("confirm:"))
async def confirm_payment(callback: CallbackQuery, bot: Bot, db: Database, config: Config):
    if not _is_admin(callback, config):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await db.update_status(order_id, "confirmed")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ Оплата подтверждена. Ожидаем выдачу Stars.",
        reply_markup=admin_delivered_kb(order_id),
    )
    await callback.answer("Оплата подтверждена")

    await bot.send_message(
        order.user_id,
        f"✅ Оплата по заявке #{order_id} подтверждена!\n"
        f"Сейчас отправим тебе {order.stars_amount} ⭐ подарком в Telegram.",
    )


@router.callback_query(F.data.startswith("reject:"))
async def reject_payment(callback: CallbackQuery, bot: Bot, db: Database, config: Config):
    if not _is_admin(callback, config):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await db.update_status(order_id, "rejected")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ Оплата отклонена."
    )
    await callback.answer("Заявка отклонена")

    await bot.send_message(
        order.user_id,
        f"❌ К сожалению, оплата по заявке #{order_id} не подтверждена. "
        f"Если это ошибка — напиши в поддержку.",
    )


@router.callback_query(F.data.startswith("delivered:"))
async def mark_delivered(callback: CallbackQuery, bot: Bot, db: Database, config: Config):
    if not _is_admin(callback, config):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await db.update_status(order_id, "delivered")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n🎁 Stars выданы. Заказ закрыт."
    )
    await callback.answer("Заказ закрыт")

    await bot.send_message(
        order.user_id,
        f"🎁 Твои {order.stars_amount} ⭐ по заявке #{order_id} отправлены подарком! "
        f"Спасибо за покупку.",
    )
