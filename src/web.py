from flask import Flask
from flask import abort, redirect, url_for, render_template, request

from flask_sqlalchemy import SQLAlchemy

from uuid import uuid4 as uuid
from os import getcwd

# RSS Schema must be initialized after db creation
# 'db' variable must be bound to SQLAlchemy instance
def create_app(sqlite_file='./feed.sqlite3'):

    app = Flask( __name__,
            static_url_path='',
            static_folder='../web/static/',
            template_folder='../web/templates/'
            )

    # Configure SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/data/{}'.format(getcwd(), sqlite_file)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Do not emit signals on object changes

    db = SQLAlchemy(app, session_options={
        'expire_on_commit': False # No need for expiration since SQLite instance
                                  # has only 1 client
        })

    # Pass SQLAlchemy instance to RSS Schema
    import rss.config
    rss.config.db = db
    import rss.rss as rss

    # Global context. Never cleared.
    feeds = dict();
    context = {
            'feeds': feeds,      # List of all feeds

            # Details of a current feed
            'feed': None,        # Current feed
            'page': None,        # Page number
            'channels': None,    # List of the feed's channels
            'posts': None        # Posts for current page
            }

    def init():
        print(' * Initialization of RSS web-server')

        print(' * Loading data from DB')
        print(' * Loaded feeds:')
        for feed in rss.RSSFeed.query.all():
            debug_desc(feed)
        print(' * Loaded channels:')
        for channel in rss.RSSChannel.query.all():
            debug_desc(channel)

    def debug_desc(obj):
        if type(obj) == rss.RSSFeed:
            feed = obj
            feeds[str(feed.title)] = feed
            print(' * - {} ({} channels)'.format(feed.title, len(feed.channels)))
            for channel in feed.channels:
                print(' *   - {}'.format(channel.title))
        elif type(obj) == rss.RSSChannel:
            channel = obj
            post_count = rss.RSSPost.query.filter(rss.RSSPost.channel_url == channel.url).count()
            print(' * - {} ({} posts)'.format(channel.title, post_count))





    def clear_feed_context():
        context['feed'] = None
        context['channels'] = None
        context['page'] = None
        context['posts'] = None

    def debug_print(s):
        print(s)
        for i in ('feed', 'page', 'channels', 'posts'):
            try:
                print('{}: {}'.format(i, context[i]))
            except Exception as e:
                print(e)

    @app.route('/')
    def feed():
        clear_feed_context()
        return render_template('main.html', 
                **context,
                )

    @app.route('/update')
    def update():
        rss.update()
        feed = context['feed']
        if feed:
            return redirect('/feed/{}'.format(feed.title))
        return redirect('/')

    @app.route('/add_feed', methods=('POST',))
    def add_feed():
        title = request.form['feed_title']
        if title not in feeds:
            feeds[title] = rss.RSSFeed.create(title)
        return redirect('/feed/{}'.format(title))


    @app.route('/feed/<string:feed_title>/') 
    def open_feed(feed_title):
        return open_feed_page(feed_title)

    @app.route('/feed/<string:feed_title>/page/<int:page>') 
    def open_feed_page(feed_title, page=1):
        if feed_title not in feeds:
            return redirect('/')

#         if feed_title != global_context['feed'].title:
#             update_current_feed(feed_title)

        feed = feeds[feed_title]

        if context['feed'] != feed or context['page'] != page:
            context['feed'] = feed

            posts = feed.get_feed(page = page)
            context['page'] = page
            context['posts'] = posts

        debug_print('Opened feed {}'.format(feed_title))

        return render_template('feed.html', 
                **context,
                )

    @app.route('/feed/<string:feed_title>/add_channel', methods=('POST',))
    def add_channel(feed_title):
        if feed_title not in feeds:
            return redirect('/')

        feed = feeds[feed_title]
        url = request.form['channel_url']

        feed.add_channel(url)
        context['page'] = None

        debug_print('Added channel {}'.format(url))

        return redirect('/feed/{}'.format(feed_title))

    init()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
