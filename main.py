
#Telegram бот для отображения расписания группы 24-ИСТ-2 (НГТУ).
#Вариант №29 по заданию к лабораторной работе №4.
#Сначала выбор чётной/нечётной недели, затем выбор дня.

import logging
from datetime import datetime
from typing import Dict, List

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Токен бота
TOKEN = "Здесь был токен, но я его убрал"

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Состояния для ConversationHandler
WEEK_SELECTION, DAY_SELECTION = range(2)

# --- Расписание для ЧЁТНОЙ недели ---
SCHEDULE_EVEN: Dict[str, List[str]] = {
    "Понедельник": ["11:35 - Физ-ра (6 корпус)"],
    "Вторник": [
        "09:45 - Методы оптимизации (практика, а.1353)",
        "11:35 - Python (лекция, а.1354)",
        "13:40 - Методы защиты информации (лаб, а.4403)",
        "13:40 - Python (лаб, а.5405)",
    ],
    "Среда": [
        "08:00 - Тех. программирование (лаб, а.4404)",
        "11:35 - Теория информации (лаб, а.4307)",
        "13:40 - Python (лаб, а.5408)",
    ],
    "Четверг": [
        "08:00 - БЖД (лекция, а.6125)",
        "09:45 - Электротехника (лекция, а.6425)",
        "11:35 - Теория вероятностей (практика, а.6531)",
        "13:40 - Электротехника (практика, а.6425)",
        "15:25 - БЖД (лаб, а.6350)",
    ],
    "Пятница": [
        "11:35 - Финансовая грамотность (лекция, а.3216)",
        "13:40 - Теория вероятностей (лекция, а.3301)",
        "15:25 - Методы защиты информации (лекция, а.4201)",
    ],
    "Суббота": ["Выходной 🎉"],
    "Воскресенье": ["Выходной 🎉"],
}

# --- Расписание для НЕЧЁТНОЙ недели ---
SCHEDULE_ODD: Dict[str, List[str]] = {
    "Понедельник": ["11:35 - Физ-ра (6 корпус)"],
    "Вторник": [
        "08:00 - Тех. программирование (лаб, а.4404)",
        "11:35 - Методы оптимизации (лекция, а.1354)",
        "13:40 - Методы защиты информации (лаб, а.4403)",
    ],
    "Среда": [
        "08:00 - Электротехника (лаб, а.4308)",
        "11:35 - Теория информации (лаб, а.4307)",
    ],
    "Четверг": [
        "08:00 - БЖД (практика, а.6351, 6347)",
        "09:45 - Теория информации (лекция, а.6259)",
        "11:35 - Теория вероятностей (практика, а.6531)",
        "13:40 - Теория информации (практика, а.6427)",
        "15:25 - БЖД (лаб, а.6350)",
    ],
    "Пятница": [
        "11:35 - Финансовая грамотность (практика, а.4301)",
        "13:40 - Теория вероятностей (лекция, а.3301)",
        "15:25 - Методы защиты информации (лекция, а.4201)",
        "17:10 - Час куратора",
    ],
    "Суббота": [
        "08:00 - Электротехника (лаб, а.4308)",
        "11:35 - Тех. программирование (лекция, а.4301)",
    ],
    "Воскресенье": ["Выходной 🎉"],
}

# Словарь для перевода дней
RU_DAYS = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}

# Порядок дней
DAYS_ORDER = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# Сокращенные названия дней
SHORT_DAYS = {
    "Пн": "Понедельник",
    "Вт": "Вторник",
    "Ср": "Среда",
    "Чт": "Четверг",
    "Пт": "Пятница",
    "Сб": "Суббота",
}


def get_current_week_type() -> str:
    #Определяет текущую неделю (чётная или нечётная)
    week_number = datetime.now().isocalendar()[1]
    result = "EVEN" if week_number % 2 == 0 else "ODD"
    logging.info(f"Текущая неделя (номер {week_number}): {result}")
    return result


