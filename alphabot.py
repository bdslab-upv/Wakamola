import json
import requests
import time
import datetime
from dbhelper import DBHelper
import urllib
from io import BytesIO
from os.path import isfile
from os import listdir
import emoji
from models import obesity_risk
import csv

# info to load at start
# token is not in the source code for security
TOKEN = open('token.txt', 'r').read().split('\n')[0].strip()
# URL to interact with the API
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
# handler to the database
db = DBHelper()
# set up
db.setup()
# caching the number of questions
nq_category = db.n_questions()
global languages
# yes / no answers
negations = [el for el in open('strings/negations.txt', 'r').read().split('\n') if el]
afirmations = [el for el in open('strings/afirmations.txt', 'r').read().split('\n') if el]
# TODO default language
def_lang_ = 'es'


###############
#
#   ERROR LOG
#
################
def log_entry(entry):
    # get actual time
    now = datetime.datetime.now()
    dateerror = now.strftime("%Y-%m-%d %H:%M")
    # open the log file in append mode
    with open('error.log', 'a', encoding='utf-8') as log:
        log.write('\n'+dateerror+'\n')
        log.write(str(entry)+'\n\n')


#################
#
#   BASIC TOOLS
#
################

def build_keyboard(items):
    # contruir un teclado para una vez
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


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

def send_file(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendDocument"
    # atributtes
    files = {'document': open(localpath, 'rb')}
    data = {'chat_id' : chat_id}
    print(requests.post(url, files=files, data=data))

###############################
#
#   BOT SPECIFIC METHODS
#
###############################

def checkanswer(str, sts):
    '''
    Accepts numbers and yes/no questions
    '''
    try:
        if sts[0] == 1 and sts[1] > 5: #personal questions
            if str.lower() in afirmations:
                return 1, True
            elif str.lower() in negations:
                return 0, True
            else:
                return None, False
        else:
            return float(str), True
    except ValueError:
        return None, False


##############################
#
#   MAIN FUNCTIONS
#
#############################


def process_lang(language):
    '''
    # TODO arreglar
    aux = language.split('-')[0]
    if aux == 'en':
        return 'en'
    else:
        return 'es'
    '''
    return def_lang_


def load_languages():
    langs_ = {}
    for f in listdir('strings'):
        dict_ = {}
        try:
            with open('strings/'+f, 'r', encoding='utf-8') as csvfile:
                # may happen this is not a csv file
                if not f.endswith('.csv'):
                    continue
                csv_ = csv.reader(csvfile, delimiter=';')
                for row in csv_:
                    dict_[row[0]] = row[1]
            langs_[f.split('.')[0]] = dict_
        except Exception as e :
            log_entry(e)
            continue # sanity check

    return langs_




def filter_update(update):
    if 'edited_message' in update:
        # check if text
            if 'text' in update['edited_message']:
                # update the answer
                process_edit(update)
                return False, update['edited_message']['chat']['id'], update['edited_message']['message_id']
            else:
                # returning none if it's an update without text
                return None, update["message"]["chat"]["id"], None

    elif 'callback_query' in update:
        # data is the text sent by the callback as a msg
        return update['callback_query']['data'], update['callback_query']['from']['id'], \
               update['callback_query']['message']['message_id']

    elif 'message' in update:
        if 'text' in update['message']:
            return update["message"]["text"].strip(), update["message"]["chat"]["id"], update['message']['message_id']

        else:
            # return none if it's a message withpout text
            return None, update["message"]["chat"]["id"], update['message']['message_id']

    else: # inline query for example
        return False, None, None

def process_edit(update):
    text = update["edited_message"]["text"]
    message_id = update['edited_message']['message_id']
    if checkanswer(text):
        try:
            db.update_response_edited(message_id, text)
        except:
            log_entry('Captured error at editing message.')


def go_main(chat, lang):
    '''
    Macro for setting up one user to the main phase
    '''
    db.change_phase(newphase = 0, id_user=chat)
    send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))

'''
# WARNING: This function is not used, but can be interesting
# to use it in future versions
def social_keyboard(lang, n_opt=2):
    items = [el.strip() for el in languages[lang]['keyboard_social'].split('\n') if el.strip()]
    keyboard = []
    count = 0
    aux = []
    for el in items:
        aux.append(el)
        count += 1
        if count == 2:
            keyboard.append(aux)
            aux = []
            count = 0
    if aux:
        keyboard.append(aux)
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)
'''


