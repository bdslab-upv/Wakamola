import json
import requests
import time
import datetime
from dbhelper import DBHelper
import urllib
from os import listdir
import emoji
from models import obesity_risk
import csv

# info to load at start
# token is not in the source code for security
TOKEN = open('token_esbirro1.txt', 'r').read().split('\n')[0].strip()
# URL to interact with the API
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
# username of the BOT that is running
BOT_USERNAME = 'eldemoni_esbirro1_bot'
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
# role calls -> avoid hardcodding them in different places
roles = ['$family', '$friend', '$coworker', '$other']

# TODO default language
def_lang_ = 'en'


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
        log.write('\n' + dateerror + '\n')
        log.write(str(entry) + '\n\n')


#################
#
#   BASIC TOOLS
#
################

def build_keyboard(items):
    # contruir un teclado para una vez
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
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


def send_photo(localpath, chat_id, caption=None, reply_markup=None):
    # give the name of a file in 'img' folder
    # send that image to the user
    url = URL + "sendPhoto"
    files = {'photo': open(localpath, 'rb')}
    data = {'chat_id': chat_id}
    if caption:
        data['caption'] = caption
    requests.post(url, files=files, data=data)


def send_sticker(sticker_id, chat_id):
    # send an sticker
    url = URL + "sendSticker"
    # atributtes
    data = {'chat_id': chat_id, 'sticker': sticker_id}
    # it returns the same file if success, can be stored in a variable
    requests.post(url, data=data)


def forward(chat_from, msg_id, chat_id):
    # forward a messege
    url = URL + "forwardMessage"
    # atributtes
    data = {'chat_id': chat_id, 'from_chat_id': chat_from, 'message_id': msg_id}
    requests.post(url, data=data)


