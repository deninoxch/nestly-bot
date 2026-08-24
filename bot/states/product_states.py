from aiogram.fsm.state import State, StatesGroup


class AddCategoryStates(StatesGroup):
    waiting_for_parent = State()
    waiting_for_name_ru = State()
    waiting_for_name_en = State()


class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name_ru = State()
    waiting_for_name_en = State()
    waiting_for_description_ru = State()
    waiting_for_description_en = State()
    waiting_for_country = State()
    waiting_for_price = State()
    waiting_for_photos = State()

class EditProductStates(StatesGroup):
    waiting_for_new_price = State()