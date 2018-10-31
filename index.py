import datetime
import logging
import os
import requests
import time

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
# @app.route('/meme/<path:path>')
# def send_meme(path):
#    return send_from_directory('meme', path)

# serve static
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/', methods=['GET', 'POST'])
def index():
    order = request.args.get('order', default='id', type=str)
    sorting = request.args.get('sorting', default='ASC', type=str)
    totals = {
        'users': db.get_user_count(),
        'words': db.get_word_count(),
        'relations': db.get_relations_count(),
        'confs': db.get_confs_count()
    }
    return render_template(
        'index.html',
        users=db.get_users(order=order, sorting=sorting),
        sorting=sorting,
        totals=totals
    )


@app.route('/conf')
def conf():
    totals = {
        'users': db.get_user_count(),
        'words': db.get_word_count(),
        'relations': db.get_relations_count(),
        'confs': db.get_confs_count()
    }

    return render_template(
        'conf.html',
        confs=db.get_confs(),
        totals=totals)

@app.route('/overview/conf/<conf_id>')
def conf_overview(conf_id):

    return render_template(
        'conf_details.html',
        conf_info=db.get_conf_info(conf_id))

@app.route('/overview/user/<user_id>')
def user_overview(user_id):

    return render_template(
        'user.html',
        user_info=db.get_user_info(user_id))


def get_threads(board):
    return requests.get(url=f'https://2ch.hk/{board}/threads.json').json()


def sort_threads(threads, order, sorting):
    is_asc = True if sorting == 'ASC' else False

    if order == 'views':
        sorted_threads = sorted(threads['threads'], key=lambda thread: (
            thread['views'], thread['score']), reverse=is_asc)
    elif order == 'score':
        sorted_threads = sorted(threads['threads'], key=lambda thread: (
            thread['score'], thread['views']), reverse=is_asc)
    elif order == 'posts':
        sorted_threads = sorted(threads['threads'], key=lambda thread: (
            thread['posts_count'], thread['views']), reverse=is_asc)
    elif order == 'timestamp':
        sorted_threads = sorted(threads['threads'], key=lambda thread: (
            thread['timestamp'], thread['views']), reverse=is_asc)
    elif order == 'lasthit':
        sorted_threads = sorted(threads['threads'], key=lambda thread: (
            thread['lasthit'], thread['views']), reverse=is_asc)
    else:
        sorted_threads = threads['threads']

    return sorted_threads


@app.template_filter('time')
def to_time(s):
    return datetime.datetime.fromtimestamp(s).strftime('%H:%M:%S %d.%m.%Y ')


@app.route('/stat', methods=['GET', 'POST'])
def stat():
    board = request.args.get('board', default='b', type=str)
    order = request.args.get('order', default='id', type=str)
    sorting = request.args.get('sorting', default='ASC', type=str)

    if board not in boards_list:
        board = 'b'

    threads = get_threads(board)
    sorted_threads = sort_threads(threads, order, sorting)

    posts = sum(thread['posts_count'] for thread in sorted_threads)

    return render_template(
        'stat.html',
        board=threads['board'],
        sorting=sorting,
        posts=posts,
        threads=sorted_threads,
        now=datetime.datetime.now().strftime('%s'),
    )


def main():
    app.run(host=flask_host, port=flask_port)


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return datetime.datetime.fromtimestamp(value).strftime(format)


@app.template_filter('readable_delta')
def readable_delta(from_seconds, until_seconds=None):
    # Returns a nice readable delta.
    def plur(it):
        try:
            size = len(it)
        except TypeError:
            size = int(it)
        return '' if size == 1 else 's'

    if not until_seconds:
        until_seconds = time.time()

    seconds = int(until_seconds) - int(from_seconds)
    delta = datetime.timedelta(seconds=seconds)
    delta_minutes = delta.seconds // 60
    delta_hours = delta_minutes // 60

    if delta.days:
        return '%d day%s, %d hour%s' % (
            delta.days,
            plur(delta.days),
            (delta_hours),
            plur(delta_hours))
    elif delta_hours:
        return '%d hour%s, %d minute%s' % (
            delta_hours,
            plur(delta_hours),
            (delta_minutes - delta_hours * 60),
            plur(delta_minutes))
    elif delta_minutes:
        return '%d minute%s' % (delta_minutes, plur(delta_minutes))
    else:
        return '%d second%s' % (delta.seconds, plur(delta.seconds))


if __name__ == '__main__':
    main()
