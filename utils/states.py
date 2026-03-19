# utils/states.py
from aiogram.fsm.state import StatesGroup, State


class PulseTargetState(StatesGroup):
    min = State()
    max = State()