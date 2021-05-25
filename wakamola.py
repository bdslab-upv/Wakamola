import json
import requests
import time
from urllib.parse import quote_plus
from os import listdir, environ
import emoji

import csv
from pandas import read_csv
from threading import Thread
from math import ceil
import datetime
import logging
# implementation of pipeline w/ graph visualization
import subprocess
from utils import md5, send_mail, create_database_connection
from g0d_m0d3 import h4ck
from models import obesity_risk
from graph_utils import update_graph_files, filtered_desglose
from generador import create_html

from singleton import NetworkCache

# these definitions are not mandatory but
# I think the code is more understable with them
global URL
global languages
global images
global def_lang_
global negations
global affirmations
global roles
global db
global nq_category
global rules
global god_mode
global statistics_word
global init_date
global network_filename
global network_link
global password_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if environ.get('MODE', 'test') == 'test':
    logger.setLevel(level=logging.INFO)
else:
    logger.setLevel(level=logging.WARNING)


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


# funcion auxiliar de nivel mas bajo para recibir mensajes
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
    try:
        # peticion para obtener las novedades
        url = URL + "getUpdates"
        # offset es el numero del ultimo mensaje recibido
        # el objetivo es no volver a pedirlo to-do
        if offset:
            url += "?offset={}".format(offset)
        # llamada a la funcion auxiliar
        js = get_json_from_url(url)
        return js
    except Exception as e:
        mail_args = {
            'sender': environ['MAIL'],
            'receivers': [environ['MAIL']],
            'subject': 'Wakamola error log',
            'body': environ['BOT_USERNAME_WAKAMOLA'] + " ha sufrido un error\n\n" + str(e),
            'smtp_server': environ['SMTPSERVER'],
            'smtp_port': environ['SMTPPORT'],
            'password': environ['PASSMAIL']
        }
        send_mail(**mail_args)
        return None


def get_last_update_id(updates):
    # el orden de llegada de los mensajes al bot produce un id creciente
    # devolvemos el maximo para saber por donde nos hemos quedado
    return max([int(el['update_id']) for el in updates['result']])


#################
#
#   TELEGRAM API MACROS
#
#################

def get_me():
    # Check API method
    getme = URL + "getMe"
    logger.info(get_url(getme))


def send_message(text, chat_id, reply_markup=None):
    text = quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    # reply_markup is for a special keyboard
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    return get_url(url)


def send_image(img, chat_id, caption=None):
    # give the name of a file in 'img' folder
    # send that image to the user
    url = URL + "sendPhoto"
    files = {'photo': img}
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


