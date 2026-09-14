import asyncio
import datetime
from datetime import timedelta
from aiogram import Bot, Dispatcher, F, BaseMiddleware, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatPermissions
from typing import Callable, Awaitable, Dict, Any


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
    if message.chat.type == "private":
        await message.answer("Смотреть информацию о пользователях можно только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, о ком хочешь узнать информацию")
        return
    user_id = message.from_user.id
    name = message.reply_to_message.from_user.full_name
    username = message.reply_to_message.from_user.username
    id = message.reply_to_message.from_user.id

    level = get_level(id)
    if level >= 100:
        role = "Владелец"
    elif level >= 50:
        role = "Администратор"
    elif level >= 25:
        role = "Модератор"
    else:
        role = "Пользователь"

    await message.reply(
        "Пользователь:\n\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"ID: {id}\n"
        f"Роль: {role}\n\n"
        "Наличие предупреждений: в разработке"
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



first = {"/info", '/time', "/weather"}

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я - вспомогательный бот.\nИспользуй /help для начала работы.")

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("Список команд бота:\n\n"'/start - запуск бота\n'"/info - посмотреть информацию о себе\n"'/nicklist - посмотреть ники участников\n''/nick - установить ник участнику беседы\n''/mute - выдать мут участнику беседы\n''/warn - выдать предупреждение участнику беседы\n''/kick - кикнуть участника беседы\n''/ban - забанить участника беседы\n''/unmute - снять бан чата участнику беседы\n''/unwarn - снять варн участнику беседы\n''/unban - снять бан участнику беседы\n''/warnlist - список участников с варнами\n''/mutelist - список участников находившихся в муте\n''/banlist - список участников находившихся в бане\n''/time - узнать сколько сейчас времени\n''/greetings - приветствие в беседе\n''/addgreetings - установить приветствие в беседе\n''/rules - правила беседы\n''/addrules - установить правила\n''/weather - узнать какая сейчас погода\n''/help - список команд')

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
    if len(parts) >= 3:
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
    if len(parts) != 3:
        await message.answer("Формат: /mute время причина")
        return
    if target.id == message.from_user.id:
        await message.answer("Выдать себе мут нельзя!")
        return
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
        await message.answer("Ответь на сообщение того, кому хочешь снять мут")
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

@dp.message(Command('delete'))
async def delete_handler(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer('У вас нет прав на выполнение этой команды')
        return
    if message.chat.type == "private":
        await message.answer("Удалять сообщения можно только в беседах")
    

@dp.message(Command('nick'))
async def nick_handler(message: Message):
    parts = message.text.split()
    if len(parts) <= 0:
        await message.answer("Формат: /nick NickName")
        return
    await message.answer("Вы успешно установили себе ник:" + message.text)

@dp.message(Command('kick'))
async def kick_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    if message.chat.type == "private":
        await message.answer("Кикать из чата можно только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кого хочешь кикнуть")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Формат: /kick причина")
        return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        await message.answer("Себя кикнуть нельзя!")
        return
    await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=target.id)
    await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=target.id)
    await message.answer(f"Пользователь {target.full_name} исключен из беседы")



@dp.message(Command('ban'))
async def ban_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
    if message.chat.type == "private":
        await message.answer("Банить участника можно только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кого хочешь забанить")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Формат: /ban время причина")
        return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        await message.answer("Себя забанить нельзя!")
        return
    await message.answer("Пользователь был успешно забанен\n\nЧтобы снять бан используйте /unban")

@dp.message(Command('warn'))
async def warn_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Варны можно выдавать только в беседах")
        return
     if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кому хочешь выдать варн")
        return
     parts = message.text.split()
     if len(parts) != 2:
        await message.answer("Формат: /warn причина")
        return
     target = message.reply_to_message.from_user
     if target.id == message.from_user.id:
        await message.answer("Выдать себе варн нельзя!")
        return
     await message.answer("В разработке")

@dp.message(Command('warnlist'))
async def warnlist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return 
     if message.chat.type == "private":
        await message.answer("Просматривать список участников с предупреждениями можно выдавать только в беседах")
        return
     await message.answer('В разработке')

@dp.message(Command('unban'))
async def unban_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Снимать баны можно только в беседах")
        return
     if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кому хочешь снять бан")
        return
     await message.answer('В разработке')

@dp.message(Command('unwarn'))
async def unwarn_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Снимать варны можно только в беседах")
        return
     if not message.reply_to_message:
        await message.answer("Ответь на сообщение того, кому хочешь снять варн")
        return
     await message.answer('В разработке')



@dp.message(Command('banlist'))
async def banlist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Просматривать список участников в бане можно только в беседах")
        return
     await message.answer('В разработке')

@dp.message(Command('mutelist'))
async def mutelist_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Просматривать список участников находящихся в муте можно только в беседах")
        return
     await message.answer('В разработке')

@dp.message(Command('greetings'))
async def greetings_handler(message: Message):
    await message.answer("В разработке")

@dp.message(Command('addgreetings'))
async def addgreetings_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     await message.answer('В разработке')

@dp.message(Command('rules'))
async def rules_handler(message: Message):
    await message.answer("В разработке")

@dp.message(Command('addrules'))
async def addgreetings_handler(message: Message):
     if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав не выполнение этой команды.")
        return
     if message.chat.type == "private":
        await message.answer("Устанавливать правила можно только в беседах")
        return
     await message.answer('В разработке')

@dp.message(Command('weather'))
async def rules_handler(message: Message):
    await message.answer("В разработке")
     

@dp.message()
async def unknown_handler(message: Message):
    pass

async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    