def get_week_keyboard() -> ReplyKeyboardMarkup:
    #кнопки выбора чётной/нечётной недели
    buttons = [
        ["✅ ЧЁТНАЯ неделя"],
        ["✅ НЕЧЁТНАЯ неделя"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_days_keyboard() -> ReplyKeyboardMarkup:
    #кнопки выбора дня недели
    buttons = [
        ["📅 Сегодня", "📅 Завтра"],
        ["Понедельник", "Вторник"],
        ["Среда", "Четверг"],
        ["Пятница", "Суббота"],
        ["Воскресенье"],
        ["🔄 Сменить неделю"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_schedule_for_day(day: str, schedule: Dict[str, List[str]], week_type: str = "") -> str:
    #вывод расписания для указанного дня
    lessons = schedule.get(day, [])

    if not lessons:
        return f"📭 *{day}*\nНет пар 🎉"

    result = f"📚 *{day}*\n"
    if week_type:
        result += f"*Неделя: {week_type}*\n\n"
    else:
        result += "\n"

    for lesson in lessons:
        result += f"• {lesson}\n"
    return result


def extract_time(lesson: str) -> str:
    #извлечение времени из строки пары
    try:
        return lesson.split(" - ")[0]
    except:
        return None


def get_current_lesson(schedule_today: List[str]) -> str:
    #функция для определения текущей или следующей пары
    now = datetime.now().time()

    for lesson in schedule_today:
        time_str = extract_time(lesson)
        if not time_str:
            continue

        start = datetime.strptime(time_str, "%H:%M").time()

        if now < start:
            return f"⏭ *Следующая пара:*\n{lesson}"

    return "🎉 *На сегодня пар больше нет*"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #Начало работы - выбор чётной/нечётной недели
    user = update.effective_user

    # Очищаем предыдущие данные
    context.user_data.clear()

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот расписания группы 24-ИСТ-2\n"
        f"Сначала выбери тип недели:\n"
        f"• ЧЁТНАЯ неделя (2, 4, 6...)\n"
        f"• НЕЧЁТНАЯ неделя (1, 3, 5...)\n\n"
        f"⬇️ Нажми на кнопку ниже ⬇️",
        parse_mode="Markdown",
        reply_markup=get_week_keyboard(),
    )
    return WEEK_SELECTION


async def select_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #Обработка выбора недели
    text = update.message.text
    user = update.effective_user

    logging.info(f"Пользователь {user.first_name} выбрал: '{text}'")
    logging.info(f"Содержит 'ЧЁТНАЯ': {'ЧЁТНАЯ' in text}")
    logging.info(f"Содержит 'НЕЧЁТНАЯ': {'НЕЧЁТНАЯ' in text}")

    if text == "✅ ЧЁТНАЯ неделя":
        context.user_data["week"] = "EVEN"
        week_type = "ЧЁТНАЯ"
        schedule = SCHEDULE_EVEN
        logging.info(f"Установлена ЧЁТНАЯ неделя для пользователя {user.first_name}")
    elif text == "✅ НЕЧЁТНАЯ неделя":
        context.user_data["week"] = "ODD"
        week_type = "НЕЧЁТНАЯ"
        schedule = SCHEDULE_ODD
        logging.info(f"Установлена НЕЧЁТНАЯ неделя для пользователя {user.first_name}")
    else:
        await update.message.reply_text(
            "❓ Пожалуйста, используй кнопки для выбора недели.",
            reply_markup=get_week_keyboard(),
        )
        return WEEK_SELECTION

    # Сохраняем расписание
    context.user_data["schedule"] = schedule

    # Показываем расписание на сегодня
    today = RU_DAYS[datetime.now().strftime("%A")]

    await update.message.reply_text(
        f"✅ Выбрана  {week_type} неделя!\n\n"
        f"{get_schedule_for_day(today, schedule, week_type)}",
        parse_mode="Markdown",
        reply_markup=get_days_keyboard(),
    )
    return DAY_SELECTION


async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #Обработка выбора дня недели
    text = update.message.text
    user = update.effective_user

    # Получаем расписание из user_data
    schedule = context.user_data.get("schedule")
    week_code = context.user_data.get("week", "EVEN")
    week_type = "ЧЁТНАЯ" if week_code == "EVEN" else "НЕЧЁТНАЯ"

    # Проверка: если расписание не выбрано, возвращаем к выбору недели
    if schedule is None:
        logging.warning(f"Пользователь {user.first_name}: расписание не выбрано!")
        await update.message.reply_text(
            "❓ Сначала выбери тип недели!",
            reply_markup=get_week_keyboard(),
        )
        return WEEK_SELECTION

    logging.info(f"Пользователь {user.first_name} выбрал день: '{text}', неделя: {week_type}")

    # Обработка сокращенных названий
    if text in SHORT_DAYS:
        text = SHORT_DAYS[text]

    # Смена недели
    if text == "🔄 Сменить неделю":
        await update.message.reply_text(
            "🔄 Выбери тип недели:",
            reply_markup=get_week_keyboard(),
        )
        return WEEK_SELECTION

    # Сегодня
    if text == "📅 Сегодня":
        today = RU_DAYS[datetime.now().strftime("%A")]
        answer = get_schedule_for_day(today, schedule, week_type)
        await update.message.reply_text(answer, parse_mode="Markdown")
        return DAY_SELECTION

    # Завтра
    if text == "📅 Завтра":
        today = RU_DAYS[datetime.now().strftime("%A")]
        idx = DAYS_ORDER.index(today)
        tomorrow = DAYS_ORDER[(idx + 1) % 7]
        answer = get_schedule_for_day(tomorrow, schedule, week_type)
        await update.message.reply_text(answer, parse_mode="Markdown")
        return DAY_SELECTION

    # Выбор конкретного дня
    if text in schedule:
        answer = get_schedule_for_day(text, schedule, week_type)
        await update.message.reply_text(answer, parse_mode="Markdown")
        return DAY_SELECTION

    # Неизвестная команда
    await update.message.reply_text(
        "❓ Пожалуйста, используй кнопки для навигации.",
        reply_markup=get_days_keyboard(),
    )
    return DAY_SELECTION


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #/help
    await update.message.reply_text(
        "📖 *Справка*\n\n"
        "🗓 *Как пользоваться:*\n"
        "1️⃣ Отправь /start\n"
        "2️⃣ Выбери ЧЁТНУЮ или НЕЧЁТНУЮ неделю\n"
        "3️⃣ Пользуйся кнопками:\n"
        "   • '📅 Сегодня' - расписание на сегодня\n"
        "   • '📅 Завтра' - расписание на завтра\n"
        "   • Дни недели - расписание на выбранный день\n"
        "   • '🔄 Сменить неделю' - смена недели\n\n"
        "📌 *Группа: 24-ИСТ-2*\n"
        "🏫 *Выполнил: Хорощь А.А.*",
        parse_mode="Markdown",
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Обработчик ошибок
    logging.error(msg="Исключение при обработке обновления:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка. Пожалуйста, попробуй /start"
        )


def main() -> None:
    # Запуск бота
    application = Application.builder().token(TOKEN).build()

    # ConversationHandler для управления состояниями
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WEEK_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_week)],
            DAY_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_day)],
        },
        fallbacks=[CommandHandler("help", help_command)],
        allow_reentry=True,
    )

    # Регистрируем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)

    # Запускаем бота
    logging.info("Бот запущен и готов к работе...")
    application.run_polling()


if __name__ == "__main__":
    main()