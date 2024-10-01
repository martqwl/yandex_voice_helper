import requests
from bot_v_kube_config import IAM_TOKEN, FOLDER_ID, params, headers, URL_STT, URL_TTS
import requests
def speech_to_text(data):
    params = "&".join([
        "topic=general",
        f"folderId={FOLDER_ID}",
        "lang=ru-RU"
    ])

    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }
    url = URL_STT + f"?{params}"

    response = requests.post(url, headers=headers, data=data)

    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, f"При запросе в SpeechKit возникла ошибка {response.status_code}"


def text_to_speech(text: str):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }

    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'marina',
        'emotion': 'whisper',
        'folderId': FOLDER_ID,
    }
    response = requests.post(URL_TTS, headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        return False, f"При запросе в SpeechKit возникла ошибка {response.status_code}"
