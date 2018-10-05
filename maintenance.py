import json
import requests
import time
import datetime
from dbhelper import DBHelper
import urllib
from io import BytesIO
from os import listdir
import emoji # pero buat the fuck
from models import obesity_risk

# info to load at start
# token is not in the source code for security
TOKEN  = '561268964:AAFAaheSH5-EibQwla3X-HFnq745LM_QcFw' #open('token.txt', 'r').read().split('\n')[0].strip()
# URL to interact with the API
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


# funcion auxiliar de nivel más bajo para recibir mensajes
def get_url(url):
    # funcion para recibir lo que se le pasa al bot
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    # obteniene lo que se le pasa al bot con la funcion auxiliar
    content = get_url(url)
    # transforma de JSON a diccionario
    js = json.loads(content)
    return js


def get_updates(offset=None):
    # peticion para obtener las novedades
    url = URL + "getUpdates"
    # offset es el numero del ultimo mensaje recibido
    # el objetivo es no volver a pedirlo todo
    if offset:
        url += "?offset={}".format(offset)
    # llamada a la funcion auxiliar
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    # el orden de llegada de los mensajes al bot produce un id creciente
    # devolvemos el maximo para saber por donde nos hemos quedado
    update_ids = []
    return max([int(el['update_id']) for el in updates['result']])


#################
#
#   TELEGRAM API MACROS
#
#################

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    # reply_markup is for a special keyboard
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def send_photo(localpath, chat_id):
    # give the name of a file in 'img' folder
    # send that image to the user
    url = URL + "sendPhoto"
    files = {'photo': open(localpath, 'rb')}
    data = {'chat_id' : chat_id}
    r = requests.post(url, files=files, data=data)

def send_sticker(sticker_id, chat_id):
    # send an sticker
    url = URL + "sendSticker"
    # atributtes
    data = {'chat_id' : chat_id, 'sticker': sticker_id}
    # it returns the same file if success, can be stored in a variable
    requests.post(url, data=data)


def forward(chat_from, msg_id, chat_id):
    # forward a messege
    url = URL + "forwardMessage"
    # atributtes
    data = {'chat_id' : chat_id, 'from_chat_id': chat_from, 'message_id':msg_id}
    requests.post(url, data=data)

def send_GIF(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendVideo"
    # atributtes
    files = {'video': open('img/'+localpath, 'rb')}
    data = {'chat_id' : chat_id}
    requests.post(url, files=files, data=data)


def handle_updates(updates):
    global languages
    for update in updates["result"]:
        chat = update['message']['chat']['id']
        send_message('Sorry, the bot is under maintenance now, try later!', chat)


def main():
    # variable para controlar el numero de mensajes
    last_update_id = None
    # bucle infinito
    while True:
        # obten los mensajes no vistos
        updates = get_updates(last_update_id)
        # si hay algun mensaje do work
        #try:
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        # hay que dejar descansar los servidores de telegram
        time.sleep(0.5)

        #except Exception as e:
        #    print('Error ocurred, watch log!')
        #    log_entry(str(updates))


if __name__ == '__main__':
    main()
