import requests
import lxml.objectify
from sys import stderr
from io import BytesIO
from email.utils import parsedate_to_datetime as parsedate_rfc822
from datetime import datetime
from hashlib import sha1

def wrong_xml(otree, tag_err):
    printerr('Wrong RSS-XML format: {}\n', tag_err)
    otree.write(stderr.buffer, pretty_print=True)
    return None

def download_feed(url):
    r = requests.get(url)
    updated = datetime.today()
    if not r.ok:
        return printerr('Error retrieving feed (code {}): {}', r.status_code, url)

    otree = lxml.objectify.parse(BytesIO(r.content))
    feed = {'url': url, 'updated': updated }
    
    root = otree.getroot()

    if root.tag == 'rss':
        return parse_rss(feed, otree)

    elif root.tag == 'feed' and root.attrib['xmlns'] == "http://www.w3.org/2005/Atom":
        return parse_atom(feed, otree)

# RSS Parsing

def parse_rss(feed, otree):
    root = otree.getroot()
    updated = datetime.today()

    if root.tag != 'rss':
        wrong_xml(otree, '<rss> tag not found')

    # Parse channel info
    
    if 'version' not in root.attrib:
        wrong_xml(otree, 'No version attrib found')

    version = root.attrib['version']
    if version != '2.0':
        wrong_xml(otree, 'Only RSS 2.0 is supported. Got version {}'.format(version))

    root = root.__dict__
    if 'channel' not in root:
        wrong_xml(otree, '<channel> tag not found')

    channel = root['channel']

    chdict = channel.__dict__
    for i in ('title', 'link', 'description'):
        if i not in chdict:
            wrong_xml(otree, '<{}> not found in <channel>'.format(i))
        feed[i] = str(chdict[i])


    # Parse items
    items = []

    for i in channel.findall('item'):
        items.append(parse_rss_item(i))
    items.sort(key = lambda item: item['date'])

    feed['items'] = items

    return feed

def parse_rss_item(item):
    item = item.__dict__
    pitem = dict()

    for i in ('title', 'link', 'description'):
        if i not in item:
            return printerr('{} not found in Feed Item', i)
        pitem[i] = str(item[i])

    if 'pubDate' in item:
        # More info:
        # https://stackoverflow.com/questions/1568856/how-do-i-convert-rfc822-to-a-python-datetime-object
        pitem['date'] = parsedate_rfc822(str(item['pubDate']))
    else:
        pitem['date'] = datetime.today()

    if 'guid' in item:
        pitem['guid'] = str(item['guid'])
    else:
        hashfunc = sha1()
        hashfunc.update(pitem['title'].encode())
        hashfunc.update(pitem['link'].encode())
        pitem['guid'] = hashfunc.hexdigest()

    return pitem


# Atom parsing
def parse_atom(feed, otree):
    wrong_xml(otree, 'Atom is not supported')
