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
from utils import md5
from g0d_m0d3 import h4ck
import argparse
from pandas import read_csv

# global variables to use
# througth different functions
global URL
global debug
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
    # el objetivo es no volver a pedirlo to-do
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

def getMe():
    # Check API method
    getme = URL + "getMe"
    print(get_url(getme))


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    # reply_markup is for a special keyboard
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


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
def load_rules():
    '''
    Loads the especific range rules for each question
    returns dict
    '''
    rules = {}
    df_ = read_csv('ranges.csv', sep=',')
    for _, row in df_.iterrows():
        question = (row['phase'], row['question'])
        aux_ = {'type': row['type'], 'low': row['low'], 'high': row['high']}
        rules[question] = aux_
    return rules


def checkanswer(str, status):
    '''
    Determine if an answer is valid
    '''
    # maximum string length accepted
    if len(str) > 20:
        return None, False

    try:
        ranges = rules[status]
        # numeric values
        if ranges['type'] == 'int' or ranges['type'] == 'float':
            val = float(str.replace(',', '.'))
            assert ranges['low'] <= val <= ranges['high']
            return val, True

        # yes/no questions
        elif ranges['type'] == 'affirmation':
            if str.lower() in affirmations:
                return 1, True
            elif str.lower() in negations:
                return 0, True
            else:
                return None, False

        # no text restrictions
        elif ranges['type'] == 'text':
            return str, True

    except:
        return None, False


##############################
#
#   MAIN FUNCTIONS
#
#############################


def process_lang(language):
    '''
    By the moment this method only allows
    one language. TODO -> Implement multilanguage as files become ready
    '''
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
                csv_ = csv.reader(csvfile, delimiter=',')
                for row in csv_:
                    dict_[row[0]] = row[1]
            langs_[f.split('.')[0]] = dict_
        except Exception as e:
            log_entry(e)
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
        text, flag = checkanswer(text, status)
        if flag:
            db.update_response_edited(message_id, text)
    except Exception as e:
        log_entry('Captured error at editing message.')


def go_main(chat, lang):
    '''
    Macro for setting up one user to the main phase
    '''
    db.change_phase(newphase=0, id_user=md5(chat))
    send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def dynamic_keyboard(chat, string, lang='en'):
    '''
    This is a keyboard created for selecting the type of person to share
    '''
    options = [el for el in languages[lang][string].split('\n') if el]
    key_ = []
    aux_ = []
    for i in range(len(options)):
        aux_.append({'text': options[i], 'callback_data': options[i]})
        if i % 2 == 1:
            key_.append(aux_)
            aux_ = []
    print(key_)
    keyboard = {'inline_keyboard': key_}
    '''
    keyboard = {'inline_keyboard': [[{'text': emoji.emojize(options[0]), 'callback_data': roles[0]},
                                     {'text': emoji.emojize(options[1]), 'callback_data': roles[1]}],
                                    [{'text': emoji.emojize(options[2]), 'callback_data': roles[2]},
                                     {'text': emoji.emojize(options[3]), 'callback_data': roles[3]}],
                                    [{'text': emoji.emojize(options[4]), 'callback_data': '_back_main'}]]}
                                    
    '''
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
                                    [{'text': emoji.emojize(options[5]), 'callback_data': 'share'},
                                     {'text': emoji.emojize(options[6]), 'callback_data': 'credits'}]]}
    return json.dumps(keyboard)


def detailed_wakamola_keyboard(chat, lang='en'):
    '''
    A simple button for getting a detailed wakamola explanation
    '''
    global languages
    keyboard = {'inline_keyboard': [[{'text': languages[lang]['get_details'], 'callback_data': 'risk_full'}]]}
    return json.dumps(keyboard)


def questionarie(num, chat, lang, msg=None):
    '''
    Method to start a questionnatie flow
    TODO This can be parametrized and be way more general
    '''
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


def avocados(score):
    '''
    This function returns a String
    containing N avocado emojis
    '''
    avo_emojis_ = " :avocado: :avocado: :avocado:"
    for its in range(int(score / 20)):
        avo_emojis_ += " :avocado:"
    return avo_emojis_


