import asyncio
import os
import re
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from soul_texts import SOUL_TEXTS, SOUL_INTRO
from expression_texts import EXPRESSION_TEXTS, EXPRESSION_INTRO
from purpose_texts import PURPOSE_TEXTS, PURPOSE_INTRO, PURPOSE_OUTRO
from destiny_texts import DESTINY_INTRO, DESTINY_TEXTS, DESTINY_OUTRO
from final_texts import FINAL_OUTRO
from varna_texts import (
    VARNA_INTRO,
    VARNA_MIX_EXPLANATION,
    VARNA_RESULT_INTRO,
    VARNA_FULL_TEXTS,
    VARNA_SECONDARY_TEXTS,
)

# =========================
# ЛОГИ
# =========================
logging.basicConfig(level=logging.INFO)


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


def get_purpose_intro_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Дальше ➡️", callback_data=f"show_purpose_number:{user_id}")]
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

paid_continue_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить разбор ➡️", callback_data="paid_continue")]
    ]
)

varna_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_varna_mix")]
    ]
)

varna_mix_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть результат ➡️", callback_data="show_varna_result")]
    ]
)
destiny_intro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Дальше ➡️", callback_data="show_destiny_text")]
    ]
)

destiny_text_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Ваше число судьбы", callback_data="show_destiny_outro")]
    ]
)

destiny_outro_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Что дальше ✨", callback_data="show_final_real")]
    ]
)

final_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Поделиться",
                url="https://t.me/LifeGuideVitaBot"
            )
        ],
        [
            InlineKeyboardButton(
                text="❤️ Совместимость",
                url="https://t.me/love_guide_bot"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Рассчитать другую дату",
                url="https://t.me/LifeGuideVitaBot?start=new"
            )
        ]
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
    "Здесь будет блок варн.\n\n"
    "Сейчас можешь вставить сюда текст или запуск следующего платного блока."
)


# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================
VARNA_NUMBERS = {
    "brahman": [3, 6],
    "kshatriya": [1, 9],
    "vaishya": [2, 5],
    "shudra": [4, 7, 8],
}

VARNA_NAMES = {
    "brahman": "Брахман / Путь Мудреца",
    "kshatriya": "Кшатрий / Путь Лидера-Воина",
    "vaishya": "Вайшья / Путь Бизнесмена",
    "shudra": "Шудра / Путь Творца-Созидателя",
}

VARNA_SHORT_NAMES = {
    "brahman": "Брахман",
    "kshatriya": "Кшатрий",
    "vaishya": "Вайшья",
    "shudra": "Шудра",
}


def get_varna_by_number(number):
    for varna, numbers in VARNA_NUMBERS.items():
        if number in numbers:
            return varna
    return None

def calculate_varna(date_str: str):

    day, month, year = date_str.split(".")

    day = int(day)
    month = int(month)
    year = int(year)

    soul_number = reduce_to_digit(day)

    month_number = reduce_to_digit(month)

    year_number = reduce_to_digit(
        sum(int(d) for d in str(year))
    )

    destiny_number = reduce_to_digit(
        sum(int(d) for d in date_str if d.isdigit())
    )

    scores = {
        "brahman": 0,
        "kshatriya": 0,
        "vaishya": 0,
        "shudra": 0,
    }

    calculations = [
        (soul_number, 40),
        (month_number, 10),
        (year_number, 10),
        (destiny_number, 40),
    ]

    for number, percent in calculations:

        varna = get_varna_by_number(number)

        if varna:
            scores[varna] += percent

    return scores

def build_varna_result_text(date_str: str):

    scores = calculate_varna(date_str)

    sorted_scores = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    main_varna = sorted_scores[0][0]
    main_score = sorted_scores[0][1]

    second_varna = sorted_scores[1][0]
    second_score = sorted_scores[1][1]

    top_varnas = [
        varna for varna, score in scores.items()
        if score == main_score
    ]

    text = ""
    text += VARNA_RESULT_INTRO

    text += "Итоговое распределение:\n"
    text += f"Брахман: {scores['brahman']}%\n"
    text += f"Кшатрий: {scores['kshatriya']}%\n"
    text += f"Вайшья: {scores['vaishya']}%\n"
    text += f"Шудра: {scores['shudra']}%\n\n"

    if len(top_varnas) > 1:
        names = " и ".join(VARNA_SHORT_NAMES[v] for v in top_varnas)

        text += (
            f"По данной методике у вас смешанный тип: {names}.\n\n"
            "Это значит, что в вашей природе одновременно сильны два направления.\n"
            "Иногда они могут поддерживать друг друга, а иногда — тянуть в разные стороны.\n"
            "Это не ошибка расчёта, а особенность внутреннего устройства.\n\n"
        )

        for varna in top_varnas:
            text += VARNA_FULL_TEXTS[varna] + "\n\n"

        return text

    text += (
        f"По данной методике ваш основной психотип:\n"
        f"{VARNA_NAMES[main_varna]} — {main_score}%\n\n"
    )

    text += VARNA_FULL_TEXTS[main_varna] + "\n\n"

    if second_score >= 20:
        text += (
            f"Дополнительное влияние: "
            f"{VARNA_SHORT_NAMES[second_varna]} — {second_score}%\n\n"
        )
        text += VARNA_SECONDARY_TEXTS[second_varna] + "\n\n"

    return text

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
        except Exception:
            data["purpose"] = None
    return data.get("purpose")


