import sqlite3
from datetime import datetime
from dateutil import parser
import logging

class DataBase:
    def __init__(self, basefile):
        self.log = logging.getLogger("pycrm." + __name__)
        try:
            self.conn = sqlite3.connect(
                basefile,
                check_same_thread=False)
        except:
            self.log.info('Could not connect to DataBase.')
            return None

    def execute(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()
        return cursor.fetchall()

    def save_word(self, word):
        sql = "INSERT OR IGNORE INTO word('word') \
        VALUES ('%s')" % word
        self.execute(sql)
        sql = "SELECT id FROM word WHERE word = '%s'" % word
        return(self.execute(sql)[0][0])

    def get_memes(self, offset=0):
        sql = "SELECT * FROM `meme` ORDER BY rowid DESC "
        return(self.execute(sql))

    def get_user_count(self):
        sql = "SELECT count(*) FROM `user`"
        return(self.execute(sql)[0])

    def get_word_count(self):
        sql = "SELECT count(*) FROM `word`"
        return(self.execute(sql)[0])

    def get_relations_count(self):
        sql = "SELECT count(*) FROM `relations`"
        return(self.execute(sql)[0])

    def get_confs_count(self):
        sql = "SELECT count(*) FROM `conf`"
        return(self.execute(sql)[0])

    def get_users(self, order='id', sorting='ASC'):
        # sql injection prevention
        if sorting == 'ASC':
            sorting = 'ASC'
        else:
            sorting = 'DESC'
        if order == 'id':
            order = 'id'
        elif order == 'first_name':
            order = 'first_name'
        elif order == 'last_name':
            order == 'last_name'
        elif order == 'username':
            order = 'username'
        elif order == 'firstly_seen':
            order = 'dt'
        elif order == 'last_activity':
            order = 'last_seen'
        elif order == 'count':
            order = 'count'
        else:
            order = 'id'
        sql = """
        SELECT * FROM (
            SELECT u.id,
            u.username,
            u.first_name,
            u.last_name,
            date(u.date, 'unixepoch') as dt,
            max(date(r.date, 'unixepoch')) as last_seen,
            count(u.id) as count
            FROM `user` u LEFT JOIN `relations` r ON
            r.user_id == u.id
            GROUP BY u.id
        )
         ORDER BY %s %s""" % (
            order, sorting)
        return(self.execute(sql))

    def get_confs(self):
        sql = """
            SELECT c.title,
            c.id,
            date(c.date, 'unixepoch') as dt,
            count(r.conf_id) as count,
            t1.users
            FROM `conf` c 
            LEFT JOIN `relations` r 
            ON c.id = r.conf_id
            LEFT JOIN `user` u
            ON u.id = r.user_id
            LEFT JOIN (
                SELECT id, title, count(user_id) as users FROM (
                SELECT c.id, c.title, r.user_id, count(r.conf_id) as words
                FROM `conf` c 
                LEFT JOIN `relations` r 
                ON c.id = r.conf_id
                GROUP BY c.id, r.user_id
            )
            GROUP BY title) as t1
            ON t1.id = c.id
            GROUP BY c.id
        """
        return(self.execute(sql))

    def get_user_info(self, user_id):
        if not user_id.isdigit():
            return False
        raw1 = self.execute("""
            SELECT u.id,
            first_name,
            last_name,
            username,
            datetime(u.date, 'unixepoch') as date,
            count(u.id) as words,
            datetime(max(r.date), 'unixepoch') as last_message
            FROM `user` u
            LEFT JOIN `relations` r ON r.user_id = u.id
            WHERE u.id = %s""" % user_id)[0]
        top = self.execute("""
            SELECT w.word, count(w.id) as count FROM `relations` r 
            LEFT JOIN `user` u ON u.id = r.user_id
            LEFT JOIN `word` w ON w.id = r.word_id
            WHERE u.id = %s
            GROUP BY w.id
            ORDER BY count DESC
            LIMIT 10
            """ % user_id)
        chats = self.execute("""SELECT c.title,
            count(c.id) count,
            min(date(r.date, 'unixepoch'))
            FROM `relations` r 
            LEFT JOIN `user` u ON u.id = r.user_id
            LEFT JOIN `conf` c ON c.id = r.conf_id
            WHERE u.id = %s
            GROUP BY c.id""" % user_id)
        avg_lenght = self.execute("""
            SELECT count(date) as words 
            FROM `relations`
            WHERE user_id = %s
            GROUP BY date""" % user_id)
        avg = 0
        for i in avg_lenght:
            avg += i[0]
        avg = avg / len(avg_lenght)
        day_known = (datetime.now() - parser.parse(raw1[4])).days
        if not day_known:
            day_known = 1
        user_info = {
            'id': raw1[0],
            'first_name': raw1[1],
            'last_name': raw1[2],
            'username': raw1[3],
            'first_date': raw1[4],
            'word_count': raw1[5],
            'last_message': raw1[6],
            'day_known': day_known,
            'top': top,
            'chats': chats,
            'avg': avg,
        }
        return user_info

    def close(self):
        self.conn.close()
