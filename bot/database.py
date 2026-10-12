import time
from dataclasses import dataclass
from typing import Optional

import aiosqlite

DB_PATH = "stars_bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    stars_amount INTEGER NOT NULL,
    amd_amount REAL NOT NULL,
    payment_method TEXT,
    status TEXT NOT NULL DEFAULT 'awaiting_receipt',
    receipt_file_id TEXT,
    admin_message_id INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Возможные статусы заказа:
# awaiting_receipt  -> клиент выбрал сумму, ждём чек
# pending_review     -> чек отправлен, ждём проверки админом
# confirmed          -> оплата подтверждена, ждём выдачи Stars
# delivered          -> Stars отправлены клиенту, заказ закрыт
# rejected           -> оплата отклонена / отменена


@dataclass
class Order:
    id: int
    user_id: int
    username: Optional[str]
    stars_amount: int
    amd_amount: float
    payment_method: Optional[str]
    status: str
    receipt_file_id: Optional[str]
    admin_message_id: Optional[int]
    created_at: int
    updated_at: int

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "Order":
        return cls(**dict(row))


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def create_order(
        self, user_id: int, username: Optional[str], stars_amount: int, amd_amount: float
    ) -> int:
        now = int(time.time())
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """INSERT INTO orders
                   (user_id, username, stars_amount, amd_amount, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'awaiting_receipt', ?, ?)""",
                (user_id, username, stars_amount, amd_amount, now, now),
            )
            await db.commit()
            return cursor.lastrowid

    async def attach_receipt(self, order_id: int, payment_method: str, file_id: str) -> None:
        now = int(time.time())
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """UPDATE orders SET receipt_file_id = ?, payment_method = ?,
                   status = 'pending_review', updated_at = ? WHERE id = ?""",
                (file_id, payment_method, now, order_id),
            )
            await db.commit()

    async def set_admin_message_id(self, order_id: int, message_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE orders SET admin_message_id = ? WHERE id = ?",
                (message_id, order_id),
            )
            await db.commit()

    async def update_status(self, order_id: int, status: str) -> None:
        now = int(time.time())
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )
            await db.commit()

    async def get_order(self, order_id: int) -> Optional[Order]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            return Order.from_row(row) if row else None

    async def get_user_orders(self, user_id: int, limit: int = 10) -> list[Order]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
            return [Order.from_row(r) for r in rows]

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            await db.commit()
