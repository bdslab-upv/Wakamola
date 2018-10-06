#import sqlite3
from os import listdir
from random import choice
import hashlib
import mysql.connector as mariadb




def md5(id):
        '''
        Hashes id_user usign MD5. Ensures anonimity.
        '''
        return hashlib.md5(str(id).encode('utf-8')).hexdigest()

class DBHelper:
    def __init__(self, dbname="alphahealth.sqlite"):

        self.conn = mariadb.connect(user='root', \
            password=open('passwd', 'r').read().split('\n')[0].strip(), database='bot', buffered=True)
        self.cursor = self.conn.cursor()


    def load_questions(self):
        blanks = 0
        try:
            for lang in listdir('questions'):
                # iterate over the phases
                for i, phase in enumerate(sorted(listdir('questions/'+lang))):
                    with open('questions/'+lang+'/'+phase, 'r', encoding='utf-8') as fich:
                        blanks = 0
                        lines = fich.read().split('\n')
                        for j, lin in enumerate(lines):
                            if lin.strip():
                                stmt = 'INSERT INTO QUESTIONS VALUES(%s, %s, %s, %s)'
                                args = (j+1-blanks, i+1, lin.strip(), lang)
                                self.cursor.execute(stmt, args)
                                self.conn.commit()
                            else:
                                blanks += 1
        except Exception as e:
            print(e)



    def setup(self):
        print("Checking database")
        stmt = "CREATE TABLE IF NOT EXISTS STATUS (id_user varchar(32) PRIMARY KEY, phase int NOT NULL, question int NOT NULL, completed_personal int, completed_food int, completed_activity int, language text);"
        self.cursor.execute(stmt)
        self.conn.commit()
        # Questions table
        stmt = "CREATE TABLE IF NOT EXISTS QUESTIONS (question int, phase int, qtext text, language varchar(2), PRIMARY KEY (question, phase, language), UNIQUE(question, phase, language));"
        self.cursor.execute(stmt)
        self.conn.commit()
        # Responses table
        stmt = "CREATE TABLE IF NOT EXISTS RESPONSES (id_user varchar(32), id_message int, question int, phase int, answer text, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id_user, id_message, question, phase));"
        self.cursor.execute(stmt)
        self.conn.commit()
        # Tips table
        stmt = 'CREATE TABLE IF NOT EXISTS TIPS (tip text, language text, category int);'
        self.cursor.execute(stmt)
        self.conn.commit()
        # Relationship tables
        stmt = 'CREATE TABLE IF NOT EXISTS RELATIONSHIPS (active varchar(32), passive varchar(32), type varchar(6), Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(active, passive), FOREIGN KEY (active) references STATUS (id_user));'
        self.cursor.execute(stmt)
        self.conn.commit()
        #
        self.load_questions()
        print('Database ready!')



    def register_user(self, id_user, language):
        stmt = "INSERT INTO STATUS (id_user, phase, question,  completed_personal, completed_food, completed_activity, language) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        # phase 0, question 0, not completed any questionarie
        args = (md5(id_user), 0, 0, 0, 0, 0, language)
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def check_user(self, id_user):
        '''
        This function is for sanity check, just force the user to do the /start if
        its not registered on the status table
        '''
        stmt = 'select phase, question from STATUS where id_user = %s'
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        return len(list(self.cursor.fetchall())) == 0

    def change_phase(self, newphase, id_user):
        stmt = "UPDATE STATUS SET phase = %s , question = 1 where id_user = %s"
        args = (newphase, md5(id_user))
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def get_phase_question(self, id_user):
        stmt = 'select phase, question from STATUS where id_user = %s'
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        return self.cursor.fetchone()


    def next_question(self, id_user):
        stmt = "update STATUS set question = question +1 where id_user = %s"
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        self.conn.commit()


    def get_question(self, phase, question, lang):
        stmt = 'select qtext from QUESTIONS where phase = %s and question = %s and language = %s'
        args = (phase, question, str(lang))
        self.cursor.execute(stmt, args)
        return str([el[0] for el in self.cursor.fetchall()][0])


    def check_start(self, id_user):
        stmt = "select count(*) from STATUS where id_user = %s"
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        return int([el[0] for el in self.cursor.fetchall()][0]) > 0

    def check_answer(self, id_user, phase, question):
        '''
        OBSOLETO TODO DELETE
        '''
        stmt = "select count(*) from RESPONSES where id_user = %s and phase = %s and question = %s"
        args = (md5(id_user), phase, question)
        self.cursor.execute(stmt, args)
        return self.cursor.fetchone()[0] == 0
        #return int([el[0] for el in self.conn.execute(stmt, args)][0]) == 0

    def add_answer(self, id_user, phase, question, message_id, answer):
        stmt = "insert into RESPONSES (id_user, phase, question, answer, id_message) values(%s, %s, %s, %s, %s)"
        args = (md5(id_user), phase, question, answer, message_id)
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def update_response(self, id_user, phase, question, message_id, answer):
        stmt = "update RESPONSES set answer = %s, id_message=%s where id_user = %s and phase = %s and question = %s"
        args = (answer, message_id, md5(id_user), phase, question)
        self.cursor.execute(stmt, args)
        self.conn.commit()


    def update_response_edited(self, id_message, answer):
        stmt = "update RESPONSES set answer = %s where id_message = %s"
        print(id_message, answer)
        args = (answer, id_message)
        self.cursor.execute(stmt, args)
        self.conn.commit()


    def completed_survey(self, id_user, phase):
        if phase == 1:
            stmt = 'update STATUS set completed_personal = 1 where id_user = %s'
        elif phase == 2:
            stmt = 'update STATUS set completed_food = 1 where id_user = %s'
        elif phase == 3:
            stmt = 'update STATUS set completed_activity = 1 where id_user = %s'
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        self.conn.commit()


    def check_completed(self, id_user):
        stmt = "select completed_personal, completed_food, completed_activity from STATUS where id_user = %s"
        args = (md5(id_user), )
        self.cursor.execute(stmt, args)
        rs = self.cursor.fetchall()
        if len(rs) == 0:
            return (False, False, False)
        return [(el[0], el[1], el[2]) for el in rs][0]


    def n_questions(self):
        '''
        Return a dict with the number of question per phase
        '''
        aux = {}
        stmt = "select count(*) from QUESTIONS where language='es' group by phase order by phase"
        self.cursor.execute(stmt)
        for i, el in enumerate(self.cursor.fetchall()):
            aux[i+1] = el[0]
        return aux


    def add_relationship(self, id_user, contact, type):
        stmt = 'Insert into RELATIONSHIPS (active, passive, type) values (%s, %s, %s)'
        args = (md5(id_user), md5(contact), type)
        self.cursor.execute(stmt, args)
        self.conn.commit()


    def get_relationships(self):
        '''
        yields all database relationships
        '''
        stmt = "select active, passive from RELATIONSHIPS"
        self.cursor.execute(stmt)
        for el in self.cursor.fetchall():
            yield el



    def get_tip(self, language = 'en', category=-1):
        '''
        Category = 0 means a general tip
        1 -> Tips about personal data, habits
        2 -> Tips about food
        3 -> Tips about physical activity
        -1 -> Any tip
        '''
        stmt = "select tip from TIPS where language = %s"
        args = (language, )
        if category > 0 :
            stmt += ' and category = %s'
            args = (language, category)
        self.cursor.execute(stmt, args)
        return choice([str(el[0]) for el in self.cursor.fetchall()])


    def getBMI(self, id_md5):
        stmt = "select answer from RESPONSES where id_user = %s and question <= 2 and Timestamp in (select max(Timestamp) \
        from RESPONSES where id_user = %s and phase = 1 group by question)"
        args = (id_md5, id_md5)
        self.cursor.execute(stmt, args)
        aux_ = self.cursor.fetchall()
        print(aux_)
        if len(aux_) != 2:
            print('Not BMI available for', id_md5)
            return 0

        return float(aux_[0][0])/((float(aux_[1][0])/100)**2)



    def get_responses_category(self, phase, id_user):
        '''
        Given one phase and one id, return all the answers of that user to that category
        '''
        stmt = 'select answer from RESPONSES where \
                id_user = %s and phase = %s  \
                and Timestamp in (select max(Timestamp) \
                from RESPONSES where id_user = %s and phase = %s group by question)'
        args = (md5(id_user), phase, md5(id_user), phase)
        self.cursor.execute(stmt, args)
        return [float(el[0]) for el in self.cursor.fetchall()]
