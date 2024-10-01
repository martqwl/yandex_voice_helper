import sqlite3
import logging
from bot_v_kube_config import DB_NAME, TABLE_NAME, vip_id, max_tokens

logging.basicConfig(filename='log_file.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s', filemode='w')


def create_db(database_name=DB_NAME):
    logging.info(f"DATABASE: база данных создана")
    db_path = f'{database_name}'
    conn = sqlite3.connect(db_path)
    conn.close()


def execute_query(sql_query, data=None, db_path=DB_NAME):
    logging.info(f"DATABASE: использована функция execute_query")
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)
        connection.commit()


def execute_selection_query(sql_query, data=None, db_path=DB_NAME):
    logging.info(f"DATABASE: использована функция execute_selection_query")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows


def create_table(TABLE_NAME):
    logging.info(f"DATABASE: использована функция create_table")
    sql_query = (f'CREATE TABLE IF NOT EXISTS {TABLE_NAME}'
                 f'(id INTEGER PRIMARY KEY,'
                 f'user_id INTEGER,'
                 f'text TEXT,'
                 f'system_content TEXT,'
                 f'user_content TEXT,'
                 f'answer TEXT,'
                 f'tokens INTEGER,'
                 f'session_id INTEGER,'
                 f'stt_blocks INTEGER,'
                 f'tts_symbols INTEGER)')
    execute_query(sql_query)


def insert_row(user_id, text, system_content, user_content, answer, tokens, session_id, stt_blocks, tts_symbols):
    logging.info(f"DATABASE: использована функция insert_row")
    sql_query = f"""
    INSERT INTO {TABLE_NAME} 
    (user_id, text, system_content, user_content, answer, tokens, session_id, stt_blocks, tts_symbols)
    VALUES(?,?,?,?,?,?,?,?,?)"""
    execute_query(sql_query, [user_id, text, system_content, user_content, answer, tokens, session_id, stt_blocks, tts_symbols])


def count_all_symbol(user_id, text):
    logging.info(f"DATABASE: использована функция count_all_symbol")
    try:
        sql_query = f"SELECT tts_symbols FROM {TABLE_NAME} WHERE user_id = {user_id}"
        data = execute_selection_query(sql_query)
        symbobls = data[0][0] + len(text)

        if data:
            return symbobls
    except IndexError:
        return 0

def count_all_blocks(user_id):
    logging.info(f"DATABASE: использована функция count_all_blocks")
    sql_query = f"SELECT stt_blocks FROM {TABLE_NAME} WHERE user_id = {user_id}"
    data = execute_selection_query(sql_query)
    blobs = data[0][0]

    if data:
        return blobs


def prepare_db(clean_if_exists=False):
    logging.info(f"DATABASE: использована функция prepare_db")
    create_db()
    create_table(TABLE_NAME)


def is_value_in_table(table_name, column_name, value):
    logging.info(f"DATABASE: использована функция is_value_in_table")
    sql_query = f'SELECT {column_name} FROM {table_name} WHERE {column_name} = {value} LIMIT 1'
    rows = execute_selection_query(sql_query)
    return any(rows) > 0


def get_data_for_user(user_id):
    logging.info(f"DATABASE: использована функция get_data_for_user")
    if is_value_in_table(TABLE_NAME, 'user_id', user_id):
        sql_query = f'SELECT * FROM {TABLE_NAME} WHERE user_id = ? LIMIT 1'
        row = execute_selection_query(sql_query, [user_id])[0]
        return {
            "user_id": row[1],
            "text": row[2],
            "system_content": row[3],
            "user_content": row[4],
            "answer": row[5],
            "tokens": row[6],
            "session_id": row[7],
            "stt_blocks": row[8],
            "tts_symbols": row[9]
        }
    else:
        logging.info(f"DATABASE: Пользователь с id {user_id} не найден")
        return {
            "user_id": "",
            "text": "",
            "system_content": "",
            "user_content": "",
            "answer": "",
            "tokens": "",
            "session_id": "",
            "stt_blocks": "",
            "tts_symbols": ""
        }


def update_row_value(user_id, column_name, new_value):
    logging.info(f"DATABASE: использована функция update_row_value")
    if is_value_in_table(TABLE_NAME, "user_id", user_id):
        sql_query = f'UPDATE {TABLE_NAME} SET {column_name} = ? WHERE user_id = {user_id}'
        execute_query(sql_query, [new_value])
    else:
        logging.info(f"DATABASE: Пользователь с id {user_id} не найден")


def add_sessions(user_id):
    logging.info(f"DATABASE: использована функция add_sessions")
    user_data = get_data_for_user(user_id)
    if user_data['user_id'] not in vip_id:
        session_id = 1
        update_row_value(user_id, 'session_id', session_id)


def check_users_limit():
    logging.info(f"DATABASE: использована функция check_users_limit")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(DISTINCT user_id) FROM {TABLE_NAME}")
    count = cursor.fetchone()[0]

    if count > 3:
        return False
    else:
        return True




def newdata(user_id, text, system_content, user_content, answer, tokens, session_id, stt_blocks, tts_symbols):
    logging.info(f"DATABASE: использована функция newdata")
    if is_value_in_table(TABLE_NAME, 'user_id', user_id):
        update_row_value(user_id, 'text', text)
        update_row_value(user_id, 'system_content', system_content)
        update_row_value(user_id, 'user_content', user_content)
        update_row_value(user_id, 'answer', answer)
        update_row_value(user_id, 'tokens', tokens)
        update_row_value(user_id, 'answer', answer)
        update_row_value(user_id, 'session_id', session_id)
        update_row_value(user_id, 'stt_blocks', stt_blocks)
        update_row_value(user_id, 'tts_symbols', tts_symbols)

        logging.info(f"DATABASE: Данные для пользователя {user_id} обновлены")
    else:
        insert_row(user_id, text, system_content, user_content, answer, tokens, session_id, stt_blocks, tts_symbols)
        logging.info(f"DATABASE: Данные для пользователя {user_id} добавлены")
    prepare_db(True)


def check_token_limit_and_sessions(user_id):
    logging.info(f"DATABASE: использована функция check_token_limit_and_sessions")
    user_data = get_data_for_user(user_id)
    session_id = user_data['session_id']
    if user_data['user_id'] not in vip_id:
        if user_data and len(user_data['tokens']) >= max_tokens:
            if session_id == 0:
                print("Превышен лимит токенов и сессий.")
                return False
        else:
            return True
