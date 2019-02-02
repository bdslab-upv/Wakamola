from dbhelper import DBHelper
from random import randint


def h4ck(id_user):
    db = DBHelper()
    nq_category = db.n_questions()
    for i in list(nq_category.keys()):
        for j in range(1, nq_category[i] + 1):
            response = randint(2, 9999999) * -1
            # peso
            if i == 1 and j == 1:
                db.add_answer(id_user, i, j, response, 80)
            # altura
            if i == 1 and j == 2:
                db.add_answer(id_user, i, j, response, 175)
            # enfermedades
            if i == 1 and 5 <= j <= 8:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 9:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 10:
                db.add_answer(id_user, i, j, response, 30)
            if i == 1 and j == 11:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 12:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 13:
                db.add_answer(id_user, i, j, response, 5)
            if i == 1 and j == 14:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 15:
                db.add_answer(id_user, i, j, response, 0)
            if i == 1 and j == 16:
                db.add_answer(id_user, i, j, response, 46400)

            else:
                db.add_answer(id_user, i, j, response, 49)

    db.completed_survey(id_user, 1)
    db.completed_survey(id_user, 2)
    db.completed_survey(id_user, 3)
    db.conn.commit()
    db.close()
    del db
