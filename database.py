class DataBase:
    def __init__(self, basefile):
        import sqlite3
        #import datetime as dt
        import logging
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

    def get_users(self, order='id', sorting='ASC'):
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
        else:
            order = 'id'
        sql = """
        SELECT * FROM 
            (SELECT u.id,
            u.username,
            u.first_name,
            u.last_name,
            datetime(u.date, 'unixepoch') as dt,
            max(datetime(r.date, 'unixepoch')) as last_seen
            FROM `user` u LEFT JOIN `relations` r ON
            r.user_id == u.id
            GROUP BY u.id)
         ORDER BY %s %s""" % (
            order, sorting)

        return(self.execute(sql))

    def close(self):
        self.conn.close()
