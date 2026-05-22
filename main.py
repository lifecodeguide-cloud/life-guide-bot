import asyncio
import os
import re
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
    FSInputFile,
    URLInputFile,
)

from soul_texts import SOUL_TEXTS, SOUL_INTRO
from expression_texts import EXPRESSION_TEXTS, EXPRESSION_INTRO
from purpose_texts import PURPOSE_TEXTS, PURPOSE_INTRO, PURPOSE_OUTRO

from varna_texts import (
    VARNA_INTRO,
    VARNA_MIX_EXPLANATION,
    VARNA_RESULT_INTRO,
    VARNA_FULL_TEXTS,
    VARNA_SECONDARY_TEXTS,
)

from destiny_texts import DESTINY_INTRO, DESTINY_TEXTS, DESTINY_OUTRO
from final_texts import FINAL_OUTRO


logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "life_guide_bot")
COMPATIBILITY_BOT_URL = os.getenv("COMPATIBILITY_BOT_URL", "https://t.me/love_guide_bot")
GIFT_PDF_URL = os.getenv("GIFT_PDF_URL", "")
GIFT_PDF_PATH = os.getenv("GIFT_PDF_PATH", "")

dp = Dispatcher()
user_data = {}


def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "date": None,
            "soul": None,
            "expression": None,
            "purpose": None,
            "destiny": None,
            "varna_main": None,
            "varna_secondary": None,
            "paid": False,
            "paid_shown": False,
            "stage": "new",
        }
    return user_data[user_id]


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


def calculate_destiny(date_str: str) -> int:
    total = sum(int(d) for d in date_str if d.isdigit())
    return reduce_to_digit(total)


VARNA_MAP = {
    1: "kshatriya",
    2: "vaishya",
    3: "brahman",
    4: "shudra",
    5: "vaishya",
    6: "brahman",
    7: "shudra",
    8: "shudra",
    9: "kshatriya",
}


def calculate_varna_main(date_str: str):

    day, month, year = map(int, date_str.split("."))

    soul = reduce_to_digit(day)

    expression = reduce_to_digit(day + month)

    year_number = reduce_to_digit(
        sum(int(d) for d in str(year))
    )

    destiny = reduce_to_digit(
        sum(int(d) for d in date_str if d.isdigit())
    )

    weights = {}

    def add(number, percent):

        varna = VARNA_MAP[number]

        weights[varna] = (
            weights.get(varna, 0)
            + percent
        )

    add(soul, 40)
    add(expression, 10)
    add(year_number, 10)
    add(destiny, 40)

    sorted_varnas = sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_varnas[0][0]


def calculate_varna_secondary(date_str: str):

    day, month, year = map(int, date_str.split("."))

    soul = reduce_to_digit(day)

    expression = reduce_to_digit(day + month)

    year_number = reduce_to_digit(
        sum(int(d) for d in str(year))
    )

    destiny = reduce_to_digit(
        sum(int(d) for d in date_str if d.isdigit())
    )

    weights = {}

    def add(number, percent):

        varna = VARNA_MAP[number]

        weights[varna] = (
            weights.get(varna, 0)
            + percent
        )

    add(soul, 40)
    add(expression, 10)
    add(year_number, 10)
    add(destiny, 40)

    sorted_varnas = sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True
    )

    if len(sorted_varnas) > 1:
        return sorted_varnas[1][0]

    return None

def has_calculation_data(data: dict) -> bool:
    return (
        data.get("date") is not None
        and data.get("soul") is not None
        and data.get("expression") is not None
        and data.get("purpose") is not None
    )


def ensure_calculations(data: dict):
    date_str = data.get("date")
    if not date_str:
        return

    if data.get("purpose") is None:
        data["purpose"] = calculate_purpose(date_str)

    if data.get("destiny") is None:
        data["destiny"] = calculate_destiny(date_str)

    if data.get("varna_main") is None:
        data["varna_main"] = calculate_varna_main(date_str)

    if data.get("varna_secondary") is None:
        data["varna_secondary"] = calculate_varna_secondary(date_str)


def get_pay_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить полный разбор",
                    url=f"https://life-guide-pay-2026.onrender.com/?user_id={user_id}",
                )
            ]
        ]
    )


soul_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_soul")]]
)

soul_result_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_expression_intro")]]
)

