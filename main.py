import asyncio
import os
import re
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from soul_texts import SOUL_TEXTS, SOUL_INTRO
from expression_texts import EXPRESSION_TEXTS, EXPRESSION_INTRO
from purpose_texts import PURPOSE_TEXTS, PURPOSE_INTRO, PURPOSE_OUTRO


# =========================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
# =========================
user_data = {}


def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "date": None,
            "soul": None,
            "expression": None,
            "purpose": None,
            "paid": False,
            "paid_shown": False,
            "stage": "new",
        }
    return user_data[user_id]


# =========================
# КЛАВИАТУРЫ
# =========================
def get_pay_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить полный разбор",
                    url=f"https://life-guide-pay-2026.onrender.com/?user_id={user_id}"
                )
            ]
        ]
    )


soul_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_soul")]
    ]
)

soul_result_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_expression_intro")]
    ]
)

expression_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить ➡️", callback_data="show_expression")]
    ]
)

open_full_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="open_sales")]
    ]
)

# ❗ ВАЖНО: отдельный callback для платной кнопки
purpose_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_number_paid")]
    ]
)

purpose_number_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_outro")]
    ]
)

purpose_outro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Самое интересное дальше ➡️", callback_data="show_next_block")]
    ]
)


# =========================
# ТЕКСТЫ
# =========================
START_TEXT = (
    "Life Guide приветствует вас ✨\n\n"
    "Дата рождения — это не просто цифры.\n"
    "Иногда в ней скрыто больше, чем мы замечаем о себе сами.\n\n"
    "Проверьте, насколько точно числа отражают ваш характер,\n"
    "внутреннюю природу и жизненный путь.👇\n\n"
)

SALES_TEXT = (
    "Если вы хотите больше понять себя, свои отношения и выборы:\n\n"
    "• базовую природу и внутренний импульс\n"
    "• сильные и уязвимые стороны характера\n"
    "• к каким людям тянет и почему\n"
    "• где возникает напряжение в паре\n"
    "• какие союзы дают рост, а какие — истощают\n"
    "• своё предназначение и более глубокие жизненные сценарии\n\n"
    "Доступ к полному разбору за 4,99 👇"
)

NEXT_BLOCK_TEXT = "Здесь будет блок варн."


# =========================
# ФУНКЦИИ
# =========================
def reduce_to_digit(num: int) -> int:
    while num > 9:
        num = sum(int(d) for d in str(num))
    return num


def calculate_soul(day: str) -> int:
    return int(day)


def calculate_expression(date_str: str) -> int:
    day, month, year = date_str.split(".")
    total = sum(int(d) for d in day + month)
    return reduce_to_digit(total)


def calculate_purpose(date_str: str) -> int:
    day, month, year = date_str.split(".")
    total = sum(int(d) for d in day + month)
    return reduce_to_digit(total)


def ensure_purpose(data: dict):
    if data.get("purpose") is None and data.get("date"):
        data["purpose"] = calculate_purpose(data["date"])
    return data.get("purpose")


async def safe_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except:
        pass


async def send_paid_flow(message: Message, data: dict):
    data["paid"] = True
    data["stage"] = "purpose_intro_shown"

    await message.answer("Оплата прошла успешно ✅\n\nПродолжаем 👇")
    await message.answer(PURPOSE_INTRO, reply_markup=purpose_intro_keyboard)


# =========================
# BOT
# =========================
TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()


# =========================
# СТАРТ
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    data = get_user(message.from_user.id)
    text = (message.text or "").strip()

    if text.startswith("/start paid"):
        data["paid"] = True
        await send_paid_flow(message, data)
        return

    await message.answer(START_TEXT)
    await message.answer("Введите дату рождения")


# =========================
# ДАТА
# =========================
@dp.message()
async def date_handler(message: Message):
    digits = re.sub(r"\D", "", message.text)

    if len(digits) != 8:
        await message.answer("Введите дату корректно")
        return

    date_str = f"{digits[0:2]}.{digits[2:4]}.{digits[4:8]}"

    data = get_user(message.from_user.id)

    data["date"] = date_str
    data["soul"] = calculate_soul(digits[0:2])
    data["expression"] = calculate_expression(date_str)
    data["purpose"] = calculate_purpose(date_str)

    await message.answer(SOUL_INTRO, reply_markup=soul_intro_keyboard)


# =========================
# ДУША
# =========================
@dp.callback_query(lambda c: c.data == "show_soul")
async def show_soul(callback: CallbackQuery):
    await safe_answer(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(
        SOUL_TEXTS[data["soul"]],
        reply_markup=soul_result_keyboard
    )


# =========================
# ЭКСПРЕССИЯ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression_intro")
async def exp_intro(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.answer(EXPRESSION_INTRO, reply_markup=expression_intro_keyboard)


@dp.callback_query(lambda c: c.data == "show_expression")
async def exp(callback: CallbackQuery):
    await safe_answer(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(
        EXPRESSION_TEXTS[data["expression"]],
        reply_markup=open_full_keyboard
    )


# =========================
# ОПЛАТА
# =========================
@dp.callback_query(lambda c: c.data == "open_sales")
async def sales(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.answer(
        SALES_TEXT,
        reply_markup=get_pay_keyboard(callback.from_user.id)
    )


# =========================
# ПРЕДНАЗНАЧЕНИЕ
# =========================
@dp.callback_query(lambda c: c.data in ["show_purpose_number", "show_purpose_number_paid"])
async def purpose_number(callback: CallbackQuery):
    await safe_answer(callback)
    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала оплата")
        return

    purpose = ensure_purpose(data)

    await callback.message.answer(
        f"Предназначение этого человека — {purpose}\n\n{PURPOSE_TEXTS[purpose]}",
        reply_markup=purpose_number_keyboard
    )


@dp.callback_query(lambda c: c.data == "show_purpose_outro")
async def purpose_outro(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.answer(PURPOSE_OUTRO, reply_markup=purpose_outro_keyboard)


@dp.callback_query(lambda c: c.data == "show_next_block")
async def next_block(callback: CallbackQuery):
    await safe_answer(callback)
    await callback.message.answer(NEXT_BLOCK_TEXT)


# =========================
# ЗАПУСК
# =========================
async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
