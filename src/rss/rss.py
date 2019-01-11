from . import config
from . import parse as rss_parse
db = config.db

# db variable must be defined
# db - SQLAlchemy engine

# For DEBUGging purposes
from sqlalchemy import inspect
def print_state(obj):
    print('{}: {}'.format(obj.__class__.__name__, obj_state(obj)))

def obj_state(obj):
    i = inspect(obj)
    if i.transient:
        return 'transient'
    if i.pending:
        return 'pending'
    if i.persistent:
        return 'persistent'
    if i.detached:
        return 'detached'
    return 'unknown state'

# Secondary table for many-to-many relationship
# feed_channels = db.Table('FeedChannels',
#         db.Column(feed_title',    db.Unicode(80), db.ForeignKey('RSSFeed.title'), primary_key=True),
#         db.Column('channel_url', db.Unicode(511), db.ForeignKey('RSSChannel.url'), primary_key=True)
#         )

class RSSFeed(db.Model):
    __tablename__ = 'RSSFeed'

    title = db.Column(db.Unicode(80), primary_key=True)

    channels = db.relationship('RSSChannel', lazy='joined')
    # For some reason, many-to-many doesn't work
    # channels = db.relationship('RSSChannel', secondary=feed_channels,
    #         lazy='joined')
            # lazy='subquery')

    @classmethod
    def create(cls, title):
        """
        Add new feed
        Return FeedExistsException if feed already exists
        """

        if cls.query.get(title):
            raise FeedExistsException('RSSFeed "{}" exists'.format(title))

        feed = cls(title=title)

        db.session.add(feed)
        db.session.commit()

        db.session.refresh(feed) # Reload lazy loading 

        return feed

    def add_channel(self, url):
        """ Add RSS Channel by url """
        channel = RSSChannel.get_or_create(url)

        self.channels.append(channel)
        db.session.commit()

    def delete_channel(self, index):
        """ Delete channel by index """
        self.channels.pop(index)
        db.session.commit()

    def get_feed(self, page=1, per_page=10):
        """ Get posts from feed """
        for c in self.channels:
            print(c.url)
        posts = (RSSPost.query
                # Error: in_() not yet supported for relationships.
                # .filter(RSSPost.channel.in_(self.channels))
                .filter(RSSPost.channel_url.in_(
                    c.url for c in self.channels))
                .order_by(RSSPost.date.desc())
                .offset((page-1)*per_page)
                .limit(per_page)
                
                .all()
                )
        return posts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<RSS Feed "{}">'.format(self.title)

class RSSChannel(db.Model):
    __tablename__ = 'RSSChannel'

    url = db.Column(db.Unicode(511), primary_key=True)
    title = db.Column(db.Unicode(255), nullable=False)
    link = db.Column(db.Unicode(255), nullable=False)
    description = db.Column(db.UnicodeText())
    updated = db.Column(db.DateTime(), nullable=False)

    # Many-to-one case
    feed_title = db.Column(db.Unicode(80), db.ForeignKey('RSSFeed.title'))

    posts = db.relationship('RSSPost', 
            # lazy='joined',
            lazy='subquery',
            backref=db.backref('channel', lazy='joined')
            )

    @classmethod 
    def get_or_create(cls, url):
        """ Return existing Channel or create new """
        return cls.query.get(url) or cls.create_new(url)

    @classmethod
    def create_new(cls, url):
        feed = rss_parse.download_feed(url)
        if not feed:
            raise FeedUpdateException('Error downloading feed')

        channel = cls(
                url         = feed['url'],
                title       = feed['title'],
                link        = feed['link'],
                description = feed['description'],
                updated     = feed['updated']
                )

        for item in feed['items']:
            post = RSSPost(**item)
            channel.posts.append(post)

        db.session.add(channel)
        db.session.commit()

        # for post in channel.posts:
        #     db.session.refresh(post)

        db.session.refresh(channel)
        db.session.close()

        return channel

    def update(self):
        feed = rss_parse.download_feed(url)
        for item in feed['items']:
            if not RSSPost.query.get(guid):
                post = RSSPost(**item)
                channel.posts.append(post)

        db.session.commit()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<RSS Channel "{}" ({})>'.format(self.title, self.url)

class RSSPost(db.Model):
    __tablename__ = 'RSSPost'

    guid = db.Column(db.Unicode(255), primary_key=True)
    channel_url = db.Column(db.Unicode(511), db.ForeignKey('RSSChannel.url'), primary_key=True)

    title = db.Column(db.Unicode(255), nullable=False)
    link = db.Column(db.Unicode(1023), nullable=False)
    description = db.Column(db.UnicodeText())
    date = db.Column(db.DateTime(), nullable=False)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<RSS Post (channel: {}) "{}" ({})>'.format(
                self.channel_url,
                self.title,
                self.link)


# EXCEPTIONS

class FeedExistsException(Exception):
    pass

class FeedUpdateException(Exception):
    pass

# METHODS
def update():
    """ Update all feeds and channels """
    # TODO
    for channel in RSSChannel.query.all():
        channel.update()


# INITIALIZATION

def init(db):
    db.create_all()

init(db)
