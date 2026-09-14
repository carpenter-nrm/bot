import asyncio
import datetime
from datetime import timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatPermissions


TOKEN = "8646453142:AAFWIT1Adxm2v4jq0Ycaf11KJ6hWB_F_KLU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ROLES = {}
OWNER_ID = 732840192
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

@dp.message(Command("info"))
async def info_handler(message: Message):
    user_id = message.from_user.id
    level = get_level(user_id)
    if level >= 100:
        role = "Владелец"
    elif level >= 50:
        role = "Администратор"
    elif level >= 25:
        role = "Модератор"
    else:
        role = "Пользователь"

    await message.answer(
        f"{message.from_user.full_name}\n"
        f"ID: {user_id}\n"
        f"Роль: {role}"
    )

@dp.message(Command("setrole"))
async def setrole_handler(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Формат: /setrole ID роль")
        return
    try:
        target_id = int(parts[1])
        role = parts[2]
    except ValueError:
        await message.answer("ID должен быть числом\n\nЧтобы узнать ID используйте /info")
        return
    if role not in LEVELS:
        await message.answer(f"Роли: {', ' .join(LEVELS.keys())}")
        return
    ROLES[target_id] = LEVELS[role]
    await message.answer(f"Пользователь {target_id} теперь {role} (уровень {LEVELS[role]})")

@dp.message(Command("test"))
async def test_handler(message: Message):
    uid = message.from_user.id
    await message.answer(
        f"Твой ID: {uid} {type(uid).__name__}\n"
        f"OWNER_ID: {OWNER_ID} {type(OWNER_ID).__name__}\n"
        f"Уровень: {get_level(uid)}\n"
        f"is_owner: {is_owner(uid)}\n"
        f"is_admin: {is_admin(uid)}"
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

@dp.message(F.text.startswith("/mute"))
async def mute_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    if message.chat.type == "private":
        await message.answer("Бан чата можно выдавать только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кому хочешь выдать мут")
        return
    target = message.reply_to_message.from_user
    parts = message.text.split()
    minutes = 120
    if len(parts) >= 2:
        try:
            minutes = int(parts[1])
        except ValueError:
            pass
        until = datetime.datetime.now() + timedelta(minutes=minutes)
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
        permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await message.answer(f"{target.full_name} получил мут на {minutes} мин.")

@dp.message(F.text.startswith("/unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав на выполнение этой команды")
        return
    if message.chat.type == "private":
        await message.answer("Снимать бан чата можно только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кому хочешь выдать мут")
        return
    target = message.reply_to_message.from_user
    await bot.restrict_chat_member(
        chat_id=message.chat.id, 
        user_id=target.id, 
        permissions=ChatPermissions(
            can_send_messages=True, 
            can_send_media_messages=True, 
            can_send_other_messages=True, 
            can_add_web_page_previews=True
        ))
    await message.answer(f"{target.full_name} получил разбан чата")

@dp.message(Command('nicklist'))
async def nicklist_handler(message: Message):
    await message.answer("Список участников с установленными никами:\n\n")

@dp.message(Command('nick'))
async def nick_handler(message: Message):
    await message.answer("У вас нет прав на это действие.")

@dp.message(Command('kick'))
async def kick_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Формат: /kick username причина")
        return
    await message.answer("Пользователь был успешно исключен из беседы")

@dp.message(Command('ban'))
async def ban_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("Формат: /ban username время причина")
        return
    await message.answer("Пользователь был успешно забанен\n\nЧтобы разбанить используйте /unban")

@dp.message(Command('warn'))
async def warn_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return 
     
     parts = message.text.split()
     if len(parts) != 3:
        await message.answer("Формат: /warn username причина")
        return
     await message.answer("Пользователь получил предупреждение\n\nЧтобы снять предупреждение используйте /unwarn")

@dp.message(Command('warnlist'))
async def warnlist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return 
     await message.answer('Список пользователей с варнами:\n\n')

@dp.message(Command('unban'))
async def unban_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     await message.answer('Вы успешно разбанили пользователя')

@dp.message(Command('unwarn'))
async def unwarn_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     await message.answer('Вы успешно сняли предупреждение пользователю')



@dp.message(Command('banlist'))
async def banlist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return 
     await message.answer('Список пользователей находящихся в бане:\b\n')

@dp.message(Command('mutelist'))
async def mutelist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return 
     await message.answer('Список пользователей находящихся в муте:\n\n')

@dp.message(Command('greetings'))
async def greetings_handler(message: Message):
    await message.answer("Приветствие не установлено.\n\nЧтобы установить приветствие используйте /addgreetings")

@dp.message(Command('addgreetings'))
async def addgreetings_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     await message.answer('Приветствие успешно установлено')

@dp.message(Command('rules'))
async def rules_handler(message: Message):
    await message.answer("Правила не установлены.\n\nЧтобы установить правила используйте /addrules")

@dp.message(Command('addrules'))
async def addgreetings_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     await message.answer('Правила успешно установлены')
     

@dp.message()
async def unknown_handler(message: Message):
    pass

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    