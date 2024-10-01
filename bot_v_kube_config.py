from true_final_boss_Ya.bot_v_kube_creds import FOLDER_ID, IAM_TOKEN



params = "&".join([
    "topic=general",  # используем основную версию модели
    f"folderId={FOLDER_ID}",
    "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
])

HEADERS = {
        f'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }

headers = {
    'Authorization': f'Bearer {IAM_TOKEN}',
}
URL_GENERATE = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
URL_STT = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?"
URL_TTS = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'

MAX_USER_STT_BLOCKS = 12  # выделяем на каждого пользователя по 12 аудиоблоков

DB_NAME = 'bot_v_kube_db.db'
TABLE_NAME = 'bot_v_kube_table'

MAX_SYMBOLS = 200
MAX_SYMBOLS_PER_USER = 200
max_tokens = 1500
vip_id = [1482726705, 5770464957]
max_users = 4
MAX_TOKENS = 10
stream = False
temperature = 0.6
modelUri = "gpt://b1gbsjnf6hdvvquf2udv/yandexgpt-lite"
tokenizer = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize"


