import telebot
from telebot import types

API_TOKEN = 'ТОКЕНБОТА'
CHANNEL_NAME = '@USERNAMEВАШЕГОКАНАЛА'
DEVELOPER_ID = СЮДАIDАДМИНА 
ADMIN_USER_ID = И СЮДАIDАДМИНА 

bot = telebot.TeleBot(API_TOKEN)

meme_storage = {}
users_data = {}  

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"👋 Приветствую тебя, {message.from_user.first_name}! Отправь пожалуйста видео или фото мем! 😄")

@bot.message_handler(commands=['send_message'])
def start_message_distribution(message):
    if message.from_user.id == DEVELOPER_ID:
        bot.send_message(DEVELOPER_ID, "Введите текст для рассылки:")
        bot.register_next_step_handler(message, handle_message_input)
    else:
        bot.send_message(message.chat.id, "Эта команда доступна только разработчикам.")

def handle_message_input(message):
    input_text = message.text
    if input_text:
        distribute_message(input_text)
    else:
        bot.send_message(DEVELOPER_ID, "Введенный текст пустой. Пожалуйста, повторите попытку.")

def distribute_message(message_text):
    delivered_users = []

    for user_id, user_data in users_data.items():
        if user_id != DEVELOPER_ID:
            try:
                bot.send_message(user_id, message_text)
                delivered_users.append(f"@{user_data.get('username', f'Пользователь_{user_id}')}")
            except telebot.apihelper.ApiException as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    delivered_text = (f"Рассылка завершена. Сообщение успешно доставлено пользователям: "
                      f"{', '.join(delivered_users)}" if delivered_users
                      else "Рассылка завершена. Не удалось доставить сообщение ни одному пользователю.")
    bot.send_message(DEVELOPER_ID, delivered_text)

@bot.message_handler(content_types=['photo', 'video'])
def handle_media(message):
    file_id = (message.photo[-1].file_id if 'photo' in message.content_type else message.video.file_id)
    key = (message.chat.id, message.message_id)
    meme_storage[key] = {'file_id': file_id, 'user_id': message.from_user.id, 'username': message.from_user.username, 'content_type': message.content_type}

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Да✅", callback_data=f"moderate_meme_{key}")
    markup.add(button)
    bot.send_message(message.chat.id, f"Хочешь отправить этот мем на модерацию? 🧐\nМем будет не принят если тут есть:\n-Пришельцы\n- Вы не любите комару\n- Вы холодильнекофил", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('moderate_meme'))
def query_handler(call):
    key = eval(call.data.split('_')[-1])
    if key in meme_storage:
        meme_info = meme_storage[key]
        markup = types.InlineKeyboardMarkup()
        button_approve = types.InlineKeyboardButton(text="Одобрить ✅", callback_data=f"approve_{key}")
        button_reject = types.InlineKeyboardButton(text="Отказать ❌", callback_data=f"reject_{key}")
        markup.add(button_approve, button_reject)
        if meme_info['content_type'] == 'photo':
            sent_message = bot.send_photo(DEVELOPER_ID, meme_info['file_id'], reply_markup=markup, caption=f"Мем от @{meme_info['username']}! 😂")
        elif meme_info['content_type'] == 'video':
            sent_message = bot.send_video(DEVELOPER_ID, meme_info['file_id'], reply_markup=markup, caption=f"Мем от @{meme_info['username']}! 😂")
        bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: 'approve_' in call.data or 'reject_' in call.data)
def moderation_handler(call):
    action, key = call.data.split('_')[0], eval('_'.join(call.data.split('_')[1:]))
    if key in meme_storage:
        meme_info = meme_storage[key]
        user_id = meme_info['user_id']
        username = meme_info['username']
        file_id = meme_info['file_id']
        if action == 'approve':
            if meme_info['content_type'] == 'photo':
                sent_message = bot.send_photo(CHANNEL_NAME, file_id, caption=f"Мем от @{username}! 😂 Отправить свой мем: @BotMemzBot")
            elif meme_info['content_type'] == 'video':
                sent_message = bot.send_video(CHANNEL_NAME, file_id, caption=f"Мем от @{username}! 😂 Отправить свой мем: @BotMemzBot")
            bot.send_message(user_id, f"Твой мем был опубликован в канале! 🎉\nВот ссылка: https://t.me/{CHANNEL_NAME[1:]}/{sent_message.message_id}")
        elif action == 'reject':
            bot.send_message(user_id, "К сожалению, твой мем не принят. ☹️ Попробуй снова!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        del meme_storage[key]

@bot.message_handler(func=lambda message: True)
def handle_unsupported_content(message):
    bot.reply_to(message, "Пожалуйста, отправляй мемы в виде фото или видео. 🙏")

if __name__ == '__main__':
    bot.infinity_polling()
