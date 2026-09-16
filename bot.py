import sqlite3
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

DB_NAME = "bot.db"

OWNER_ID = 732840192
LEVELS = {
    "user": 0,
    "admin": 50,
    "owner": 100,

}


async def get_level(user_id, chat_id=None):
    if user_id == OWNER_ID:
        return 100
    if chat_id:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status == "creator":
                return 100
        except Exception:
            pass
    return get_role(user_id)

async def is_admin(user_id, chat_id=None):
    level = await get_level(user_id, chat_id)
    return level >= 50

async def is_owner(user_id, chat_id=None):
    if user_id == OWNER_ID:
        return True
    if chat_id:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status == "creator":
                return True
        except Exception:
            pass
    return False



async def can_punish(admin_id, target_id, chat_id=None):
    admin_level = await get_level(admin_id, chat_id)
    target_level = await get_level(target_id, chat_id)
    return admin_level > target_level

async def check_bot_admin(message, need_right=None):
    try:
        bot_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
    except Exception as e:
        await message.answer(f"Ошибка проверки прав бота: {e}")
        return False
    if bot_member.status not in ("administrator", "creator"):
        await message.answer(
            "Я не являюсь администратором в этой беседе.\n\n"
            "Выдайте мне права чтобы я мог выполнять свои функции")
        return False
    if need_right:
        has_right = getattr(bot_member, need_right, False)
        if not has_right:
            rights_names = {
                "can_pin_messages": "Закреплять сообщения",
                "can_delete_messages": "Удалять сообщения",
                "can_restrict_members": "Ограничивать участников",
                "can_invite_users": "Приглашать пользователей",
                "can_promote_members": "Назначать администраторов",
            }
            right_name = rights_names.get(need_right, need_right)
            await message.answer(f"У меня нет права: «{right_name}»\n\nВыдайте мне права администратора чтобы я мог выполнять свои функции")
            return False
    return True

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Таблица юзеров
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            last_seen TEXT
        )
    """)
    # Таблица ролей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY,
            level INTEGER
        )
    """)
    conn.commit()
    conn.close()
    print("БД инициализирована")

def set_role(user_id, level):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO roles (user_id, level) VALUES (?, ?)",
        (user_id, level)
    )
    conn.commit()
    conn.close()

def get_role(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT level FROM roles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

@dp.message(Command("info"))
async def info_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Смотреть информацию о пользователях можно только в беседах")
        return
    if not message.reply_to_message:
        await message.answer("Ошибка: Ответь на сообщение того, о ком хочешь узнать информацию")
        return
    user_id = message.from_user.id
    name = message.reply_to_message.from_user.full_name
    username = message.reply_to_message.from_user.username
    id = message.reply_to_message.from_user.id

    level = await get_level(id, message.chat.id)
    if level >= 100:
        role = "Владелец"
    elif level >= 50:
        role = "Администратор"
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
    if not await is_owner(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав не выполнение этой команды.")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Ошибка: Введите /setrole ID роль")
        return
    try:
        target_id = int(parts[1])
        role = parts[2]
    except ValueError:
        await message.answer("Ошибка: ID должен быть числом\n\nЧтобы узнать ID используйте /info")
        return
    if role not in LEVELS:
        await message.answer(f"Ошибка: Такой роли не существует\n\nСписок всех существующих ролей:\n {', ' .join(LEVELS.keys())}")
        return
    set_role(target_id, LEVELS[role])
    if message.chat.type != "private" and role == "admin":
        try:
            await bot.promote_chat_member(
                chat_id=message.chat.id,
                user_id=target_id,
                can_delete_messages=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_invite_users=True
            )
            await message.answer(f"Пользователь {target_id} теперь {role}")
        except Exception as e:
            await message.asnwer("Ошибка: Выдать роль не удалось.")
    else:
        await message.answer(f"Пользователь {target_id} теперь {role} ")



first = {"/info", '/time', "/weather"}

@dp.message(CommandStart())
async def start_handler(message: Message):

    await message.answer("Добро пожаловать. Я — Chat Guard, административный ассистент. \n\nЯ предназначен для автоматизации управления участниками и поддержания порядка в чате.\n\nФункционал:\n• Система ников\n• Система предупреждений\n• Исключение из чата\n• Блокировка чата\n• Список участников чата с наказаниями\n\nДля подробного ознакомления с командами введите /help.\n\n-----------------------------------\nГораздо больше о боте вы можете узнать в нашем ТГК - https://t.me/botchatguard")

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("Список команд бота:\n\n"'/start - запуск бота\n'"/info - посмотреть информацию об участнике чата\n"'/nicklist - посмотреть ники участников чата\n''/nick - установить ник участнику чата\n''/mute - выдать мут участнику чата\n''/warn - выдать предупреждение участнику чата\n''/kick - кикнуть участника чата\n''/ban - забанить участника чата\n''/unmute - снять бан чата участнику чата\n''/unwarn - снять варн участнику чата\n''/unban - снять бан участнику чата\n''/warnlist - список участников с варнами\n''/mutelist - список участников находившихся в муте\n''/banlist - список участников находившихся в бане\n''/greetings -посмотреть приветствие чата\n''/addgreetings - установить приветствие в чате\n''/rules - посмотреть правила чата\n''/addrules - установить правила чата\n''/delete - удалить сообщение участника чата\n''/pin - закрепить сообщение\n'"/top - топ участников по сообщениям в чате\n"'/time - узнать сколько сейчас времени\n''/weather - узнать какая сейчас погода\n''/help - список команд')

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



@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Снимать мут можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
             return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
   
    parts = message.text.split()
    target_input = None
    if message.reply_to_message:
        target_input = str(message.reply_to_message.from_user.id)
    elif len(parts) >= 2:
        target_input = parts[1]
    else:
        await message.answer(
            "Ошибка:\n\n Введите:\n"
            "1) /unmute в ответ на сообщение того, кому хотите снять мут\n"
            "2) /unmute @username\n"
            "3) /unmute ID\n\n")
        return
    target_id = None
    target_name = target_input
    if target_input.startswith("@"):
        username = target_input[1:]
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=username
            )
            target_id = member.user.id
            target_name = member.user.full_name
        except Exception:
            await message.answer(
                f"Пользователь @{username} не найден в чате.\nПопробуйте через ID.")
            return
    else:
        try:
            target_id = int(target_input)
        except ValueError:
            await message.answer("Ошибка: Вы не указали кому хотите снять мут.\n\nИспользуйте @username или ID")
            return
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=target_id
            )
            target_name = member.user.full_name
        except Exception:
            target_name = f"ID {target_id}"
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"Пользователь {target_name} больше не имеет бан чата")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command('nicklist'))
async def nicklist_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать список установленных ников можно только в чатах")
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    await message.answer("Список участников с установленными никами:\n\n")

