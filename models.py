'''
This class is meant to have the risk models
'''

from dbhelper import DBHelper
from statistics import mean
from math import log, ceil
from pandas import read_csv
import logging
import time

MAX_NETWORK = 10


######################
#
# IMPLEMENTACION TABLAS ALIMENTACION
#
######################
def table_1(group, n):

    # daily consume subtables
    def daily_consume(n):
        # sanity check
        n = round(n)
        if n >= 7:
            return 10
        elif n >= 3:
            return 7.5
        elif 2 <= n < 3:
            return 5
        elif 1 <= n < 2:
            return 2.5
        elif n < 1:
            return 0

    # weekly consume
    def weekly_consume(n):
        # sanity check
        n = round(n)
        if n >= 1 or n <= 2:
            return 10
        elif n >= 7:
            return 2.5
        elif n == 1:
            return 5
        elif n >= 3:
            return 7.5
        elif n < 1:
            return 0

    # ocasional consume
    def casual_consume(n):
        # sanity check
        n = round(n)
        if n < 1:
            return 10
        elif 1 <= n < 2:
            return 7.5
        elif 2 <= n < 3:
            return 5
        elif n >= 7:
            return 0
        elif n >= 3:
            return 2.5

    if group <= 4:
        return daily_consume(n)
    elif group > 4 or group <= 6:
        return weekly_consume(n)
    else:
        return casual_consume(n)


def table_2(n):
    '''
    Scores for oil and fats by Ana Frigola
    '''
    if n <= 3:
        return 10
    elif n == 4:
        return 7.5
    elif n == 5:
        return 5
    elif n == 6:
        return 2.5
    else:
        return 0


def table_3(n):
    '''
    Scores for nuts by Ana Frigola
    '''
    if n <= 7:
        return 10
    elif n == 8:
        return 7.5
    elif n == 9:
        return 5
    elif n == 10:
        return 2.5
    else:
        return 0


def risk_bmi(id_user, db=None):
    '''
    Gives a risk score
    this is a modular function in order be easier to update
    '''
    while db is None:
        try:
            db = DBHelper()
        except:
            time.sleep(20)
            db = None
    bmi = db.getBMI(id_user)
    if bmi == 0:  # sanity check
        return 0, 0

    # TODO REVIEW
    if bmi >= 40:
        return 0, bmi
    elif 35 <= bmi < 40:
        return 25, bmi
    elif 30 <= bmi < 35:
        return 50, bmi
    elif 25 <= bmi < 30:
        return 75, bmi
    elif bmi < 25:
        return 100, bmi


def risk_nutrition(id_user, comp=False, db=DBHelper()):
    '''
    Give a risk using nutrition information
    WARNING: untested rules
    '''
    score = 0
    if not comp:
        return 0
    # obtain the responses
    ans = db.get_responses_category(id_user=id_user, phase=2)
    # load the rules file
    table = read_csv('food_model.csv', sep=',')
    for _, row in table.iterrows():
        # Item Table Group
        table_ = round(row['Table'])
        if table_ == 1:
            score += table_1(group=row['Group'], n=ans[row['Item']])
        elif table_ == 2:
            score += table_2(ans[row['Item']])
        elif table_ == 3:
            score += table_3(ans[row['Item']])

    return score * 10 / table.shape[0]


def risk_activity(id_user, comp=False, db=DBHelper()):
    if not comp:
        return 0

    ans = db.get_responses_category(id_user=id_user, phase=3)
    # compute the METS-min/week
    METS = ans[0] * ans[1] * 8 + ans[2] * ans[3] * 4 + ans[4] * ans[5] * 3.3
    # this have to be reviewed for sure!
    superior_limit = 1800
    return (min(METS, superior_limit) / superior_limit) * 100


def network_influence(id_user, actual_wakaestado, db, comp):
    # Internal function, first search for cache cause its lots faster
    def get_friend_wakaestado(id_friend):
        # try to get the last friends wakaestado
        last_wakaestado_ = db.get_last_wakaestado(id_friend)
        if last_wakaestado_ is None:
            # if no last wakaestado was recorded previously
            aux_, _ = obesity_risk(id_friend, None, False)
            return aux_
        else:
            # sanity check
            if 0 < last_wakaestado_ <= 100:
                return last_wakaestado_
            else:
                return 0

    if not comp:
        return 0, 0, 0
    # get the WakaStatus of each of the "neighbours"
    friends = db.get_user_relationships(id_user)
    if len(friends) == 0:
        return 0, 0, 0
    # now obtain the wakascore for them
    wakaestados = [get_friend_wakaestado(f) for f in friends]
    # return the value, the number of friends and the mean
    return min(max(0, mean(wakaestados) - actual_wakaestado) / MAX_NETWORK + log(len(friends), 2), MAX_NETWORK), \
           len(wakaestados), mean(wakaestados) if len(wakaestados) > 0 else 0


def obesity_risk(id_user, completed, network=True):
    '''
    Update for "explained version"
    :param network:
    :param id_user:
    :param completed:
    :return: score, dict with the subscores
    '''
    # make connection
    db = DBHelper()
    print('Completed', completed)
    if completed is None:
        completed = db.check_completed(id_user)

    # coeficient for each part
    coef = (0.33, 0.34, 0.33)

    bmi_score, bmi = risk_bmi(id_user, db)
    part_1 = bmi_score * coef[0]
    part_2 = risk_nutrition(id_user, completed[1], db) * coef[1]
    part_3 = risk_activity(id_user, completed[2], db) * coef[2]

    network_correction, n_contacts, mean_contacts = 0, 0, 0

    raw_wakaestado = min(part_1 + part_2 + part_3, 100)
    if network:
        # TODO EDIT THIS ON NETWORK IMPLEMENTATION
        network_correction, n_contacts, mean_contacts = network_influence(id_user, raw_wakaestado, db, all(completed))

    final_wakaestado = min(raw_wakaestado + network_correction, 100)
    # pack the different parts
    partial_scores = {
        'wakascore': final_wakaestado,
        'bmi_score': bmi_score,
        'nutrition': part_2 / coef[1],
        'activity': part_3 / coef[2],
        'network': network_correction * 10,  # visualizacion
        'bmi': bmi,
        'n_contacts': n_contacts,
        'mean_contacts': ceil(mean_contacts)
    }

    # store the last wakaestado
    db.set_last_wakaestado(id_user, final_wakaestado)
    # close stuff
    db.close()
    del db
    return final_wakaestado, partial_scores