def send_GIF(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendVideo"
    # atributtes
    files = {'video': open('img/' + localpath, 'rb')}
    data = {'chat_id': chat_id}
    requests.post(url, files=files, data=data)


def send_file(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendDocument"
    # atributtes
    files = {'document': open(localpath, 'rb')}
    data = {'chat_id': chat_id}
    print(requests.post(url, files=files, data=data))


###############################
#
#   BOT SPECIFIC METHODS
#
###############################


def checkanswer(str, status):
    '''
    Accepts numbers and yes/no questions
    '''
    try:
        if status[0] == 1 and status[1] > 5:
            if str.lower() in afirmations:
                return 1, True
            elif str.lower() in negations:
                return 0, True
            else:
                return None, False
        else:
            aux_ = float(str)
            # weight
            if status[0] == 1 and status[1] == 1:
                if aux_ < 35 or aux_ > 300:
                    return None, False
                else:
                    return aux_, True

            # height
            if status[0] == 1 and status[1] == 2:
                if aux_ < 130 or aux_ > 230:
                    return None, False
                else:
                    return aux_, True

            # age
            if status[0] == 1 and status[1] == 2:
                if aux_ < 5 or aux_ > 115:
                    return None, False
                else:
                    return aux_, True

            # other case REVIEW WARNING
            if aux_ < 0 or aux_ > 25:
                return None, False
            else:
                return aux_, True

    except ValueError:
        return None, False


##############################
#
#   MAIN FUNCTIONS
#
#############################


def process_lang(language):
    # TODO include other language support
    aux = language.split('-')[0]
    if aux == 'en':
        return 'en'
    else:
        return 'es'


def load_languages():
    langs_ = {}
    for f in listdir('strings'):
        dict_ = {}
        try:
            with open('strings/' + f, 'r', encoding='utf-8') as csvfile:
                # may happen this is not a csv file
                if not f.endswith('.csv'):
                    continue
                csv_ = csv.reader(csvfile, delimiter=',')
                for row in csv_:
                    dict_[row[0]] = row[1]
            langs_[f.split('.')[0]] = dict_
        except Exception as e:
            log_entry(e)
            continue  # sanity check

    return langs_


def get_chat(update):
    if 'edited_message' in update and'text' in update['edited_message']:
        return update['edited_message']['chat']['id']

    elif 'callback_query' in update:
        return update['callback_query']['from']['id']

    else:
        return update["message"]["chat"]["id"]


def filter_update(update):
    if 'edited_message' in update:
        if 'text' in update['edited_message']:
            process_edit(update)
            return False, update['edited_message']['message_id']
        else:
            # returning none if it's an update without text -> i.e and image
            return None,  None

    elif 'callback_query' in update:
        # data is the text sent by the callback as a msg
        return update['callback_query']['data'], update['callback_query']['message']['message_id']

    elif 'message' in update:
        if 'text' in update['message']:
            return update["message"]["text"].strip(), update['message']['message_id']

        else:
            # return none if it's a message withpout text
            return None, update['message']['message_id']

    else:  # inline query for example
        return False, None


def process_edit(update):
    text = update["edited_message"]["text"]
    message_id = update['edited_message']['message_id']
    # get the status of that message_id
    status = db.get_status_by_id_message(message_id)
    try:
        if checkanswer(text, status):
            db.update_response_edited(message_id, text)
    except Exception as e:
        log_entry('Captured error at editing message.')


def go_main(chat, lang):
    '''
    Macro for setting up one user to the main phase
    '''
    db.change_phase(newphase=0, id_user=chat)
    send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def social_rol_keyboard(chat, lang='en'):
    '''
    This is a keyboard created for selecting the type of person to share
    '''
    options = [el for el in languages[lang]['social_roles'].split('\n') if el]
    keyboard = {'inline_keyboard': [[{'text': emoji.emojize(options[0]), 'callback_data': roles[0]},
                                     {'text': emoji.emojize(options[1]), 'callback_data': roles[1]}],
                                    [{'text': emoji.emojize(options[2]), 'callback_data': roles[2]},
                                     {'text': emoji.emojize(options[3]), 'callback_data': roles[3]}],
                                    [{'text': emoji.emojize(options[4]), 'callback_data': '_back_main'}]]}
    return json.dumps(keyboard)


def main_menu_keyboard(chat, lang='en'):
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
    keyboard = {'inline_keyboard': [[{'text': emoji.emojize(personal), 'callback_data': 'personal'},
                                     {'text': emoji.emojize(food), 'callback_data': 'food'}],
                                    [{'text': emoji.emojize(activity), 'callback_data': 'activity'},
                                     {'text': emoji.emojize(options[3]), 'callback_data': 'risk'}],
                                    [{'text': emoji.emojize(options[5]), 'callback_data': 'share'},
                                     {'text': emoji.emojize(options[6]), 'callback_data': 'credits'}]]}
    return json.dumps(keyboard)


def questionarie(num, chat, lang, msg=None):
    '''
    Method to start a questionnatie flow
    TODO This can be parametrized and be way more general
    '''
    db.change_phase(newphase=num, id_user=chat)
    if num == 1:
        send_photo('img/' + lang + '/personal.jpg', chat)
    elif num == 2:
        send_photo('img/' + lang + '/food.jpg', chat)
    elif num == 3:
        send_photo('img/' + lang + '/activity.jpg', chat)

    if msg:
        send_message(msg, chat)
    # throw first question
    q1 = db.get_question(phase=num, question=1, lang=lang)
    # error on the database
    if q1 is None:
        return
    extra_messages(num, 1, chat, lang)
    send_message(emoji.emojize(q1), chat)


def create_shared_link(chat: str, social_role: str) -> str:
    return 'https://telegram.me/{}?start={}AAA{}'.format(BOT_USERNAME, chat, social_role)


def extra_messages(phase, question, chat, lang):
    '''
    This method includes all the extra messages that break the
    usual question - response - question... flow
    TODO parametrize this in order to be less horrendous
    '''
    # food
    if phase == 2 and question == 10:  # weekly questionnarie
        send_message(languages[lang]['food_weekly'], chat)


def wakaestado(chat, lang):
    '''
    Piece of the standard flow to calculate and send the wakaestado
    '''
    global languages
    completed = db.check_completed(chat)
    print(completed)
    # put phase to 0
    db.change_phase(newphase=0, id_user=chat)

    # check if completed all questionaries
    risk = obesity_risk(chat, completed)

    # add the avocado emojis
    avo_emojis_ = " :avocado: :avocado: :avocado:"
    for its in range(int(risk / 20)):
        avo_emojis_ += " :avocado:"

    # Wakaestado completo
    if completed[0] and completed[1] and completed[2]:
        # obtain the obsity risk: 0, 1 or 2
        send_message(emoji.emojize(languages[lang]['wakaestado'] + ' ' + str(risk) + avo_emojis_), chat)
    # WakaEstado parcial
    else:
        # give a general advice
        send_message(emoji.emojize(languages[lang]['wakaestado_parcial'] + ' ' + str(risk) + avo_emojis_), chat)
    # imagen wakaestado
    send_photo('img/' + lang + '/wakaestado.jpg', chat)
    # instrucciones social
    if completed[0] and completed[1] and completed[2]:
        send_message(languages[lang]['social'], chat)


def handle_updates(updates):
    global languages
    for update in updates["result"]:

        chat = get_chat(update)
        text, message_id = filter_update(update)

        # no valid text
        if text is False:
            continue
        elif text is None:
            lang = process_lang(update['message']['from']['language_code'])
            send_message(languages[lang]['not_supported'], chat)
            continue

        # get user language
        lang = def_lang_
        if 'message' in update:
            if 'language_code' in update['message']['from']:
                lang = process_lang(update['message']['from']['language_code'])
            else:
                lang = def_lang_
        # callback version of the language
        elif 'callback_query' in update:
            if 'language_code' in update['callback_query']['from']:
                lang = process_lang(update['callback_query']['from']['language_code'])


        # start command / second condition it's for the shared link
        if text.lower() == 'start' or '/start' in text.lower():
            # wellcome message
            send_photo('img/' + lang + '/welcome.jpg', chat)
            send_message(emoji.emojize(languages[lang]['welcome']), chat, main_menu_keyboard(chat, lang))

            # insert user into the db, check collisions
            if not db.check_start(chat):
                # sanity check
                try:
                    db.register_user(id_user=chat, language=lang)
                except Exception as e:
                    print(e)
                    # log_entry("Error registering the user")
            else:
                db.change_phase(newphase=0, id_user=chat)

            # check for the token
            aux = text.split(' ')
            # TOKEN CHECK -> AFTER REGISTRATION
            if len(aux) == 2:
                # it comes with the token. The separator is AAA
                info_ = aux[1].split('AAA')
                friend_token = info_[0]
                role = info_[1]
                try:
                    # all ids are ints
                    int(friend_token)
                    db.add_relationship(chat, friend_token, role)
                except Exception as e:
                    print('Error ocurred on relationship add')
                    log_entry(e)

        # Check if the user have done the start command
        elif db.check_user(chat):
            # if not, just register him and made him select
            db.register_user(id_user=chat, language=lang)
            db.change_phase(newphase=0, id_user=chat)
            send_message(languages[lang]['select'], chat)

        elif text.startswith('$'):
            # the different social roles option
            if text in roles:
                role_ = text[1:]
                send_photo('img/' + lang + '/' + role_ + '.jpg', chat,
                           caption= languages[lang]['share_caption']+': '+create_shared_link(chat, role_))
                send_message(languages[lang]['share_more'], chat, social_rol_keyboard(chat, lang))
                continue

            # if its not a correct callback
            else:
                continue

        # Credits
        elif text.lower() == 'credits':
            # junst sed a message with the credits and return to the main menu
            send_message(languages[lang]['credits'], chat)
            # send_file('theme definitivo.tdesktop-theme', chat)
            go_main(chat, lang)

        elif text.lower() == 'share':
            # Send a message with the role keyboard
            send_message(languages[lang]['share'], chat, social_rol_keyboard(chat, lang))
            continue

        # return from the share phase
        elif text == '_back_main':
            go_main(chat, lang)
            continue
        elif text.lower() == 'personal':
            # set to phase and question 1
            questionarie(1, chat, lang)
            continue

        elif text.lower() == 'food':
            # set to phase and question 2
            questionarie(2, chat, lang, msg=languages[lang]['food_intro'])
            continue

        elif text.lower() == 'activity':
            # set to phase and question 3
            questionarie(3, chat, lang)
            continue

        elif text.lower() == 'risk':
            # already contain
            wakaestado(chat, lang)
            go_main(chat=chat, lang=lang)
            continue

        else:
            # rescata a que responde
            status = db.get_phase_question(chat)
            if status[0] == 0:
                send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))
                continue

            text, correct_ = checkanswer(text, status)
            if correct_:
                # store the user response
                db.add_answer(id_user=chat, phase=status[0], question=status[1], message_id=message_id, answer=text)

            else:
                send_message(languages[lang]['numeric_response'], chat)
                # repeat last question
                q = db.get_question(status[0], status[1], lang)
                # error on the database
                if q is None:
                    continue
                send_message(emoji.emojize(q), chat)
                continue

            # check for more questions in the same phase
            if nq_category[status[0]] > status[1]:
                # advance status
                db.next_question(chat)
                # pick up next question
                q = db.get_question(status[0], status[1] + 1, lang)
                # error on the database
                if q is None:
                    continue
                # comprueba si tiene que lanzar algun mensaje antes de la pregunta
                extra_messages(status[0], status[1] + 1, chat, lang)
                send_message(emoji.emojize(q), chat)
            else:
                # si lo es, actualiza estatus y "vuelve" al menu principal
                db.completed_survey(chat, status[0])
                db.change_phase(newphase=0, id_user=chat)

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
            if 'result' in updates and len(updates['result']) > 0:  # REVIEW provisional patch for result error
                last_update_id = get_last_update_id(updates) + 1
                handle_updates(updates)
                # have to be gentle with the telegram server
                time.sleep(0.5)
            else:
                # if no messages lets be *more* gentle with telegram servers
                time.sleep(1)

        except Exception as e:
            print('Error ocurred, watch log!')
            log_entry(str(e))
            print(e)
            # sleep 20 seconds so the problem may solve
            time.sleep(20)



if __name__ == '__main__':
    main()