@dp.message(Command('delete'))
async def delete_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Удалять сообщения можно только в чатах")
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    target = message.reply_to_message.from_user
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer('Ошибка: У вас нет прав на выполнение этого действия')
        return
    if not message.reply_to_message:
        await message.answer("Ошибка: Ответьте на то сообщение, которое хотите удалить")
        return
    if not await can_punish(message.from_user.id, target.id, message.chat.id):
        await message.answer("Ошибка: Вы не можете удалить сообщение человека, который имеет должность равнную вашей или выше")
        return
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)

@dp.message(Command('nick'))
async def nick_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Устанавливать ники можно только в чатах")
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    parts = message.text.split()
    if len(parts) <= 0:
        await message.answer("Ошибка: Формат: /nick NickName")
        return
    await message.answer("Вы успешно установили себе ник:" + message.text)

@dp.message(Command("kick"))
async def kick_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Кикать можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
            return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    
    parts = message.text.split(maxsplit=3)
    target_input = None
    reason = "не указана"
    if message.reply_to_message:
        target_input = str(message.reply_to_message.from_user.id)
        if len(parts) >= 2:
            reason = parts[1]
    elif len(parts) >= 2:
        target_input = parts[1]
        if len(parts) >= 3:
            reason = parts[2]
    else:
        await message.answer(
            "Ошибка:\n\n Введите:\n"
            "1) /kick [причина] в ответ на сообщение того, кого хотите кикнуть\n"
            "2) /kick @username [причина]\n"
            "3) /kick ID [причина]"
        )
        return
    target_id = None
    target_name = target_input
    if target_input.startswith("@"):
        username = target_input[1:]
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=username
            )
            target_id = member.user.id
            target_name = member.user.full_name
        except Exception:
            await message.answer(
                f"Пользователь @{username} не найден в чате.\n\nПопробуйте через ID или reply.")
            return
    else:
        try:
            target_id = int(target_input)
        except ValueError:
            await message.answer("Ошибка: Вы не указали кого кикнуть\n\nИспользуйте @username или ID")
            return
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=target_id
            )
            target_name = member.user.full_name
        except Exception:
            target_name = f"ID {target_id}"
    if target_id == message.from_user.id:
        await message.answer("Ошибка: Себя кикнуть нельзя!")
        return
    if not await can_punish(message.from_user.id, target_id, message.chat.id):
        await message.answer("Ошибка: Вы не можете кикнуть человека, который имеет должность равнную вашей или выше")
        return
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id
        )
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            only_if_banned=True
        )
        await message.answer(
            f"Пользователь {target_name} исключен из чата\n\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("mute"))
async def mute_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Муты можно выдавать только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    
    parts = message.text.split(maxsplit=3)
    target_input = None
    reason = "не указана"
    if message.reply_to_message:
        target_input = str(message.reply_to_message.from_user.id)
        if len(parts) >= 2:
            try:
                minutes = int(parts[1])
            except ValueError:
                reason = parts[1]
        if len(parts) >= 3:
            reason = parts[2]
    elif len(parts) >= 2:
        target_input = parts[1]
        if len(parts) >= 3:
            try:
                minutes = int(parts[2])
            except ValueError:
                reason = parts[2]
        if len(parts) >= 4:
            reason = parts[3]
    else:
        await message.answer(
            "Ошибка:\n\n Введите:\n"
            "1) /mute [минуты] [причина] в ответ на сообщение того, кому хочешь выдать мут\n"
            "2) /mute @username [минуты] [причина]\n"
            "3) /mute ID [минуты] [причина]"
        )
        return
    target_id = None
    target_name = target_input
    if target_input.startswith("@"):
        username = target_input[1:]
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=username
            )
            target_id = member.user.id
            target_name = member.user.full_name
        except Exception:
            await message.answer(
                f"Ошмбка: Пользователь @{username} не найден в чате.\n\nПопробуйте через ID или reply на его сообщение.")
            return
    else:
        try:
            target_id = int(target_input)
        except ValueError:
            await message.asnwer("Ошибка: Вы не указали кому выдать мут\n\nИспользуйте @username или ID")
            return

        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=target_id
            )
            target_name = member.user.full_name
        except Exception:
            target_name = f"ID {target_id}"
    if target_id == message.from_user.id:
        await message.answer("Ошибка: Выдать мут самому себе нельзя!")
        return
    if not await can_punish(message.from_user.id, target_id, message.chat.id):
        await message.answer("Ошибка: Вы не можете выдать мут человеку, который имеет должность равнную вашей или выше")
        return
    until = datetime.datetime.now() + timedelta(minutes=minutes)
    try:
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=target_id, permissions=ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"Пользователь {target_name} получил мут на {minutes} мин. Причина: {reason}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("ban"))
async def ban_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Банить можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
            return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    parts = message.text.split(maxsplit=3)
    target_input = None
    days = None
    reason = "не указана"
    if message.reply_to_message:
        target_input = str(message.reply_to_message.from_user.id)
        if len(parts) >= 2:
            try:
                days = int(parts[1].lower().replace("d", ""))
            except ValueError:
                reason = parts[1]
        if len(parts) >= 3:
            reason = parts[2]
    elif len(parts) >= 2:
        target_input = parts[1]
        if len(parts) >= 3:
            try:
                days = int(parts[2].lower().replace("d", ""))
            except ValueError:
                reason = parts[2]
        if len(parts) >= 4:
            reason = parts[3]
    else:
        await message.answer(
            "Ошибка:\n\n Введите:\n"
            "1) /ban [дни] причина в ответ на сообщение того, кого хотите забанить\n"
            "2) /ban @username [дни] причина\n"
            "3) /ban ID [дни] причина\n\n"
    
        )
        return
    target_id = None
    target_name = target_input
    if target_input.startswith("@"):
        username = target_input[1:]
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=username
            )
            target_id = member.user.id
            target_name = member.user.full_name
        except Exception:
            await message.answer(f"Ошибка: Пользователь @{username} не найден в чате\n\nПопробуйте через ID")
            return
    else:
        try:
            target_id = int(target_input)
        except ValueError:
            await message.answer("Ошибка: Вы не указали кого забанить\n\nИспользуйте @username или ID")
            return
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=target_id
            )
            target_name = member.user.full_name
        except Exception:
            target_name = f"ID {target_id}"
    if target_id == message.from_user.id:
        await message.answer("Ошибка: Себя забанить нельзя!")
        return
    if not await can_punish(message.from_user.id, target_id, message.chat.id):
        await message.answer("Ошибка: Вы не можете выдать бан человеку, который имеет должность равнную вашей или выше")
        return
    bot_member = await bot.get_chat_member(message.chat.id, bot.id)
    until = None
    days_text = "навсегда"
    if days:
        until = datetime.datetime.now() + timedelta(days=days)
        days_text = f"на {days} дн."
    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            until_date=until
        )
        await message.answer(
            f"Пользователь {target_name} забанен {days_text}\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command('warn'))
async def warn_handler(message: Message):
     if message.chat.type == "private":
        await message.answer("Ошибка: Варны можно выдавать только в чатах")
        return
     if not await check_bot_admin(message, "can_pin_messages"):
        return
     if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
     
     
     if not message.reply_to_message:
        await message.answer("Ошибка: Ответьте на сообщение того, кому хотите выдать варн")
        return
     parts = message.text.split()
     if len(parts) > 2:
        await message.answer("Ошибка: Введите /warn причина")
        return
     target = message.reply_to_message.from_user
     if target.id == message.from_user.id:
        await message.answer("Ошибка: Выдать варн нельзя!")
        return
     target_id = message.from_user.id
     if not await can_punish(message.from_user.id, target.id, message.chat.id):
        await message.answer("Ошибка: Вы не можете выдать варн человеку, который имеет должность равнную вашей или выше")
        return
     await message.answer("В разработке")

@dp.message(Command('warnlist'))
async def warnlist_handler(message: Message):
     if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать список участников с предупреждениями можно выдавать только в чатах")
        return
     if not await check_bot_admin(message, "can_pin_messages"):
        return
     if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return 
     
     await message.answer('В разработке')

@dp.message(Command("unban"))
async def unban_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Разбанивать можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
            return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    
    parts = message.text.split()
    target_input = None
    if message.reply_to_message:
        target_input = str(message.reply_to_message.from_user.id)
    elif len(parts) >= 2:
        target_input = parts[1]
    else:
        await message.answer(
            "Ошибка:\n\n Введите:\n"
            "1) /unban в ответ на сообщение того, кого хотите разбанить\n"
            "2) /unban @username\n"
            "3) /unban ID"
        )
        return
    target_id = None
    target_name = target_input
    if target_input.startswith("@"):
        username = target_input[1:]
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=username
            )
            target_id = member.user.id
            target_name = member.user.full_name
        except Exception:
            await message.answer(
                f"Ошибка: Пользователь @{username} не найден в чате.\n\nПопробуйте через ID.")
            return
    else:
        try:
            target_id = int(target_input)
        except ValueError:
            await message.answer("Ошибка: Вы не указали кого разбанить\n\nИспользуйте @username или ID")
            return
        try:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=target_id
            )
            target_name = member.user.full_name
        except Exception:
            target_name = f"ID {target_id}"
    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            only_if_banned=True
        )
        await message.answer(f"Пользователь {target_name} разбанен")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command('unwarn'))