def send_file(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendDocument"
    # atributtes
    files = {'document': open(localpath, 'rb')}
    data = {'chat_id': chat_id}
    logger.info(requests.post(url, files=files, data=data))


###############################
#
#   BOT SPECIFIC METHODS
#
###############################
def load_rules():
    """
    Loads the especific range rules for each question
    returns dict
    """
    rules_ = {}
    df_ = read_csv('ranges.csv', sep=',')
    for _, row in df_.iterrows():
        question = (row['phase'], row['question'])
        aux_ = {'type': row['type'], 'low': row['low'], 'high': row['high']}
        rules_[question] = aux_
    return rules_


def check_answer(string_, status):
    """
    Determine if an answer is valid
    """
    # maximum string length accepted
    if len(string_) > 20:
        return None, False

    try:
        ranges = rules[status]
        # numeric values
        if ranges['type'] == 'int' or ranges['type'] == 'float':
            val = float(string_.replace(',', '.'))
            assert ranges['low'] <= val <= ranges['high']
            return val, True

        # yes/no questions
        elif ranges['type'] == 'affirmation':
            if string_.lower() in affirmations:
                return 1, True
            elif string_.lower() in negations:
                return 0, True
            else:
                return None, False

        # no text restrictions
        elif ranges['type'] == 'text':
            return string_, True

    except:
        return None, False


##############################
#
#   MAIN FUNCTIONS
#
#############################


def get_language(chat):
    lang_ = db.get_language(md5(chat))
    if lang_ is None:
        return def_lang_
    else:
        return lang_


def set_language(chat, new_lang):
    if new_lang in languages.keys():
        db.set_language(md5(chat), new_lang)
        return new_lang
    else:
        return def_lang_


def load_images():
    # since there is only few pictures
    # load the in advance
    images_ = {}
    for lang in listdir('img'):
        dict_ = {}
        if lang.startswith('.'):
            continue
        for f in listdir('img/' + lang):
            with open('img/' + lang + '/' + f, 'rb') as img:
                dict_[f] = img.read()
        images_[lang] = dict_
    return images_


def load_languages():
    langs_ = {}
    for f in listdir('strings'):
        dict_ = {}
        try:
            with open('strings/' + f, 'r', encoding='utf-8') as csvfile:
                # may happen this is not a csv file
                if not f.endswith('.csv'):
                    continue
                csv_ = csv.reader(csvfile, delimiter=';')
                for row in csv_:
                    dict_[row[0]] = row[1]
            langs_[f.split('.')[0]] = dict_
        except Exception as e:
            logger.error(e)
            continue  # sanity check
    return langs_


def get_chat(update):
    if 'edited_message' in update and 'text' in update['edited_message']:
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
            return None, None

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
        text, flag = check_answer(text, status)
        if flag:
            db.update_response_edited(message_id, text)
    except:
        logger.error('Captured error at editing message.')


def go_main(chat, lang):
    """
    Macro for setting up one user to the main phase
    """
    db.change_phase(newphase=0, id_user=md5(chat))
    send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def dynamic_keyboard(string, lang='en'):
    """
    This is a keyboard created for selecting the type of person to share
    """
    options = [el for el in languages[lang][string].split('\n') if el]
    key_ = []
    aux_ = []
    for i in range(len(options)):
        callback_ = options[i]
        if ':' in callback_:
            # TODO IMPROVE THIS -> maybe regex
            # Just remove from the first : to the end
            callback_ = callback_[:callback_.index(':')]
        aux_.append({'text': emoji.emojize(options[i]), 'callback_data': options.index(callback_)})
        if i % 2 == 1:
            key_.append(aux_)
            aux_ = []
    keyboard = {'inline_keyboard': key_}
    return json.dumps(keyboard)


def main_menu_keyboard(chat, lang='en'):
    options = [el for el in languages[lang]['options'].split('\n') if el]
    personal = options[0]
    food = options[1]
    activity = options[2]
    completed = db.check_completed(md5(chat))

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
                                    [{'text': emoji.emojize(options[5]), 'callback_data': 'network'},
                                     {'text': emoji.emojize(options[6]), 'callback_data': 'credits'}],
                                    [{'text': emoji.emojize(options[7]), 'callback_data': 'share'}]
                                    ]}
    return json.dumps(keyboard)


def questionnaire(num, chat, lang, msg=None):
    """
    Method to start a questionnatie flow
    TODO This can be parametrized and be way more general
    """
    db.change_phase(newphase=num, id_user=md5(chat))
    if num == 1:
        send_image(images[lang]['personal.jpg'], chat)
    elif num == 2:
        send_image(images[lang]['food.jpg'], chat)
    elif num == 3:
        send_image(images[lang]['activity.jpg'], chat)

    if msg:
        send_message(msg, chat)
    # edit instruction
    send_message(languages[lang]['edit'], chat)
    # throw first question
    q1 = db.get_question(phase=num, question=1, lang=lang)
    # error on the database
    if q1 is None:
        return
    # check for "extra" (out of the normal q-a flow) messages
    extra_messages(num, 1, chat, lang)
    send_message(emoji.emojize(q1), chat)


def create_shared_link(chat, social_role):
    token = db.create_short_link(id_user=md5(chat), type=social_role)
    return 't.me/{}?start={}'.format(BOT_USERNAME, token)


# TODO VERY IMPORTANT TO BREAK FLOW
def extra_messages(phase, question, chat, lang):
    """
    This method includes all the extra messages that break the
    usual question - response - question... flow
    TODO parametrize this in order to be less horrendous
    """
    # food
    if phase == 2 and question == 10:  # weekly questionnarie
        send_message(languages[lang]['food_weekly'], chat)


def avocados(score):
    """
    This function returns a String
    containing N avocado emojis
    """
    avo_emojis_ = " :avocado: :avocado: :avocado:"
    for _ in range(int(score / 20)):
        avo_emojis_ += " :avocado:"
    return avo_emojis_


def weight_category(bmi, lang):
    categories = languages[lang]['pesos'].split('\n')
    if bmi < 18.5:
        weight_cat = categories[0]
    elif bmi < 25:
        weight_cat = categories[1]
    elif bmi < 30:
        weight_cat = categories[2]
    elif bmi < 35:
        weight_cat = categories[3]
    else:
        weight_cat = categories[4]
    return weight_cat