def wakaestado(chat, lang):
    '''
    Piece of the standard flow to calculate and send the wakaestado
    '''
    global languages
    global images
    completed = db.check_completed(md5(chat))
    # put phase to 0
    db.change_phase(newphase=0, id_user=md5(chat))

    # final risk and "explanation"
    risk, _ = obesity_risk(md5(chat), completed)
    risk = round(risk)

    # imagen wakaestado
    send_image(images[lang]['wakaestado.jpg'], chat)

    # Full Wakaestado
    if completed[0] and completed[1] and completed[2]:
        # append the button for the whole description
        send_message(emoji.emojize(languages[lang]['wakaestado'] + ' ' + str(risk) + avocados(risk)), chat,
                     detailed_wakamola_keyboard(chat, lang))
    # WakaEstado partial
    else:
        # give a general advice
        send_message(emoji.emojize(languages[lang]['wakaestado_parcial'] + ' ' + str(risk) + avocados(risk)), chat)


def wakaestado_detailed(chat, lang):
    '''
    This piece of code throws a message explaining the whole score
    WARNING: Only allow this is all the questions are complete
    '''
    global languages
    completed = db.check_completed(md5(chat))
    # check all answers are completed
    # Its sanity check
    if not all(completed):
        go_main(chat, lang)
        return

    _, partial_scores = obesity_risk(md5(chat), completed)
    details = languages[lang]['wakaestado_detail']
    # nutrition, activity, bmi, risk, network
    three_avocados = ' :avocado: :avocado: :avocado:'
    weight_category = None
    aux = partial_scores['bmi']
    categories = languages[lang]['pesos'].split('\n')
    if aux < 18.5:
        weight_category = categories[0]
    elif aux < 25:
        weight_category = categories[1]
    elif aux < 30:
        weight_category = categories[2]
    elif aux < 35:
        weight_category = categories[3]
    else:
        weight_category = categories[4]

    details = details.format(str(round(partial_scores['nutrition'])) + three_avocados,
                             str(round(partial_scores['activity'])) + three_avocados,
                             str(round(partial_scores['bmi'])),
                             weight_category,
                             str(round(partial_scores['bmi_score'])) + three_avocados,
                             str(round(partial_scores['risk'])) + three_avocados,
                             str(round(partial_scores['network'])) + three_avocados)

    send_message(emoji.emojize(details), chat)


