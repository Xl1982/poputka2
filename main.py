import logging
import random
import re
import time
from enum import Enum
from aiogram.dispatcher.filters import Command, ChatTypeFilter
import aiogram
print(aiogram.__version__)
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
import sqlite3
from config import TOKEN_POPUTKA
API_TOKEN = TOKEN_POPUTKA
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class RideInputState(Enum):
    NAME = 0
    SEATS = 1
    FROM_PLACE = 2
    TO_PLACE = 3
    DATE = 4
    TIME = 5
    PRICE = 6

user_states = {}
user_data = {}

btn_goto_bot = InlineKeyboardButton("Перейти к боту", url="https://t.me/poputka3_bot")
inline_kb1 = InlineKeyboardMarkup().add(btn_goto_bot)

keyboard_private = InlineKeyboardMarkup()
btn_add_private = InlineKeyboardButton("Добавить поездку", callback_data="add")
btn_show_private = InlineKeyboardButton("Показать поездки", callback_data="show")
keyboard_private.add(btn_add_private, btn_show_private)



keyboard_group = InlineKeyboardMarkup()
btn_goto_bot = InlineKeyboardButton("Добавить поездку", url="https://t.me/poputka3_bot")  # Замените YourBotUsername на имя пользователя вашего бота
btn_add_group = InlineKeyboardButton("Показать поездки", url="https://t.me/poputka3_bot")
keyboard_group.add(btn_goto_bot, btn_add_group)


# База данных
def init_db():
    try:
        with sqlite3.connect('rides.db') as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                seats INTEGER,
                from_place TEXT,
                to_place TEXT,
                date TEXT,
                time TEXT,
                price_per_person INTEGER
            )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")