def n_avocados(value, minimum=0, maximum=10):
    base = ':avocado:'
    res = ''
    # change base from 0 to max, then set a minimum value
    # 100 is the max value in all the metrics
    n = max(ceil(value * maximum / 100), minimum)
    for _ in range(n):
        res += base
    return res


def wakaestado(chat, lang):
    """
    Piece of the standard flow to calculate and send the wakaestado
    """

    completed = db.check_completed(md5(chat))
    # put phase to 0
    db.change_phase(newphase=0, id_user=md5(chat))

    # final risk and "explanation"
    risk, partial_scores = obesity_risk(md5(chat), completed)
    risk = round(risk)

    # imagen wakaestado
    send_image(images[lang]['wakaestado.jpg'], chat)

    # wakaestado detailed
    if completed[0] and completed[1] and completed[2]:
        # nutrition, activity, bmi, risk, network
        # normal weight, overweight...
        weight_cat = weight_category(round(partial_scores['bmi']), lang)

        difference = partial_scores['mean_contacts'] - partial_scores['wakascore']
        # load "debajo/arriba" string
        index = 0 if difference > 0 else 1
        position = languages[lang]['posicion_media'].split('\n')[index]
        details = languages[lang]['wakaestado_detail']
        details = details.format(str(risk) + n_avocados(risk),
                                 str(abs(round(difference))),
                                 position,
                                 str(partial_scores['n_contacts']),
                                 str(round(partial_scores['nutrition'])) + n_avocados(partial_scores['nutrition']),
                                 str(round(partial_scores['activity'])) + n_avocados(partial_scores['activity']),
                                 str(round(partial_scores['bmi_score'])) + n_avocados(partial_scores['bmi_score']),
                                 str(round(partial_scores['bmi'])),
                                 weight_cat,
                                 str(round(partial_scores['network'])) + n_avocados(partial_scores['network']))

        send_message(emoji.emojize(details), chat)

    # WakaEstado partial
    else:
        # give a general advice
        send_message(emoji.emojize(languages[lang]['wakaestado_parcial'].format(str(risk) + avocados(risk))), chat)


def create_graph():
    """
    This method updates the graph
    and moves it to the apache folder
    """
    # update the files
    # first return is the graph, second the ids
    _, ids_ = update_graph_files()
    # create the html
    create_html()
    # move the file to /var/www
    subprocess.call(["mv {}_es.html /var/www/html/index.html".format(network_filename)], shell=True)
    logger.info("moved to apache!")
    return ids_


def network_message(chat, lang):
    """
    This method is invoked when the user
    visualize the networks
    """
    # first we regenerate the network and get the graph ids
    ids_ = create_graph()
    # transform the id
    graph_id = ids_[md5(chat)][0]
    # send messages and stuff
    send_image(images[lang]['wakanetwork.jpg'], chat)
    contacts_counter = len(db.get_user_relationships(md5(chat)))
    msg_share = languages[lang]['share'].format(contacts_counter)
    send_message(emoji.emojize(msg_share), chat)
    send_message(emoji.emojize(languages[lang]['see_network']), chat)
    send_message(network_link + '?id=' + str(graph_id), chat)


