import asyncio
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


purpose_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_number")]
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


NEXT_BLOCK_TEXT = (
    "Здесь будет следующий блок после предназначения.\n\n"
    "Сейчас можешь вставить сюда тот текст, который должен открываться "
    "после кнопки «Самое интересное дальше ➡️»."
)


# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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


# =========================
# BOT / DP
# =========================
TOKEN = "8425994397:AAG2pEZyV-Z-jYSRkBsCbRImm5WNBX5kNUM"


dp = Dispatcher()


# =========================
# СТАРТ
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    if message.text and message.text.startswith("/start paid"):
        user_id = message.from_user.id
        data = user_data.get(user_id)


        if not data:
            await message.answer("Оплата прошла успешно ✅")
            return


        if data.get("paid_shown"):
            return


        data["paid_shown"] = True


        await message.answer("Оплата прошла успешно ✅\n\nПродолжаем 👇")
        await message.answer(
            PURPOSE_INTRO,
            reply_markup=purpose_intro_keyboard
        )
        return


    await message.answer(START_TEXT)
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")


# =========================
# ВВОД ДАТЫ
# =========================
@dp.message()
async def date_handler(message: Message):
    text = (message.text or "").strip()
    digits = re.sub(r"\D", "", text)


    if len(digits) != 8:
        await message.answer(
            "Введите дату рождения.\n"
            "Можно так: ДДММГГГГ или ДД.ММ.ГГГГ"
        )
        return


    day = digits[0:2]
    month = digits[2:4]
    year = digits[4:8]


    date_str = f"{day}.{month}.{year}"


    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await message.answer("Такой даты не существует. Проверьте ввод.")
        return


    soul_number = calculate_soul(day)
    expression_number = calculate_expression(date_str)
    purpose_number = calculate_purpose(date_str)


    user_data[message.from_user.id] = {
        "date": date_str,
        "soul": soul_number,
        "expression": expression_number,
        "purpose": purpose_number,
        "paid_shown": False,
    }


    await message.answer("⏳ Анализируем данные...")
    await asyncio.sleep(2)
    await message.answer("Почти готово...")
    await asyncio.sleep(2)


    await message.answer(f"Дата принята ✅\n{date_str}")
    await asyncio.sleep(1)


    await message.answer(SOUL_INTRO, reply_markup=soul_intro_keyboard)


    asyncio.create_task(remind_later(message))
    asyncio.create_task(remind_next_day(message))


# =========================
# ШАГ 1: ЧИСЛО ДУШИ
# =========================
@dp.callback_query(lambda c: c.data == "show_soul")
async def show_soul_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)


    if not data:
        await callback.message.answer("Сначала введите дату рождения.")
        await callback.answer()
        return


    soul = data["soul"]


    await callback.message.answer(
        SOUL_TEXTS[soul],
        reply_markup=soul_result_keyboard
    )
    await callback.answer()


# =========================
# ШАГ 2: ВСТУПЛЕНИЕ К ЭКСПРЕССИИ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression_intro")
async def show_expression_intro_handler(callback: CallbackQuery):
    await callback.message.answer(
        EXPRESSION_INTRO,
        reply_markup=expression_intro_keyboard
    )
    await callback.answer()


# =========================
# ШАГ 3: ЭКСПРЕССИЯ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression")
async def show_expression_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)


    if not data:
        await callback.message.answer("Сначала введите дату рождения.")
        await callback.answer()
        return


    expression = data["expression"]


    await callback.message.answer(
        EXPRESSION_TEXTS[expression],
        reply_markup=open_full_keyboard
    )
    await callback.answer()


# =========================
# ШАГ 4: ПРОДАЖА
# =========================
@dp.callback_query(lambda c: c.data == "open_sales")
async def open_sales_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)


    if data and data.get("paid_shown"):
        await callback.answer()
        return


    await callback.message.answer(
        SALES_TEXT,
        reply_markup=get_pay_keyboard(user_id)
    )
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 1
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_intro")
async def show_purpose_intro_handler(callback: CallbackQuery):
    await callback.message.answer(
        PURPOSE_INTRO,
        reply_markup=purpose_intro_keyboard
    )
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 2
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_number")
async def show_purpose_number_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)


    if not data:
        await callback.message.answer("Сначала введите дату рождения.")
        await callback.answer()
        return


    purpose = data.get("purpose")


    if purpose not in PURPOSE_TEXTS:
        await callback.message.answer("Не удалось определить предназначение.")
        await callback.answer()
        return


    text = (
        f"Предназначение этого человека — {purpose}\n\n"
        f"{PURPOSE_TEXTS[purpose]}"
    )


    await callback.message.answer(
        text,
        reply_markup=purpose_number_keyboard
    )
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 3
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_outro")
async def show_purpose_outro_handler(callback: CallbackQuery):
    await callback.message.answer(
        PURPOSE_OUTRO,
        reply_markup=purpose_outro_keyboard
    )
    await callback.answer()


# =========================
# СЛЕДУЮЩИЙ БЛОК ПОСЛЕ PURPOSE OUTRO
# =========================
@dp.callback_query(lambda c: c.data == "show_next_block")
async def show_next_block_handler(callback: CallbackQuery):
    await callback.message.answer(NEXT_BLOCK_TEXT)
    await callback.answer()


# =========================
# НАПОМИНАНИЯ
# =========================
async def remind_later(message: Message):
    await asyncio.sleep(600)


    await message.answer(
        "Вы остановились на самом интересном месте.\n\n"
        "Дальше — больше про отношения, сценарии и предназначение.\n\n"
        "Доступ всё ещё открыт 👇",
        reply_markup=get_pay_keyboard(message.from_user.id)
    )


async def remind_next_day(message: Message):
    await asyncio.sleep(86400)


    await message.answer(
        "Иногда одного первого впечатления мало.\n\n"
        "Полный разбор помогает увидеть связи глубже:\n"
        "в отношениях, повторяющихся сценариях и жизненном пути.\n\n"
        "Если хотите дочитать — доступ открыт 👇",
        reply_markup=get_pay_keyboard(message.from_user.id)
    )


# =========================
# ЗАПУСК
# =========================
async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