def add_ride(user_id, name, seats, from_place, to_place, date, time, price_per_person):  # Добавить price_per_person
    with sqlite3.connect('rides.db') as conn:
        conn.execute("INSERT INTO rides (user_id, name, seats, from_place, to_place, date, time, price_per_person) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (user_id, name, seats, from_place, to_place, date, time, price_per_person))
        conn.commit()

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import BoundFilter
from config import ADMINS

class IsGroup(BoundFilter): #
    async def check(self, message: types.Message):
        return message.chat.type in (
            types.ChatType.GROUP,
            types.ChatType.SUPERGROUP,
        )


class IsAdminFilter(BoundFilter): # фильтр определяет по списку админов из файла конфиг
    async def check(self, message: types.Message):
        return message.from_user.id in ADMINS

class IsPrivate(BoundFilter):
   async def check(self, message: types.Message):
       return message.chat.type == types.ChatType.PRIVATE


mess1= f"""
🚗 Поиск попутчиков на авто из Торревьехи 🚗

🚘 Водители:
Готовы подвезти пассажиров?
🤔 Нажмите на кнопку "Добавить поездку" ниже!

🛣️ Планируемые поездки с 📅 датой, ⏰ временем и 💶 ценой будут публиковаться каждый день в этом чате.

🔍 Пассажиры:
Ищете поездку до Аликанте, аэропорта или других направлений?
📍 Нажмите "Показать поездки" и выберите удобное для вас предложение! 🚕"""
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
        await message.answer(mess1, reply_markup=keyboard_group)

    else:
        await message.answer("Привет! Я бот для поиска попутных поездок.", reply_markup=keyboard_private)

@dp.callback_query_handler(lambda c: c.data == 'add')
async def process_callback_add(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    user_states[user_id] = RideInputState.NAME
    user_data[user_id] = {}
    await bot.send_message(user_id, "Введите ваш ник или телефон:")


#обращение к базе данных за выводом
# Измененная функция для получения информации о поездках
def get_rides_info():
    with sqlite3.connect('rides.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rides")
        rows = cursor.fetchall()

        rides_info = []
        for row in rows:
            ride_info = {
                'name': row[2],
                'seats': row[3],
                'from_place': row[4],
                'to_place': row[5],
                'date': row[6],
                'time': row[7],
                'price_per_person': row[8] if len(row) > 8 else "N/A"
            }
            rides_info.append(ride_info)
        return rides_info

@dp.callback_query_handler(lambda c: c.data == 'show')
async def process_callback_show(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    rides_info = get_rides_info()
    if not rides_info:
        await bot.send_message(callback_query.from_user.id, "Пока нет поездок")
    else:
        for ride in rides_info:
            ride_message = f"Имя водителя: [{ride['name']}](tg://user?id={callback_query.from_user.id})\n" \
                           f"Доступные места: {ride['seats']}\n" \
                           f"Место отправления: {ride['from_place']}\n" \
                           f"Место назначения: {ride['to_place']}\n" \
                           f"Дата поездки: {ride['date']}\n" \
                           f"Время отправления: {ride['time']}\n" \
                           f"Цена за человека: {ride['price_per_person']} евро.\n"
            await bot.send_message(callback_query.from_user.id, ride_message, parse_mode=ParseMode.MARKDOWN)
            await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_private)


@dp.message_handler(lambda message: message.from_user.id in user_states)
async def process_input(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]

    if state == RideInputState.NAME:
        user_data[user_id]["name"] = message.text
        user_states[user_id] = RideInputState.SEATS
        await message.answer("Сколько мест у вас доступно?")

    elif state == RideInputState.SEATS:
        try:
            seats = int(message.text)
            user_data[user_id]["seats"] = seats
            user_states[user_id] = RideInputState.FROM_PLACE
            await message.answer("Введите место отправления:")
        except ValueError:
            await message.answer("Пожалуйста, введите корректное число мест.")


    elif state == RideInputState.FROM_PLACE:
        user_data[user_id]["from_place"] = message.text
        user_states[user_id] = RideInputState.TO_PLACE
        await message.answer("Введите место назначения:")


    elif state == RideInputState.TO_PLACE:
        user_data[user_id]["to_place"] = message.text
        user_states[user_id] = RideInputState.DATE
        await message.answer("Введите дату поездки (например, 12.04.2023):")

    elif state == RideInputState.DATE:
        user_data[user_id]["date"] = message.text
        user_states[user_id] = RideInputState.TIME
        await message.answer("Введите время отправления (например, 15:30):")

    elif state == RideInputState.TIME:
        user_data[user_id]["time"] = message.text
        user_states[user_id] = RideInputState.PRICE  # Move to the PRICE state after getting the time
        await message.answer("Введите цену за человека в евро:")

    elif state == RideInputState.PRICE:
        try:
            price = int(message.text)
            user_data[user_id]["price_per_person"] = price

            add_ride(user_id, user_data[user_id]["name"], user_data[user_id]["seats"], user_data[user_id]["from_place"],
                     user_data[user_id]["to_place"], user_data[user_id]["date"], user_data[user_id]["time"], price)

            await send_ride_to_chat(user_data[user_id])  # отправляем информацию о поездке в чат

            await message.answer("Ваша поездка добавлена!")
            del user_states[user_id]
            del user_data[user_id]
            await message.answer("Выберите действие:", reply_markup=keyboard_private)

        except ValueError:
            await message.answer("Пожалуйста, введите корректную цену.")


from config import CHAT_ID
async def send_ride_to_chat(ride_info):
    chat_id = CHAT_ID  # замените на ваш chat_id
    message_text = (
        f"Новая поездка 🚗\n"
        f"Контакты водителя: {ride_info['name']}\n"
        f"Доступные места: {ride_info['seats']}\n"
        f"Место отправления: {ride_info['from_place']}\n"
        f"Место назначения: {ride_info['to_place']}\n"
        f"Дата поездки: {ride_info['date']}\n"
        f"Время отправления: {ride_info['time']}\n"
        f"Цена за человека: {ride_info['price_per_person']} евро."
    )
    await bot.send_message(chat_id, message_text)


if __name__ == '__main__':
    init_db()

    executor.start_polling(dp, skip_updates=True)