async def safe_answer_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass


async def send_paid_flow(message: Message, data: dict):
    data["paid"] = True
    data["paid_shown"] = True
    data["stage"] = "purpose_intro_shown"

    user_id = message.chat.id

    await message.answer("Оплата прошла успешно ✅\n\nПродолжаем 👇")
    await message.answer(
        PURPOSE_INTRO,
        reply_markup=get_purpose_intro_keyboard(user_id)
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
    data["stage"] = "purpose_number_shown"


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
    if text.startswith("/start new"):

        user_data[user_id] = {
            "date": None,
            "soul": None,
            "expression": None,
            "purpose": None,
            "paid": False,
            "paid_shown": False,
            "stage": "new",
        }

        await message.answer(START_TEXT)
        await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")
        return

    # Запасной вариант после оплаты через /start paid
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

    # Если уже оплатил и снова нажал /start
    if data.get("paid"):
        stage = data.get("stage")

        await message.answer(
            "Вы уже открыли полный разбор ✅\n\n"
            "Продолжаем с того места, где остановились 👇"
        )

        if stage == "purpose_number_shown":
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

        if stage == "next_block_shown":
            await message.answer(NEXT_BLOCK_TEXT)
            return

        await message.answer(
            PURPOSE_INTRO,
            reply_markup=get_purpose_intro_keyboard(user_id)
        )
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

    if not has_calculation_data(data):
        data["stage"] = "awaiting_date_after_payment"
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
        await callback.message.answer("Оплата уже подтверждена ✅\n\nПродолжаем 👇")
        await callback.message.answer(
            PURPOSE_INTRO,
            reply_markup=get_purpose_intro_keyboard(user_id)
        )
        data["stage"] = "purpose_intro_shown"
        return

    await callback.message.answer(
        SALES_TEXT,
        reply_markup=get_pay_keyboard(user_id)
    )
    data["stage"] = "sales_shown"


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
        reply_markup=get_purpose_intro_keyboard(user_id)
    )
    data["stage"] = "purpose_intro_shown"


# =========================
# ПРЕДНАЗНАЧЕНИЕ — ЧАСТЬ 2
# =========================
@dp.callback_query(lambda c: c.data.startswith("show_purpose_number"))
async def show_purpose_number_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    if ":" in callback.data:
        paid_user_id = int(callback.data.split(":")[1])
    else:
        paid_user_id = callback.from_user.id

    data = get_user(paid_user_id)

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

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    data["stage"] = "varna_intro_shown"

    await callback.message.answer(
        VARNA_INTRO,
        reply_markup=varna_intro_keyboard
    )

@dp.callback_query(lambda c: c.data == "show_varna_mix")
async def show_varna_mix_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)
    data = get_user(callback.from_user.id)

    if not data.get("paid"):
        await callback.message.answer("Сначала откройте полный разбор.")
        return

    data["stage"] = "varna_mix_shown"

    await callback.message.answer(
        VARNA_MIX_EXPLANATION,
        reply_markup=varna_mix_keyboard
    )


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

    data["stage"] = "varna_result_shown"

    varna_text = build_varna_result_text(data["date"])
    await callback.message.answer(
    varna_text,
    reply_markup=destiny_intro_keyboard
)

@dp.callback_query(lambda c: c.data == "show_destiny_text")
async def show_destiny_intro_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    if not data.get("date"):
        await callback.message.answer("Сначала введите дату рождения.")
        return

    destiny = calculate_destiny(data["date"])
    data["destiny_number"] = destiny

    await callback.message.answer(
        DESTINY_INTRO,
        reply_markup=destiny_text_keyboard
    )


@dp.callback_query(lambda c: c.data == "show_destiny_outro")
async def show_destiny_text_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    data = get_user(callback.from_user.id)

    destiny = data.get("destiny_number")

    if destiny is None:
        destiny = calculate_destiny(data["date"])

    destiny_text = DESTINY_TEXTS.get(destiny)

    await callback.message.answer(
        f"Число судьбы {destiny}\n\n{destiny_text}",
        reply_markup=destiny_outro_keyboard
    )


@dp.callback_query(lambda c: c.data == "show_final_real")
async def show_final_real_handler(callback: CallbackQuery):
    await safe_answer_callback(callback)

    await callback.message.answer(
        DESTINY_OUTRO,
        reply_markup=final_keyboard
    )

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
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
