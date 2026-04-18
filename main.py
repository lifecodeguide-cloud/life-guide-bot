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


def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "date": None,
            "soul": None,
            "expression": None,
            "purpose": None,
            "paid": False,
            "paid_shown": False,
            "stage": "new",  # new / date_entered / soul_shown / expression_intro_shown / expression_shown / sales_shown / purpose_intro_shown / purpose_number_shown / purpose_outro_shown / next_block_shown
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

# ИСПРАВЛЕНО: отдельный callback только для платного вступления
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


async def send_paid_flow(message: Message, data: dict):
    """
    Продолжение после оплаты.
    Никакого повторного запуска полной воронки.
    """
    if data.get("paid_shown"):
        return

    data["paid"] = True
    data["paid_shown"] = True
    data["stage"] = "purpose_intro_shown"

    await message.answer("Оплата прошла успешно ✅\n\nПродолжаем 👇")
    await message.answer(
        PURPOSE_INTRO,
        reply_markup=purpose_intro_keyboard
    )


def has_calculation_data(data: dict) -> bool:
    return (
        data.get("date") is not None
        and data.get("soul") is not None
        and data.get("expression") is not None
        and data.get("purpose") is not None
    )


# =========================
# BOT / DP
# =========================
import os
TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


# =========================
# СТАРТ
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    data = get_user(user_id)
    text = (message.text or "").strip()

    # ВАЖНО:
    # после оплаты НЕ запускаем общий старт заново,
    # а продолжаем сценарий с нужного места
    if text.startswith("/start paid"):
        if not has_calculation_data(data):
            data["paid"] = True
            # ИСПРАВЛЕНО: не ставим paid_shown=True заранее,
            # чтобы после ввода даты send_paid_flow реально отправил вступление
            data["paid_shown"] = False
            data["stage"] = "awaiting_date_after_payment"

            await message.answer(
                "Оплата прошла успешно ✅\n\n"
                "Теперь отправьте дату рождения в формате ДД.ММ.ГГГГ"
            )
            return

        await send_paid_flow(message, data)
        return

    # Если человек уже оплатил и снова нажал /start — не сбрасываем его
    if data.get("paid"):
        if has_calculation_data(data):
            await message.answer(
                "Вы уже открыли полный разбор ✅\n\n"
                "Продолжаем с того места, где остановились 👇"
            )

            stage = data.get("stage")

            if stage in ["purpose_intro_shown", "sales_shown", "expression_shown"]:
                await message.answer(
                    PURPOSE_INTRO,
                    reply_markup=purpose_intro_keyboard
                )
                return

            if stage == "purpose_number_shown":
                purpose = data["purpose"]
                text = (
                    f"Предназначение этого человека — {purpose}\n\n"
                    f"{PURPOSE_TEXTS[purpose]}"
                )
                await message.answer(
                    text,
                    reply_markup=purpose_number_keyboard
                )
                return

            if stage == "purpose_outro_shown":
                await message.answer(
                    PURPOSE_OUTRO,
                    reply_markup=purpose_outro_keyboard
                )
                return

            await message.answer(
                PURPOSE_INTRO,
                reply_markup=purpose_intro_keyboard
            )
            return
        else:
            await message.answer(
                "Оплата уже прошла успешно ✅\n\n"
                "Теперь отправьте дату рождения в формате ДД.ММ.ГГГГ"
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

    old_data = get_user(message.from_user.id)

    user_data[message.from_user.id] = {
        "date": date_str,
        "soul": soul_number,
        "expression": expression_number,
        "purpose": purpose_number,
        "paid": old_data.get("paid", False),
        "paid_shown": old_data.get("paid_shown", False),
        "stage": "date_entered",
    }

    data = user_data[message.from_user.id]

    await message.answer("⏳ Анализируем данные...")
    await asyncio.sleep(2)
    await message.answer("Почти готово...")
    await asyncio.sleep(2)

    await message.answer(f"Дата принята ✅\n{date_str}")
    await asyncio.sleep(1)

    # Если человек уже оплатил раньше — сразу продолжаем платную часть
    if data.get("paid"):
        await send_paid_flow(message, data)
        return

    await message.answer(SOUL_INTRO, reply_markup=soul_intro_keyboard)
    data["stage"] = "soul_intro_shown"

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
    data["stage"] = "soul_shown"
    await callback.answer()


# =========================
# ШАГ 2: ВСТУПЛЕНИЕ К ЭКСПРЕССИИ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression_intro")
async def show_expression_intro_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if data:
        data["stage"] = "expression_intro_shown"

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
    data["stage"] = "expression_shown"
    await callback.answer()


# =========================
# ШАГ 4: ПРОДАЖА
# =========================
@dp.callback_query(lambda c: c.data == "open_sales")
async def open_sales_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if not data:
        await callback.message.answer("Сначала введите дату рождения.")
        await callback.answer()
        return

    # Если уже оплачено — больше не показываем продажу, а продолжаем
    if data.get("paid"):
        await callback.message.answer(
            "Оплата уже подтверждена ✅\n\nПродолжаем 👇"
        )
        await callback.message.answer(
            PURPOSE_INTRO,
            reply_markup=purpose_intro_keyboard
        )
        data["stage"] = "purpose_intro_shown"
        await callback.answer()
        return

    await callback.message.answer(
        SALES_TEXT,
        reply_markup=get_pay_keyboard(user_id)
    )
    data["stage"] = "sales_shown"
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 1
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_intro")
async def show_purpose_intro_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if not data or not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        await callback.answer()
        return

    await callback.message.answer(
        PURPOSE_INTRO,
        reply_markup=purpose_intro_keyboard
    )
    data["stage"] = "purpose_intro_shown"
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 2
# =========================
# ИСПРАВЛЕНО: ловим и старый callback, и новый платный callback
@dp.callback_query(lambda c: c.data in ["show_purpose_number", "show_purpose_number_paid"])
async def show_purpose_number_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if not data:
        await callback.message.answer("Сначала введите дату рождения.")
        await callback.answer()
        return

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        await callback.answer()
        return

    purpose = data.get("purpose")

    if purpose not in PURPOSE_TEXTS:
        await callback.message.answer("Не удалось определить предназначение.")
        await callback.answer()
        return

    text = (
        f"Предназначение  {purpose}\n\n"
        f"{PURPOSE_TEXTS[purpose]}"
    )

    await callback.message.answer(
        text,
        reply_markup=purpose_number_keyboard
    )
    data["stage"] = "purpose_number_shown"
    await callback.answer()


# =========================
# ПРЕДНАЗНАЧЕНИЕ ПОСЛЕ ОПЛАТЫ — ЧАСТЬ 3
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_outro")
async def show_purpose_outro_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if not data or not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        await callback.answer()
        return

    await callback.message.answer(
        PURPOSE_OUTRO,
        reply_markup=purpose_outro_keyboard
    )
    data["stage"] = "purpose_outro_shown"
    await callback.answer()


# =========================
# СЛЕДУЮЩИЙ БЛОК ПОСЛЕ PURPOSE OUTRO
# =========================
@dp.callback_query(lambda c: c.data == "show_next_block")
async def show_next_block_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id)

    if data:
        data["stage"] = "next_block_shown"

    await callback.message.answer(NEXT_BLOCK_TEXT)
    await callback.answer()


# =========================
# НАПОМИНАНИЯ
# =========================
async def remind_later(message: Message):
    await asyncio.sleep(600)

    data = user_data.get(message.from_user.id)
    if not data or data.get("paid"):
        return

    await message.answer(
        "Вы остановились на самом интересном месте.\n\n"
        "Дальше — больше про отношения, сценарии и предназначение.\n\n"
        "Доступ всё ещё открыт 👇",
        reply_markup=get_pay_keyboard(message.from_user.id)
    )


async def remind_next_day(message: Message):
    await asyncio.sleep(86400)

    data = user_data.get(message.from_user.id)
    if not data or data.get("paid"):
        return

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
