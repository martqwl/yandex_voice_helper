import telebot
import logging
import io
from telebot.types import Message
from bot_v_kube_validators import is_stt_block_limit
from bot_v_kube_speechkit import speech_to_text, text_to_speech
from telebot.types import ReplyKeyboardMarkup
from bot_v_kube_info import start_message, help_message
from true_final_boss_Ya.bot_v_kube_creds import TOKEN
from bot_v_kube_config import MAX_SYMBOLS, MAX_SYMBOLS_PER_USER
from bot_v_kube_db import update_row_value, newdata, get_data_for_user, count_all_symbol, check_token_limit_and_sessions, prepare_db
from bot_v_kube_debug import clear_log_file, debugger, start_debug_mode, stop_debug_mode
from bot_v_kube_gpt import GPT

bot = telebot.TeleBot(TOKEN)

gpt = GPT()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.log",
    filemode="a",
)

def log_action(action):
    logging.info(action)

def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

@bot.message_handler(commands=['start'])
def bot_start(message):
    user_id = message.from_user.id
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь начал использовать бота")
    log_action("Пользователь начал использовать бота")
    keyboard = create_keyboard(["/help"])
    bot.send_message(user_id, text=start_message, reply_markup=keyboard)
    newdata(message.chat.id, '', '', '', '', 0, 0, 0, '')

@bot.message_handler(commands=['help'])
def bot_help(message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь использовал команду /help")
    log_action("Пользователь использовал команду /help")
    keyboard = create_keyboard(["/start", "/help", "/stt", "/tts", "Начни помогать"])
    bot.send_message(chat_id=message.chat.id, text=help_message, reply_markup=keyboard)


@bot.message_handler(commands=['debug'])
def debug(message):
    log_action("Режим отладки активирован")
    logging.getLogger().setLevel(logging.DEBUG)
    bot.send_message(message.chat.id, 'Режим отладки активирован')
    try:
        with open('log_file.log', 'r') as file:
            logs = file.read()
    except FileNotFoundError:
        logging.error("Файл log_file.log не найден")
        bot.reply_to(message, 'Файл не найден')

    bot.send_document(message.chat.id, io.BytesIO(logs.encode()))
    clear_log_file(message)

@bot.message_handler(commands=['debug_mode_on'])
def debug_mode_on(message):
    start_debug_mode(message)


@bot.message_handler(commands=['debug_mode_off'])
def debug_mode_off(message):
    stop_debug_mode(message)


# Обрабатываем команду /stt
@bot.message_handler(commands=['stt'])
def stt_handler(message: Message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь использовал команду /stt")
    log_action("Пользователь использовал команду /stt")
    bot.send_message(message.chat.id, "Отправьте гс")
    bot.register_next_step_handler(message, stt)

def stt(message: Message):
    user_id = message.chat.id

    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        bot.send_message(message.chat.id, "Не гс!")
        return

    # Считаем аудиоблоки и проверяем сумму потраченных аудиоблоков
    stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
    if not stt_blocks:
        bot.send_message(user_id, error_message)
        return


    voice_id = message.voice.file_id
    info_file = bot.get_file(voice_id)
    file = bot.download_file(info_file.file_path)

    status, message_text = speech_to_text(file)

    if status:
        update_row_value(user_id, 'stt_blocks', stt_blocks)
        update_row_value(user_id, 'text', message_text)
        bot.send_message(user_id, message_text)

@bot.message_handler(commands=['tts'])
def tts_handler(message: Message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь исспользовал команду /tts")
    log_action("Пользователь исспользовал команду /tts")
    bot.send_message(message.chat.id, "Введите текст: ")
    bot.register_next_step_handler(message, tts)


def tts(message: Message):
    user_id = message.chat.id
    text = message.text
    gpt_data = get_data_for_user(user_id)


    if gpt_data['tts_symbols'] == '':
        update_row_value(user_id, 'tts_symbols', len(text))
    else:
        update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))

    if message.content_type != 'text':
        bot.send_message(user_id, "Отправьте текст")
        bot.register_next_step_handler(message, tts)
        return

    if len(message.text) >= MAX_SYMBOLS:
        bot.send_message(user_id, "Слишком много симбоблс")
        bot.register_next_step_handler(message, tts)
        return

    if count_all_symbol(user_id, text) >= MAX_SYMBOLS_PER_USER:
        bot.send_message(message.chat.id, "Слишком много симбоблс")
        return

    status, message_data = text_to_speech(text)
    update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))
    if not status:
        bot.send_message(user_id, message_data)
        return

    bot.send_voice(user_id, message_data)


@bot.message_handler(func=lambda message: message.text == "Начни помогать")
def hello(message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь начал работу с ботом")
    log_action("Пользователь начал работу с ботом")
    bot.send_message(message.chat.id, text='Напиши "Продолжить объяснение", если хочешь, чтобы я продолжил объяснять. Напиши "Конец", если хочешь, чтобы я закончил')
    bot.send_message(message.chat.id, text='На все про все у вас есть 1000 токенов, используйте их с умом!')
    bot.send_message(chat_id=message.chat.id, text="Напиши запрос текстом или отправьте голосове сообщение")


@bot.message_handler(func=lambda message: message.text == "Конец")
def end_handler(message):
    user_id = message.chat.id
    if debugger.active:
        bot.send_message(user_id, f"Log: Пользователь закончил работу с GPT")
    log_action("Пользователь закончил работу с GPT")
    bot.send_message(user_id, text='До свидания!')
    bot.send_message(user_id, "Текущее решение завершено")
    gpt.clear_history()
    keyboard = create_keyboard(["/start", "/help", "/stt", "/tts", "Начни помогать"])
    bot.send_message(chat_id=user_id, text=help_message, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "Продолжить объяснение")
def continue_handler(message):
    user_id = message.from_user.id
    user_request_data = get_data_for_user(user_id)
    json = gpt.make_promt(user_request_data['answer'], user_id)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp, user_id)
    gpt.save_history(response[1], user_id)
    update_row_value(user_id, 'answer', response[1])
    bot.send_message(user_id, response[1])
    if check_token_limit_and_sessions(user_id) == False:
        bot.send_message(message.chat.id, text='Вы привысили лимит на количество сессий.')
        bot.register_next_step_handler(message, bot_help)


