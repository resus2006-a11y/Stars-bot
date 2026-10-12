from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


STAR_OPTIONS = [50, 100, 250, 500, 1000, 2500]


def amounts_kb(rate_amd_per_star: float) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for stars in STAR_OPTIONS:
        amd = round(stars * rate_amd_per_star)
        row.append(
            InlineKeyboardButton(text=f"{stars} ⭐ — {amd} AMD", callback_data=f"amount:{stars}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✏️ Своё количество", callback_data="custom_amount")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_purchase")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Купить Stars")],
            [KeyboardButton(text="📦 Мои заказы"), KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm:{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{order_id}"),
            ]
        ]
    )


def admin_delivered_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Stars отправлены", callback_data=f"delivered:{order_id}")]
        ]
    )