expression_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Продолжить ➡️", callback_data="show_expression")]]
)

open_full_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="open_sales")]]
)

purpose_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_text")]]
)

purpose_text_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_outro")]]
)

purpose_outro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Желания", callback_data="show_varna_intro")]]
)

varna_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_varna_mix")]]
)

varna_mix_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_varna_result")]]
)

varna_result_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Число судьбы", callback_data="show_destiny_intro")]]
)

destiny_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_destiny_text")]]
)

destiny_text_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Важно", callback_data="show_destiny_outro")]]
)

destiny_outro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Дальше ➡️", callback_data="show_final_outro")]]
)

final_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Поделиться", callback_data="share_bot")],
        [InlineKeyboardButton(text="Совместимость", url=COMPATIBILITY_BOT_URL)],
        [InlineKeyboardButton(text="Другая дата", callback_data="other_date")],
    ]
)

gift_keyboard_buttons = [[InlineKeyboardButton(
    text="Поделиться ботом",
    url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=Посмотри — интересно ✨ ✨"
)]]
gift_keyboard_buttons.append([
    InlineKeyboardButton(
        text="Забрать подарок 🎁",
        callback_data="get_gift_pdf"
    )
])

gift_keyboard = InlineKeyboardMarkup(inline_keyboard=gift_keyboard_buttons)


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


async def safe_answer_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass


async def send_paid_flow(message: Message, data: dict):
    data["paid"] = True
    data["paid_shown"] = True
    data["stage"] = "purpose_intro_shown"

    await message.answer(
        "Оплата прошла успешно ✅\n\nПродолжаем 👇",
        reply_markup=ReplyKeyboardRemove(),
    )

    await message.answer(PURPOSE_INTRO, reply_markup=purpose_intro_keyboard)


async def send_purpose_text(callback: CallbackQuery, data: dict):
    ensure_calculations(data)

    purpose = data.get("purpose")
    if purpose is None:
        await callback.message.answer("Не удалось определить предназначение.")
        return

    purpose_text = PURPOSE_TEXTS.get(purpose)
    if not purpose_text:
        await callback.message.answer(f"Не найден текст для числа предназначения {purpose}.")
        return

    await callback.message.answer(
        f"Предназначение {purpose}\n\n{purpose_text}",
        reply_markup=purpose_text_keyboard,
    )

    data["stage"] = "purpose_text_shown"


def build_varna_result_text(data: dict) -> str:
    ensure_calculations(data)

    main = data.get("varna_main")
    secondary = data.get("varna_secondary")

    parts = [VARNA_RESULT_INTRO]

    main_text = VARNA_FULL_TEXTS.get(main)
    if main_text:
        parts.append(main_text)
    else:
        parts.append(f"Не найден основной текст варны для числа {main}.")

    if secondary and secondary != main:
        secondary_text = VARNA_SECONDARY_TEXTS.get(secondary)
        if secondary_text:
            parts.append(secondary_text)

    return "\n\n".join(parts)