@bot.message_handler(func=lambda message: message.text == "Продолжить голосовое объяснение")
def voice_continue_handler(message):
    user_id = message.chat.id
    user_request_data = get_data_for_user(user_id)
    json = gpt.make_promt(user_request_data['answer'], user_id)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp, user_id)
    gpt.save_history(response[1], user_id)
    update_row_value(user_id, 'answer', response[1])
    if check_token_limit_and_sessions(user_id) == False:
        bot.send_message(user_id, text='Вы привысили лимит на количество сессий.')
    text = response[1]
    if user_request_data['tts_symbols'] == '':
        update_row_value(user_id, 'tts_symbols', len(text))
    else:
        update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))

    status, message_data = text_to_speech(text)
    update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))
    if not status:
        bot.send_message(user_id, message_data)
        return

    bot.send_voice(user_id, message_data)
    gpt.count_tokens(user_id)

@bot.message_handler(content_types=['voice'])
def voice_dialog(message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь начал работу с GPT")
    log_action("Пользователь начал работу с GPT")

    user_id = message.from_user.id

    system_content = gpt.system_content
    update_row_value(user_id, "system_content", system_content)
    stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
    if not stt_blocks:
        bot.send_message(user_id, error_message)
        return
    voice_id = message.voice.file_id
    info_file = bot.get_file(voice_id)
    file = bot.download_file(info_file.file_path)
    status, message_text = speech_to_text(file)

    if status:
        update_row_value(user_id, 'user_content', message_text)
        gpt_dialog_voice(message)


@bot.message_handler(func=lambda message: message.text != 'Конец' and message.text != 'Продолжить объяснение' and message.text != 'Продолжить голосовое объяснение')
def dialog(message):
    if debugger.active:
        bot.send_message(message.chat.id, f"Log: Пользователь начал работу с GPT")
    log_action("Пользователь начал работу с GPT")

    user_id = message.from_user.id
    user_content = message.text
    system_content = gpt.system_content
    update_row_value(user_id, "system_content", system_content)
    update_row_value(user_id, "user_content", user_content)
    gpt_dialog(message)



def gpt_dialog(message):
    user_id = message.chat.id
    bot.send_message(user_id, text='Выберете, что сделать: ', reply_markup=create_keyboard(['Конец', 'Продолжить объяснение']))

    if debugger.active:
        bot.send_message(user_id, f"Log: GPT_dialog вызвана")
    log_action("GPT_dialog вызвана")
    user_request_data = get_data_for_user(user_id)
    json = gpt.make_promt(user_request_data['user_content'], user_id)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp, user_id)

    if not response[0]:
        if debugger.active:
            bot.send_message(user_id, f"Log: Не удалось выполнить запрос")
        logging.error("Не удалось выполнить запрос")
        bot.send_message(user_id, text="Не удалось выполнить запрос...")
    bot.send_message(user_id, response[1])
    assistant_content = response[1]
    update_row_value(user_id, "answer", assistant_content)
    gpt.count_tokens(user_id)

def gpt_dialog_voice(message):
    user_id = message.chat.id
    bot.send_message(user_id, text='Выберете, что сделать: ', reply_markup=create_keyboard(['Конец', 'Продолжить голосовое объяснение']))
    if debugger.active:
        bot.send_message(user_id, f"Log: GPT_dialog вызвана")
    log_action("GPT_dialog вызвана")
    user_request = message.text
    user_request_data = get_data_for_user(user_id)
    json = gpt.make_promt(user_request_data['user_content'], user_id)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp, user_id)

    if not response[0]:
        if debugger.active:
            bot.send_message(user_id, f"Log: Не удалось выполнить запрос")
        logging.error("Не удалось выполнить запрос")
        bot.send_message(user_id, text="Не удалось выполнить запрос...")
    user_id = message.chat.id
    text = response[1]
    gpt_data = get_data_for_user(user_id)

    if gpt_data['tts_symbols'] == '':
        update_row_value(user_id, 'tts_symbols', len(text))
    else:
        update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))

    status, message_data = text_to_speech(text)
    update_row_value(user_id, 'tts_symbols', count_all_symbol(user_id, text))
    if not status:
        bot.send_message(user_id, message_data)
        return



    bot.send_voice(user_id, message_data)
    assistant_content = response[1]
    update_row_value(user_id, "answer", assistant_content)
    gpt.count_tokens(user_id)



@bot.message_handler(func=lambda message: message.text[0] == '/' and message.text != '/debug' or message.text != '/help' or message.text != '/start' or message.text != '/stt' or message.text != '/tts')
def invalid_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Такой комманды не существует')
    if debugger.active:
        bot.send_message(user_id, f"Пользователь {user_id} попытался использовать команду {message.text}.")
    log_action(f"Пользователь {user_id} попытался использовать команду {message.text}.")


if __name__ == '__main__':
    prepare_db()
    bot.infinity_polling()
