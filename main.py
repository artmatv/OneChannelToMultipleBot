import asyncio
import os
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    ChatMemberHandler,
    ContextTypes, ChatJoinRequestHandler,
)
from config import BOT_TOKEN, ADDITIONAL_CHANNEL_IDS, MAIN_FORUM_ID, LOGS_CHANNEL_ID
from logs import add_message_to_queue, message_sender


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title

    if chat_id == MAIN_FORUM_ID:
        for chat in ADDITIONAL_CHANNEL_IDS:
            await context.bot.unban_chat_member(chat_id=chat, user_id=user_id, only_if_banned=True)

    if chat_id in ADDITIONAL_CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(chat_id=MAIN_FORUM_ID, user_id=user_id)
            if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
                await add_message_to_queue(LOGS_CHANNEL_ID,
                                           f"Пользователь {user_name} (ID: {user_id}) успешно принят в канал {chat_name} (ID: {chat_id})")
            else:
                await context.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        except Exception as e:
            print(f"error {e}")
            await context.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
            await add_message_to_queue(LOGS_CHANNEL_ID,
                                       f"Ошибка обработки вступления пользователя {user_name} (ID: {user_id}): {e}")
            await context.bot.send_message(chat_id=user_id,
                                           text="Произошла ошибка при проверке вашего членства. Пожалуйста, попробуйте позже или свяжитесь с администратором.")

async def member_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    user = result.from_user
    user_id = user.id
    user_name = user.full_name
    status = result.new_chat_member.status

    if status in ['left', 'kicked']:
        try:
            member = await context.bot.get_chat_member(chat_id=MAIN_FORUM_ID, user_id=user_id)
            if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                for channel_id in ADDITIONAL_CHANNEL_IDS:
                    try:
                        chat = await context.bot.get_chat(chat_id=channel_id)
                        chat_name = chat.title
                        await context.bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
                        await context.bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
                        await add_message_to_queue(LOGS_CHANNEL_ID,
                                                   f"Пользователь {user_name} (ID: {user_id}) удален из канала {chat_name} (ID: {channel_id})")
                    except Exception as e:
                        await add_message_to_queue(LOGS_CHANNEL_ID,
                                                   f"Ошибка обработки удаления пользователя {user_name} (ID: {user_id}) из канала {channel_id}: {e}")
                        print(f"Ошибка при удалении пользователя {user_id} из канала {channel_id}: {e}")
        except Exception as e:
            print(f"Ошибка при проверке статуса пользователя {user_name} (ID: {user_id}): {e}")

def main():
    print("Запуск бота")
    print(os.environ)
    print(MAIN_FORUM_ID)
    application = Application.builder().token(BOT_TOKEN).build()

    loop = asyncio.get_event_loop()
    loop.create_task(message_sender(application.bot))

    application.add_handler(ChatMemberHandler(member_status_change, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(ChatJoinRequestHandler(join_request))

    application.run_polling(allowed_updates=Update.CHAT_MEMBER)

if __name__ == '__main__':
    main()
