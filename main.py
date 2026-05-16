import asyncio
import os
import re
import logging
import json
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from soul_texts import SOUL_TEXTS, SOUL_INTRO
from expression_texts import EXPRESSION_TEXTS, EXPRESSION_INTRO
from purpose_texts import PURPOSE_TEXTS, PURPOSE_INTRO, PURPOSE_OUTRO
from varna_texts import (
    VARNA_INTRO,
    VARNA_MIX_EXPLANATION,
    VARNA_RESULT_INTRO,
    VARNA_FULL_TEXTS,
    VARNA_SECONDARY_TEXTS,
    VARNA_NAMES,
    VARNA_SHORT_NAMES,
    calculate_varna
)


# =========================
# ЛОГИ
# =========================
logging.basicConfig(level=logging.INFO)


# =========================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
# =========================
user_data = {}
DATA_FILE = "users.json"


def load_users():
    global user_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            user_data = {int(k): v for k, v in user_data.items()}
    except Exception:
        user_data = {}


def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)


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
        save_users()
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


purpose_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_text")]
    ]
)


purpose_number_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_purpose_outro")]
    ]
)

purpose_outro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Желания", callback_data="show_varna_intro")]
    ]
)

varna_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_varna_mix")]
    ]
)

varna_mix_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_varna_result")]
    ]
)

varna_main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Описание варны ➡️", callback_data="show_varna_main")]
    ]
)

varna_destiny_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Число судьбы ➡️", callback_data="show_next_block")]
    ]
)

paid_continue_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить разбор ➡️", callback_data="paid_continue")]
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
    "На этом текущая часть полного разбора завершена.\n\n"
    "Дальше сюда можно подключить следующий блок, когда он будет готов."
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


def has_calculation_data(data: dict) -> bool:
    return (
        data.get("date") is not None
        and data.get("soul") is not None
        and data.get("expression") is not None
        and data.get("purpose") is not None
    )


def ensure_purpose(data: dict):
    if data.get("purpose") is None and data.get("date"):
        try:
            data["purpose"] = calculate_purpose(data["date"])
            save_users()
        except Exception:
            data["purpose"] = None
    return data.get("purpose")


def build_varna_short_text(date_str: str, data: dict) -> str:
    day, month, year = map(int, date_str.split("."))

    result = calculate_varna(day, month, year)
    data["varna_result"] = result
    save_users()

    scores = result["scores"]
    details = result["details"]

    text = ""
    text += VARNA_RESULT_INTRO
    text += "Расчёт по вашей дате рождения:\n\n"

    for item in details:
        text += (
            f"{item['title']}: {item['number']} → "
            f"{VARNA_SHORT_NAMES[item['varna']]} → {item['percent']}%\n"
        )

    text += "\nИтоговое распределение:\n"
    text += f"Брахман: {scores['brahman']}%\n"
    text += f"Кшатрий: {scores['kshatriya']}%\n"
    text += f"Вайшья: {scores['vaishya']}%\n"
    text += f"Шудра: {scores['shudra']}%\n\n"

    main_varna = result["main_varna"]
    main_score = result["main_score"]

    top_varnas = [
        varna for varna, score in scores.items()
        if score == main_score
    ]

    if len(top_varnas) > 1:
        names = " и ".join(VARNA_SHORT_NAMES[v] for v in top_varnas)
        text += f"По данной методике у вас смешанный тип: {names}.\n"
    else:
        text += (
            f"По данной методике ваш основной психотип:\n"
            f"{VARNA_NAMES[main_varna]} — {main_score}%\n"
        )

    return text


async def safe_answer_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass


async def send_paid_flow(message: Message, data: dict):
    data["paid"] = True
    data["paid_shown"] = True
    data["stage"] = "purpose_intro_shown"
    save_users()

    await message.answer("Оплата прошла успешно ✅\n\nПродолжаем 👇")
    await message.answer(
        PURPOSE_INTRO,
        reply_markup=purpose_intro_keyboard
    )


