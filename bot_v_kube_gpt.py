import requests
import logging
from bot_v_kube_db import update_row_value, get_data_for_user
from bot_v_kube_config import HEADERS, MAX_TOKENS, modelUri, tokenizer, stream, temperature, URL_GENERATE


class GPT:
    def __init__(self, system_content=""):
        self.headers = HEADERS
        self.system_content = system_content
        self.MAX_TOKENS = MAX_TOKENS
        self.assistant_content = "Хорошо, я начну свой рассказ: \n"

    def process_resp(self, response, user_id) -> [bool, str]:
        if response.status_code < 200 or response.status_code >= 300:
            self.clear_history()
            return False, f"Ошибка: {response.status_code}"
        logging.info(f"Ошибка: {response.status_code}")

        try:
            full_response = response.json()
        except:
            self.clear_history()
            return False, "Ошибка получения JSON"
        logging.info("Ошибка получения JSON")

        if "error" in full_response:
            self.clear_history()
            return False, f"Ошибка: {full_response}"
        logging.info(f"Ошибка: {full_response}")

        try:
            result = full_response['result']['alternatives'][0]['message']['text']
        except KeyError:
            self.clear_history()
            return False, "Ошибка: неверный формат ответа от сервера"
        logging.info("Ошибка: неверный формат ответа от сервера")

        if result is None or result == "":
            self.clear_history()
            return True, "Объяснение закончено"

        self.save_history(result, user_id)
        return True, self.assistant_content

    def count_tokens(self, user_id):
        user_data = get_data_for_user(user_id)
        combined_text = ' '.join(filter(None, [user_data['system_content'], user_data['user_content'], user_data['answer']]))
        data = {
            "modelUri": modelUri,
            "text": combined_text
        }

        token_count = len(requests.post(tokenizer, json=data, headers=self.headers).json()['tokens'])

        if token_count is not None:
            update_row_value(user_id, 'tokens', token_count)

    def make_promt(self, user_request, user_id):
        system_content = ("Ты помощник по яйцам, ты должен помочь пользователю разобраться с яйцами.")
        update_row_value(user_id, 'system_content', system_content)
        json = {
            "modelUri": modelUri,
            "completionOptions": {
                "stream": stream,
                "temperature": temperature,
                "maxTokens": self.MAX_TOKENS,
            },
            "messages": [
                {"role": "system", "text": system_content},
                {"role": "user", "text": user_request},
                {"role": "assistant", "text": self.assistant_content}
            ]
        }
        return json

    def send_request(self, json):
        resp = requests.post(URL_GENERATE, headers=self.headers, json=json)
        return resp

    def save_history(self, content_response, user_id):
        if content_response not in self.assistant_content:
            self.assistant_content += content_response
            update_row_value(user_id, 'answer', f' {self.assistant_content}')

    def clear_history(self):
        self.assistant_content = "Хорошо, я объяснять: \n"