def handle_updates(updates):
    # updates is a list
    for update in updates:
        chat = get_chat(update)
        text, message_id = filter_update(update)
        # get user language
        lang = get_language(chat)

        logger.info(str(chat) + " - " + str(text))

        # no valid text
        if text is False:
            return

        elif text is None:
            send_message(languages[lang]['not_supported'], chat)
            return

        # start command / second condition it's for the shared link
        if text.lower() == 'start' or '/start' in text.lower():
            # welcome message
            send_image(images[lang]['welcome.jpg'], chat)
            send_message(emoji.emojize(languages[lang]['welcome']), chat, main_menu_keyboard(chat, lang))
            # insert user into the db, check collisions
            if not db.check_start(md5(chat)):
                db.register_user(id_user=md5(chat), language=lang)
            else:
                db.change_phase(newphase=0, id_user=md5(chat))

            # check for the token
            if ' ' in text:
                aux = text.split(' ')
                # TOKEN CHECK -> AFTER REGISTRATION
                if len(aux) == 2:
                    # token base64 is in the second position
                    friend_token, role = db.get_short_link(aux[1])
                    try:
                        # friend token already in md5 -> after next code block
                        db.add_relationship(md5(chat), friend_token, role)
                    except Exception as e:
                        logger.error("Error occurred on relationship add" + str(e))

        # Check if the user have done the start command
        elif db.check_user(md5(chat)):
            # if not, just register him and made him select
            db.register_user(id_user=md5(chat), language=lang)
            db.change_phase(newphase=0, id_user=md5(chat))
            send_message(languages[lang]['select'], chat)

        elif text.lower() == 'credits':
            # just sed a message with the credits and return to the main menu
            send_message(languages[lang]['credits'], chat)
            go_main(chat, lang)

        elif text.lower() == 'network':
            network_message(chat, lang)
            go_main(chat, lang)
            return

        elif text.lower() == 'share':
            # generate link w/ one fixed relationship
            link_ = create_shared_link(chat, 'relation').replace('_', '\\_')
            # send link with cosmetics for telegram
            send_image(images[lang]['share.jpg'], chat)
            send_message(text=emoji.emojize(languages[lang]['share_unique']), chat_id=chat)
            send_message(text=link_, chat_id=chat)
            go_main(chat, lang)
            return

        elif text.lower() == network_pass:
            create_graph()
            go_main(chat, lang)
            return

        elif 'change_lang:' in text.lower():
            lang = set_language(chat, text.lower().split(':')[1])
            go_main(chat, lang)
            return

        elif text.lower() == 'personal':
            # set to phase and question 1
            questionnaire(1, chat, lang)
            return

        elif text.lower() == 'food':
            # set to phase and question 2
            questionnaire(2, chat, lang, msg=languages[lang]['food_intro'])
            return

        elif text.lower() == 'activity':
            # set to phase and question 3
            questionnaire(3, chat, lang)
            return

        elif text.lower() == 'risk':
            wakaestado(chat=chat, lang=lang)
            go_main(chat=chat, lang=lang)
            return

        elif text.lower() == god_mode:
            h4ck(md5(chat))
            go_main(chat=chat, lang=lang)
            return

        # hardcoded statistics
        elif text.lower() == statistics_word:

            db_statistics = db.statistics()
            date_now = datetime.datetime.now()
            time_diff = date_now - init_date
            days_ = time_diff.days
            seconds_ = time_diff.seconds
            minutes_ = seconds_ // 60
            seconds_ = seconds_ % 60
            hours_ = minutes_ // 60
            minutes_ = minutes_ % 60
            txt_ = "Completado todo: {}\nIniciado el bot: {}\nNumero de relaciones: {}\nUptime: {}".format(
                str(db_statistics[0]),
                str(db_statistics[1]),
                str(db_statistics[2]),
                "Days: {} Hours: {} Minutes: {} Seconds: {}".format(days_, hours_, minutes_, seconds_)
            )
            send_message(txt_, chat)
            go_main(chat=chat, lang=lang)
            return

        # just before default option, check if the its the password to protect the data
        # <PASSWORD_DATA> yyyymmdd date
        elif text.startswith(password_data):
            try:
                date_filt = text.split()[1]
                # generate the new filtered data
                path_desglose = filtered_desglose(date_filt=date_filt)
                # send it to the user
                send_file(chat_id=chat, localpath=path_desglose)
                go_main(chat=chat, lang=lang)
            finally:
                return

        else:
            # rescata a que responde
            status = db.get_phase_question(md5(chat))
            if status[0] == 0:
                send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))
                return

            text, correct_ = check_answer(text, status)
            if correct_:
                # store the user response
                network_cache = NetworkCache()
                db.add_answer(id_user=md5(chat), phase=status[0], question=status[1], message_id=message_id,
                              answer=text)
                network_cache.remove_from_cache(md5(chat))

            else:
                send_message(languages[lang]['numeric_response'], chat)
                # repeat last question
                q = db.get_question(status[0], status[1], lang)
                # error on the database
                if q is None:
                    return
                send_message(emoji.emojize(q), chat)
                return

            # check for more questions in the same phase
            if nq_category[status[0]] > status[1]:
                # advance status
                db.next_question(md5(chat))
                # special cases
                skip_one_ = False
                # if the users answers 0 in certain question
                # we have to omit the following questions
                if (status[0] == 3 and status[1] == 1) or (status[0] == 3 and status[1] == 3) or \
                        (status[0] == 3 and status[1] == 5):
                    if int(text) < 1:
                        skip_one_ = True

                if skip_one_:
                    # save 0 in the next question
                    db.add_answer(id_user=md5(chat), phase=status[0], question=status[1] + 1,
                                  message_id=message_id * -1,
                                  answer=0)
                    # forward the status again
                    db.next_question(md5(chat))
                    # get the corresponding question
                    q = db.get_question(status[0], status[1] + 2, lang)
                else:
                    # pick up next question
                    q = db.get_question(status[0], status[1] + 1, lang)
                    # error on the database
                if q is None:
                    return
                # comprueba si tiene que lanzar algun mensaje antes de la pregunta
                extra_messages(status[0], status[1] + 1, chat, lang)

                if status[0] == 1 and status[1] == 8:  # genero

                    logger.info(send_message(emoji.emojize(q), chat, dynamic_keyboard('generos', lang)))

                elif status[0] == 1 and status[1] == 10:  # nivel estudios
                    logger.info(send_message(emoji.emojize(q), chat, dynamic_keyboard('estudios', lang)))

                elif status[0] == 1 and status[1] == 11:  # estado civil
                    logger.info(send_message(emoji.emojize(q), chat, dynamic_keyboard('estado_civil', lang)))

                else:
                    send_message(emoji.emojize(q), chat)
            else:
                # si lo es, actualiza estatus y "vuelve" al menu principal
                db.completed_survey(md5(chat), status[0])
                db.change_phase(newphase=0, id_user=md5(chat))

                # NEW V2, depending on the questionnarie displat a diferent message
                if status[0] == 1:
                    send_message(emoji.emojize(languages[lang]['end_personal']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 2:
                    send_message(emoji.emojize(languages[lang]['end_food']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 3:
                    send_message(emoji.emojize(languages[lang]['end_activity']), chat, main_menu_keyboard(chat, lang))


def main():
    # variable para controlar el numero de mensajes
    last_update_id = None
    get_me()
    # force bd to stay clean
    db.conn.commit()
    # main loop
    while True:
        # obten los mensajes no vistos
        updates = get_updates(last_update_id)
        # si hay algun mensaje do work
        try:
            if 'result' in updates and len(updates['result']) > 0:
                last_update_id = get_last_update_id(updates) + 1

                # Updates joint by user
                joint_updates = dict()
                for update in updates['result']:

                    id_ = get_chat(update)
                    if id_ in joint_updates:
                        joint_updates[id_].append(update)
                    else:
                        joint_updates[id_] = [update]

                for update in joint_updates.values():
                    t = Thread(target=handle_updates, args=(update,))
                    t.start()

                # have to be gentle with the telegram server
                time.sleep(float(environ.get('CONSULTING_TIME', 0.4)))
            else:
                # if no messages lets be *more* gentle with telegram servers
                time.sleep(float(environ.get('NO_MESSAGE_TIME', 0.8)))

        except Exception as e:
            logger.error(e)
            logger.error('Bot to sleep!')
            time.sleep(float(environ.get('ERROR_TIME', 2)))


if __name__ == '__main__':
    # TODO QUESTIONS ON CACHE FOR NEXT VERSION
    init_date = datetime.datetime.now()

    db = create_database_connection()
    db.setup()
    # caching the number of questions
    nq_category = db.n_questions()

    # very important, this password is used to serve the data as file
    password_data = environ.get('PASSWORD_DATA')

    # default language
    def_lang_ = environ.get('DEFAULT_LANG', 'es')
    
    # link to the network
    network_link = environ.get('NETWORK_LINK').replace('_', '\\_')
    network_filename = environ.get('NETWORK_FILENAME', 'netweb').lower()
    # god mode
    god_mode = environ.get('GOD_MODE').lower()
    # hidden statistics message
    statistics_word = environ.get('STATISTICS').lower()
    # network
    network_pass = environ.get('NETWORK_PASSWORD').lower()

    # languages
    languages = load_languages()
    # images
    images = load_images()
    # rules
    rules = load_rules()

    # yes / no answers
    negations = [el for el in open('strings/negations.txt', 'r').read().split('\n') if el]
    affirmations = [el for el in open('strings/affirmations.txt', 'r').read().split('\n') if el]
    # role calls -> avoid hardcodding them in different places
    roles = ['home', 'family', 'friend', 'coworker']

    TOKEN = environ.get('TOKEN_WAKAMOLA')
    BOT_USERNAME = environ.get('BOT_USERNAME_WAKAMOLA')
    # URL to interact with the API
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)

    # Create the network before starting the main loop
    # TODO optimize this crap
    # create_graph()

    main()
