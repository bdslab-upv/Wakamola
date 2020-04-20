from os import environ
import requests
from urllib.parse import quote_plus

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