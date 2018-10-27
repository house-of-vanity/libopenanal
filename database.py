class DataBase:
    def __init__(self, basefile):
        import sqlite3
        import datetime as dt
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


    def close(self):
        self.conn.close()
