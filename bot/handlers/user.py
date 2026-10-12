from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import Config
from bot.database import Database
from bot.keyboards import main_menu_kb, cancel_kb, admin_order_kb, amounts_kb
from bot.states import PurchaseStates

router = Router()


def payment_details_text(config: Config, stars: int, amd: float) -> str:
    return (
        f"Реквизиты для оплаты:\n"
        f"Карта: {config.card_number}\n\n"
        f"Сумма к оплате: {amd:.0f} AMD за {stars} ⭐\n\n"
        f"После оплаты пришли сюда скриншот или фото чека."
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Здесь можно купить Telegram Stars за драмы.\n\n"
        "Выбери действие в меню ниже 👇",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message, config: Config):
    await message.answer(
        f"Как это работает:\n"
        f"1. Нажми «Купить Stars» и выбери количество из списка (или укажи своё).\n"
        f"2. Переведи нужную сумму в драмах на карту, которую покажет бот.\n"
        f"3. Пришли скриншот/чек об оплате прямо в чат.\n"
        f"4. После проверки тебе отправят Stars подарком в Telegram.\n\n"
        f"Курс: 1 ⭐ = {config.rate_amd_per_star} AMD"
    )


@router.message(F.text == "❌ Отмена")
async def cancel_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заявка отменена.", reply_markup=main_menu_kb())


@router.callback_query(F.data == "cancel_purchase")
async def cancel_flow_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Заявка отменена.")
    await callback.answer()


@router.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message, db: Database):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("У тебя пока нет заказов.")
        return

    status_labels = {
        "awaiting_receipt": "⏳ ждём чек",
        "pending_review": "🔍 на проверке",
        "confirmed": "✅ оплата подтверждена, готовим выдачу",
        "delivered": "🎁 выдано",
        "rejected": "❌ отклонено",
    }
    lines = []
    for o in orders:
        label = status_labels.get(o.status, o.status)
        lines.append(f"Заказ #{o.id}: {o.stars_amount} ⭐ — {o.amd_amount:.0f} AMD — {label}")
    await message.answer("\n".join(lines))


@router.message(F.text == "⭐ Купить Stars")
async def start_purchase(message: Message, state: FSMContext, config: Config):
    await state.set_state(PurchaseStates.choosing_amount)
    await message.answer(
        "Выбери, сколько Stars хочешь купить:",
        reply_markup=amounts_kb(config.rate_amd_per_star),
    )


@router.callback_query(PurchaseStates.choosing_amount, F.data.startswith("amount:"))
async def process_amount(callback: CallbackQuery, state: FSMContext, config: Config):
    amount = int(callback.data.split(":", 1)[1])
    amd_amount = round(amount * config.rate_amd_per_star, 0)
    await state.update_data(stars_amount=amount, amd_amount=amd_amount)
    await state.set_state(PurchaseStates.waiting_receipt)
    await callback.message.edit_text(payment_details_text(config, amount, amd_amount))
    await callback.answer()


@router.callback_query(PurchaseStates.choosing_amount, F.data == "custom_amount")
async def ask_custom_amount(callback: CallbackQuery, state: FSMContext, config: Config):
    await state.set_state(PurchaseStates.entering_custom_amount)
    await callback.message.edit_text(
        f"Введи, сколько Stars хочешь купить (число от {config.min_stars} до {config.max_stars}):"
    )
    await callback.answer()


@router.message(PurchaseStates.entering_custom_amount)
async def process_custom_amount(message: Message, state: FSMContext, config: Config):
    text = (message.text or "").strip().replace(" ", "")
    if not text.isdigit():
        await message.answer("Пожалуйста, введи целое число.")
        return

    amount = int(text)
    if amount < config.min_stars or amount > config.max_stars:
        await message.answer(
            f"Количество должно быть от {config.min_stars} до {config.max_stars}."
        )
        return

    amd_amount = round(amount * config.rate_amd_per_star, 0)
    await state.update_data(stars_amount=amount, amd_amount=amd_amount)
    await state.set_state(PurchaseStates.waiting_receipt)
    await message.answer(payment_details_text(config, amount, amd_amount))


@router.message(PurchaseStates.waiting_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext, bot: Bot, db: Database, config: Config):
    data = await state.get_data()
    order_id = await db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        stars_amount=data["stars_amount"],
        amd_amount=data["amd_amount"],
    )
    file_id = message.photo[-1].file_id
    await db.attach_receipt(order_id, "card", file_id)

    await state.clear()
    await message.answer(
        f"Спасибо! Заявка #{order_id} отправлена на проверку. "
        f"Как только оплата подтвердится — тебе придут Stars 🎁",
        reply_markup=main_menu_kb(),
    )

    caption = (
        f"🆕 Новая заявка #{order_id}\n"
        f"От: @{message.from_user.username or message.from_user.id} (id {message.from_user.id})\n"
        f"Количество: {data['stars_amount']} ⭐\n"
        f"Сумма: {data['amd_amount']:.0f} AMD"
    )
    sent = await bot.send_photo(
        chat_id=config.admin_chat_id,
        photo=file_id,
        caption=caption,
        reply_markup=admin_order_kb(order_id),
    )
    await db.set_admin_message_id(order_id, sent.message_id)


@router.message(PurchaseStates.waiting_receipt)
async def waiting_receipt_wrong_content(message: Message):
    await message.answer("Пришли, пожалуйста, именно фото/скриншот чека об оплате.")
