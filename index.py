import passlib
#import sqlite3
import logging
from flask import Flask, request, send_from_directory
from flask import render_template

from database import DataBase

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("pycrm." + __name__)
try:
    from settings import *
except:
    log.warning("You should have to create settings.py \
    file. Look into settings.py-example")
    import sys
    sys.exit(1)

app = Flask(__name__, static_url_path='')
db = DataBase(db_location)

# serve memes
#@app.route('/meme/<path:path>')
#def send_meme(path):
#    return send_from_directory('meme', path)

# serve static
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    order = request.args.get('order', default = 'id', type = str)
    sorting = request.args.get('sorting', default = 'ASC', type = str)
    return render_template('index.html', users=db.get_users(order=order, sorting=sorting), sorting=sorting)

@app.route('/users_overview')
def users_overview():
    return render_template('users_overview.html')


def main():
    app.run(host=flask_host, port=flask_port)

if __name__ == '__main__':
    main()
