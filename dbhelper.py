from os import listdir
import mysql.connector as mariadb
from base64 import b64encode, b64decode

'''
Refactored: ALL id_user is now the hashed version
'''

DATABASE = 'bot_preprod'

class DBHelper:
    def __init__(self, dbname="alphahealth.sqlite"):
        self.conn = mariadb.connect(user='bothandler',
                                    password=open('passwd', 'r').read().split('\n')[0].strip(), database=DATABASE,
                                    buffered=True)
        self.cursor = self.conn.cursor()

    def load_questions(self):
        self.conn.commit()
        self.cursor = self.conn.cursor()

        for lang in listdir('questions'):
            try:
                # iterate over the phases
                for i, phase in enumerate(sorted(listdir('questions/' + lang))):
                    with open('questions/' + lang + '/' + phase, 'r', encoding='utf-8') as fich:
                        blanks = 0
                        lines = fich.read().split('\n')
                        for j, lin in enumerate(lines):
                            if lin.strip():
                                stmt = 'INSERT INTO QUESTIONS VALUES(%s, %s, %s, %s)'
                                args = (j + 1 - blanks, i + 1, lin.strip(), lang)
                                self.cursor.execute(stmt, args)
                                self.conn.commit()
                            else:
                                blanks += 1
            except Exception as e:
                print(e)
        self.cursor.close()



    def reconnect(self, dbname="alphahealth.sqlite"):
        '''
        Create a fresh connection to the database
        also a new cursor
        '''
        self.conn = mariadb.connect(user='bothandler',
                                    password=open('passwd', 'r').read().split('\n')[0].strip(), database=DATABASE,
                                    buffered=True)
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def setup(self):
        self.cursor = self.conn.cursor()
        queries = [query.strip() for query in open('init_db_queries.sql', 'r').read().split(';') if query]
        for query in queries:
            if query:
                self.cursor.execute(query)
        self.conn.commit()
        self.cursor.close()
        self.load_questions()

    def register_user(self, id_user, language):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'insert INTO STATUS (id_user, phase, question,  completed_personal, \
            completed_food, completed_activity, language) VALUES (%s, %s, %s, %s, %s, %s, %s)'
            # phase 0, question 0, not completed any questionarie
            args = (id_user, 0, 0, 0, 0, 0, language)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            self.cursor.close()
        except Exception as e:
            print(e)
            self.reconnect()

    def check_user(self, id_user):
        '''
        This function is for sanity check, just force the user to do the /start if
        its not registered on the status table
        '''
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select phase, question from STATUS where id_user = %s'
            args = (id_user,)
            self.cursor.execute(stmt, args)
            rs = list(self.cursor.fetchall())
            self.cursor.close()
            return len(rs) == 0
        except Exception as e:
            self.reconnect()
            # WARNING check this
            return True

    def change_phase(self, newphase, id_user):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = "UPDATE STATUS SET phase = %s , question = 1 where id_user = %s"
            args = (newphase, id_user)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            self.cursor.close()
        except Exception as e:
            print(e)
            self.reconnect()

    def get_phase_question(self, id_user):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select phase, question from STATUS where id_user = %s'
            args = (id_user,)
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchone()
            self.cursor.close()
            return rs
        except Exception as e:
            print(e)
            self.reconnect()
            return 0, 0

    def next_question(self, id_user):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = "update STATUS set question = question +1 where id_user = %s"
            args = (id_user,)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            self.cursor.close()
        except Exception as e:
            print(e)
            self.reconnect()

    def get_question(self, phase, question, lang):

        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select qtext from QUESTIONS where phase = %s and question = %s and language = %s'
            args = (phase, question, str(lang))
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchall()
            self.cursor.close()
            return str([el[0] for el in rs][0])
        except Exception as e:
            print(e)
            self.reconnect()
            return None

    def check_start(self, id_user):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = "select count(*) from STATUS where id_user = %s"
            args = (id_user,)
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchall()
            self.cursor.close()
            return int(rs[0][0]) > 0
        except Exception as e:
            print(e)
            self.reconnect()
            return None

    def add_answer(self, id_user, phase, question, message_id, answer):
        self.conn.commit()
        self.cursor = self.conn.cursor()
        try:
            stmt = "insert into RESPONSES (id_user, phase, question, answer, id_message) values(%s, %s, %s, %s, %s)"
            args = (id_user, phase, question, answer, message_id)
            self.cursor.execute(stmt, args)
            self.conn.commit()
        except Exception as e:
            print(e)
            print("Primary key exception for Add Answer - dbhelper")
            self.reconnect()
        self.cursor.close()

    def update_response_edited(self, id_message, answer):
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = "update RESPONSES set answer = %s where id_message = %s"
        print(id_message, answer)
        args = (answer, id_message)
        self.cursor.execute(stmt, args)
        self.conn.commit()
        self.cursor.close()

    def completed_survey(self, id_user, phase):
        '''
        TODO error controls on this method
        '''
        self.conn.commit()
        self.cursor = self.conn.cursor()
        if phase == 1:
            stmt = 'update STATUS set completed_personal = 1 where id_user = %s'
        elif phase == 2:
            stmt = 'update STATUS set completed_food = 1 where id_user = %s'
        else:
            stmt = 'update STATUS set completed_activity = 1 where id_user = %s'
        args = (id_user,)
        self.cursor.execute(stmt, args)
        self.conn.commit()
        self.cursor.close()

    def check_completed(self, id_user):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = "select completed_personal, completed_food, completed_activity from STATUS where id_user = %s"
            args = (id_user,)
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchall()
            self.cursor.close()
            if len(rs) > 0:
                return rs[0][0], rs[0][1], rs[0][2]
            else:
                return False, False, False
            # TODO remove if test is okay
            # return [(el[0], el[1], el[2]) for el in rs][0]
        except Exception as e:
            print(e)
            return False, False, False

    def n_questions(self):
        '''
        Return a dict with the number of question per phase
        This method is called at the start, so no error control
        '''
        self.conn.commit()
        self.cursor = self.conn.cursor()
        aux = {}
        stmt = "select count(*) from QUESTIONS where language='es' group by phase order by phase"
        self.cursor.execute(stmt)
        for i, el in enumerate(self.cursor.fetchall()):
            aux[i + 1] = el[0]
        self.cursor.close()
        return aux

    def exists_relationship(self, id_user, contact):
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = 'select type from RELATIONSHIPS where active = %s and passive = %s'
        args = (id_user, contact)
        self.cursor.execute(stmt, args)
        rs = self.cursor.fetchall()
        self.cursor.close()
        if len(rs) > 0:
            return True, rs[0][0]
        else:
            return False, None

    def add_relationship(self, id_user, contact, type):
        try:
            exists, existent_type = self.exists_relationship(id_user, contact)
            self.conn.commit()
            self.cursor = self.conn.cursor()
            if exists:
                # if the type is different update it
                if not type == existent_type:
                    stmt = 'UPDATE RELATIONSHIPS SET type = %s where active = %s and passive = %s'
                    args = (type, id_user, contact)
                    self.cursor.execute(stmt, args)
            else:
                stmt = 'Insert into RELATIONSHIPS (active, passive, type) values (%s, %s, %s)'
                args = (id_user, contact, type)
                self.cursor.execute(stmt, args)
            self.conn.commit()
            self.cursor.close()
        except Exception as e:
            self.reconnect()
            print(e)

    def get_relationships(self):
        '''
        yields all database relationships
        '''
        # WARNING yield on a cursor
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = "select active, passive from RELATIONSHIPS"
        self.cursor.execute(stmt)
        rs = self.cursor.fetchall()
        self.cursor.close()
        for el in rs:
            yield el

    def get_user_relationships(self, id_user):
        '''
        Return a list of MD5 id's for all the relationshios of one person
        '''
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            # active list
            stmt1 = "select active from RELATIONSHIPS where passive = %s"
            stmt2 = "select passive from RELATIONSHIPS where active = %s"
            args = (id_user, )
            self.cursor.execute(stmt1, args)
            rs1 = self.cursor.fetchall()
            self.cursor.execute(stmt2, args)
            rs2 = self.cursor.fetchall()
            self.cursor.close()
            return list(set([el[0] for el in rs1+rs2]))
        except Exception as e:
            print(e)
            self.reconnect()

    def getBMI(self, id_user):
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = "select answer from RESPONSES where id_user = %s and question <= 2 and phase = 1 and " \
               "Timestamp in (select max(Timestamp) from RESPONSES where id_user = %s " \
               "and phase = 1 group by question)"
        args = (id_user, id_user)
        self.cursor.execute(stmt, args)
        rs = self.cursor.fetchall()
        self.cursor.close()
        if len(rs) != 2:
            return 0
        return float(rs[0][0]) / ((float(rs[1][0]) / 100) ** 2)

    def get_responses_category(self, phase, id_user):
        '''
        Given one phase and one id, return all the answers of that user to that category
        '''
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = 'select answer from RESPONSES where \
                id_user = %s and phase = %s  \
                and Timestamp in (select max(Timestamp) \
                from RESPONSES where id_user = %s and phase = %s group by question)'
        args = (id_user, phase, id_user, phase)
        self.cursor.execute(stmt, args)
        rs = self.cursor.fetchall()
        self.cursor.close()
        return [float(el[0]) for el in rs]

    def get_status_by_id_message(self, id_message):
        '''
        Given one id_message, return the question and phase asociated
        :param id_message:
        :return: tuple
        '''
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select phase, question from RESPONSES where id_message = %s'
            self.cursor.execute(stmt, (id_message,))
            rs = self.cursor.fetchall()
            self.cursor.close()
            return tuple(rs[0])
        except:
            self.reconnect()
            return None

    def get_contacts_by_categorie(self):
        try:
            res = {'home': 0, 'family': 0, 'friend': 0, 'coworker': 0}
            self.conn.commit()
            self.cursor = self.conn.cursor()
            # TODO things
            return res
        except:
            self.reconnect()
            return None

    def create_short_link(self, id_user, type):
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'insert into SHORT_URLS (id_user, type) values (%s, %s)'
            args = (id_user, type)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            # get the last id introduced in the database
            last_id = self.cursor.lastrowid
            self.cursor.close()
            return b64encode(str(last_id).encode()).decode('utf-8')
        except:
            self.reconnect()
            self.cursor = self.conn.cursor()
            stmt = 'select ID from SHORT_URLS where id_user = %s and type = %s'
            args = (id_user, type)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            rs = self.cursor.fetchall()
            self.cursor.close()
            return b64encode(str(rs[0][0]).encode()).decode('utf-8')

    def get_short_link(self, id):
        try:
            id = int(b64decode(id))
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select id_user, type from SHORT_URLS where ID = %s'
            args = (id, )
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchall()
            self.cursor.close()
            # return a tuple id_user, type
            return rs[0]
        except:
            self.reconnect()
            return None

    def statistics(self):
        try:
            results = []
            self.conn.commit()
            self.cursor = self.conn.cursor()
            # completed everything
            stmt = 'select count(*) from STATUS where completed_personal + completed_food + completed_activity = 3;'
            self.cursor.execute(stmt)
            results.append(self.cursor.fetchall()[0][0])
            # started the bot
            stmt = 'select count(*) from STATUS;'
            self.cursor.execute(stmt)
            results.append(self.cursor.fetchall()[0][0])
            # number of relationships
            stmt = 'select count(*) from RELATIONSHIPS;'
            self.cursor.execute(stmt)
            results.append(self.cursor.fetchall()[0][0])
            self.cursor.close()
        except:
            self.reconnect()
            return [None, None, None]
        return results



    ################################
    #
    # "Crontab mecanics for version 3"
    #
    ################################

    def set_last_wakaestado(self, id_user, score):
        """
        :param id_user: Unhashed user id
        :param score: Score obtained at last wakaestado
        :return:
        """
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'update STATUS SET last_wakaestado = %s where id_user = %s'
            args = (score, id_user)
            self.cursor.execute(stmt, args)
            self.conn.commit()
            self.cursor.close()
        except Exception as e:
            print(e)
            self.reconnect()

    def get_last_wakaestado(self, id_user):
        """
        Method called during 'crontab' time
        :param id_user:
        :return: Last wakaestado, -1 if error occurs
        """
        try:
            self.conn.commit()
            self.cursor = self.conn.cursor()
            stmt = 'select last_wakaestado from STATUS where id_user = %s'
            args = (id_user,)
            self.cursor.execute(stmt, args)
            rs = self.cursor.fetchall()
            self.cursor.close()
            if len(rs) == 0:
                return None
            else:
                return float(rs[0][0])
        except Exception as e:
            print(e)
            self.reconnect()
            return None

    def get_users(self):
        """
        :return: Generator with all hashed IDs on the system
        """
        self.conn.commit()
        self.cursor = self.conn.cursor()
        stmt = 'select id_user from STATUS'
        self.cursor.execute(stmt)
        rs = self.cursor.fetchall()
        self.cursor.close()
        for el in rs:
            yield el
