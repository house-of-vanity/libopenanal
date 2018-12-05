import logging
import sqlite3
from datetime import datetime

from dateutil import parser


class DataBase:
    def __init__(self, basefile):
        self.log = logging.getLogger("pycrm." + __name__)
        try:
            self.conn = sqlite3.connect(
                basefile,
                check_same_thread=False)
        except:
            self.log.info('Could not connect to DataBase.')

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
        return self.execute(sql)[0][0]

    '''
    def get_memes(self, offset=0):
        sql = "SELECT * FROM `meme` ORDER BY rowid DESC "
        return self.execute(sql)
    '''

    def get_user_count(self):
        sql = "SELECT count(*) FROM `user`"
        return self.execute(sql)[0]

    def get_word_count(self):
        sql = "SELECT count(*) FROM `word`"
        return self.execute(sql)[0]

    def get_relations_count(self):
        sql = "SELECT count(*) FROM `relations`"
        return self.execute(sql)[0]

    def get_confs_count(self):
        sql = "SELECT count(*) FROM `conf`"
        return self.execute(sql)[0]

    def get_users(self, order='id', sorting='ASC'):
        # sql injection prevention
        if sorting == 'ASC':
            pass
        else:
            sorting = 'DESC'
        if order == 'id':
            pass
        elif order == 'first_name':
            pass
        elif order == 'last_name':
            pass
        elif order == 'username':
            pass
        elif order == 'firstly_seen':
            order = 'dt'
        elif order == 'last_activity':
            order = 'last_seen'
        elif order == 'count':
            pass
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
        return self.execute(sql)

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
        return self.execute(sql)

    def get_conf_info(self, conf_id):
        if not conf_id[1:].isdigit():
            return False
        raw1 = self.execute("""
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
            WHERE c.id = '%s'
            GROUP BY c.id
        """ % conf_id)[0]
        print(raw1)
        conf_info = {
            'title': raw1[0],
            'id': raw1[1],
            'date': raw1[2],
            'word_count': raw1[3],
            'users_cunt': raw1[4],
        }
        return conf_info

    def get_user_word_count_per_day(self, user_id):
        sql = """
            SELECT count(*), 
            date(date, 'unixepoch') as dt 
            FROM relations r 
            WHERE r.user_id = '%s' 
            GROUP BY dt order by dt
            """ % user_id
        return self.execute(sql)

    def get_user_message_count_per_day(self, user_id):
        sql = """
            SELECT count(dt), dt 
            FROM(
                SELECT count(date), 
                date(date, 'unixepoch') as dt 
                FROM relations WHERE 
                user_id='%s' GROUP BY date
                ) 
            GROUP BY dt ORDER BY dt
            """ % user_id
        return self.execute(sql)

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
            min(date(r.date, 'unixepoch')),
			m.messages
            FROM `relations` r
            LEFT JOIN `user` u ON u.id = r.user_id
            LEFT JOIN `conf` c ON c.id = r.conf_id
			LEFT JOIN (
				SELECT COUNT(messages) as messages, title FROM (
                    SELECT COUNT(r.date) AS messages, c.title
                    FROM `relations` r
                    LEFT JOIN `conf` c ON c.id = r.conf_id
                    WHERE user_id = %s
                    GROUP BY c.title, r.date
                ) GROUP BY title
			) m ON c.title = m.title
            WHERE u.id = %s
            GROUP BY c.id""" % (user_id, user_id))

        avg_lenght = self.execute("""
            SELECT count(date) as words
            FROM `relations`
            WHERE user_id = %s
            GROUP BY date""" % user_id)
        messages = self.execute("""
        SELECT count(*) FROM(
                SELECT count(date) as words
                FROM `relations`
                WHERE user_id = %s
                GROUP BY date
            )""" % user_id)
        avg = 0
        for i in avg_lenght:
            avg += i[0]
        if len(avg_lenght) != 0:
            avg = avg / len(avg_lenght)
        else:
            avg = 0
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
            'messages': messages[0][0],
            'day_known': day_known,
            'top': top,
            'chats': chats,
            'avg': avg,

        }
        return user_info

    def close(self):
        self.conn.close()
