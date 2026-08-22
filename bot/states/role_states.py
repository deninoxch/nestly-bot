from aiogram.fsm.state import State, StatesGroup


class AssignAdminStates(StatesGroup):
    waiting_for_telegram_id = State()