def main_menu_keyboard(chat, lang=None):
    options = [el for el in languages[lang]['options'].split('\n') if el]
    personal = options[0]
    food = options[1]
    activity = options[2]
    completed = db.check_completed(chat)
    if completed[0]:
        personal += '\t\t:white_heavy_check_mark:'
    if completed[1]:
        food += '\t\t:white_heavy_check_mark:'
    if completed[2]:
        activity += '\t\t:white_heavy_check_mark:'
    # TODO  anyadir texto en social
    keyboard = {'inline_keyboard':[[{'text': emoji.emojize(personal), 'callback_data':'personal'},  {'text':emoji.emojize(food), 'callback_data':'food'}],
                    [{'text':emoji.emojize(activity), 'callback_data':'activity'},{'text':emoji.emojize(options[3]), 'callback_data':'risk'}],
                    [{'text':emoji.emojize(options[5]), 'switch_inline_query': languages[lang]['share']+' '+'https://telegram.me/alphahealthbot?start='+str(chat)}, {'text':emoji.emojize(options[6]), 'callback_data':'credits'}]]}
    return json.dumps(keyboard)


def questionarie(num, chat, lang, msg=None):
    '''
    Method to start a questionnatie flow
    TODO This can be parametrized and be way more general
    '''
    db.change_phase(newphase= num, id_user=chat)
    if num == 1:
        send_photo('img/'+lang+'/personal.jpg', chat)
    elif num == 2:
        send_photo('img/'+lang+'/food.jpg', chat)
    elif num == 3:
        send_photo('img/'+lang+'/activity.jpg', chat)

    if msg:
        send_message(msg, chat)
    # throw first question
    q1 = db.get_question(phase=num, question=1, lang=lang)
    extra_messages(num, 1, chat, lang)
    send_message(emoji.emojize(q1), chat)


def extra_messages(phase, question, chat, lang):
    '''
    This method includes all the extra messages that break the
    usual question - response - question... flow
    TODO parametrize this in order to be less horrendous
    '''
    # food
    if phase == 2 and question == 10: # weekly questionnarie
        send_message(languages[lang]['food_weekly'], chat)


def wakaestado(chat, lang):
    '''
    Piece of the standard flow to calculate and send the wakaestado
    '''
    global languages
    completed = db.check_completed(chat)
    print(completed)
    # put phase to 0
    db.change_phase(newphase = 0, id_user=chat)

    # check if completed all questionaries
    risk = obesity_risk(chat, completed)
    # Wakaestado completo
    if completed[0] and completed[1] and completed[2]:
        # obtain the obsity risk: 0, 1 or 2
        send_message(languages[lang]['wakaestado']+' '+str(risk), chat)
    # WakaEstado parcial
    else:
        # give a general advice
        send_message(languages[lang]['wakaestado_parcial']+' '+str(risk), chat)
    # imagen wakaestado
    send_photo('img/'+lang+'/wakaestado.jpg', chat)
    # instrucciones social
    if completed[0] and completed[1] and completed[2]:
        send_message(languages[lang]['social'], chat)
    go_main(chat=chat, lang=lang)


