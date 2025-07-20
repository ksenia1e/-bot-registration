from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()

class AddOrganizer(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_user_name = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()