async def send_destiny_text(callback: CallbackQuery, data: dict):
    ensure_calculations(data)

    destiny = data.get("destiny")
    if destiny is None:
        await callback.message.answer("Не удалось определить число судьбы.")
        return

    destiny_text = DESTINY_TEXTS.get(destiny)
    if not destiny_text:
        await callback.message.answer(f"Не найден текст для числа судьбы {destiny}.")
        return

    await callback.message.answer(
        destiny_text,
        reply_markup=destiny_text_keyboard,
    )

    data["stage"] = "destiny_text_shown"


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    data = get_user(user_id)
    text = (message.text or "").strip()

    if text.startswith("/start paid"):
        data["paid"] = True

        if not has_calculation_data(data):
            data["stage"] = "awaiting_date_after_payment"
            await message.answer(
                "Оплата прошла успешно ✅\n\n"
                "Теперь отправьте дату рождения в формате ДД.ММ.ГГГГ"
            )
            return

        await send_paid_flow(message, data)
        return

    if data.get("paid"):
        stage = data.get("stage")

        await message.answer(
            "Вы уже открыли полный разбор ✅\n\n"
            "Продолжаем с того места, где остановились 👇"
        )

        if stage == "purpose_intro_shown":
            await message.answer(PURPOSE_INTRO, reply_markup=purpose_intro_keyboard)
            return

        if stage == "purpose_text_shown":
            await send_purpose_text_from_message(message, data)
            return

        if stage == "purpose_outro_shown":
            await message.answer(PURPOSE_OUTRO, reply_markup=purpose_outro_keyboard)
            return

        if stage == "varna_intro_shown":
            await message.answer(VARNA_INTRO, reply_markup=varna_intro_keyboard)
            return

        if stage == "varna_mix_shown":
            await message.answer(VARNA_MIX_EXPLANATION, reply_markup=varna_mix_keyboard)
            return

        if stage == "varna_result_shown":
            await message.answer(build_varna_result_text(data), reply_markup=varna_result_keyboard)
            return

        if stage == "destiny_intro_shown":
            await message.answer(DESTINY_INTRO, reply_markup=destiny_intro_keyboard)
            return

        if stage == "destiny_text_shown":
            await send_destiny_text_from_message(message, data)
            return

        if stage == "destiny_outro_shown":
            await message.answer(DESTINY_OUTRO, reply_markup=destiny_outro_keyboard)
            return

        if stage == "final_outro_shown":
            await message.answer(FINAL_OUTRO, reply_markup=final_keyboard)
            return

        await send_paid_flow(message, data)
        return

    await message.answer(START_TEXT)
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")


async def send_purpose_text_from_message(message: Message, data: dict):
    ensure_calculations(data)

    purpose = data.get("purpose")
    purpose_text = PURPOSE_TEXTS.get(purpose)

    if not purpose or not purpose_text:
        await message.answer("Не удалось восстановить текст предназначения.")
        return

    await message.answer(
        f"Предназначение {purpose}\n\n{purpose_text}",
        reply_markup=purpose_text_keyboard,
    )


async def send_destiny_text_from_message(message: Message, data: dict):
    ensure_calculations(data)

    destiny = data.get("destiny")
    destiny_text = DESTINY_TEXTS.get(destiny)

    if not destiny or not destiny_text:
        await message.answer("Не удалось восстановить текст числа судьбы.")
        return

    await message.answer(
        f"Число судьбы {destiny}\n\n{destiny_text}",
        reply_markup=destiny_text_keyboard,
    )


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
    destiny_number = calculate_destiny(date_str)
    varna_main = calculate_varna_main(date_str)
    varna_secondary = calculate_varna_secondary(date_str)

    old_data = get_user(message.from_user.id)

    user_data[message.from_user.id] = {
        "date": date_str,
        "soul": soul_number,
        "expression": expression_number,
        "purpose": purpose_number,
        "destiny": destiny_number,
        "varna_main": varna_main,
        "varna_secondary": varna_secondary,
        "paid": old_data.get("paid", False),
        "paid_shown": old_data.get("paid_shown", False),
        "stage": "date_entered",
    }

    data = get_user(message.from_user.id)

    await message.answer("⏳ Анализируем данные...")
    await asyncio.sleep(2)
    await message.answer("Почти готово...")
    await asyncio.sleep(2)
    await message.answer(f"Дата принята ✅\n{date_str}")
    await asyncio.sleep(1)

    if data.get("paid"):
        await send_paid_flow(message, data)
        return

    await message.answer(SOUL_INTRO, reply_markup=soul_intro_keyboard)
    data["stage"] = "soul_intro_shown"

    asyncio.create_task(remind_later(message))
    asyncio.create_task(remind_next_day(message))


@dp.callback_query(lambda c: c.data == "show_soul")
async def show_soul_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    soul = data["soul"]

    await callback.message.answer(SOUL_TEXTS[soul], reply_markup=soul_result_keyboard)
    data["stage"] = "soul_shown"


@dp.callback_query(lambda c: c.data == "show_expression_intro")
async def show_expression_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(EXPRESSION_INTRO, reply_markup=expression_intro_keyboard)
    data["stage"] = "expression_intro_shown"


@dp.callback_query(lambda c: c.data == "show_expression")
async def show_expression_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    expression = data["expression"]

    await callback.message.answer(EXPRESSION_TEXTS[expression], reply_markup=open_full_keyboard)
    data["stage"] = "expression_shown"


