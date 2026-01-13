from aiogram.fsm.state import State, StatesGroup

class VacancyForm(StatesGroup):
    format = State()
    experience = State()
    salary = State()
