import asyncio
import datetime
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


TOKEN = "8646453142:AAFWIT1Adxm2v4jq0Ycaf11KJ6hWB_F_KLU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

first = {"/info", '/time', "/weather"}

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я - вспомогательный бот.\nИспользуй /help для начала работы.")

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("Список команд бота:\n\n"'/start - запуск бота\n''/nicklist - посмотреть ники участников\n''/nick - установить ник участнику беседы\n''/mute - выдать мут участнику беседы\n''/warn - выдать предупреждение участнику беседы\n''/kick - кикнуть участника беседы\n''/ban - забанить участника беседы\n''/warnlist - список участников с варнами\n''/mutelist - список участников находившихся в муте\n''/banlist - список участников находившихся в бане\n''/time - узнать сколько сейчас времени\n''/greetings - приветствие в беседе\n''/addgreetings - установить приветствие в беседе\n''/rules - правила беседы\n''/addrules - установить правила\n''/weather - узнать какая сейчас погода\n''/help - список команд')

@dp.message(Command("time"))
async def time_handler(message: Message):
    now = datetime.datetime.now()

    months = ['января', "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября","декабря"]
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

    month_name = months[now.month - 1]
    day_name = days[now.weekday()]

    text = f"Сегодня {day_name}, {now.day} {month_name} {now.year}\n"
    text += f"Время: {now.strftime('%H:%M')}"
    await message.answer(text)

@dp.message(Command('mute'))
async def mute_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('nicklist'))
async def nicklist_handler(message: Message):
    await message.answer("Список участников с установленными никами:\n\n")

@dp.message(Command('nick'))
async def nick_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('kick'))
async def kick_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('ban'))
async def ban_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('warn'))
async def warn_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('addadm'))
async def addadm_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('greetings'))
async def greetings_handler(message: Message):
    await message.answer("Приветствие не установлено.\n\nЧтобы установить приветствие используйте /addgreetings")

@dp.message(Command('addgreetings'))
async def addgreetings_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('rules'))
async def rules_handler(message: Message):
    await message.answer("Правила не установлены.\n\nЧтобы установить правила используйте /addgreetings")

@dp.message()
async def echo_handler(message: Message):
    await message.answer("К сожалению я тебя не понимаю, используй /help")

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    