import os.path
import re
import sys
import time
import urllib2


USER_AGENT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
WRETCH_SEARCH = 'http://tw.blog.search.yahoo.com/search?fr=cb-wretch&type=web&provider=wretch&p={query}&xargs=0&pstart=1&b={start}'
YAHOO_SEARH = 'http://hk.blog.search.yahoo.com/search/blog?p={query}&ygmasrchbtn=blog+search&fr=uh-yblog&xargs=0&pstart=1&b={start}'


def main(query, data_dir):
    print('Starting search...')

    paginate(query, WRETCH_SEARCH, 'wretch', r'wretch\.cc/blog/([^/<?%]+)',
        data_dir)
    paginate(query, YAHOO_SEARH, 'yahoo', r'blog\.yahoo\.com/([^/<?%]+)',
        data_dir)


def paginate(query, template_url, name, pattern, data_dir):
    page = 1
    usernames = set()
    while True:
        print('{1} - Page {0}'.format(page, name))
        item_start = 10 * (page - 1) + 1
        content = search(template_url.format(query=query, start=item_start))

        for match in re.finditer(pattern, content):
            usernames.add(match.group(1))

        if 'id="pg-next"' in content:
            page += 1
        else:
            break

        time.sleep(1)

    path = '{0}.{1}.txt'.format(data_dir, name)
    with open(path, 'wb') as out_file:
        for username in usernames:
            out_file.write(username)
            out_file.write('\n')


def search(url):
    headers = {
        'User-Agent': USER_AGENT
    }

    while True:
        try:
            request = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(request)
            content = response.read()
        except urllib2.HTTPError as error:
            status_code = error.code
            content = error.read()
        else:
            status_code = response.getcode()

        if status_code != 200:
            print('Yahooed! (Error {0}). Sleeping.'.format(status_code))
            time.sleep(120)
        else:
            return content


if __name__ == '__main__':
    if os.environ.get('SCRAPER_BIND_ADDRESS'):
        # http://stackoverflow.com/questions/1150332/source-interface-with-python-and-urllib2
        sourceIP = os.environ['SCRAPER_BIND_ADDRESS']
        import socket
        true_socket = socket.socket

        def bound_socket(*a, **k):
            sock = true_socket(*a, **k)
            sock.bind((sourceIP, 0))
            return sock
        socket.socket = bound_socket

        print('+' * 20)
        print('Scraper will bind to IP address', sourceIP)
        print('+' * 20)

    query = sys.argv[1]
    data_dir = sys.argv[2]

    if query.startswith('=PUNY='):
        print('Depuny', query, query[6:])
        query = query[6:].decode('punycode').encode('utf8')
        print('Depuny result', query)

    main(query, data_dir)
