from dbhelper import DBHelper
from random import randint


def h4ck(id_user):
    db = DBHelper()
    nq_category = db.n_questions()
    for i in list(nq_category.keys()):
        response = randint(2, 9999999) * -1
        for j in range(1, nq_category[i] + 1):
            if i == 1 and j == 1:
                db.add_answer(id_user, i, j, response, 80)
            if i == 1 and j == 2:
                db.add_answer(id_user, i, j, response, 175)
            if i == 1 and j > 5:
                db.add_answer(id_user, i, j, response, 0)
            else:
                db.add_answer(id_user, i, j, response, 49)

    db.completed_survey(id_user, 1)
    db.completed_survey(id_user, 2)
    db.completed_survey(id_user, 3)
    db.conn.commit()
    db.close()
    del db