def handle_updates(updates):
    global languages
    for update in updates["result"]:
        #print(update)
        # controlar si hay texto
        # funcion auxiliar que trata eltipo de mensaje
        text, chat, message_id = filter_update(update)

        # no valid text
        if text == False:
            continue
        elif text == None:
            lang = process_lang(update['message']['from']['language_code'])
            send_message(languages[lang]['not_supported'], chat)


        # try to get current status
        try:
            status = db.get_phase_question(chat)
        except Exception as e:
            status = (0, 0)


        # get user language
        if 'message' in update:
            if 'language_code' in update['message']['from']:
                lang = process_lang(update['message']['from']['language_code'])
            else:
                lang = def_lang_
        # callback version of the language
        elif 'callback_query' in update:
            if 'language_code' in update['callback_query']['from']:
                lang = process_lang(update['callback_query']['from']['language_code'])
            else:
                lang = def_lang_


        # start command / second condition it's for the shared link
        if text.lower() == 'start' or '/start' in text.lower():
            # wellcome message
            send_photo('img/'+lang+'/welcome.jpg', chat)
            send_message(emoji.emojize(languages[lang]['welcome']), chat, main_menu_keyboard(chat, lang))


            # take the username if exists
            username = None
            if 'message' in update and 'username' in update['message']['chat']:
                username = update['message']['chat']['username']
            if 'callback_query' in update and update['message']['chat']:
                username = update['callback_query']['chat']['username']
            # insert user into the db, check collisions
            if not db.check_start(chat):
                # sanity check
                try:
                    db.register_user(id_user=chat, language=lang)
                except Exception as e:
                    print(e)
                    #log_entry("Error registering the user")
            else:
                db.change_phase(newphase = 0, id_user=chat)

            # check for the token
            aux = text.split(' ')
            # TOKEN CHECK -> AFTER REGISTRATION
            if len(aux) == 2:
                # it comes with the token
                friend_token = aux[1]
                try:
                    # all ids are ints
                    int(friend_token)
                    db.add_relationship(chat, friend_token, 'shared')
                except Exception as e:
                    print('Error ocurred on relationship add')
                    log_entry(e)


        # Check if the user have done the start command
        elif db.check_user(chat):
            # if not, just register him and made him select
            db.register_user(id_user=chat, language=lang)
            db.change_phase(newphase = 0, id_user=chat)
            send_message(languages[lang]['select'], chat)

        # Credits
        elif text.lower() == 'credits':
            # junst sed a message with the credits and return to the main menu
            send_message(languages[lang]['credits'], chat)
            #send_file('theme definitivo.tdesktop-theme', chat)
            go_main(chat, lang)

        elif text.lower() == 'personal':
            # set to phase and question 1
            questionarie(1, chat, lang)
            continue
        elif text.lower() == 'food':
            # set to phase and question 2
            questionarie(2, chat, lang, msg=languages[lang]['food_intro'])
        elif text.lower() == 'activity':
            # set to phase and question 3
            questionarie(3, chat, lang)

        elif text.lower() == 'risk':
            # encapsulated code
            wakaestado(chat, lang)

        else:
            # rescata a que responde
            status = db.get_phase_question(chat)
            if (status[0] == 0):
                send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))
                continue


            # TODO FLAW TO STORE LINEAL SH1T
            text, correct_ = checkanswer(text, status)
            if correct_:
                # store the user response
                db.add_answer(id_user=chat, phase=status[0], question=status[1], message_id=message_id, answer=text)

            else:
                send_message(languages[lang]['numeric_response'], chat)
                # repeat last question
                q = db.get_question(status[0], status[1], lang)
                send_message(emoji.emojize(q), chat)
                continue


            # check for more questions in the same phase
            if nq_category[status[0]] > status[1]:
                # advance status
                db.next_question(chat)
                # pick up next question
                q = db.get_question(status[0], status[1]+1, lang)
                # comprueba si tiene que lanzar algun mensaje antes de la pregunta
                extra_messages(status[0], status[1]+1, chat, lang)
                send_message(emoji.emojize(q), chat)
            else:
                # si lo es, actualiza estatus y "vuelve" al menu principal
                db.completed_survey(chat, status[0])
                db.change_phase(newphase = 0, id_user=chat)

                # NEW V2, depending on the questionnarie displat a diferent message
                if status[0] == 1:
                    send_message(emoji.emojize(languages[lang]['end_personal']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 2:
                    send_message(emoji.emojize(languages[lang]['end_food']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 3:
                    send_message(emoji.emojize(languages[lang]['end_activity']), chat, main_menu_keyboard(chat, lang))
                # send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def main():
    global languages
    languages = load_languages()
    # variable para controlar el numero de mensajes
    last_update_id = None
    # bucle infinito
    while True:
        # obten los mensajes no vistos
        updates = get_updates(last_update_id)
        # si hay algun mensaje do work
        try:
            if 'result' in updates and len(updates['result']) > 0: # REVIEW provisional patch for result error
                last_update_id = get_last_update_id(updates) + 1
                handle_updates(updates)
                # hay que dejar descansar los servidores de telegram
                time.sleep(0.2)
            else:
                # if no messages lets be gentle with telegram servers
                time.sleep(1)

            except Exception as e:
                print('Error ocurred, watch log!')
                log_entry(str(updates))


if __name__ == '__main__':
    main()
