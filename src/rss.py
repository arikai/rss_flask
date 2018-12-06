import requests
import lxml.objectify
from sys import stderr
from io import BytesIO
from email.utils import parsedate_to_datetime as parsedate_rfc822
import time
from hashlib import sha1


# Helper print functions for errors 
def printerr(str_fmt, *values):
    print(str_fmt.format(*values), file=stderr)
    return None

def wrong_xml(otree, tag_err):
    printerr('Wrong RSS-XML format: {}\n', tag_err)
    otree.write(stderr.buffer, pretty_print=True)
    return None


class RSSFeed(object):
    def __init__(self, title,
            aggregate_format='{channel_title}: {title}\n{description}\n{link}\n\n'
            ):
        self.__channels = []
        self.__title = title
        self.__feed = []
        self.__aggregate_format = aggregate_format

    def __str__(self):
        return 'RSS feed "{}". Channels:\n\t{}'.format(
                self.get_title(),
                '\n\t'.join(map(lambda c: c.get_url(), self.get_channels()))
                )

    def get_title(self):
        return self.__title

    def get_feed(self):
        return self.__feed

    def get_channels(self):
        return self.__channels

    def add_channel(self, url):
        channel = RSSChannel(url)
        self.__channels.append(channel)
        self.update()

    def update(self):
        """ Update contents of all channels """

        for c in self.__channels:
            c.update()
        self.aggregate()

    def aggregate(self):
       """ Aggregate results from all feeds in a single feed """

       fmt = self.__aggregate_format 

       agg_list = []
       for channel in self.__channels:
           channel_info = channel.get_info()
           for item in channel.get_items():
               item['channel_title'] = channel_info['channel_title']
               agg_list.append((item['date'], item))

       agg_list.sort(key = lambda item: item[0])
       self.__feed = list(map(lambda item: item[1], agg_list))


class RSSChannel(object):

    def __init__(self, url):
        self.__url = url

        feed = RSSChannel.download_new_feed(url)

        self.__title = feed['title']
        self.__link = feed['link']
        self.__description = feed['description']
        self.__items = feed['items']
        self.__last_update = time.time()

    def __str__(self):
        return 'RSS Channel "{}" ({}): {}'.format(
                self.__title,
                self.__link,
                self.__description)

    def get_link(self):
        return self.__link

    def get_url(self):
        return self.__url

    def get_title(self):
        return self.__title

    def get_info(self):
        return {
                'channel_title': self.__title,
                'channel_link': self.__link,
                'channel_description': self.__description,
                }

    def get_items(self):
        return self.__items


    @staticmethod
    def download_new_feed(url):
        """ Download RSS feed in XML format and parse to dict """

        otree, channel = RSSChannel.download_feed(url)

        feed = dict()

        chdict = channel.__dict__
        for i in ('title', 'link', 'description'):
            if i not in chdict:
                wrong_xml(otree, '<{}> not found in <channel>'.format(i))
            feed[i] = str(chdict[i])

        items = []
        for i in channel.findall('item'):
            items.append(RSSChannel.parse_channel_item(i))
        items.sort(key = lambda item: item['date'])

        feed['items'] = items

        return feed

    def update(self):
        """ Update channel's feed """
        otree, channel = RSSChannel.download_feed(self.__url)
        items = []
        for i in channel.findall('item'):
            items.append(RSSChannel.parse_channel_item(i))
        items.sort(key = lambda item: item['date'])

        self.__items = items
        self.__last_update = time.time()

    @staticmethod
    def parse_channel_item(item):
        item = item.__dict__
        pitem = dict()

        for i in ('title', 'link', 'description'):
            if i not in item:
                return printerr('{} not found in Feed Item', i)
            pitem[i] = str(item[i])

        if 'pubDate' in item:
            # https://stackoverflow.com/questions/1568856/how-do-i-convert-rfc822-to-a-python-datetime-object
            pitem['date'] = parsedate_rfc822(str(item['pubDate'])).timestamp()
        else:
            pitem['date'] = time.time()

        if 'guid' in item:
            pitem['guid'] = item['guid']
        else:
            hashfunc = sha1()
            hashfunc.update(pitem['title'].encode())
            hashfunc.update(pitem['link'].encode())
            pitem['guid'] = hashfunc.hexdigest()

        return pitem

    @staticmethod
    def download_feed(url):
        r = requests.get(url)
        if not r.ok:
            return printerr('Error retrieving feed (code {}): {}', r.status_code, url)
        otree = lxml.objectify.parse(BytesIO(r.content))
        
        root = otree.getroot()
        if root.tag != 'rss':
            wrong_xml(otree, '<rss> tag not found')

        if 'version' not in root.attrib:
            wrong_xml(otree, 'No version attrib found')

        version = root.attrib['version']
        if version != '2.0':
            wrong_xml(otree, 'Only RSS 2.0 is supported. Got version {}'.format(version))

        root = root.__dict__
        if 'channel' not in root:
            wrong_xml(otree, '<channel> tag not found')
        channel = root['channel']

        return otree, channel


# DEBUG
if __name__ == '__main__':
    feed = RSSFeed('My feed')
    # feed.add_channel('https://venam.nixers.net/blog/feed.xml')
    feed.add_channel('https://habr.com/rss/interesting/')
    # feed.add_channel('https://news.ycombinator.com/rss')
    print(feed.get_feed())
