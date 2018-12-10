'''
This class is meant to have the risk models
'''

from dbhelper import DBHelper
from statistics import mean
from math import log


######################
#
# IMPLEMENTACIÓN TABLAS ALIMENTACION
#
######################
def table_1(group, n):
    # daily consume subtables
    def daily_consume(n):
        if n >= 7:
            return 10
        elif n >= 3:
            return 7.5
        elif n == 2:
            return 5
        elif n == 1:
            return 2.5
        elif n < 1:
            return 0

    # weekly consume
    def weekly_consume(n):
        if n == 1 or n == 2:
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
        if n < 1:
            return 10
        elif n == 1:
            return 7.5
        elif n == 2:
            return 5
        elif n >= 7:
            return 0
        elif n >= 3:
            return 2.5

    if group <= 4:
        return daily_consume(n)
    elif group == 5 or group == 6:
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


def risk_bmi(id_user, db=DBHelper()):
    '''
    Gives a risk score
    this is a modular function in order be easier to update
    '''

    bmi = db.getBMI(id_user)
    if bmi == 0: # sanity check
        return 0

    # TODO REVIEW
    if bmi >= 40:
        return 0
    elif 35 <= bmi < 40:
        return 25
    elif 30 <= bmi < 35:
        return 50
    elif 25 <= bmi < 30:
        return 75
    elif bmi < 25:
        return 100


def risk_nutrition(id_user, comp = False, db=DBHelper()):
    '''
    Give a risk using nutrition information
    WARNING: untested rules
    '''
    score = 0
    if not comp:
        return 0

    # obtain the responses
    ans = db.get_responses_category(id_user=id_user, phase=2)
    # TODO review these rules
    score += table_1(group=4, n=ans[0])
    score += table_1(group=4, n=ans[1])
    score += table_1(group=1, n=ans[2])
    score += table_1(group=8, n=ans[3])
    score += table_1(group=1, n=ans[4])
    score += table_1(group=1, n=ans[5]) # pan integral
    # secon block
    score += table_2(ans[6])
    score += table_2(ans[7])
    score += table_2(ans[8]) # mantequilla
    # thrid block weekly
    score += table_1(group=8, n=ans[9])
    score += table_1(group=8, n=ans[10])
    score += table_1(group=8, n=ans[11])
    score += table_1(group=8, n=ans[12]) # ensaimada, donut, croisant
    # 4th block
    score += table_1(group=2, n=ans[13])
    score += table_1(group=2, n=ans[14])
    score += table_1(group=2, n=ans[15]) # verdura de guarnicion
    score += table_1(group=1, n=ans[16]) # patatas
    score += table_1(group=6, n=ans[17])
    score += table_1(group=1, n=ans[18])
    score += table_1(group=1, n=ans[19])
    score += table_1(group=1, n=ans[20])
    # 5th block #21
    score += table_1(group=5, n=ans[21])
    score += table_1(group=5, n=ans[22])
    score += table_1(group=5, n=ans[23])
    score += table_1(group=7, n=ans[24])
    score += table_1(group=5, n=ans[25])
    score += table_1(group=5, n=ans[26])
    score += table_1(group=5, n=ans[27]) # marisco
    # 28 have no score
    # 6th block
    score += table_1(group=7, n=ans[29]) #jamon #29
    # 30 have no score
    score += table_1(group=4, n=ans[31])
    score += table_1(group=4, n=ans[32])
    score += table_1(group=3, n=ans[33])
    score += table_1(group=3, n=ans[34])
    score += table_1(group=8, n=ans[35]) # fruta en almibar
    score += table_1(group=3, n=ans[36])
    score += table_1(group=3, n=ans[37])
    score += table_3(ans[38]) # frutos secos
    score += table_1(group=8, n=ans[39])
    score += table_1(group=8, n=ans[40])
    score += table_1(group=8, n=ans[41])
    score += table_1(group=8, n=ans[42])
    score += table_1(group=8, n=ans[43])
    # 7th block
    score += table_1(group=9, n=ans[44])
    # last quesions have not asociated score

    # WARNING -> now we have 43 items!!
    # get an score between 0-100 for this part
    return score*10/43


def risk_activity(id_user, comp = False, db = DBHelper()):

    if not comp:
        return 0

    ans = db.get_responses_category(id_user=id_user, phase=3)
    # compute the METS-min/week
    METS = ans[0]*ans[1]*8 + ans[2]*ans[3]*4 + ans[4]*ans[5]*3.3
    # this have to be reviewed for sure!
    superior_limit = 1800
    return (min(METS, superior_limit)/superior_limit)*100


def network_influence(id_user, actual_wakaestado,  db, comp):

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

        return 0
    # get the WakaStatus of each of the "neighbours"
    friends = db.get_user_relationships(id_user)
    if len(friends) == 0:
        return 0
    # now obtain the wakascore for them
    # TODO implement the db-cache friend risk
    wakaestados = [get_friend_wakaestado(f) for f in friends]
    [print(el) for el in zip(friends, wakaestados)]
    print('DEBUG Log N Friends', log(len(friends), 2))
    print('DEBUG Network correction', max(0, mean(wakaestados) - actual_wakaestado) + log(len(friends), 2))
    # added a roof value at 20
    return min(max(0, mean(wakaestados) - actual_wakaestado) + log(len(friends), 2), 20)


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

    if completed is None:
        completed = db.check_completed(id_user)

    # coeficient for each part
    coef = (0.33, 0.34, 0.33)
    # compute disease risk
    if completed[0]:
        ans = db.get_responses_category(id_user=id_user, phase=1)
        # if people is healthy risk = 1, if people have all conditions risk = 0.25
        risk = 1 - sum([float(el) * 0.25 for el in ans[-3:]])
    else:
        risk = 1

    part_1 = risk_bmi(id_user, db) * coef[0]
    part_2 = risk_nutrition(id_user, completed[1], db) * coef[1]
    part_3 = risk_activity(id_user, completed[2], db) * coef[2]

    network_correction = 0
    raw_wakaestado = min(part_1 + part_2 + part_3, 100) * risk
    if network:
        # TODO EDIT THIS ON NETWORK IMPLEMENTATION
        network_correction = network_influence(id_user, raw_wakaestado, db, all(completed))

    # pack the different parts
    partial_scores = {
        'bmi': part_1/coef[0],
        'nutrition': part_2/coef[1],
        'activity': part_3/coef[2],
        'risk': risk * 100, # for better visualization
        'network': network_correction
    }
    # revert the risk, add the network correction and risk it again
    final_wakaestado = min((raw_wakaestado/risk) + network_correction, 100) * risk
    # store the last wakaestado
    db.set_last_wakaestado(id_user, final_wakaestado)
    # close stuff
    db.close()
    del db
    return final_wakaestado, partial_scores