@dp.callback_query(lambda c: c.data == "open_sales")
async def open_sales_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    user_id = callback.from_user.id
    data = get_user(user_id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    if data.get("paid"):
        await send_paid_flow(callback.message, data)
        return

    await callback.message.answer(SALES_TEXT, reply_markup=get_pay_keyboard(user_id))
    data["stage"] = "sales_shown"


@dp.callback_query(lambda c: c.data == "show_purpose_text")
async def show_purpose_text_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    await send_purpose_text(callback, data)


@dp.callback_query(lambda c: c.data == "show_purpose_outro")
async def show_purpose_outro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(PURPOSE_OUTRO, reply_markup=purpose_outro_keyboard)
    data["stage"] = "purpose_outro_shown"


@dp.callback_query(lambda c: c.data == "show_varna_intro")
async def show_varna_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(VARNA_INTRO, reply_markup=varna_intro_keyboard)
    data["stage"] = "varna_intro_shown"


@dp.callback_query(lambda c: c.data == "show_varna_mix")
async def show_varna_mix_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(VARNA_MIX_EXPLANATION, reply_markup=varna_mix_keyboard)
    data["stage"] = "varna_mix_shown"


@dp.callback_query(lambda c: c.data == "show_varna_result")
async def show_varna_result_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    await callback.message.answer(build_varna_result_text(data), reply_markup=varna_result_keyboard)
    data["stage"] = "varna_result_shown"


@dp.callback_query(lambda c: c.data == "show_destiny_intro")
async def show_destiny_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(DESTINY_INTRO, reply_markup=destiny_intro_keyboard)
    data["stage"] = "destiny_intro_shown"


@dp.callback_query(lambda c: c.data == "show_destiny_text")
async def show_destiny_text_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    await send_destiny_text(callback, data)


@dp.callback_query(lambda c: c.data == "show_destiny_outro")
async def show_destiny_outro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(DESTINY_OUTRO, reply_markup=destiny_outro_keyboard)
    data["stage"] = "destiny_outro_shown"


@dp.callback_query(lambda c: c.data == "show_final_outro")
async def show_final_outro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(FINAL_OUTRO, reply_markup=final_keyboard)
    data["stage"] = "final_outro_shown"


@dp.callback_query(lambda c: c.data == "share_bot")
async def share_bot_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    bot_link = f"https://t.me/{BOT_USERNAME}"

    await callback.message.answer(
        "Можно поделиться ботом по этой ссылке:\n\n"
        f"{bot_link}\n\n"
        "После этого можно забрать подарок 👇",
        reply_markup=gift_keyboard,
    )


@dp.callback_query(lambda c: c.data == "get_gift_pdf")
async def get_gift_pdf_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    await callback.message.answer(
    "🎁 Ваш подарок готов\n\n"
    "PDF-инструкция «Персональный день силы» 👇"
)

if GIFT_PDF_URL:
    await callback.message.answer_document(
        URLInputFile(GIFT_PDF_URL)
    )
    return

if GIFT_PDF_PATH and os.path.exists(GIFT_PDF_PATH):
    await callback.message.answer_document(
        FSInputFile(GIFT_PDF_PATH)
    )
    return

await callback.message.answer(
    "PDF пока не подключён."
)


@dp.callback_query(lambda c: c.data == "other_date")
async def other_date_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)
    paid = data.get("paid", False)

    user_data[callback.from_user.id] = {
        "date": None,
        "soul": None,
        "expression": None,
        "purpose": None,
        "destiny": None,
        "varna_main": None,
        "varna_secondary": None,
        "paid": paid,
        "paid_shown": data.get("paid_shown", False),
        "stage": "awaiting_other_date",
    }

    await callback.message.answer("Введите другую дату рождения в формате ДД.ММ.ГГГГ")


async def remind_later(message: Message):
    await asyncio.sleep(600)

    data = user_data.get(message.from_user.id)

    if not data or data.get("paid"):
        return

    await message.answer(
        "Вы остановились на самом интересном месте.\n\n"
        "Дальше — больше про отношения, сценарии и предназначение.\n\n"
        "Доступ всё ещё открыт 👇",
        reply_markup=get_pay_keyboard(message.from_user.id),
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
        reply_markup=get_pay_keyboard(message.from_user.id),
    )


@dp.errors()
async def errors_handler(event):
    logging.exception("Ошибка в боте: %s", event.exception)
    return True


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