async def send_purpose_number(callback: CallbackQuery, data: dict):
    purpose = ensure_purpose(data)

    if purpose is None:
        await callback.message.answer("Не удалось определить предназначение.")
        return

    purpose_text = PURPOSE_TEXTS.get(purpose)
    if not purpose_text:
        await callback.message.answer(f"Не найден текст для числа предназначения {purpose}.")
        return

    await callback.message.answer(
        f"Предназначение {purpose}\n\n{purpose_text}",
        reply_markup=purpose_number_keyboard
    )
    data["stage"] = "purpose_result_shown"
    save_users()


# =========================
# BOT / DP
# =========================
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

    if text.startswith("/start paid"):
        data["paid"] = True
        save_users()

        if not has_calculation_data(data):
            data["stage"] = "awaiting_date_after_payment"
            save_users()
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
            await message.answer(
                PURPOSE_INTRO,
                reply_markup=purpose_intro_keyboard
            )
            return

        if stage == "purpose_result_shown":
            purpose = ensure_purpose(data)
            purpose_text = PURPOSE_TEXTS.get(purpose)
            if purpose and purpose_text:
                await message.answer(
                    f"Предназначение {purpose}\n\n{purpose_text}",
                    reply_markup=purpose_number_keyboard
                )
                return

        if stage == "purpose_outro_shown":
            await message.answer(
                PURPOSE_OUTRO,
                reply_markup=purpose_outro_keyboard
            )
            return

        if stage == "varna_intro_shown":
            await message.answer(
                VARNA_INTRO,
                reply_markup=varna_intro_keyboard
            )
            return

        if stage == "varna_mix_shown":
            await message.answer(
                VARNA_MIX_EXPLANATION,
                reply_markup=varna_mix_keyboard
            )
            return

        await send_paid_flow(message, data)
        return

    await message.answer(START_TEXT)
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")


# =========================
# ПРОДОЛЖЕНИЕ ПОСЛЕ ОПЛАТЫ БЕЗ /START
# =========================
@dp.callback_query(lambda c: c.data == "paid_continue")
async def paid_continue_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    user_id = callback.from_user.id
    data = get_user(user_id)

    data["paid"] = True
    save_users()

    if not has_calculation_data(data):
        data["stage"] = "awaiting_date_after_payment"
        save_users()
        await callback.message.answer(
            "Оплата прошла успешно ✅\n\n"
            "Теперь отправьте дату рождения в формате ДД.ММ.ГГГГ"
        )
        return

    await send_paid_flow(callback.message, data)


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
    save_users()

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
    save_users()

    asyncio.create_task(remind_later(message))
    asyncio.create_task(remind_next_day(message))


# =========================
# ШАГ 1: ЧИСЛО ДУШИ
# =========================
@dp.callback_query(lambda c: c.data == "show_soul")
async def show_soul_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    soul = data["soul"]

    await callback.message.answer(
        SOUL_TEXTS[soul],
        reply_markup=soul_result_keyboard
    )
    data["stage"] = "soul_shown"
    save_users()


# =========================
# ШАГ 2: ВСТУПЛЕНИЕ К ЭКСПРЕССИИ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression_intro")
async def show_expression_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(
        EXPRESSION_INTRO,
        reply_markup=expression_intro_keyboard
    )
    data["stage"] = "expression_intro_shown"
    save_users()


# =========================
# ШАГ 3: ЭКСПРЕССИЯ
# =========================
@dp.callback_query(lambda c: c.data == "show_expression")
async def show_expression_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    expression = data["expression"]

    await callback.message.answer(
        EXPRESSION_TEXTS[expression],
        reply_markup=open_full_keyboard
    )
    data["stage"] = "expression_shown"
    save_users()


