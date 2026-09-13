import asyncio
import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, setrole, mute, ban, kick, warn, info
from aiogram.types import Message


TOKEN = "c"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ROLES = {}
OWNER_ID = 0
LEVELS = {
    "user": 0,
    "moder": 25,
    "admin": 50,
    "owner": 100,

}

def get_level(user_Id):
    if user_Id == OWNER_ID:
        return 100
    return ROLES.get(user_Id, 0)

def is_admin(user_id):
    return get_level(user_id) >= 50

def is_owner(user_id):
    return user_id == OWNER_ID

@dp.message(Command(info))
async def info_handler(message: Message):
    user_id = message.from_user.id
    level = get_level(user_id)
    if level >= 100:
        role = "Владелец"
    elif level >+ 50:
        role = "Администратор"
    elif level >= 25:
        role = "Модератор"
    else:
        role = "Пользователь"

    await message.answer(
        f"{message.from_user.fullname}\n"
        f"ID: {user_id}\n"
        f"Роль: {role}"
    )





first = {"/info", '/time', "/weather"}

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я - вспомогательный бот.\nИспользуй /help для начала работы.")

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("Список команд бота:\n\n"'/start - запуск бота\n'"/info - посмотреть информацию о себе\n"'/nicklist - посмотреть ники участников\n''/nick - установить ник участнику беседы\n''/mute - выдать мут участнику беседы\n''/warn - выдать предупреждение участнику беседы\n''/kick - кикнуть участника беседы\n''/ban - забанить участника беседы\n''/warnlist - список участников с варнами\n''/mutelist - список участников находившихся в муте\n''/banlist - список участников находившихся в бане\n''/time - узнать сколько сейчас времени\n''/greetings - приветствие в беседе\n''/addgreetings - установить приветствие в беседе\n''/rules - правила беседы\n''/addrules - установить правила\n''/weather - узнать какая сейчас погода\n''/help - список команд')

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
    await message.answer("Правила не установлены.\n\nЧтобы установить правила используйте /addrules")

@dp.message(Command('addrules'))
async def addgreetings_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")



@dp.message()
async def echo_handler(message: Message):
    await message.answer("К сожалению я тебя не понимаю, используй /help")

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    