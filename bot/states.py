from aiogram.fsm.state import State, StatesGroup


class PurchaseStates(StatesGroup):
    choosing_amount = State()
    entering_custom_amount = State()
    waiting_receipt = State()
