import os
import threading

import requests


# def log_to_telegram(text):
#     thread = threading.Thread(target=_log_to_telegram, args=(text,))
#     thread.start()
#     thread.join()
#
#
# def _log_to_telegram(text):
#     base_url = f"https://api.telegram.org/bot{os.environ.get('TOKEN')}/sendMessage"
#     payload = {
#         "chat_id": os.environ.get('CHAT_ID'),
#         "text": text
#     }
#     response = requests.post(base_url, data=payload)
#     print('notified')


def news(text):
    pass
    # thread = threading.Thread(target=_news_to_telegram, args=(text,))
    # thread.start()
    # # thread.join()


def _news_to_telegram(text):
    base_url = f"https://api.telegram.org/bot{os.environ.get('ALGO_TOKEN')}/sendMessage"
    payload = {
        "chat_id": os.environ.get('CHAT_ID'),
        "text": text
    }
    response = requests.post(base_url, data=payload)
    print('notified',response)
