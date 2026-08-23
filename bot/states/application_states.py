from aiogram.fsm.state import State, StatesGroup


class CooperationStates(StatesGroup):
    waiting_for_company_name = State()
    waiting_for_contact_info = State()
    waiting_for_message = State()