from rss import RSSFeed

from flask import Flask
from flask import abort, redirect, url_for, render_template, request
from flask_uuid import FlaskUUID
from uuid import uuid4 as uuid

def create_app():
    app = Flask( __name__,
            static_url_path='',
            static_folder='../web/static/',
            template_folder='../web/templates/'
            )
    FlaskUUID(app) # add support for UUID's in urls
    
    feeds = dict()

    # Global context. Never cleared.
    global_context = {
            'feed_names': [],
            'feed_title': '', # current feed
            }

    # Feed-specific context. Cleared when another feed is selected.
    feed_context = {
            'feed_channels': [], # (name, url)
            'feed_items': [],
            }

    # Page-specific context. Cleared for new visit.
    # Specified inside method handler
    # context = {}

    @app.route('/')
    def feed():
        return render_template('main.html', 
                **global_context,
                **feed_context,
                # **context
                )

    @app.route('/update')
    def update():
        # TODO
        return redirect(url_for('/'))

    @app.route('/add_feed', methods=('POST',))
    def add_feed():
        title = request.form['feed_title']
        if title not in feeds:
            feeds[title] = RSSFeed(title)
            global_context['feed_names'].append(title)
        return redirect('/feed/{}'.format(title))

    @app.route('/feed/<string:feed_title>/') 
    def open_feed(feed_title):
        if feed_title not in feeds:
            return redirect('/')

        if feed_title != global_context['feed_title']:
            update_current_feed(feed_title)

        return render_template('feed.html', 
                **global_context,
                **feed_context,
                # **context
                )

    @app.route('/feed/<string:feed_title>/add_channel', methods=('POST',))
    def add_channel(feed_title):
        if feed_title not in feeds:
            return redirect('/')

        feed = feeds[feed_title]
        url = request.form['channel_url']

        feed.add_channel(url)
        update_current_feed(feed_title)

        return redirect('/feed/{}'.format(feed_title))

    def update_current_feed(feed_title):
        feed = feeds[feed_title]
        global_context['feed_title'] = feed_title
        feed_context['feed_channels'] = list(map(lambda x: (x.get_title(), x.get_link()), feed.get_channels()))
        feed_context['feed_items'] = feed.get_feed()
        print(feed_context['feed_items'])
        
        # feed_context['feed_items']

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