# =========================
# ШАГ 4: ПРОДАЖА
# =========================
@dp.callback_query(lambda c: c.data == "open_sales")
async def open_sales_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    user_id = callback.from_user.id
    data = get_user(user_id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    if data.get("paid"):
        await callback.message.answer("Оплата подтверждена ✅\n\nПродолжаем 👇")
        await send_paid_flow(callback.message, data)
        return

    await callback.message.answer(
        SALES_TEXT,
        reply_markup=get_pay_keyboard(user_id)
    )
    data["stage"] = "sales_shown"
    save_users()


# =========================
# ПРЕДНАЗНАЧЕНИЕ — ЧАСТЬ 1
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_intro")
async def show_purpose_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    user_id = callback.from_user.id
    data = get_user(user_id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(
        PURPOSE_INTRO,
        reply_markup=purpose_intro_keyboard
    )
    data["stage"] = "purpose_intro_shown"
    save_users()


# =========================
# ПРЕДНАЗНАЧЕНИЕ — ЧАСТЬ 2
# =========================
@dp.callback_query(lambda c: c.data in {"show_purpose_text", "show_purpose_number"})
async def show_purpose_text_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    await send_purpose_number(callback, data)


@dp.callback_query(lambda c: c.data.startswith("show_purpose_number:"))
async def show_purpose_number_old_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    await send_purpose_number(callback, data)


# =========================
# ПРЕДНАЗНАЧЕНИЕ — ЧАСТЬ 3
# =========================
@dp.callback_query(lambda c: c.data == "show_purpose_outro")
async def show_purpose_outro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    await callback.message.answer(
        PURPOSE_OUTRO,
        reply_markup=purpose_outro_keyboard
    )
    data["stage"] = "purpose_outro_shown"
    save_users()


# =========================
# ВАЖНО / ВАРНЫ
# =========================
@dp.callback_query(lambda c: c.data == "show_varna_intro")
async def show_varna_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(
        VARNA_INTRO,
        reply_markup=varna_intro_keyboard
    )

    data["stage"] = "varna_intro_shown"
    save_users()


@dp.callback_query(lambda c: c.data == "show_varna_mix")
async def show_varna_mix_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    await callback.message.answer(
        VARNA_MIX_EXPLANATION,
        reply_markup=varna_mix_keyboard
    )

    data["stage"] = "varna_mix_shown"
    save_users()


@dp.callback_query(lambda c: c.data == "show_varna_result")
async def show_varna_result_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    varna_text = build_varna_short_text(data["date"], data)

    await callback.message.answer(
        varna_text,
        reply_markup=varna_main_keyboard
    )

    data["stage"] = "varna_result_shown"
    save_users()


@dp.callback_query(lambda c: c.data == "show_varna_main")
async def show_varna_main_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)
    result = data.get("varna_result")

    if not result:
        if not data.get("date"):
            await callback.message.answer("Сначала введите дату рождения.")
            return
        build_varna_short_text(data["date"], data)
        result = data.get("varna_result")

    scores = result["scores"]
    main_score = result["main_score"]
    main_varna = result["main_varna"]
    second_varna = result["second_varna"]
    second_score = result["second_score"]

    top_varnas = [
        varna for varna, score in scores.items()
        if score == main_score
    ]

    text = ""

    if len(top_varnas) > 1:
        for varna in top_varnas:
            text += VARNA_FULL_TEXTS[varna] + "\n\n"
    else:
        text += VARNA_FULL_TEXTS[main_varna] + "\n\n"

        if second_score >= 20:
            text += (
                f"Дополнительное влияние: "
                f"{VARNA_SHORT_NAMES[second_varna]} — {second_score}%\n\n"
            )
            text += VARNA_SECONDARY_TEXTS[second_varna] + "\n\n"

    await callback.message.answer(
        text,
        reply_markup=varna_destiny_keyboard
    )

    data["stage"] = "varna_full_shown"
    save_users()


# =========================
# СЛЕДУЮЩИЙ БЛОК / ВАРНЫ
# =========================
@dp.callback_query(lambda c: c.data == "show_next_block")
async def show_next_block_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    data["stage"] = "next_block_shown"
    save_users()
    await callback.message.answer(NEXT_BLOCK_TEXT)


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
# ОБЩИЙ ХЕНДЛЕР ОШИБОК
# =========================
@dp.errors()
async def errors_handler(event):
    logging.exception("Ошибка в боте: %s", event.exception)
    return True


# =========================
# ЗАПУСК
# =========================
async def main():
    load_users()

    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