async def unwarn_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Снимать варны можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    if not message.reply_to_message:
        await message.answer("Ошибка: Ответь на сообщение того, кому хочешь снять варн")
        return
    await message.answer('В разработке')



@dp.message(Command('banlist'))
async def banlist_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать список участников в бане можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    await message.answer('В разработке')

@dp.message(Command('mutelist'))
async def mutelist_handler(message: Message):
     if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать список участников находящихся в муте можно только в чатах")
        return
     if not await check_bot_admin(message, "can_pin_messages"):
        return
     if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
     
     
     await message.answer('В разработке')

@dp.message(Command('greetings'))
async def greetings_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать приветствие можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    await message.answer("В разработке")

@dp.message(Command('addgreetings'))
async def addgreetings_handler(message: Message):
     if message.chat.type == "private":
        await message.answer("Ошибка: Устанавливать приветствия можно только в чатах")
        return
     if not await check_bot_admin(message, "can_pin_messages"):
        return
     if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
     await message.answer('В разработке')

@dp.message(Command('rules'))
async def rules_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать правила можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    await message.answer("В разработке")

@dp.message(Command('addrules'))
async def addruless_handler(message: Message):
     if message.chat.type == "private":
        await message.answer("Ошибка: Устанавливать правила можно только в чатах")
        return
     if not await check_bot_admin(message, "can_pin_messages"):
        return
     if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
     await message.answer('В разработке')

@dp.message(Command("pin"))
async def pin_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Закреплять сообщения можно только в чатах")
        return
    if not await check_bot_admin(message, "can_pin_messages"):
        return
    if not await is_admin(message.from_user.id, message.chat.id):
        await message.answer("Ошибка: У вас нет прав на выполнение этого действия")
        return
    if not message.reply_to_message:
        await message.answer("Ошибка: Ответьте на сообщение которое хотите закрепить")
        return
    try:
        await bot.pin_chat_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
        await message.answer("Сообщение успешно закреплено")
    except Exception as e:
        await message.asnwer(f"Ошибка: {e}")

@dp.message(Command('weather'))
async def weather_handler(message: Message):
    await message.answer("В разработке")

@dp.message(Command('top'))
async def top_handler(message: Message):
    if message.chat.type == "private":
        await message.answer("Ошибка: Просматривать топ по сообщениям можно только в чатах")
        return
    await message.answer("В разработке")

@dp.message()
async def unknown_handler(message: Message):
    pass

async def main():
    print("Бот запущен...")
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    