def handle_updates(updates):
    for update in updates["result"]:

        chat = get_chat(update)
        text, message_id = filter_update(update)

        if debug:
            print(chat, text)

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
            send_image(images[lang]['welcome.jpg'], chat)
            send_message(emoji.emojize(languages[lang]['welcome']), chat, main_menu_keyboard(chat, lang))

            # insert user into the db, check collisions
            if not db.check_start(md5(chat)):
                # sanity check
                try:
                    db.register_user(id_user=md5(chat), language=lang)
                except Exception as e:
                    log_entry("Error registering the user")
            else:
                db.change_phase(newphase=0, id_user=md5(chat))

            # check for the token
            if ' ' in text:
                aux = text.split(' ')
                # TOKEN CHECK -> AFTER REGISTRATION
                if len(aux) == 2:
                    # it comes with the token. The separator is AAA
                    info_ = aux[1].split('AAA')
                    if debug:
                        print('Info token', info_)
                    friend_token = info_[0]
                    role = info_[1]
                    try:
                        # friend token already in md5 -> after next code block
                        db.add_relationship(md5(chat), friend_token, role)
                    except Exception as e:
                        print('Error ocurred on relationship add')
                        log_entry(e)

        # Check if the user have done the start command
        elif db.check_user(md5(chat)):
            # if not, just register him and made him select
            db.register_user(id_user=md5(chat), language=lang)
            db.change_phase(newphase=0, id_user=md5(chat))
            send_message(languages[lang]['select'], chat)

        elif text.startswith('$'):
            # the different social roles option
            if text in roles:
                role_ = text[1:]
                # send_message(languages[lang]['share3'], chat)
                options = [el for el in languages[lang]['social_roles'].split('\n') if el]

                send_image(images[lang][role_ + '.jpg'], chat,
                           caption=(languages[lang]['share_caption'].format(create_shared_link(md5(chat), role_))))
                send_message(languages[lang]['share_more'], chat, dynamic_keyboard(chat, 'social_roles',lang))
                continue

            # if its not a correct callback
            else:
                continue

        # Credits
        elif text.lower() == 'credits':
            # just sed a message with the credits and return to the main menu
            send_message(languages[lang]['credits'], chat)
            # send_file('theme definitivo.tdesktop-theme', chat)
            go_main(chat, lang)

        elif text.lower() == 'share':
            # Send a message with the role keyboard
            send_message(languages[lang]['share'], chat, dynamic_keyboard(chat, 'social_roles', lang))
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
            wakaestado(chat=chat, lang=lang)
            go_main(chat=chat, lang=lang)
            continue

        elif text.lower() == 'risk_full':
            wakaestado_detailed(chat=chat, lang=lang)
            # Added instruction for refill
            send_message(languages[lang]['after_wakaestado_detail'], chat)
            go_main(chat=chat, lang=lang)
            continue

        elif text.lower() == god_mode:
            h4ck(md5(chat))
            go_main(chat=chat, lang=lang)

        else:
            # rescata a que responde
            status = db.get_phase_question(md5(chat))
            if status[0] == 0:
                send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))
                continue

            text, correct_ = checkanswer(text, status)
            if correct_:
                # store the user response
                db.add_answer(id_user=md5(chat), phase=status[0], question=status[1], message_id=message_id,
                              answer=text)

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
                db.next_question(md5(chat))
                # special cases
                skip_one_ = False
                # if the users answers 0 in certain question
                # we have to omit the folowing questions
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
                    continue
                # comprueba si tiene que lanzar algun mensaje antes de la pregunta
                extra_messages(status[0], status[1] + 1, chat, lang)
                # TODO OPCIONES DE RESPUESTA DINAMICAS

                if status[0] == 1 and status[1]+1 == 8: # genero

                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard(chat, 'generos', lang)))

                elif status[0] == 1 and status[1]+1 == 10: # nivel estudios
                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard(chat, 'estudios', lang)))

                elif status[0] == 1 and status[1]+1 == 11:  # estado civil
                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard(chat, 'estado_civil', lang)))

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
                # send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def main():
    # variable para controlar el numero de mensajes
    last_update_id = None
    getMe()

    # fix try
    db.conn.commit()
    # bucle infinito
    while True:
        # obten los mensajes no vistos
        updates = get_updates(last_update_id)
        # si hay algun mensaje do work

        if 'result' in updates and len(updates['result']) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
            # have to be gentle with the telegram server
            time.sleep(0.5)
        else:
            # if no messages lets be *more* gentle with telegram servers
            time.sleep(1)
        '''
        except Exception as e:
            print('Error ocurred, watch log!')
            log_entry(str(e))
            print(e)
            # sleep 20 seconds so the problem may solve
            time.sleep(20)
        '''


if __name__ == '__main__':
    # TODO QUESTIONS ON CACHE FOR NEXT VERSION
    # argument parser
    parser = argparse.ArgumentParser(description="Telegram BOT")
    parser.add_argument('-d', action="store_true", default=True, help="Debug mode: Print the messages on console")
    parser.add_argument('-t', action="store", help="Token to use", required=True)
    parser.add_argument('-l', action="store", default='es', help="Default languages")
    parser.add_argument('--godmode', action="store", default="wakafill", help="god mode password")
    spacename = parser.parse_args()

    # handler to the database
    db = DBHelper()
    # set up
    db.setup()
    # caching the number of questions
    nq_category = db.n_questions()

    # default language
    def_lang_ = spacename.l
    # debug
    debug = spacename.d
    # god mode
    god_mode = spacename.godmode.lower()
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
    roles = ['$home', '$family', '$friend', '$coworker']

    with open(spacename.t, 'r') as sec_info:
        credentials_text = sec_info.read().split('\n')
        TOKEN = credentials_text[0]
        BOT_USERNAME = credentials_text[1]

    # URL to interact with the API
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)

    main()
