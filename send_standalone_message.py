"""
WARNING: THIS HAS NOT BEEN TESTED YET
"""

from os import environ
import requests
from urllib.parse import quote_plus
import json

TOKEN = environ['TOKEN_WAKAMOLA']
# URL to interact with the API
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
    # funcion para recibir lo que se le pasa al bot
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def send_message(text, chat_id, reply_markup=None):
    text = quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    # reply_markup is for a special keyboard
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    return get_url(url)


# send a standalone message
with open ('message.txt', 'r') as message:
    text = message.read()

with open('ids_dict.txt', 'r') as ids_dict:
    ids = json.load(ids_dict)

for id in ids:
    send_message(text=text, chat_id=id)